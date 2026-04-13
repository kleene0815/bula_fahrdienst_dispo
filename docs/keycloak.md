# Keycloak-Konfiguration (Produktion)

Diese Anleitung beschreibt die manuelle Einrichtung des zentralen Keycloak-Realms für den Produktivbetrieb. In der Entwicklungsumgebung wird der Realm automatisch aus `keycloak/fahrdienst-realm.json` importiert und der Service Account per Init-Skript konfiguriert — das entfällt hier.

---

## 1. Realm

Falls noch kein dedizierter Realm existiert, einen neuen anlegen:

- **Realm-Name:** `fahrdienst` (oder nach Konvention der Umgebung — muss mit `KEYCLOAK_REALM` übereinstimmen)
- „User registration" und „Forgot password" nach Bedarf deaktivieren

---

## 2. Rollen

Unter **Realm roles** zwei Rollen anlegen:

| Rolle | Beschreibung |
|---|---|
| `disponent` | Kann Aufträge und Fahrten verwalten |
| `fahrer` | Kann eigene Fahrten einsehen und Statusübergänge durchführen |

---

## 3. Nutzer

Für jeden Disponenten und Fahrer einen Keycloak-Nutzer anlegen und die entsprechende Rolle zuweisen. Die Nutzer müssen sich **nicht** einloggen, um in der Anwendung zur Auswahl zu stehen — der Fahrer-Sync holt sie direkt aus Keycloak (siehe Abschnitt 5).

---

## 4. Client: `fahrdienst-disposition` (Frontend)

Unter **Clients → Create**:

| Einstellung | Wert |
|---|---|
| Client ID | `fahrdienst-disposition` |
| Client type | `OpenID Connect` |
| Client authentication | **Aus** (Public Client) |
| Standard flow | **Ein** |
| Direct access grants | **Aus** |

Unter **Settings → Access settings**:

| Einstellung | Wert |
|---|---|
| Valid redirect URIs | `https://<app-domain>/*` |
| Web origins | `https://<app-domain>` |
| Post logout redirect URIs | `https://<app-domain>/*` |

---

## 5. Client: `fahrdienst-backend` (Service Account)

Dieser Client ermöglicht dem Backend, Fahrer aus Keycloak zu synchronisieren, bevor sie sich das erste Mal einloggen.

### Client anlegen

Unter **Clients → Create**:

| Einstellung | Wert |
|---|---|
| Client ID | `fahrdienst-backend` |
| Client type | `OpenID Connect` |
| Client authentication | **Ein** (Confidential) |
| Standard flow | **Aus** |
| Service account roles | **Ein** |

Nach dem Speichern das **Client Secret** unter **Credentials** kopieren — wird als `KEYCLOAK_SERVICE_CLIENT_SECRET` benötigt.

### Berechtigung vergeben

Der Service Account benötigt nur das Recht, Nutzer abzufragen (`view-users`). Keine Admin-Rechte.

1. **Clients → `fahrdienst-backend` → Service accounts roles**
2. **Assign role** → Filter auf „Filter by clients" umstellen
3. Client **`realm-management`** auswählen → Rolle **`view-users`** zuweisen

---

## 6. Backend-Umgebungsvariablen

| Variable | Beispielwert | Beschreibung |
|---|---|---|
| `KEYCLOAK_URL` | `https://keycloak.intern/` | Interne URL für JWKS-Abruf und Admin API |
| `KEYCLOAK_REALM` | `fahrdienst` | Realm-Name |
| `KEYCLOAK_PUBLIC_URL` | `https://keycloak.example.com/` | Öffentliche URL (muss mit dem `iss`-Claim im JWT übereinstimmen) |
| `KEYCLOAK_SERVICE_CLIENT_ID` | `fahrdienst-backend` | Client ID des Service Accounts |
| `KEYCLOAK_SERVICE_CLIENT_SECRET` | `…` | Client Secret (aus Schritt 5) |

`KEYCLOAK_ADMIN_USER` und `KEYCLOAK_ADMIN_PASSWORD` werden in der Produktion **nicht** benötigt — die Rollenzuweisung wurde manuell vorgenommen.
