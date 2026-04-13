#!/usr/bin/env python3
"""Weist dem Service Account 'fahrdienst-backend' die 'view-users'-Rolle zu.

Wird beim Backend-Start ausgeführt und ist idempotent (prüft vor der
Zuweisung, ob die Rolle bereits vergeben ist). Scheitert die Initialisierung,
wird nur eine Warnung ausgegeben — das Backend startet trotzdem.
"""
import os
import sys
import time

import httpx

KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://keycloak:8080")
REALM = os.environ.get("KEYCLOAK_REALM", "fahrdienst")
ADMIN_USER = os.environ.get("KEYCLOAK_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "admin")
SERVICE_CLIENT_ID = os.environ.get("KEYCLOAK_SERVICE_CLIENT_ID", "fahrdienst-backend")

MAX_RETRIES = 30
RETRY_INTERVAL = 2


def _wait_for_keycloak(client: httpx.Client) -> bool:
    for _ in range(MAX_RETRIES):
        try:
            resp = client.get(f"{KEYCLOAK_URL}/realms/{REALM}", timeout=3.0)
            if resp.status_code == 200:
                return True
        except httpx.RequestError:
            pass
        time.sleep(RETRY_INTERVAL)
    return False


def _admin_token(client: httpx.Client) -> str:
    resp = client.post(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": ADMIN_USER,
            "password": ADMIN_PASSWORD,
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _get(client: httpx.Client, token: str, path: str) -> list | dict:
    resp = client.get(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


def _post(client: httpx.Client, token: str, path: str, json: list | dict) -> None:
    resp = client.post(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}{path}",
        headers={"Authorization": f"Bearer {token}"},
        json=json,
    )
    resp.raise_for_status()


def main() -> None:
    with httpx.Client(timeout=10.0) as client:
        print("Keycloak-Init: Warte auf Keycloak…")
        if not _wait_for_keycloak(client):
            print("Keycloak-Init: Keycloak nicht erreichbar — übersprungen.", file=sys.stderr)
            return

        token = _admin_token(client)

        # Service-Account-User finden
        sa_username = f"service-account-{SERVICE_CLIENT_ID}"
        users = _get(client, token, f"/users?username={sa_username}&exact=true")
        if not users:
            print(f"Keycloak-Init: Service Account '{sa_username}' nicht gefunden.", file=sys.stderr)
            return
        sa_user_id = users[0]["id"]

        # realm-management Client-ID ermitteln
        rm_clients = _get(client, token, "/clients?clientId=realm-management")
        if not rm_clients:
            print("Keycloak-Init: realm-management client nicht gefunden.", file=sys.stderr)
            return
        rm_client_id = rm_clients[0]["id"]

        # Prüfen welche Rollen bereits zugewiesen sind (Idempotenz)
        existing = _get(client, token, f"/users/{sa_user_id}/role-mappings/clients/{rm_client_id}")
        existing_names = {r["name"] for r in existing}
        needed = {"view-users", "query-users", "view-realm"} - existing_names
        if not needed:
            print("Keycloak-Init: Rollen bereits zugewiesen – nichts zu tun.")
            return

        # Fehlende Rollen holen und zuweisen
        roles_to_add = [_get(client, token, f"/clients/{rm_client_id}/roles/{role}") for role in needed]
        _post(client, token, f"/users/{sa_user_id}/role-mappings/clients/{rm_client_id}", roles_to_add)
        print(f"Keycloak-Init: {needed} erfolgreich zugewiesen an '{sa_username}'.")


if __name__ == "__main__":
    main()
