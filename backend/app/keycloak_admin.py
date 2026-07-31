"""Keycloak Admin API — Fahrer-Sync.

Synchronisiert Nutzer mit der Rolle 'fahrer' aus Keycloak in die lokale DB,
damit sie bereits vor ihrem ersten Login zur Fahrt-Zuteilung verfügbar sind.
Berücksichtigt sowohl direkt zugewiesene Rollen als auch Rollen, die über
Gruppenmitgliedschaften (inkl. Untergruppen) vererbt werden.
Fehler (Keycloak nicht erreichbar, falsche Credentials) werden stumm ignoriert —
der Endpoint gibt in diesem Fall einfach die lokalen Daten zurück.
"""
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import User, UserRole

logger = logging.getLogger(__name__)


async def _get_admin_token() -> str | None:
    if not settings.keycloak_service_client_secret:
        logger.warning("KEYCLOAK_SERVICE_CLIENT_SECRET nicht konfiguriert — Fahrer-Sync übersprungen")
        return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.keycloak_service_client_id,
                    "client_secret": settings.keycloak_service_client_secret,
                },
                timeout=5.0,
            )
            resp.raise_for_status()
            return resp.json()["access_token"]
    except Exception as exc:
        logger.warning("Keycloak Service-Account-Token nicht abrufbar: %s", exc)
        return None


async def _get(client: httpx.AsyncClient, token: str, path: str, params: dict | None = None):
    resp = await client.get(
        f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=5.0,
    )
    resp.raise_for_status()
    return resp.json()


async def _get_users_with_direct_role(client: httpx.AsyncClient, token: str, role: str) -> list[dict]:
    """Nutzer, denen die Rolle direkt zugewiesen ist (Gruppen-Vererbung liefert dieser Endpunkt nicht)."""
    try:
        return await _get(client, token, f"/roles/{role}/users", params={"max": 1000})
    except Exception as exc:
        logger.warning("Keycloak-Rolle '%s' nicht abrufbar: %s", role, exc)
        return []


async def _get_users_with_role_via_groups(client: httpx.AsyncClient, token: str, role: str) -> list[dict]:
    """Nutzer, die die Rolle über eine Gruppenmitgliedschaft erben.

    Eine Rolle an einer Gruppe vererbt sich auch auf die Mitglieder aller
    Untergruppen. Ältere Keycloak-Versionen liefern Untergruppen inline
    (`subGroups`), neuere (ab 23) nur noch über `/groups/{id}/children`.
    """
    try:
        groups: list[dict] = []
        children: dict[str, list[str]] = {}
        stack = list(await _get(client, token, "/groups", params={"max": 1000}))
        while stack:
            group = stack.pop()
            groups.append(group)
            subgroups = group.get("subGroups") or []
            if not subgroups and group.get("subGroupCount", 0):
                subgroups = await _get(client, token, f"/groups/{group['id']}/children", params={"max": 1000})
            children[group["id"]] = [s["id"] for s in subgroups]
            stack.extend(subgroups)

        role_group_ids: set[str] = set()
        for group in groups:
            mappings = await _get(client, token, f"/groups/{group['id']}/role-mappings/realm")
            if any(r.get("name") == role for r in mappings):
                role_group_ids.add(group["id"])

        # Vererbung: Untergruppen von Rollen-Gruppen ebenfalls aufnehmen
        queue = list(role_group_ids)
        while queue:
            for child_id in children.get(queue.pop(), []):
                if child_id not in role_group_ids:
                    role_group_ids.add(child_id)
                    queue.append(child_id)

        members: list[dict] = []
        for group_id in role_group_ids:
            members.extend(await _get(client, token, f"/groups/{group_id}/members", params={"max": 1000}))
        return members
    except Exception as exc:
        logger.warning("Keycloak-Gruppen für Rolle '%s' nicht abrufbar: %s", role, exc)
        return []


def _display_name(kc_user: dict) -> str:
    first = kc_user.get("firstName", "")
    last = kc_user.get("lastName", "")
    full = f"{first} {last}".strip()
    return full or kc_user.get("username", kc_user.get("id", ""))


async def sync_fahrer_from_keycloak(db: AsyncSession) -> None:
    """Synchronisiert alle Fahrer aus der Keycloak Admin API in die lokale DB."""
    token = await _get_admin_token()
    if token is None:
        return

    async with httpx.AsyncClient() as client:
        direct = await _get_users_with_direct_role(client, token, "fahrer")
        via_groups = await _get_users_with_role_via_groups(client, token, "fahrer")

    kc_users = list({u["id"]: u for u in [*direct, *via_groups]}.values())
    if not kc_users:
        return

    subs = [u["id"] for u in kc_users]
    result = await db.execute(
        select(User).where(User.keycloak_sub.in_(subs)).options(selectinload(User.roles))
    )
    existing_by_sub = {u.keycloak_sub: u for u in result.scalars().all()}

    for kc_user in kc_users:
        sub = kc_user["id"]
        name = _display_name(kc_user)
        email = kc_user.get("email", "")

        user = existing_by_sub.get(sub)
        if user is None:
            user = User(keycloak_sub=sub, name=name, email=email)
            db.add(user)
            await db.flush()
            db.add(UserRole(user_id=user.id, role="fahrer"))
        else:
            user.name = name
            user.email = email
            if not any(r.role == "fahrer" for r in user.roles):
                db.add(UserRole(user_id=user.id, role="fahrer"))

    await db.commit()
