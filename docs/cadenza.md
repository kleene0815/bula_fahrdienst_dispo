# Cadenza-Integration

## Übersicht

Die Anwendung ist in drei Punkten mit Cadenza verknüpft:

1. **Disponenten-Ansicht eingebettet in Cadenza** — die App läuft im Browser innerhalb von Cadenza und kann dort direkt aufgerufen werden.
2. **Historische Auswertungen in Cadenza** — Cadenza verbindet sich direkt auf die PostgreSQL-Datenbank und wertet `trips`, `orders` und `status_log` aus.
3. **Kartenansicht über cadenza.js** — aus der eingebetteten Disponenten-Ansicht heraus kann eine Zieladresse in einer Cadenza-Karte angezeigt werden.


## 1. Disponenten-Ansicht in Cadenza einbetten

Die Disponenten-Ansicht wird als externer Anwendungslink in Cadenza registriert. Cadenza lädt sie in einem iframe. Nutzer öffnen die Anwendung direkt aus dem Cadenza-Navigator heraus.

**Konfiguration in Cadenza Management Center:**
- Externe Anwendung mit der URL der Disponenten-Ansicht registrieren
- URL-Muster des Embedding-Targets: `{publicCadenzaUrl}/w/{embeddingTargetId}`
- Für die Cross-Origin-Kommunikation (postMessage) muss die App als externer Anwendungslink in Cadenza hinterlegt sein — nicht der Development-Mode (`postMessageAnyOrigin`)

**Seitens der App:**
- Kein struktureller Umbau nötig — die Disponenten-Ansicht ist eine normale SPA
- Das Frontend bindet `@disy/cadenza.js@~10.4.9` ein (passend zu Cadenza 10.4)
- Da App und Cadenza dieselbe Keycloak-Instanz (gleicher Realm) nutzen, ist der Nutzer in der eingebetteten App bereits authentifiziert — kein separater Login-Flow nötig
- Initialisierung für die Kommunikation mit dem Eltern-Cadenza:
  ```javascript
  // Kein Argument = kommuniziere mit dem Parent-Cadenza-Fenster
  const cadenzaClient = window.cadenza();
  ```


## 2. Historische Auswertungen

Cadenza liest direkt aus PostgreSQL. Kein zusätzlicher API-Aufwand.

**Relevante Tabellen für Auswertungen:**

| Tabelle | Beispiel-Auswertungen |
|---|---|
| `trips` | Fahrten pro Tag, Fahrten nach Status |
| `orders` | Aufträge nach Typ, häufigste Zielorte, Auftragslage nach Station |
| `status_log` | Statusübergangszeiten, Wartezeiten, Durchlaufzeiten |

**Beispiel-Dashboard-Kennzahlen:**
- Fahrten heute: gesamt / aktiv / abgeschlossen
- Offene Aufträge nach Priorität
- Durchschnittliche Bearbeitungszeit (Auftrag `offen` → `erledigt`)

> Die App selbst enthält keine Auswertungs-UI — alles läuft über Cadenza-Dashboards.


## Nicht im Scope: Kartenansicht

Eine Anzeige der Zieladresse in einer Cadenza-Karte ist mangels Geocoding nicht umsetzbar und wird nicht implementiert. Kein Koordinatenfeld im Datenmodell nötig.
