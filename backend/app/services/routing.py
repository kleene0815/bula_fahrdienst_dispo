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
from datetime import datetime, timedelta

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

    # Verweilzeiten je Auftragstyp (in Sekunden)
    def dwell(trip_type: str) -> int:
        attr = STOP_DURATIONS.get(trip_type, "stop_duration_besorgung")
        return getattr(config, attr, 15) * 60

    # Gesamtdauer: alle Fahrsegmente + alle Verweilzeiten
    total_drive_seconds = sum(seg["duration"] for seg in segments)
    total_dwell_seconds = sum(dwell(to.order.trip_type) for to in orders)
    total_seconds = total_drive_seconds + total_dwell_seconds
    trip.estimated_duration_minutes = round(total_seconds / 60)

    # Startzeit: für jeden Stopp frühestmöglichsten Start rückrechnen
    if not trip.start_time_manual_override:
        latest_starts = []
        cumulative_seconds = 0
        for i, to in enumerate(orders):
            cumulative_seconds += segments[i]["duration"]  # Fahrt bis zu diesem Stopp
            # Verweilzeiten aller vorherigen Stopps
            dwell_so_far = sum(dwell(orders[j].order.trip_type) for j in range(i))
            time_to_reach = cumulative_seconds + dwell_so_far
            deadline = to.order.deadline
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline)
            latest_start = deadline - timedelta(seconds=time_to_reach)
            latest_starts.append(latest_start)

        trip.planned_start_time = min(latest_starts).replace(tzinfo=None)
