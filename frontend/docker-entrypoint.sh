#!/bin/sh
set -e

# Keycloak-Konfiguration zur Laufzeit in config.js schreiben
cat > /usr/share/nginx/html/config.js << EOF
window.__env__ = {
  KEYCLOAK_URL: "${KEYCLOAK_URL}",
  KEYCLOAK_REALM: "${KEYCLOAK_REALM}",
  KEYCLOAK_CLIENT_ID: "${KEYCLOAK_CLIENT_ID}",
}
EOF

exec nginx -g 'daemon off;'
