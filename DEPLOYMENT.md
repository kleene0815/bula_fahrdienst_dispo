# Deployment-Anleitung

Diese Anleitung beschreibt das Production-Deployment mit Docker Compose.
Der Source-Code wird **nicht** auf der Produktivmaschine benötigt — nur die
Images aus der Registry und die hier beschriebenen Konfigurationsdateien.

---

## Voraussetzungen

- Docker mit Compose-Plugin
- Bestehender Keycloak-Realm (Konfigurationsschritte siehe [Keycloak-Konfiguration](#keycloak-konfiguration))

Die Images sind öffentlich auf der GitHub Container Registry verfügbar — kein `docker login` zum Pullen erforderlich.

---

## Verzeichnisstruktur auf dem Server

```
/opt/fahrdienst/
├── docker-compose.yml
└── .env
```

---

## Keycloak-Konfiguration

Die folgenden Schritte müssen **einmalig vor dem ersten Start** in der
Keycloak Admin-Konsole des bestehenden Realms durchgeführt werden.

---

### 1. Realm-Rollen anlegen

_Realm roles → Create role_

| Rollenname | Beschreibung |
|---|---|
| `disponent` | Kann Aufträge und Fahrten verwalten |
| `fahrer` | Kann eigene Fahrten einsehen und Statusübergänge durchführen |

> Die Rollen werden vom Backend direkt aus `realm_access.roles` im JWT gelesen.
> Benutzer erhalten Zugriff auf die jeweilige Ansicht ausschließlich über diese
> Realm-Rollen — eine oder beide Rollen können pro Benutzer vergeben werden.

---

### 2. Frontend-Client anlegen

_Clients → Create client_

| Einstellung | Wert |
|---|---|
| **Client type** | `OpenID Connect` |
| **Client ID** | `fahrdienst-disposition` |
| **Client authentication** | aus (Public Client) |
| **Standard flow** | ein |
| **Direct access grants** | aus |

Unter _Clients → fahrdienst-disposition → Settings_:

| Einstellung | Wert |
|---|---|
| **Valid redirect URIs** | `https://fahrdienst.example.com/*` |
| **Valid post logout redirect URIs** | `https://fahrdienst.example.com/*` |
| **Web origins** | `https://fahrdienst.example.com` |

---

### 3. Backend-Client anlegen

Das Backend benötigt einen Confidential Client mit Service Account, um die
Fahrerliste aus Keycloak abrufen zu können.

_Clients → Create client_

| Einstellung | Wert |
|---|---|
| **Client type** | `OpenID Connect` |
| **Client ID** | `fahrdienst-backend` |
| **Client authentication** | ein (Confidential Client) |
| **Standard flow** | aus |
| **Direct access grants** | aus |
| **Service accounts roles** | ein |

#### 3a. Protokoll-Mapper hinzufügen

Damit der Service-Account-Token die `realm-management`-Audience enthält, muss
ein Mapper angelegt werden.

_Clients → fahrdienst-backend → Client scopes →
fahrdienst-backend-dedicated → Add mapper → By configuration →
Audience_

| Einstellung | Wert |
|---|---|
| **Name** | `realm-management-audience` |
| **Included Client Audience** | `realm-management` |
| **Add to access token** | ein |

#### 3b. Service-Account-Rollen zuweisen

_Clients → fahrdienst-backend → Service accounts roles →
Assign role → Filter by clients → `realm-management`_

| Rolle | Zweck |
|---|---|
| `view-users` | Benutzerliste abrufen |
| `query-users` | Benutzer nach ID/Name suchen |
| `view-realm` | Realm-Metadaten lesen |

#### 3c. Client-Secret in .env eintragen

_Clients → fahrdienst-backend → Credentials → Client secret_

Den angezeigten Wert als `KEYCLOAK_SERVICE_CLIENT_SECRET` in die `.env` eintragen.

---

## docker-compose.yml

```yaml
services:

  backend:
    image: ghcr.io/kleene0815/bula_fahrdienst_dispo/backend:latest
    environment:
      DATABASE_URL: ${DATABASE_URL}
      KEYCLOAK_URL: ${KEYCLOAK_URL}
      KEYCLOAK_REALM: ${KEYCLOAK_REALM}
      KEYCLOAK_PUBLIC_URL: ${KEYCLOAK_PUBLIC_URL}
      KEYCLOAK_SERVICE_CLIENT_ID: ${KEYCLOAK_SERVICE_CLIENT_ID}
      KEYCLOAK_SERVICE_CLIENT_SECRET: ${KEYCLOAK_SERVICE_CLIENT_SECRET}
      CORS_ORIGINS: ${CORS_ORIGINS}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    image: ghcr.io/kleene0815/bula_fahrdienst_dispo/frontend:latest
    environment:
      KEYCLOAK_URL: ${KEYCLOAK_PUBLIC_URL}
      KEYCLOAK_REALM: ${KEYCLOAK_REALM}
      KEYCLOAK_CLIENT_ID: ${KEYCLOAK_CLIENT_ID}
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## Umgebungsvariablen

### Backend (`backend`)

| Variable | Beschreibung | Beispiel |
|---|---|---|
| `DATABASE_URL` | PostgreSQL-Connection-String (asyncpg) | `postgresql+asyncpg://fahrdienst:secret@db/fahrdienst` |
| `KEYCLOAK_URL` | Interne URL zu Keycloak — für JWKS-Abruf vom Backend aus | `https://keycloak.example.com` |
| `KEYCLOAK_REALM` | Name des Keycloak-Realms | `fahrdienst` |
| `KEYCLOAK_PUBLIC_URL` | Öffentliche Keycloak-URL — muss mit dem `iss`-Claim im JWT übereinstimmen (Browser-seitig ausgestellt). Wenn leer, wird `KEYCLOAK_URL` verwendet. | `https://keycloak.example.com` |
| `KEYCLOAK_SERVICE_CLIENT_ID` | Client-ID des Backend-Service-Accounts | `fahrdienst-backend` |
| `KEYCLOAK_SERVICE_CLIENT_SECRET` | Client-Secret des Backend-Service-Accounts | _(aus Keycloak, siehe oben)_ |
| `CORS_ORIGINS` | JSON-Array der erlaubten CORS-Origins | `["https://fahrdienst.example.com"]` |

---

### Frontend (`frontend`)

Die Keycloak-Konfiguration wird **zur Laufzeit** per Umgebungsvariable
injiziert (nicht zur Build-Zeit). Ein Rebuild ist bei URL-Änderungen
nicht nötig.

| Variable | Beschreibung | Beispiel |
|---|---|---|
| `KEYCLOAK_URL` | Öffentliche Keycloak-URL (Browser-seitig erreichbar) | `https://keycloak.example.com` |
| `KEYCLOAK_REALM` | Name des Keycloak-Realms | `fahrdienst` |
| `KEYCLOAK_CLIENT_ID` | Client-ID der Frontend-Anwendung | `fahrdienst-disposition` |

---

## .env Beispieldatei

```dotenv
# Datenbank-URL (muss zu den PostgreSQL-Werten passen)
DATABASE_URL=postgresql+asyncpg://fahrdienst:CHANGE_ME@db/fahrdienst

# Keycloak
KEYCLOAK_URL=https://keycloak.example.com
KEYCLOAK_PUBLIC_URL=https://keycloak.example.com
KEYCLOAK_REALM=fahrdienst

# Backend Service Account (Secret aus Keycloak Admin-Konsole, siehe Abschnitt Keycloak-Konfiguration)
KEYCLOAK_SERVICE_CLIENT_ID=fahrdienst-backend
KEYCLOAK_SERVICE_CLIENT_SECRET=CHANGE_ME

# Frontend
KEYCLOAK_CLIENT_ID=fahrdienst-disposition

# CORS: öffentliche URL der Frontend-Anwendung
CORS_ORIGINS=["https://fahrdienst.example.com"]
```

---

## Deployment-Ablauf

### Erstinstallation

```bash
cd /opt/fahrdienst
docker compose pull
docker compose up -d
```

Die Datenbank-Migrationen laufen automatisch beim Backend-Start.

### Update auf neue Version

```bash
# Image-Tag in docker-compose.yml auf die neue Version setzen, dann:
docker compose pull
docker compose up -d
```

## Images veröffentlichen (GitHub Actions)

Das Bauen und Pushen der Images übernimmt der GitHub Actions Workflow
`.github/workflows/docker-publish.yml` vollautomatisch:

| Auslöser | Image-Tag |
|---|---|
| Push auf `main` | `latest` |
| Git-Tag `0.9.1` oder `v0.9.1` | `0.9.1` |

**Neue Version veröffentlichen:**

```bash
git tag 0.9.1
git push origin 0.9.1
```

GitHub Actions baut dann beide Images und pusht sie nach:
- `ghcr.io/kleene0815/bula_fahrdienst_dispo/backend:0.9.1`
- `ghcr.io/kleene0815/bula_fahrdienst_dispo/frontend:0.9.1`

> **Hinweis:** Beim ersten Push eines neuen Packages setzt GitHub die Sichtbarkeit
> auf "private". Unter _GitHub → Packages → Package settings → Danger Zone_ muss
> das Package einmalig auf "public" gestellt werden.
