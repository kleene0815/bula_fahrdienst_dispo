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
- [x] Doppelte Darstellung: von Aufträgen/Fahrten nach dem Anlegen beheben (Deduplizierung zwischen lokalem Push und SSE-Event)
- [x] Deadline-UX verbessern: Datumsauswahl als Schnellauswahl (Heute / Morgen / Datum wählen) + separates Uhrzeitfeld mit konfigurierbarem Standardwert
- [x] Standard-Deadline-Uhrzeit: in den App-Einstellungen konfigurierbar machen
- [x] Prioritäten umbenennen: `mittel` → `gering`
- [x] Fahrtformular (Bearbeitung): bereits zugeteilte Aufträge der Fahrt im Auftragsfeld anzeigen
- [x] Drag & Drop: Auftragskarten auf Fahrtkarten ziehen; Neue-Fahrt-Ablagezone in der Fahrten-Spalte
- [x] Fahrer-Sync aus Keycloak: Fahrer werden vor dem ersten Login via Keycloak Admin API synchronisiert

### Offene Änderungswünsche
- [ ] In der Auftragsübersicht soll der Typ des Auftrags (Besorgung, Abholung, Hinfahrt) angezeigt werden, stattdessen muss die AuftragsID nicht angezeigt werden.
- [ ] Auftragsübersicht: Buttons für Bearbeiten und Stornieren sind zu präsent. Besser durch Icons ersetzen. Der Bearbeiten-Button sollte mehr auffallen, weil dieser häufiger benutzt wird.
- [ ] Fahrtenübersicht Disponent: Buttons durch Icons ersetzen. Abbrechen sollte weniger präsent sein. 
- [ ] Beim Abbrechen einer Fahrt oder Stornieren eines Auftrags sollte noch eine Abfrage kommen, dass man sich nicht versehentlich verklickt.
- [ ] Eine Fahrt soll optional einen Namen haben können. Wird kein Name angegeben, soll der Name "Fahrt #<id>" lauten.
- [ ] Eine Fahrt soll auch ohne Fahrer und ohne Fahrzeug gespeichert werden können. Dies sollte in der Übersicht dann aber kenntlich gemacht werden, dass hier noch ein Fahrer bzw. ein Fahrzeug fehlt.
- [ ] Wenn man mit der Maus über einen Auftrag fährt, der nicht mehr offen ist, dann soll man am Mauszeiger klar erkennen, dass man den Auftrag nicht mehr per Drag & Drop verschieben kann.
- [ ] Bei Aufträgen in einer Fahrt soll die Reihenfolge manuell festgelegt werden können.
- [ ] Aufträge, die schon einer Fahrt zugeordnet sind, die noch nicht gestartet ist, sollen per Drag & Drop in eine andere Fahrt verschoben werden können.

### Bugs
- [ ] Aufträge mit Priorität gering können nicht erstellt werden. "Mittel" soll die Standard-Priorität sein.