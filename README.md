# Fahrdienst-Disposition

Webanwendung zur Disposition von Fahrdiensten im Sicherheitsbereich eines Großzeltlagers.

## Projektstruktur

```
docs/
├── konzept.md          Fachlicher Kontext, Rollen, Workflows, Auftragstypen
├── datenmodell.md      Datenbankschema, Tabellen, Felder, Enums
├── konfiguration.md    Globale App-Einstellungen
└── ui/
    ├── disponent.md    UI-Konzept Desktop (Disponenten-Ansicht)
    └── fahrer.md       UI-Konzept Mobile (Fahrer-Ansicht)
```

## Technischer Stack (geplant)

- **Frontend:** Responsive Web-App (Desktop + Mobile)
- **Backend:** Node.js oder Python (REST API)
- **Datenbank:** PostgreSQL (zentral, vorhanden)
- **Authentifizierung:** OAuth 2.0 / OIDC via Keycloak
- **Deployment:** Internet-erreichbare Infrastruktur (vorhanden)

## Status

Konzeptionsphase abgeschlossen. Nächste Schritte:

- [ ] API-Endpunkte definieren
- [ ] Technologie-Entscheidung Backend
- [ ] Datenbankschema als SQL-Migration
- [ ] Implementierung
