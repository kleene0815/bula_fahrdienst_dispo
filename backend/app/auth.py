"""JWT-Validierung gegen Keycloak JWKS.

Der Public Key wird beim ersten Request geladen und für die Laufzeit gecacht.
Rollen werden aus `realm_access.roles` gelesen.
"""
import uuid
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import User, UserRole

_jwks_cache: dict | None = None
bearer_scheme = HTTPBearer()


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.keycloak_jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache


def _decode_token(token: str, jwks: dict) -> dict:
    try:
        header = jwt.get_unverified_header(token)
        key = next(
            (k for k in jwks["keys"] if k.get("kid") == header.get("kid")),
            None,
        )
        if key is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unbekannter Signaturschlüssel")
        return jwt.decode(
            token,
            key,
            algorithms=[header.get("alg", "RS256")],
            issuer=settings.keycloak_issuer,
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    jwks = await _get_jwks()
    payload = _decode_token(credentials.credentials, jwks)

    sub: str = payload.get("sub", "")
    name: str = payload.get("name") or payload.get("preferred_username", "")
    email: str = payload.get("email", "")
    realm_roles: list[str] = payload.get("realm_access", {}).get("roles", [])
    app_roles = [r for r in realm_roles if r in ("disponent", "fahrer")]

    # Nutzer anlegen oder aktualisieren
    result = await db.execute(
        select(User).where(User.keycloak_sub == sub).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(keycloak_sub=sub, name=name, email=email)
        db.add(user)
        await db.flush()
    else:
        user.name = name
        user.email = email

    # Rollen synchronisieren
    existing_roles = {r.role for r in user.roles}
    for role in app_roles:
        if role not in existing_roles:
            db.add(UserRole(user_id=user.id, role=role))
    for role_obj in list(user.roles):
        if role_obj.role not in app_roles:
            await db.delete(role_obj)

    await db.commit()
    await db.refresh(user, ["roles"])
    return user


def require_role(*roles: str):
    """Dependency-Factory: wirft 403 wenn der Nutzer keine der geforderten Rollen hat."""
    async def _check(user: Annotated[User, Depends(get_current_user)]) -> User:
        user_roles = {r.role for r in user.roles}
        if not user_roles.intersection(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fehlende Berechtigung")
        return user
    return _check


CurrentUser = Annotated[User, Depends(get_current_user)]
DisponentUser = Annotated[User, Depends(require_role("disponent"))]
FahrerUser = Annotated[User, Depends(require_role("fahrer", "disponent"))]
