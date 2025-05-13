import time
from typing import Annotated, Optional 
from datetime import datetime # Já estava, mas garantindo

import structlog
from asyncache import cached
from cachetools import TTLCache
from fastapi import Header, HTTPException, status, Request
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError

from skyvern.config import settings
from skyvern.forge import app
from skyvern.forge.sdk.core import skyvern_context
from skyvern.forge.sdk.db.client import AgentDB
from skyvern.forge.sdk.models import TokenPayload # Usado se o token for JWT
# Importando o modelo Organization do local correto (ajuste o caminho se necessário)
from skyvern.forge.sdk.schemas.organizations import Organization, OrganizationAuthTokenType

LOG = structlog.get_logger()

AUTHENTICATION_TTL = 60 * 60  # one hour
CACHE_SIZE = 128
ALGORITHM = "HS256" # Usado para JWTs


async def get_current_org(
    x_api_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> Organization:
    if not x_api_key and not authorization:
        LOG.warning("Attempt to access get_current_org without X-Api-Key or Authorization header.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials - No authentication provided",
        )
    if x_api_key:
        LOG.debug(f"Authenticating with X-Api-Key: {x_api_key[:10]}...")
        return await _get_current_org_cached(x_api_key, app.DATABASE)
    elif authorization:
        LOG.debug(f"Authenticating with Authorization header: {authorization[:20]}...")
        return await _authenticate_helper(authorization)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid credentials - Authentication method not determined",
    )


async def get_current_org_with_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> Organization:
    if not x_api_key:
        LOG.warning("Attempt to access get_current_org_with_api_key without X-Api-Key header.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials - X-Api-Key header missing",
        )
    LOG.debug(f"Authenticating (api_key_only) with X-Api-Key: {x_api_key[:10]}...")
    return await _get_current_org_cached(x_api_key, app.DATABASE)


async def get_current_org_with_authentication(
    authorization: Annotated[str | None, Header()] = None,
) -> Organization:
    if not authorization:
        LOG.warning("Attempt to access get_current_org_with_authentication without Authorization header.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials - Authorization header missing",
        )
    LOG.debug(f"Authenticating (auth_header_only) with Authorization header: {authorization[:20]}...")
    return await _authenticate_helper(authorization)


async def _authenticate_helper(authorization: str) -> Organization:
    LOG.debug("Entering _authenticate_helper")
    try:
        auth_type, token = authorization.strip().split(" ", 1)
        if auth_type.lower() != "bearer":
            LOG.warning(f"Authorization header type is not Bearer: {auth_type}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Authorization header format. Expected 'Bearer token'.",
            )
    except ValueError:
        LOG.warning("Malformed Authorization header. Could not split into type and token.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Authorization header format.",
        )

    if not app.authentication_function:
        LOG.error("app.authentication_function is not defined. Cannot authenticate JWT.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server authentication method not configured",
        )
    organization = await app.authentication_function(token)
    if not organization:
        LOG.warning("Authentication function returned no organization for the provided token.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials or token",
        )
    LOG.info(f"Successfully authenticated organization via JWT: {organization.organization_id if hasattr(organization, 'organization_id') else 'Unknown ID'}")
    return organization


@cached(cache=TTLCache(maxsize=CACHE_SIZE, ttl=AUTHENTICATION_TTL))
async def _get_current_org_cached(x_api_key: str, db: AgentDB) -> Organization:
    """
    Authentication is cached for one hour.
    Handles both JWT-like API keys (for specific orgs) and the global system API key.
    """
    LOG.debug(f"Entering _get_current_org_cached with X-Api-Key: {x_api_key[:10]}...")

    # --- INÍCIO DA MODIFICAÇÃO ---
    # Verificar se o x_api_key fornecido é a chave API global do sistema
    if settings.SKYVERN_API_KEY and x_api_key == settings.SKYVERN_API_KEY:
        LOG.info("Global System API Key provided. Bypassing JWT decoding.")
        LOG.warning(
            "Global System API Key used. Returning a generic system organization object. "
            "Ensure this provides adequate access and context."
        )
        
        current_time = datetime.utcnow()
        
        # Criar o objeto Organization com os campos corretos e obrigatórios
        try:
            system_organization = Organization(
                organization_id="SYSTEM_GLOBAL_API_KEY_ORG", # ID Fixo para a "organização" da chave API
                organization_name="System Global API Key Access", # Campo correto do modelo
                # webhook_callback_url: Opcional, None por padrão
                # max_steps_per_run: Opcional, None por padrão
                # max_retries_per_step: Opcional, None por padrão
                # domain: Opcional, None por padrão
                # bw_organization_id: Opcional, None por padrão
                # bw_collection_ids: Opcional, None por padrão (se for lista, pode ser [] ou None)
                bw_collection_ids=[], # Exemplo se precisar ser uma lista, mesmo que vazia
                created_at=current_time,
                modified_at=current_time # Campo correto do modelo
            )
        except Exception as e:
            LOG.error(f"Erro ao instanciar o objeto Organization genérico: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Erro interno ao criar contexto de organização para API key.")

        context = skyvern_context.current()
        if context:
            context.organization_id = system_organization.organization_id
            context.organization_name = system_organization.organization_name
        return system_organization
    # --- FIM DA MODIFICAÇÃO ---

    LOG.debug("X-Api-Key is not the global system key. Attempting JWT decode for org-specific API key.")
    try:
        payload = jwt.decode(
            x_api_key,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        api_key_data = TokenPayload(**payload)
        LOG.debug(f"JWT decoded successfully. Payload sub: {api_key_data.sub}, exp: {api_key_data.exp}")
    except JWTError as e:
        LOG.error(f"Error decoding X-Api-Key as JWT: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not validate API key (JWT decode error: {e})",
        )
    except ValidationError as e:
        LOG.error(f"Error validating token payload from X-Api-Key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid token payload structure ({e})",
        )

    if api_key_data.exp < time.time():
        LOG.warning(f"Auth token (X-Api-Key) is expired. EXP: {api_key_data.exp}, Current: {time.time()}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auth token is expired",
        )

    LOG.debug(f"Fetching organization from DB with ID: {api_key_data.sub}")
    organization = await db.get_organization(organization_id=api_key_data.sub)
    if not organization:
        LOG.warning(f"Organization not found in DB for ID: {api_key_data.sub}")
        raise HTTPException(status_code=404, detail=f"Organization '{api_key_data.sub}' not found")

    LOG.debug(f"Validating org auth token in DB for org: {organization.organization_id}")
    api_key_db_obj = await db.validate_org_auth_token(
        organization_id=organization.organization_id,
        token_type=OrganizationAuthTokenType.api,
        token=x_api_key,
        valid=None,
    )
    if not api_key_db_obj:
        LOG.warning(f"Org auth token (X-Api-Key) not found or invalid in DB for org: {organization.organization_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials (token not registered or revoked)",
        )

    if api_key_db_obj.valid is False:
        LOG.warning(f"Org auth token (X-Api-Key) marked as invalid in DB for org: {organization.organization_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your API key has been deactivated or expired. Please check your organization settings.",
        )

    LOG.info(f"Successfully authenticated organization via X-Api-Key (JWT): {organization.organization_id}")
    context = skyvern_context.current()
    if context:
        context.organization_id = organization.organization_id
        context.organization_name = organization.organization_name
    return organization
