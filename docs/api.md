# API-Endpunkte

Alle Endpunkte unter `/api/v1/`. Authentifizierung via Bearer-Token (JWT aus Keycloak) im `Authorization`-Header. Nicht authentifizierte Anfragen werden mit `401` abgelehnt, fehlende Berechtigung mit `403`.

Fehlerformat (alle Fehler):
```json
{ "detail": "Beschreibung des Fehlers" }
```


## Rollen

| Rolle | Kürzel |
|---|---|
| `disponent` | D |
| `fahrer` | F |
| beide | D+F |


---

## Benutzer

### `GET /api/v1/me`
Gibt den aktuell angemeldeten Benutzer zurück. Wird beim App-Start aufgerufen, um Rollen und Anzeigename zu laden.

**Berechtigung:** D+F

**Response:**
```json
{
  "id": "uuid",
  "name": "Max Mustermann",
  "email": "max@example.com",
  "roles": ["disponent", "fahrer"]
}
```

---

### `GET /api/v1/users`
Liste aller Benutzer mit Rolle `fahrer`. Wird im Fahrtformular für die Fahrerauswahl benötigt.

Vor der Rückgabe werden Nutzer mit den Rollen `fahrer` oder `disponent` über die Keycloak Admin API abgerufen und in der lokalen DB synchronisiert — damit stehen Fahrer bereits vor ihrem ersten Login zur Auswahl.

**Berechtigung:** D

**Response:**
```json
[
  { "id": "uuid", "name": "Max Mustermann", "roles": ["fahrer"] }
]
```

---

## Aufträge

### `GET /api/v1/orders`
Liste aller Aufträge, sortiert nach Deadline aufsteigend.

**Berechtigung:** D

**Query-Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `status` | string | Filter: `offen`, `zugeteilt`, `unterwegs`, `erledigt`, `storniert` |

**Response:** Array von Auftragsobjekten (siehe unten).

---

### `POST /api/v1/orders`
Neuen Auftrag anlegen.

**Berechtigung:** D

**Request Body:**
```json
{
  "trip_type": "hinfahrt",
  "destination_type": "arzt",
  "destination": "Dr. Müller",
  "destination_address": "Hauptstraße 1, 12345 Musterstadt",
  "deadline": "2026-07-15T10:00:00Z",
  "priority": "normal",  // gering | normal | hoch
  "patient_name": "Anna Schmidt",
  "phone": "0721 123456",
  "companion": false,
  "notes": "Bitte pünktlich",
  "requester_station": "Sanistation Nord"
}
```

Pflichtfelder: `trip_type`, `destination_type`, `destination`, `deadline`, `priority`.

**Response:** `201` + angelegter Auftrag.

---

### `GET /api/v1/orders/{order_id}`
Einzelnen Auftrag abrufen.

**Berechtigung:** D

**Response:** Auftragsobjekt.

---

### `PATCH /api/v1/orders/{order_id}`
Auftrag bearbeiten. Nur möglich solange `status = offen` oder `zugeteilt`.

**Berechtigung:** D

**Request Body:** Beliebige Teilmenge der schreibbaren Felder aus POST (außer `status`).

**Response:** Aktualisierter Auftrag.

---

### `POST /api/v1/orders/{order_id}/cancel`
Auftrag stornieren. Setzt `status → storniert`. Entfernt den Auftrag ggf. aus einer Fahrt.

**Berechtigung:** D

**Response:** `200` + aktualisierter Auftrag.

---

### Auftragsobjekt (Referenz)
```json
{
  "id": "uuid",
  "status": "offen",
  "priority": "normal",  // gering | normal | hoch
  "trip_type": "hinfahrt",
  "destination": "Dr. Müller",
  "destination_address": "Hauptstraße 1",
  "destination_type": "arzt",
  "deadline": "2026-07-15T10:00:00Z",
  "patient_name": "Anna Schmidt",
  "phone": "0721 123456",
  "companion": false,
  "notes": "Bitte pünktlich",
  "requester_station": "Sanistation Nord",
  "created_by": "uuid",
  "created_at": "2026-07-15T08:00:00Z",
  "updated_at": "2026-07-15T08:00:00Z"
}
```

