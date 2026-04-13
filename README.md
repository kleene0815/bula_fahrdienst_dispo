# Fahrdienst-Disposition

Webanwendung zur Disposition von Fahrdiensten im Sicherheitsbereich eines Großzeltlagers.

## Projektstruktur

```
docs/
├── konzept.md          Fachlicher Kontext, Rollen, Workflows, Auftragstypen
├── datenmodell.md      Datenbankschema, Tabellen, Felder, Enums
├── konfiguration.md    Globale App-Einstellungen
├── cadenza.md          Cadenza-Integration (Embedding, Karte, Auswertungen)
└── ui/
    ├── disponent.md    UI-Konzept Desktop (Disponenten-Ansicht)
    └── fahrer.md       UI-Konzept Mobile (Fahrer-Ansicht)
```

## Lokale Entwicklungsumgebung

### Voraussetzungen

- Docker + Docker Compose

### Starten

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API + Docs | http://localhost:8000/docs |
| Keycloak Admin | http://localhost:8088 (admin / admin) |

Die Datenbank-Migrationen werden beim Backend-Start automatisch ausgeführt.

### Testnutzer

| Benutzername | Passwort | Rollen |
|---|---|---|
| `disponent` | `disponent` | Disponent |
| `fahrer` | `fahrer` | Fahrer |
| `beides` | `beides` | Disponent + Fahrer |

### Neu starten (inkl. Datenbankinhalt löschen)

```bash
docker compose down -v && docker compose up --build
```

---

## Technischer Stack

- **Frontend:** Vue 3 + Vite
- **Backend:** Python / FastAPI + SQLAlchemy (async) + Alembic
- **Datenbank:** PostgreSQL (zentral, vorhanden)
- **Authentifizierung:** OAuth 2.0 / OIDC via Keycloak
- **Echtzeit:** Server-Sent Events (SSE)
- **Cadenza-Integration:** Cadenza.js (`@disy/cadenza.js`) für Embedding und Kartenansicht
- **Deployment:** Internet-erreichbare Infrastruktur (vorhanden)

## Status

Grundimplementierung abgeschlossen und in der Entwicklungsumgebung getestet. Offene Punkte aus dem ersten Testlauf:

### Abgeschlossen

- [x] API-Endpunkte definieren
- [x] Technologie-Entscheidung Backend
- [x] Datenbankschema als SQL-Migration
- [x] Implementierung (Backend + Frontend)
- [x] Docker-Compose Entwicklungsumgebung
- [x] Korrekte initiale Routenweiterleitung (Disponent → Desktop-Ansicht, Fahrer → Mobile-Ansicht)

### Offen (nächste Iteration)

- [ ] **Doppelte Darstellung** von Aufträgen/Fahrten nach dem Anlegen beheben (Deduplizierung zwischen lokalem Push und SSE-Event)
- [ ] **Deadline-UX verbessern:** Datumsauswahl als Schnellauswahl (Heute / Morgen / Datum wählen) + separates Uhrzeitfeld mit konfigurierbarem Standardwert
- [ ] **Standard-Deadline-Uhrzeit** in den App-Einstellungen konfigurierbar machen
- [x] **Prioritäten umbenennen:** `mittel` → `gering`
- [ ] **Fahrtformular (Bearbeitung):** bereits zugeteilte Aufträge der Fahrt im Auftragsfeld anzeigen
- [ ] **Drag & Drop:** Auftragskarten auf Fahrtkarten ziehen; Neue-Fahrt-Ablagezone in der Fahrten-Spalte
- [ ] **Fahrer-Sync aus Keycloak:** Fahrer werden vor dem ersten Login via Keycloak Admin API synchronisiert
