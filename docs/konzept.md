# Konzept

## Fachlicher Kontext

Die Anwendung dient der Disposition von Fahrdiensten im Sicherheitsbereich eines Großzeltlagers. Sie unterstützt ausschließlich **nicht-dringende** Fahrten:

- Medikamenten- oder Materialabholungen in Apotheken
- Transport von Patienten zu Arztterminen oder ins Krankenhaus (Hinfahrt)
- Abholung von Patienten nach einem Termin (Abholung)

Der Disponent sammelt Aufträge — typischerweise von der Sanistation — und koordiniert den Fahrdienst. Mehrere Aufträge können manuell zu einer Fahrt gebündelt werden, um Fahrten einzusparen.


## Rollen

| Rolle | Beschreibung |
|---|---|
| **Disponent** | Legt Aufträge an, bündelt sie zu Fahrten, teilt Fahrer und Fahrzeug zu, führt Statusübergänge durch. Standardansicht bei Anmeldung über Desktop-Browser. |
| **Fahrer** | Sieht eigene zugeteilte Fahrt(en), aktualisiert den Status unterwegs, schließt die Fahrt ab. Optimierte Mobile-Ansicht. |

Eine Person kann beide Rollen haben. In diesem Fall stehen alle Funktionen beider Rollen zur Verfügung. Die Rollenverwaltung erfolgt über Keycloak; die App spiegelt die Rollen aus dem JWT-Token.

**Routing bei Doppelrolle:**
- Desktop-Browser → Disponenten-Ansicht als Standard
- Mobiler Browser (direkter Aufruf) → Fahrer-Ansicht
- QR-Code-Link → direkt zur betreffenden Fahrt


## Auftragstypen

Jeder Auftrag hat einen `trip_type`, der bestimmt, ob ein abtrenntbarer Patientenabschnitt auf dem Auftragsschein erscheint:

| Typ | Beschreibung | Patientenabschnitt |
|---|---|---|
| `besorgung` | Medikamente, Material — kein Patient | Nein |
| `hinfahrt` | Patient wird zu Arzt / Krankenhaus gebracht | Ja |
| `abholung` | Patient wird nach Termin abgeholt | Nein |


## Auftragsstatus

```
Offen → Zugeteilt → Unterwegs → Erledigt
                             ↘ Storniert
```

| Status | Beschreibung |
|---|---|
| `offen` | Neu angelegt, noch keiner Fahrt zugeordnet |
| `zugeteilt` | Auftrag ist einer Fahrt und einem Fahrer zugewiesen |
| `unterwegs` | Fahrt ist gestartet |
| `erledigt` | Stopp wurde vom Fahrer oder Disponenten abgehakt |
| `storniert` | Auftrag wurde storniert |


## Fahrt-Status

```
Geplant → Aktiv → Abgeschlossen
                ↘ Abgebrochen
```

| Status | Beschreibung |
|---|---|
| `geplant` | Fahrt angelegt, Fahrer und Fahrzeug zugeteilt, noch nicht gestartet |
| `aktiv` | Fahrer hat Fahrt gestartet |
| `abgeschlossen` | Fahrer oder Disponent hat Fahrt abgeschlossen; Fahrer und Fahrzeug wieder frei |
| `abgebrochen` | Fahrt wurde abgebrochen |


## Fahrzeuge

Es stehen drei feste Fahrzeuge zur Verfügung. Bei Bedarf können zusätzlich Privatfahrzeuge genutzt werden. Ein Fahrzeug wird pro Fahrt zugeteilt (nicht pro Tag). Mehrere Fahrer können dasselbe Fahrzeug an einem Tag nacheinander nutzen.

Die Kapazitätsprüfung beim Bündeln von Aufträgen basiert auf:
- 1 Sitz für den Fahrer
- 1 Sitz pro Auftrag mit Patient
- +1 Sitz wenn Begleitperson mitfährt


## Authentifizierung

- OAuth 2.0 / OIDC via Keycloak
- Jeder Nutzer hat einen eigenen Login (kein geteiltes Passwort)
- Rollen werden aus dem Keycloak-Token übernommen
- Die Anwendung ist über das Internet erreichbar (HTTPS Pflicht)
- Benutzerverwaltung erfolgt ausschließlich über Keycloak (keine eigene Admin-UI)


## QR-Code / Auftragsschein

Der Disponent kann für eine Fahrt einen Auftragsschein drucken. Dieser enthält:

- Fahrtinformationen (Fahrer, Fahrzeug, Datum, Fahrtnummer)
- QR-Code, der direkt zur Fahrt in der App führt (nach OIDC-Login)
- Tabelle aller Aufträge mit Ziel, Adresse, Typ, Termin und Patient
- Abtrenntbarer Patientenabschnitt pro Hinfahrt-Auftrag

Der QR-Code kodiert die URL `https://<app>/trip/<qr_token>`. Nach dem Login wird der Fahrer direkt zur Fahrt weitergeleitet (OIDC `state`-Parameter).


## Globale Konfiguration

Folgende Werte sind einmalig in den App-Einstellungen konfigurierbar und erscheinen auf jedem Patientenabschnitt des Auftragsscheins:

- Name der Sicherheitszentrale
- Telefonnummer der Sicherheitszentrale
- Name des Veranstalters
- Adresse des Lagerplatzes

Weitere konfigurierbare Felder können bei Bedarf ergänzt werden.
