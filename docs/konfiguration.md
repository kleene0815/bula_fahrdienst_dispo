# Globale Konfiguration

## Übersicht

Die App enthält eine Einstellungsseite, über die einmalig globale Werte konfiguriert werden können. Diese Werte sind in der Tabelle `app_config` gespeichert (immer genau eine Zeile).

Nur Nutzer mit der Rolle `disponent` haben Zugriff auf die Einstellungsseite.


## Konfigurierbare Werte

| Einstellung | Beschreibung | Verwendung |
|---|---|---|
| Name der Sicherheitszentrale | z.B. „Sicherheitszentrale Zeltlager" | Patientenabschnitt auf Auftragsschein |
| Telefonnummer der Sicherheitszentrale | z.B. „0721 / 555 100" | Patientenabschnitt auf Auftragsschein |
| Name des Veranstalters | z.B. „DLRG Ortsgruppe Muster" | Patientenabschnitt auf Auftragsschein |
| Adresse des Lagerplatzes | z.B. „Festwiese Nord, Musterstadt" | Patientenabschnitt auf Auftragsschein |


## Fahrzeugverwaltung

Fahrzeuge werden ebenfalls in den Einstellungen gepflegt. Verfügbare Aktionen:

- Neues Fahrzeug anlegen (Name, Kennzeichen, Sitzanzahl, Typ)
- Bestehendes Fahrzeug bearbeiten
- Fahrzeug deaktivieren (`active = false`) — z.B. bei Werkstattaufenthalt

Deaktivierte Fahrzeuge erscheinen nicht mehr in der Fahrzeugauswahl beim Anlegen einer Fahrt, bleiben aber in der Datenbank erhalten und sind in historischen Fahrten weiterhin referenziert.


## Hinweise zur Erweiterbarkeit

Die Konfigurationstabelle ist bewusst einfach gehalten (feste Spalten statt key-value-Paare). Sollten weitere globale Einstellungen hinzukommen, können einfach neue Spalten ergänzt werden.