---

## Fahrten

### `GET /api/v1/trips`
Liste aller Fahrten.

**Berechtigung:** D — gibt alle Fahrten zurück (Standard: nur `geplant` und `aktiv`).

**Query-Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `status` | string | Filter: `geplant`, `aktiv`, `abgeschlossen`, `abgebrochen` |
| `include_completed` | boolean | `true` = auch abgeschlossene/abgebrochene einschließen (default: `false`) |

**Response:** Array von Fahrtobjekten.

---

### `GET /api/v1/trips/mine`
Eigene Fahrten des angemeldeten Fahrers. Gibt `geplant` und `aktiv` zurück.

**Berechtigung:** F

**Response:** Array von Fahrtobjekten (mit aufgelösten Auftragsdaten).

---

### `POST /api/v1/trips`
Neue Fahrt anlegen.

**Berechtigung:** D

**Request Body:**
```json
{
  "driver_id": "uuid",
  "vehicle_id": "uuid",
  "order_ids": ["uuid", "uuid"],
  "notes": "Hinweis für den Fahrer"
}
```

Pflichtfelder: `driver_id`, `vehicle_id`, `order_ids` (mindestens 1).

Validierung:
- Alle `order_ids` müssen `status = offen` haben
- Kapazitätsprüfung (belegte Sitze ≤ `vehicles.seats`)

**Response:** `201` + Fahrtobjekt. Betroffene Aufträge wechseln auf `status = zugeteilt`.

---

### `GET /api/v1/trips/{trip_id}`
Einzelne Fahrt abrufen, inkl. aller zugehörigen Aufträge in `sort_order`.

**Berechtigung:** D, oder F wenn `driver_id = aktueller Nutzer`.

**Response:** Fahrtobjekt mit `orders`-Array.

---

### `GET /api/v1/trips/by-token/{qr_token}`
Fahrt anhand des QR-Code-Tokens abrufen. Wird nach dem QR-Code-Scan und OIDC-Login aufgerufen.

**Berechtigung:** D+F (jeder authentifizierte Nutzer — der QR-Code ist nicht rollengebunden)

**Response:** Fahrtobjekt. Weiterleitung zur Fahrer- oder Disponenten-Ansicht erfolgt im Frontend anhand der Rollen.

---

### `PATCH /api/v1/trips/{trip_id}`
Fahrt bearbeiten (Fahrer, Fahrzeug, Bemerkungen, Reihenfolge der Stopps). Nur möglich solange `status = geplant`.

**Berechtigung:** D

**Request Body:**
```json
{
  "driver_id": "uuid",
  "vehicle_id": "uuid",
  "notes": "Aktualisierter Hinweis",
  "order_ids": ["uuid", "uuid"]
}
```

`order_ids` ersetzt die vollständige Liste der Aufträge (inkl. neuer Reihenfolge). Aufträge, die entfernt werden, wechseln zurück auf `status = offen`.

**Response:** Aktualisiertes Fahrtobjekt.

---

### `POST /api/v1/trips/{trip_id}/start`
Fahrt starten. Setzt Fahrt auf `aktiv`, alle Aufträge auf `unterwegs`.

**Berechtigung:** F (nur eigene Fahrt), D

Nur möglich wenn `status = geplant`.

**Response:** `200` + aktualisiertes Fahrtobjekt.

---

### `POST /api/v1/trips/{trip_id}/orders/{order_id}/complete`
Einzelnen Stopp als erledigt markieren. Setzt Auftrag auf `erledigt`.

**Berechtigung:** F (nur eigene Fahrt), D

Nur möglich wenn Fahrt `status = aktiv` und Auftrag `status = unterwegs`.

**Response:** `200` + aktualisierter Auftrag.

---

### `POST /api/v1/trips/{trip_id}/complete`
Fahrt abschließen. Setzt Fahrt auf `abgeschlossen`. Fahrer und Fahrzeug gelten wieder als frei.

**Berechtigung:** F (nur eigene Fahrt), D

Nur möglich wenn `status = aktiv`. Alle Aufträge müssen `status = erledigt` haben.

