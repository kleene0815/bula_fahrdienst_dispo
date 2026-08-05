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
- [x] Warnen, wenn zwei Fahrten sich zeitlich überschneiden, aber das gleiche Auto oder den gleichen Fahrer nutzen.
- [x] In der Dispo-Ansicht sollte bei der Auftragsliste der Standart-Filter "Offen" sein.
- [x] In der Fahrtenliste sollte es auch die möglichkeit geben, abgeschlossene Fahrten anzuzeigen.
- [x] Des Disponent sollte die Möglichkeit haben, in die Fahrer-Ansicht einer beliebigen Fahrt zu wechseln um in Vertretung für den Fahrer Ziele zu erledigen, oder die gesamte Fahrt als erledigt zu markieren
- [x] Auch für nicht mehr offene Aufträge sollte eine Detail-Maske sichtbar sein, ähnlich wie der Erstellen-Dialog, allerdings nicht mehr editierbar.
- [x] Bei Hinfahrten, soll es die Möglichkeit geben, direkt auch die Rückfahrt vorzumerken
  - Es soll bei Erstellung einer Hinfahrt eine Checkbox geben, die default an ist. Wenn diese an ist, soll bei abgeschlossenem Auftrag automatisch eine Abholung als Auftrag angelegt werden
  - Der neue Auftrag soll zunächst in einem neuen Status "erwartete Rückfahrt" sein. Ansonsten soll der Status gleich behandelt werden, wie der Status offen.
  - Die automatisch angelegte Rückfahrt hat zunächst keine Deadline; sie kann trotzdem einer Fahrt zugeteilt werden, die Deadline lässt sich jederzeit im Auftrag nachtragen.
- [x] Des Disponent soll die Möglichkeit haben, eine Fahrt abzuschließen, auch wenn nicht alle Aufträge erledigt sind. Dann soll eine Rückfrage kommen, ob die Aufträge alle abgeschlossen werden sollen.
- [x] Eine berechnete Startzeit darf nie in der Vergangenheit liegen. Aufträge, deren Deadline in der Vergangenheit liegen oder Fahrten deren Startzeitpunkt in der Vergangenheit liegen, die aber noch nicht gestartet sind, sollen leicht rot eingefärbt werden.
- [x] Wenn eine Fahrt nur Aufträge ohne Deadline hat, soll bei der Berechnung der Startzeit einfach die aktuelle Uhrzeit eingetragen werden. Es soll keine Fehlermeldung kommen.
- [x] Bei Filterung der Aufträge nach "Erledigt", sollte immer der zuletzt abgeschlossene Auftrag oben stehen. Ältere Aufträge dann weiter unten. 
- [x] Der Disponent kann eine geplante Fahrt auch direkt aus der Fahrtenübersicht starten (mit Rückfrage).
- [x] Fahrer mit Kontaktdaten hinterlegen
  - Fahrer-Kontaktdaten sollen in der lokalen Datenbank abgelegt werden.
  - Es soll in den Einstellungen durch den Disponenten die Telefonnummer des Fahrers erfasst werden können. In dem Zuge können die Verschiedenen Einstellungs-Abschnitte in unterschiedlichen Seiten/Tabs aufgeteilt werden.
  - In der Fahrer-Ansicht soll, wenn für den Fahrer noch keine Telefonnummer hinterlegt ist, eine rote Box erscheinen, in der der FAhrer seine Telefonnummer angeben kann.
- [x] Geo-Link für Zieladresse, damit auf dem Handy direkt die Navi-App geöffnet werden kann.
- [x] Änderungshistorie für Aufträge und Fahrten (Wer hat wann welchen Status verändert.)
- [x] Beim Auftragsschein soll als letzes Ziel wieder der Lagerplatz angezeigt werden (auch in der Fahrer-Ansicht)
- [] In der Auftragsliste der offenen Aufträge sollen die Aufträge in mehrere Kategorien aufgeteilt werden. Die Kategorien sollen auf- und zugeklaptt werden können. Die Anzahl der enthaltenen Aufträge soll auch im zugeklappten Zustand angezeigt werden:
  - Überfällige Aufträge (Deadline in der Vergangenheit)-> Kategorie darf nicht zugeklappt werden
  - Aktuelle Aufträge (Aufträge mit einer Deadline innerhalb der nächsten 12 Stunden) -> Kategorie inial aufgeklappt
  - zukünftige Aufträge -> Kategorie initial geschlossen
  - Aufträge ohne Deadline -> Kategorie initial geschlossen
- [x] Die Angabe einer Deadline bei Aufträge sollte optional sein, damit man auch Aufträge anlegen kann, bei denen der Ausführungszeitpunkt noch nicht feststeht.
- [] Die Kapazitäts-Berechnung soll umgebaut werden, dass nicht einfach nur die Personen aller Aufträge zusammen gerechnet werden.
  - Die Berechnung der Personenzahlen soll für jeden Fahrtabschnitt berechnet werden. Bei Hinfahrten sollen die Personen vom Start bis zum Zielort einberechnet werden
  - Bei Rückfahrten sollen die Personen vom Zielort bis zurück zum Lagerplatz berechnet werden.
### Offene Änderungswünsche

### Bugs
- [x] In der Druckansicht für Fahrten passiert beim Klick auf den Drucken-Button gar nichts. Es gibt auch keine Fehlermeldung.
- [x] Benutzer, die sowohl Fahrer als auch Disponent sind, können die Fahrer-Sicht nicht aufrufen.
