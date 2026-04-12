-- Migration 001: Initiales Schema
-- Datenbank: PostgreSQL 13+
-- gen_random_uuid() ist ab PostgreSQL 13 ohne Extension verfügbar.

BEGIN;

-- ---------------------------------------------------------------------------
-- users
-- Lokale Spiegelung der Keycloak-Identität. Wird beim ersten Login angelegt.
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id            uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_sub  text        NOT NULL UNIQUE,
    name          text        NOT NULL,
    email         text        NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- user_roles
-- Spiegelung der Keycloak-Rollen. Eine Person kann mehrere Einträge haben.
-- ---------------------------------------------------------------------------
CREATE TABLE user_roles (
    user_id  uuid  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role     text  NOT NULL CHECK (role IN ('disponent', 'fahrer')),
    PRIMARY KEY (user_id, role)
);

-- ---------------------------------------------------------------------------
-- vehicles
-- ---------------------------------------------------------------------------
CREATE TABLE vehicles (
    id            uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    name          text        NOT NULL,
    license_plate text        NOT NULL UNIQUE,
    seats         integer     NOT NULL CHECK (seats >= 1),
    type          text        NOT NULL CHECK (type IN ('fest', 'privat')),
    active        boolean     NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- orders
-- ---------------------------------------------------------------------------
CREATE TABLE orders (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    status              text        NOT NULL DEFAULT 'offen'
                                    CHECK (status IN ('offen', 'zugeteilt', 'unterwegs', 'erledigt', 'storniert')),
    priority            text        NOT NULL DEFAULT 'normal'
                                    CHECK (priority IN ('normal', 'mittel', 'hoch')),
    trip_type           text        NOT NULL
                                    CHECK (trip_type IN ('besorgung', 'hinfahrt', 'abholung')),
    destination         text        NOT NULL,
    destination_address text,
    destination_type    text        NOT NULL
                                    CHECK (destination_type IN ('apotheke', 'arzt', 'krankenhaus', 'sonstiges')),
    deadline            timestamptz NOT NULL,
    patient_name        text,
    phone               text,
    companion           boolean     NOT NULL DEFAULT false,
    notes               text,
    requester_station   text,
    created_by          uuid        NOT NULL REFERENCES users(id),
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

-- Patient-Konsistenz: Begleitperson nur sinnvoll wenn Patient angegeben
ALTER TABLE orders ADD CONSTRAINT orders_companion_requires_patient
    CHECK (companion = false OR patient_name IS NOT NULL);

-- ---------------------------------------------------------------------------
-- trips
-- ---------------------------------------------------------------------------
CREATE TABLE trips (
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_number  integer     NOT NULL GENERATED ALWAYS AS IDENTITY,
    status       text        NOT NULL DEFAULT 'geplant'
                             CHECK (status IN ('geplant', 'aktiv', 'abgeschlossen', 'abgebrochen')),
    driver_id    uuid        REFERENCES users(id),
    vehicle_id   uuid        REFERENCES vehicles(id),
    qr_token     text        NOT NULL UNIQUE,
    notes        text,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- trip_orders
-- Verknüpfungstabelle Fahrten <-> Aufträge mit Stoppreihenfolge
-- ---------------------------------------------------------------------------
CREATE TABLE trip_orders (
    trip_id     uuid     NOT NULL REFERENCES trips(id)  ON DELETE CASCADE,
    order_id    uuid     NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    sort_order  integer  NOT NULL,
    PRIMARY KEY (trip_id, order_id)
);

-- Ein Auftrag darf nur in einer aktiven Fahrt sein
-- (wird per Applikationslogik sichergestellt, nicht per DB-Constraint,
--  da stornierte/abgebrochene Fahrten historisch erhalten bleiben)

-- ---------------------------------------------------------------------------
-- status_log
-- Unveränderliches Protokoll aller Statusübergänge
-- ---------------------------------------------------------------------------
CREATE TABLE status_log (
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type  text        NOT NULL CHECK (entity_type IN ('order', 'trip')),
    entity_id    uuid        NOT NULL,
    old_status   text,
    new_status   text        NOT NULL,
    changed_by   uuid        NOT NULL REFERENCES users(id),
    changed_at   timestamptz NOT NULL DEFAULT now(),
    note         text
);

-- ---------------------------------------------------------------------------
-- app_config
-- Genau eine Zeile (id = 1), wird per INSERT initialisiert.
-- ---------------------------------------------------------------------------
CREATE TABLE app_config (
    id                    integer     PRIMARY KEY CHECK (id = 1),
    security_center_name  text        NOT NULL DEFAULT '',
    security_center_phone text        NOT NULL DEFAULT '',
    organizer_name        text        NOT NULL DEFAULT '',
    camp_address          text        NOT NULL DEFAULT '',
    updated_at            timestamptz NOT NULL DEFAULT now()
);

-- Initiale Zeile anlegen (Werte werden über die Einstellungsseite befüllt)
INSERT INTO app_config (id) VALUES (1);

-- ---------------------------------------------------------------------------
-- Indizes
-- ---------------------------------------------------------------------------

-- Aufträge: häufige Filter- und Sortieroperationen
CREATE INDEX idx_orders_status     ON orders (status);
CREATE INDEX idx_orders_deadline   ON orders (deadline);
CREATE INDEX idx_orders_created_by ON orders (created_by);

-- Fahrten: häufige Lookups
CREATE INDEX idx_trips_status     ON trips (status);
CREATE INDEX idx_trips_driver_id  ON trips (driver_id);
CREATE INDEX idx_trips_qr_token   ON trips (qr_token);  -- UNIQUE erzeugt bereits Index, explizit zur Klarheit weggelassen

-- Status-Log: Abfragen nach Entity
CREATE INDEX idx_status_log_entity ON status_log (entity_type, entity_id);
CREATE INDEX idx_status_log_time   ON status_log (changed_at);

COMMIT;
