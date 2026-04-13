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
| Keycloak Admin | http://localhost:8080 (admin / admin) |

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

Konzeptionsphase abgeschlossen. Nächste Schritte:

- [x] API-Endpunkte definieren
- [x] Technologie-Entscheidung Backend
- [x] Datenbankschema als SQL-Migration
- [x] Implementierung
- [x] Docker-Compose Entwicklungsumgebung
