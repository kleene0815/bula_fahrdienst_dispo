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
- [x] In der Auftragsübersicht soll der Typ des Auftrags (Besorgung, Abholung, Hinfahrt) angezeigt werden, stattdessen muss die AuftragsID nicht angezeigt werden.
- [x] Auftragsübersicht: Buttons für Bearbeiten und Stornieren sind zu präsent. Besser durch Icons ersetzen. Der Bearbeiten-Button sollte mehr auffallen, weil dieser häufiger benutzt wird.
- [x] Fahrtenübersicht Disponent: Buttons durch Icons ersetzen. Abbrechen sollte weniger präsent sein. 
- [x] Beim Abbrechen einer Fahrt oder Stornieren eines Auftrags sollte noch eine Abfrage kommen, dass man sich nicht versehentlich verklickt.
- [x] Eine Fahrt soll optional einen Namen haben können. Wird kein Name angegeben, soll der Name "Fahrt #<id>" lauten.
- [x] Eine Fahrt soll auch ohne Fahrer und ohne Fahrzeug gespeichert werden können. Dies sollte in der Übersicht dann aber kenntlich gemacht werden, dass hier noch ein Fahrer bzw. ein Fahrzeug fehlt.
- [x] Wenn man mit der Maus über einen Auftrag fährt, der nicht mehr offen ist, dann soll man am Mauszeiger klar erkennen, dass man den Auftrag nicht mehr per Drag & Drop verschieben kann.
- [x] Bei Aufträgen in einer Fahrt soll die Reihenfolge manuell festgelegt werden können.
- [x] Aufträge, die schon einer Fahrt zugeordnet sind, die noch nicht gestartet ist, sollen per Drag & Drop in eine andere Fahrt verschoben werden können.

### Offene Änderungswünsche 
- [x] Auftragsschein abändern:
  - Überschriftszeile: `Auftragsschein - <Name der Fahrt>`
  - Die Felder aus der Konfiguration ersetzen durch eine Box, die z.B. durch ein HTML-Template in der Konfiguration gefüllt werden kann.
  - Die Fahrtnummer kann entfallen.
  - Anstatt Termin sollte immer Termin/Deadline stehen.
  - Die Fahrtnummer auf den Patientenbegleitscheinen können auch entfallen.
- [x] Möglichkeit schaffen, schon begonnenen Fahrten neue Aufträge hinzuzufügen. (Fahrer-Ansicht muss dann den neuen Auftrag klar kennzeichnen)
- [x] Liste mit gängigen Zielen einführen, die dann automatisch beim erstellen eines Auftrags beim Tippen vorgeschlagen werden.
- [x] ungefähre Dauer der Fahrt berechnen (automatische Abfrage am Routenplaner, z.B. Google-Maps)
- [x] Startzeitpunkt der Fahrt aus Fahrtdauer zum Ziel automatisch ermitteln, Startzeit muss aber anpassbar sein.
- [ ] Warnen, wenn zwei Fahrten sich zeitlich überschneiden, aber das gleiche Auto oder den gleichen Fahrer nutzen.

### Bugs
- [x] In der Druckansicht für Fahrten passiert beim Klick auf den Drucken-Button gar nichts. Es gibt auch keine Fehlermeldung.
- [x] Benutzer, die sowohl Fahrer als auch Disponent sind, können die Fahrer-Sicht nicht aufrufen.