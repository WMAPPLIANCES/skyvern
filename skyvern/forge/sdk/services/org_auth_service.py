import time
from typing import Annotated, Optional # Adicionado Optional para consistência, embora não usado diretamente na modificação

import structlog
from asyncache import cached
from cachetools import TTLCache
from fastapi import Header, HTTPException, status, Request # Adicionado Request para uso potencial no futuro
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError

from skyvern.config import settings # Já estava aqui, ótimo!
from skyvern.forge import app
from skyvern.forge.sdk.core import skyvern_context
from skyvern.forge.sdk.db.client import AgentDB
from skyvern.forge.sdk.models import TokenPayload
from skyvern.forge.sdk.schemas.organizations import Organization, OrganizationAuthTokenType
from datetime import datetime # Adicionado para criar timestamps

LOG = structlog.get_logger()

AUTHENTICATION_TTL = 60 * 60  # one hour
CACHE_SIZE = 128
ALGORITHM = "HS256"


async def get_current_org(
    x_api_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
    # Adicionar request: Request = None para que _get_current_org_cached possa recebê-lo se necessário
    # Embora a modificação atual não use 'request' diretamente em _get_current_org_cached,
    # é bom tê-lo disponível se a lógica de organização padrão precisar dele.
    # No entanto, para manter a assinatura original de _get_current_org_cached,
    # vamos passar apenas o x_api_key e o db por enquanto.
) -> Organization:
    if not x_api_key and not authorization:
        LOG.warning("Attempt to access get_current_org without X-Api-Key or Authorization header.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials - No authentication provided",
        )
    if x_api_key:
        LOG.debug(f"Authenticating with X-Api-Key: {x_api_key[:10]}...") # Log apenas parte da chave
        return await _get_current_org_cached(x_api_key, app.DATABASE)
    elif authorization:
        LOG.debug(f"Authenticating with Authorization header: {authorization[:20]}...") # Log apenas parte do token
        return await _authenticate_helper(authorization)

    # Este raise teoricamente não deveria ser alcançado se a lógica acima estiver correta
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
        # Adicionado strip para remover espaços em branco acidentais
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Mudado para 500, pois é um erro de configuração do servidor
            detail="Server authentication method not configured",
        )
    organization = await app.authentication_function(token) # Assume que authentication_function lida com a decodificação JWT
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
        # Se a chave API do sistema for usada, precisamos retornar um objeto Organization.
        # Esta organização pode ser uma "organização padrão do sistema".
        # Verifique a definição de skyvern.forge.sdk.schemas.organizations.Organization
        # para os campos obrigatórios. O exemplo abaixo é especulativo e pode precisar de ajustes.

        # Tentar buscar uma organização "sistema" ou "admin" pelo nome ou ID se existir
        # system_org_name_or_id = "SystemDefaultOrganization" # Ou um ID de settings.DEFAULT_SYSTEM_ORG_ID
        # try:
        #     organization = await db.get_organization_by_name(name=system_org_name_or_id) # Supondo que tal método exista
        #     if organization:
        #         LOG.info(f"Found default system organization: {organization.organization_id}")
        #         # Definir contexto
        #         context = skyvern_context.current()
        #         if context:
        #             context.organization_id = organization.organization_id
        #             context.organization_name = organization.organization_name
        #         return organization
        # except Exception as e:
        #     LOG.warning(f"Could not fetch default system organization by name/ID '{system_org_name_or_id}': {e}. Falling back to generic object.")

        # Se não houver uma organização padrão específica, crie um objeto genérico.
        # Certifique-se de que todos os campos obrigatórios do modelo Organization são preenchidos.
        LOG.warning(
            "Global System API Key used. Returning a generic system organization object. "
            "Ensure this provides adequate access and context."
        )
        system_organization = Organization(
            organization_id="SYSTEM_GLOBAL_API_KEY_ORG", # ID Fixo para a "organização" da chave API
            name="System Global API Key Access",
            # Preencha outros campos obrigatórios com valores padrão ou apropriados
            # Verifique o modelo Organization para campos como:
            # created_at, updated_at, api_keys (lista), users (lista), invites (lista), etc.
            created_at=datetime.utcnow(), # Exemplo
            updated_at=datetime.utcnow(), # Exemplo
            api_keys=[], # Exemplo: Lista vazia ou mock
            users=[],    # Exemplo: Lista vazia ou mock
            invites=[],  # Exemplo: Lista vazia ou mock
            # Adicione quaisquer outros campos obrigatórios do modelo Organization.
        )
        # Definir contexto para a chave API global
        context = skyvern_context.current()
        if context:
            context.organization_id = system_organization.organization_id
            context.organization_name = system_organization.name
        return system_organization
    # --- FIM DA MODIFICAÇÃO ---

    # Se não for a chave API global, prossiga com a tentativa de decodificação JWT
    # (assumindo que outras chaves API são JWTs específicos de organização)
    LOG.debug("X-Api-Key is not the global system key. Attempting JWT decode for org-specific API key.")
    try:
        payload = jwt.decode(
            x_api_key,
            settings.SECRET_KEY, # Certifique-se que settings.SECRET_KEY está definido e é o correto para estes JWTs
            algorithms=[ALGORITHM],
        )
        api_key_data = TokenPayload(**payload)
        LOG.debug(f"JWT decoded successfully. Payload sub: {api_key_data.sub}, exp: {api_key_data.exp}")
    except JWTError as e: # Captura JWTError especificamente
        LOG.error(f"Error decoding X-Api-Key as JWT: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not validate API key (JWT decode error: {e})",
        )
    except ValidationError as e: # Captura erros de validação do TokenPayload
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

    # check if the token exists in the database
    LOG.debug(f"Validating org auth token in DB for org: {organization.organization_id}")
    api_key_db_obj = await db.validate_org_auth_token(
        organization_id=organization.organization_id,
        token_type=OrganizationAuthTokenType.api, # Assumindo que este é o tipo correto
        token=x_api_key, # O token original (JWT)
        valid=None, # Passar None para apenas verificar a existência e validade
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
    # set organization_id in skyvern context and log context
    context = skyvern_context.current()
    if context:
        context.organization_id = organization.organization_id
        context.organization_name = organization.organization_name
    return organization
