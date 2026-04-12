# UI — Fahrer-Ansicht (Mobile)

## Allgemeines

Die Fahrer-Ansicht ist für Smartphones optimiert. Sie zeigt ausschließlich die dem Fahrer zugeteilten Fahrten — keine Disponenten-Funktionen. Nutzer mit nur der Rolle `fahrer` landen immer in dieser Ansicht. Nutzer mit beiden Rollen landen bei Aufruf über einen mobilen Browser (ohne QR-Code-Link) ebenfalls hier.

**QR-Code-Einstieg:** Der QR-Code auf dem Auftragsschein führt direkt zur betreffenden Fahrt. Nach dem OIDC-Login wird der Fahrer automatisch zur Fahrt weitergeleitet (kein manuelles Navigieren nötig).


## Fahrtansicht

Die Fahrtansicht zeigt eine einzelne Fahrt mit allen zugehörigen Stopps.

**Kopfbereich der Fahrt:**
- Fahrtnummer, Anzahl Stopps, Status-Badge
- Fahrzeugname und Kennzeichen

**Stoppliste:**
- Stopps in nummerierter Reihenfolge, verbunden durch eine vertikale Linie
- Erledigte Stopps: grüner Kreis mit Häkchen, Zielname durchgestrichen
- Aktiver Stopp: oranger Kreis mit Nummer
- Ausstehende Stopps: grauer Kreis mit Nummer
- Jeder Stopp zeigt: Zielname, Deadline / Termin, Auftragstyp (Besorgung / Patient)

**Detailansicht pro Stopp (aufklappbar per Tippen):**
- Zielname und Adresse
- Bei Besorgung: Auftragsbezeichnung, Bemerkungen
- Bei Patient: Patientenname, Begleitperson-Hinweis, Telefonnummer (als tippbarer Anruf-Link), Station, Bemerkungen


## Statusaktionen

| Zustand | Sichtbare Aktion |
|---|---|
| Fahrt `geplant`, alle Stopps ausstehend | „Fahrt starten" (grüner Button) |
| Fahrt `aktiv`, Stopp ausstehend | „Stopp erledigt" |
| Fahrt `aktiv`, alle Stopps erledigt | „Fahrt abschließen" (grüner Button) |

**Ablauf:**
1. Fahrer tippt „Fahrt starten" → Fahrt wechselt auf `aktiv`, alle Aufträge auf `unterwegs`
2. Fahrer tippt „Stopp erledigt" → aktueller Auftrag wechselt auf `erledigt`, nächster Stopp wird aktiv
3. Nach letztem Stopp erscheint ein „Rückfahrt zum Lager"-Element mit Button „Fahrt abschließen"
4. Fahrer tippt „Fahrt abschließen" → Fahrt wechselt auf `abgeschlossen`, Bestätigungsmeldung erscheint

Nach dem Abschluss zeigt die App eine Bestätigung: „Fahrt abgeschlossen — [Fahrzeugname] und du bist wieder frei."


## Hinweise

- Der Fahrer sieht keine anderen Fahrten außer seinen eigenen.
- Es gibt keine Möglichkeit, Aufträge hinzuzufügen, zu stornieren oder Fahrten zu bearbeiten — das bleibt dem Disponenten vorbehalten.
- Der QR-Code wird nur auf dem Auftragsschein (Druckansicht) und in der Disponenten-Ansicht angezeigt, nicht in der Fahrer-App selbst.
