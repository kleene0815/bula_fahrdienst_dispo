# UI — Disponenten-Ansicht (Desktop)

## Allgemeines

Die Disponenten-Ansicht ist für Desktop/Laptop optimiert. Sie ist die Standardansicht für Nutzer mit der Rolle `disponent`. Nutzer mit beiden Rollen landen bei Anmeldung über einen Desktop-Browser ebenfalls in dieser Ansicht.


## Hauptansicht

Die Hauptansicht ist zweigeteilt:

**Linke Spalte — Aufträge:**
- Filterschalter: Alle / Offen / Zugeteilt / Unterwegs / Erledigt
- Liste aller Aufträge als Karten, sortiert nach Deadline
- Jede Karte zeigt: Prioritätspunkt (farbig), Ziel, Status-Badge, Deadline, Patient (falls vorhanden), Begleitperson-Icon (falls vorhanden), Auftrags-ID
- Button „+ Neuer Auftrag" öffnet das Auftragsformular als Modal

**Rechte Spalte — Fahrten:**
- Liste aller aktiven und geplanten Fahrten
- Jede Fahrt zeigt: Fahrtnummer, Fahrername, Status-Badge, enthaltene Stopps mit Reihenfolge
- Nicht abgeschlossene Fahrten zeigen Kapazitätsindikator (belegte / verfügbare Sitze)
- Button „+ Neue Fahrt" öffnet das Fahrtformular
- Aufträge können per Drag-and-drop oder Button einer Fahrt hinzugefügt werden

**Topbar:**
- Tagesübersicht: Anzahl offener, unterwegs befindlicher und erledigter Aufträge
- Name und Avatar des angemeldeten Benutzers


## Auftragsformular (Modal)

Felder:

| Feld | Typ | Pflicht |
|---|---|---|
| Auftraggeber / Station | Freitext | Nein |
| Zieltyp | Auswahl (Apotheke / Arzt / Krankenhaus / Sonstiges) | Ja |
| Auftragstyp | Auswahl (Besorgung / Hinfahrt / Abholung) | Ja |
| Name / Adresse des Ziels | Freitext | Ja |
| Adresse des Ziels | Freitext | Nein |
| Deadline / Termin | Datum + Uhrzeit | Ja |
| Priorität | Auswahl (Normal / Mittel / Hoch) | Ja |
| Patientenname | Freitext | Nein |
| Telefonnummer | Freitext | Nein |
| Begleitperson mitfährt | Toggle (ja/nein) | Nein |
| Bemerkungen | Freitext (mehrzeilig) | Nein |

Patientenfelder (Name, Telefon, Begleitperson) erscheinen bei `trip_type = hinfahrt` oder `abholung`.


## Fahrtformular (Modal)

Das Fahrtformular erlaubt die manuelle Zusammenstellung einer Fahrt.

**Abschnitte:**
1. **Fahrer** — Auswahl per Karte. Verfügbare Fahrer sind hervorgehoben, Fahrer im Einsatz grau markiert (aber wählbar).
2. **Fahrzeug** — Auswahl per Karte. Zeigt Name, Kennzeichen, Sitzanzahl und Typ (fest/privat).
3. **Aufträge** — Checkboxliste aller offenen Aufträge. Zeigt Ziel, Typ, Deadline und Patienteninfo.
4. **Kapazitätsanzeige** — Balken mit belegten / verfügbaren Sitzen. Wird gelb bei hoher Auslastung, rot bei Überschreitung. Der Speichern-Button ist bei Überschreitung deaktiviert.
5. **Bemerkungen** — Freitext für Fahrerhinweise.

Die Kapazität berechnet sich automatisch aus den gewählten Aufträgen und dem gewählten Fahrzeug.


## Fahrt abschließen (Disponenten-Sicht)

Sobald alle Stopps einer Fahrt erledigt sind, erscheint in der Fahrt-Karte der Button „Fahrt abschließen". Damit wechselt der Fahrt-Status auf `abgeschlossen` und Fahrer sowie Fahrzeug sind wieder als verfügbar markiert.

Dies ist eine Fallback-Möglichkeit für den Fall, dass der Fahrer die Fahrt nicht selbst abschließt.


## Auftragsschein (Druckansicht)

Erreichbar über die Fahrt-Karte als „Auftragsschein drucken"-Aktion. Öffnet eine druckoptimierte Ansicht.

**Aufbau:**

1. **Kopfbereich:** Fahrtnummer, Fahrer, Fahrzeug, Datum, Erstellungszeit, QR-Code
2. **Auftragstabelle:** Alle Aufträge der Fahrt mit Stopp-Nummer, Zielname, Zieladresse (zweite Zeile), Typ-Badge, Deadline und Patient
3. **Patientenabschnitte:** Pro Auftrag mit `trip_type = hinfahrt` ein abtrenntbarer Abschnitt (Scherenlinie). Enthält:
   - Zielname und Zieladresse
   - Datum und Uhrzeit des Termins
   - Patientenname und Begleitperson-Hinweis
   - Telefonnummer der Sicherheitszentrale (aus globaler Konfiguration)
   - Name des Veranstalters und Adresse des Lagerplatzes (aus globaler Konfiguration)

Bemerkungen aus dem Auftrag erscheinen **nicht** im Patientenabschnitt (sind für den Fahrer bestimmt), wohl aber in der Auftragstabelle.
