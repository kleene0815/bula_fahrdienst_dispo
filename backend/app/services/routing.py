"""
OpenRouteService-Integration für Fahrtdauer- und Startzeitberechnung.

Ablauf:
  1. Lagerplatz-Adresse + alle Stopp-Adressen per ORS Geocoding → Koordinaten
  2. ORS Directions API: Camp → Stopp1 → … → StoppN → Camp
  3. Segment-Dauern + Stop-Verweilzeiten → Gesamtdauer + Startzeit je Stopp
  4. planned_start_time = min(Deadline_i − kumulative_Zeit_bis_Stopp_i)
  5. Verbleibende Requests aus Response-Header speichern; bei < 200 → manual
"""

import logging
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

_LOCAL_TZ = ZoneInfo("Europe/Berlin")

import httpx

logger = logging.getLogger(__name__)

ORS_BASE = "https://api.openrouteservice.org"

STOP_DURATIONS = {
    "hinfahrt": "stop_duration_hinfahrt",
    "abholung": "stop_duration_abholung",
    "besorgung": "stop_duration_besorgung",
}


async def geocode(address: str, api_key: str) -> tuple[float, float]:
    """Gibt (lon, lat) zurück oder wirft ValueError."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{ORS_BASE}/geocode/search",
            params={"api_key": api_key, "text": address, "size": 1},
        )
        resp.raise_for_status()
    features = resp.json().get("features", [])
    if not features:
        raise ValueError(f"Keine Koordinaten für: {address!r}")
    coords = features[0]["geometry"]["coordinates"]  # [lon, lat]
    return coords[0], coords[1]


async def calculate_route_for_trip(trip, config, db) -> None:
    """
    Berechnet estimated_duration_minutes und planned_start_time für die Fahrt.
    Schreibt Ergebnis direkt auf das Trip-Objekt und aktualisiert routing_remaining_requests.
    Wirft bei jedem Fehler eine Exception — Aufrufer setzt dann beide Felder auf None.
    """
    from app.models import AppConfig  # lokaler Import vermeidet Zirkel

    api_key = config.routing_api_key
    if not api_key:
        raise ValueError("Kein API-Key konfiguriert")

    orders = sorted(trip.trip_orders, key=lambda to: to.sort_order)
    if not orders:
        raise ValueError("Keine Aufträge in der Fahrt")

    # Adressen zusammenbauen
    camp_addr = config.camp_address
    if not camp_addr:
        raise ValueError("Keine Lageradresse konfiguriert")

    stop_addresses = []
    for to in orders:
        o = to.order
        parts = [p for p in [o.destination_street, o.destination_city] if p]
        if not parts:
            raise ValueError(f"Auftrag {o.id} hat keine vollständige Adresse")
        stop_addresses.append(", ".join(parts))

    # Geocoding
    camp_coord = await geocode(camp_addr, api_key)
    stop_coords = []
    for addr in stop_addresses:
        stop_coords.append(await geocode(addr, api_key))

    # Koordinaten-Liste: Camp → Stopps → Camp
    coordinates = [list(camp_coord)] + [list(c) for c in stop_coords] + [list(camp_coord)]

    # ORS Directions
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{ORS_BASE}/v2/directions/driving-car",
            headers={"Authorization": api_key, "Content-Type": "application/json"},
            json={"coordinates": coordinates, "units": "m"},
        )
        resp.raise_for_status()

    # Verbleibende Requests speichern
    remaining = resp.headers.get("X-RateLimit-Remaining")
    if remaining is not None:
        remaining_int = int(remaining)
        config.routing_remaining_requests = remaining_int
        if remaining_int < 200:
            config.routing_mode = "manual"
        await db.flush()

    data = resp.json()
    segments = data["routes"][0]["segments"]
    # segments[0] = Camp→Stopp1, segments[1] = Stopp1→Stopp2, ..., segments[-1] = StoppN→Camp

    # Debug-Ausgabe der Teilrouten
    waypoint_labels = ["Lager"] + [to.order.destination for to in orders] + ["Lager"]
    for i, seg in enumerate(segments):
        logger.debug(
            "Segment %d: %s → %s  %.1f min  %.1f km",
            i,
            waypoint_labels[i],
            waypoint_labels[i + 1],
            seg["duration"] / 60,
            seg["distance"] / 1000,
        )

    # Verweilzeiten je Auftragstyp (in Sekunden)
    def dwell(trip_type: str) -> int:
        attr = STOP_DURATIONS.get(trip_type, "stop_duration_besorgung")
        return getattr(config, attr, 15) * 60

    # Gesamtdauer: alle Fahrsegmente + alle Verweilzeiten + Puffer
    buffer_minutes = getattr(config, "routing_buffer_minutes", 0) or 0
    total_drive_seconds = sum(seg["duration"] for seg in segments)
    total_dwell_seconds = sum(dwell(to.order.trip_type) for to in orders)
    total_minutes_raw = total_drive_seconds / 60 + total_dwell_seconds / 60 + buffer_minutes
    # Dauer auf 5 Minuten aufrunden
    trip.estimated_duration_minutes = math.ceil(total_minutes_raw / 5) * 5

    # Startzeit: rückwärts planen vom letzten Stopp
    # latest_arrival[i] = spätester Ankunftszeitpunkt bei Stopp i, der alle
    # nachfolgenden Deadlines noch einhält. Aufträge ohne Deadline (z.B.
    # erwartete Rückfahrten) liefern keine Beschränkung.
    if not trip.start_time_manual_override:
        n = len(orders)

        def normalize(dt) -> datetime | None:
            if dt is None:
                return None
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            return dt

        latest_arrival: list[datetime | None] = [None] * n

        # Letzter Stopp: nur durch eigene Deadline beschränkt
        latest_arrival[n - 1] = normalize(orders[n - 1].order.deadline)

        # Rückwärts: jeder Stopp ist durch seine Deadline UND die Abfahrtszeit
        # zum nächsten Stopp beschränkt (Verweilzeit + Fahrt)
        for i in range(n - 2, -1, -1):
            # segments[i+1] = Fahrt von Stopp i zu Stopp i+1
            drive_to_next = segments[i + 1]["duration"]
            dwell_here = dwell(orders[i].order.trip_type)
            constraint_from_next = (
                latest_arrival[i + 1] - timedelta(seconds=dwell_here + drive_to_next)
                if latest_arrival[i + 1] is not None
                else None
            )
            own_deadline = normalize(orders[i].order.deadline)
            candidates = [c for c in (own_deadline, constraint_from_next) if c is not None]
            latest_arrival[i] = min(candidates) if candidates else None

        now_local = datetime.now(_LOCAL_TZ).replace(second=0, microsecond=0, tzinfo=None)

        if latest_arrival[0] is not None:
            # Startzeit: späteste Ankunft bei Stopp 0 minus Fahrt vom Lager minus Puffer
            # Auf 5 Minuten abrunden, UTC → Europe/Berlin, tzinfo entfernen
            raw_start = (
                latest_arrival[0]
                - timedelta(seconds=segments[0]["duration"])
                - timedelta(minutes=buffer_minutes)
            ).astimezone(_LOCAL_TZ).replace(tzinfo=None)
            floored_minutes = (raw_start.minute // 5) * 5
            raw_start = raw_start.replace(minute=floored_minutes, second=0, microsecond=0)
        else:
            # Kein Stopp hat eine Deadline — Start ab jetzt
            raw_start = now_local

        # Eine berechnete Startzeit darf nie in der Vergangenheit liegen
        trip.planned_start_time = max(raw_start, now_local)
