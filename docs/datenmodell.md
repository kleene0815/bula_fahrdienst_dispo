# Datenmodell

Datenbank: PostgreSQL. Alle Tabellen enthalten `created_at` (und wo sinnvoll `updated_at`) als Zeitstempel. Gelöschte Datensätze werden nicht hart gelöscht (soft delete via `active`-Flag oder Status `storniert` / `abgebrochen`).


## Übersicht

```
users ──< user_roles
users ──< orders          (created_by)
users ──< trips           (driver_id)
users ──< status_log      (changed_by)
vehicles ──< trips        (vehicle_id)
trips ──< trip_orders
orders ──< trip_orders
```


## Tabellen

### `users`

Lokale Spiegelung der Keycloak-Identität. Wird beim ersten Login angelegt und bei Bedarf aktualisiert.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | `uuid` PK | Interner Primärschlüssel |
| `keycloak_sub` | `text` UNIQUE | Subject-ID aus dem JWT (unveränderlich) |
| `name` | `text` | Anzeigename |
| `email` | `text` | E-Mail-Adresse |
| `created_at` | `timestamptz` | Zeitpunkt der ersten Anmeldung |


### `user_roles`

Spiegelung der Keycloak-Rollen. Eine Person kann mehrere Einträge haben.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `user_id` | `uuid` FK → `users.id` | |
| `role` | `text` | Enum: `disponent`, `fahrer` |

Primärschlüssel: `(user_id, role)`


### `vehicles`

Feste und private Fahrzeuge.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | `uuid` PK | |
| `name` | `text` | Bezeichnung, z.B. „VW Bus 1" |
| `license_plate` | `text` UNIQUE | Kennzeichen |
| `seats` | `integer` | Gesamtzahl Sitzplätze inkl. Fahrersitz |
| `type` | `text` | Enum: `fest`, `privat` |
| `active` | `boolean` | `false` = deaktiviert (z.B. Werkstatt) |
| `created_at` | `timestamptz` | |

> **Hinweis:** Ob ein Fahrzeug gerade im Einsatz ist, ergibt sich aus aktiven Fahrten (`trips.status = 'aktiv'`), kein eigenes Status-Feld nötig.


### `orders`

Einzelner Auftrag. Wird ausschließlich vom Disponenten angelegt.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | `uuid` PK | |
| `status` | `text` | Enum: `offen`, `zugeteilt`, `unterwegs`, `erledigt`, `storniert` |
| `priority` | `text` | Enum: `normal`, `mittel`, `hoch` |
| `trip_type` | `text` | Enum: `besorgung`, `hinfahrt`, `abholung` |
| `destination` | `text` | Name des Ziels, z.B. „Apotheke am Markt" |
| `destination_address` | `text` | Adresse des Ziels (Freitext, für Auftragsschein) |
| `destination_type` | `text` | Enum: `apotheke`, `arzt`, `krankenhaus`, `sonstiges` |
| `deadline` | `timestamptz` | Gewünschter Termin oder Deadline |
| `patient_name` | `text` | Name des Patienten (nullable — leer bei Besorgungen) |
| `phone` | `text` | Telefonnummer Patient oder Begleitperson (nullable) |
| `companion` | `boolean` | `true` = Begleitperson fährt mit |
| `notes` | `text` | Bemerkungen für den Fahrer (nullable) |
| `requester_station` | `text` | Auftraggeber, z.B. „Sanistation Nord" (nullable) |
| `created_by` | `uuid` FK → `users.id` | Disponent, der den Auftrag angelegt hat |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

**Sitzplatzberechnung pro Auftrag:**
- `trip_type = 'besorgung'` → 0 Sitze
- `patient_name IS NOT NULL AND companion = false` → 1 Sitz
- `patient_name IS NOT NULL AND companion = true` → 2 Sitze


### `trips`

Eine Fahrt fasst mehrere Aufträge zusammen und wird einem Fahrer und Fahrzeug zugeteilt.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | `uuid` PK | |
| `status` | `text` | Enum: `geplant`, `aktiv`, `abgeschlossen`, `abgebrochen` |
| `driver_id` | `uuid` FK → `users.id` | Zugeteilter Fahrer (nullable bis Zuteilung) |
| `vehicle_id` | `uuid` FK → `vehicles.id` | Zugeteiltes Fahrzeug (nullable bis Zuteilung) |
| `qr_token` | `text` UNIQUE | Kryptografisch sicherer Token für QR-Code-Link |
| `notes` | `text` | Hinweise für den Fahrer (nullable) |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

**QR-Code-URL:** `https://<app>/trip/<qr_token>`
Der Token wird beim Anlegen der Fahrt generiert (32-Byte random hex oder UUID v4).

**Kapazitätsprüfung:**
```
belegte_sitze = 1 (Fahrer)
              + Σ (patient_name IS NOT NULL ? 1 : 0) über alle Aufträge
              + Σ companion über alle Aufträge
```
`belegte_sitze` darf `vehicles.seats` nicht überschreiten.


### `trip_orders`

Verknüpfungstabelle zwischen Fahrten und Aufträgen (n:m).

| Spalte | Typ | Beschreibung |
|---|---|---|
| `trip_id` | `uuid` FK → `trips.id` | |
| `order_id` | `uuid` FK → `orders.id` | |
| `sort_order` | `integer` | Reihenfolge der Stopps innerhalb der Fahrt |

Primärschlüssel: `(trip_id, order_id)`


### `status_log`

Unveränderliches Protokoll aller Statusübergänge — sowohl für Aufträge als auch für Fahrten. Dient der Nachvollziehbarkeit und als Basis für externe Auswertungen direkt auf der Datenbank.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | `uuid` PK | |
| `entity_type` | `text` | `order` oder `trip` |
| `entity_id` | `uuid` | ID des betreffenden Auftrags oder der Fahrt |
| `old_status` | `text` | Status vor dem Übergang (nullable beim ersten Eintrag) |
| `new_status` | `text` | Status nach dem Übergang |
| `changed_by` | `uuid` FK → `users.id` | Benutzer, der den Übergang ausgelöst hat |
| `changed_at` | `timestamptz` | Zeitpunkt des Übergangs |
| `note` | `text` | Optionale Bemerkung zum Übergang (nullable) |

> Auswertungen (z.B. Fahrten pro Tag, häufigste Zielorte) erfolgen extern direkt auf der Datenbank — keine eigene Auswertungs-UI in der App.


### `app_config`

Globale Konfigurationswerte der App. Enthält genau eine Zeile.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | `integer` PK | Immer `1` |
| `security_center_name` | `text` | Name der Sicherheitszentrale |
| `security_center_phone` | `text` | Telefonnummer der Sicherheitszentrale |
| `organizer_name` | `text` | Name des Veranstalters |
| `camp_address` | `text` | Adresse des Lagerplatzes |
| `updated_at` | `timestamptz` | |
