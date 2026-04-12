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

## Technischer Stack (geplant)

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
- [ ] Implementierung