**Response:** `200` + aktualisiertes Fahrtobjekt.

---

### `POST /api/v1/trips/{trip_id}/abort`
Fahrt abbrechen. Setzt Fahrt auf `abgebrochen`.

**Berechtigung:** D

Nur möglich wenn `status = geplant` oder `aktiv`.

**Response:** `200` + aktualisiertes Fahrtobjekt.

---

### Fahrtobjekt (Referenz)
```json
{
  "id": "uuid",
  "trip_number": 42,
  "status": "geplant",
  "driver": { "id": "uuid", "name": "Max Mustermann" },
  "vehicle": { "id": "uuid", "name": "VW Bus 1", "license_plate": "KA-AB 123", "seats": 8 },
  "qr_token": "abc123...",
  "notes": "Hinweis",
  "orders": [
    { "sort_order": 1, ...Auftragsobjekt },
    { "sort_order": 2, ...Auftragsobjekt }
  ],
  "created_at": "2026-07-15T08:00:00Z",
  "updated_at": "2026-07-15T08:00:00Z"
}
```

---

## Fahrzeuge

### `GET /api/v1/vehicles`
Liste aller Fahrzeuge.

**Berechtigung:** D

**Query-Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `active_only` | boolean | `true` = nur aktive Fahrzeuge (default: `true`) |

**Response:** Array von Fahrzeugobjekten.

---

### `POST /api/v1/vehicles`
Neues Fahrzeug anlegen.

**Berechtigung:** D

**Request Body:**
```json
{
  "name": "VW Bus 1",
  "license_plate": "KA-AB 123",
  "seats": 8,
  "type": "fest"
}
```

**Response:** `201` + Fahrzeugobjekt.

---

### `PATCH /api/v1/vehicles/{vehicle_id}`
Fahrzeug bearbeiten oder deaktivieren (`active: false`).

**Berechtigung:** D

**Request Body:** Beliebige Teilmenge der Felder inkl. `active`.

**Response:** Aktualisiertes Fahrzeugobjekt.

---

## App-Konfiguration

### `GET /api/v1/config`
Globale App-Konfiguration abrufen.

**Berechtigung:** D

**Response:**
```json
{
  "security_center_name": "Sicherheitszentrale Zeltlager",
  "security_center_phone": "0721 / 555 100",
  "organizer_name": "DLRG Ortsgruppe Muster",
  "camp_address": "Festwiese Nord, Musterstadt",
  "default_deadline_time": "10:00"
}
```

---

### `PUT /api/v1/config`
Globale App-Konfiguration speichern (überschreibt alle Felder).

**Berechtigung:** D

**Request Body:** Alle fünf Felder aus GET (alle Pflicht).

**Response:** `200` + aktualisierte Konfiguration.

---

## Echtzeit (SSE)

### `GET /api/v1/events`
Server-Sent Events Stream. Der Disponent abonniert diesen Endpunkt beim Laden der Hauptansicht. Der Server sendet Events bei Statusänderungen von Aufträgen und Fahrten.

**Berechtigung:** D

**Event-Format:**
```
event: order_updated
data: {"id": "uuid", "status": "zugeteilt", ...}

event: trip_updated
data: {"id": "uuid", "status": "aktiv", ...}

event: order_created
data: {"id": "uuid", ...}
```

**Hinweis:** Der Client reconnectet automatisch (Browser-Verhalten bei SSE). Kein gesonderter Reconnect-Mechanismus nötig.

---

## Auftragsschein (Druckansicht)

### `GET /api/v1/trips/{trip_id}/printout`
Alle Daten für den Auftragsschein in einem Aufruf: Fahrtdaten, Aufträge in Reihenfolge, Fahrzeug, Fahrer und globale Konfiguration (für Patientenabschnitt).

**Berechtigung:** D

**Response:**
```json
{
  "trip": { ...Fahrtobjekt },
  "config": { ...App-Konfiguration }
}
```

> Die Druckansicht selbst ist eine reine Frontend-Komponente (CSS `@media print`). Dieser Endpunkt liefert nur die Daten.
