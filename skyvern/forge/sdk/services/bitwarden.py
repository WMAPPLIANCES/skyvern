import asyncio
import json
import os
import re
import urllib.parse
from enum import IntEnum, StrEnum
from typing import Tuple

import structlog
import tldextract # type: ignore
from pydantic import BaseModel

from skyvern.config import settings
from skyvern.exceptions import (
    BitwardenAccessDeniedError,
    BitwardenCreateCollectionError,
    BitwardenCreateCreditCardItemError,
    BitwardenCreateLoginItemError,
    BitwardenGetItemError,
    BitwardenListItemsError,
    BitwardenLoginError,
    BitwardenLogoutError,
    BitwardenSecretError,
    BitwardenSyncError,
    BitwardenUnlockError,
)
# Removido import de aws_client, pois não vamos usá-lo nesta versão dummy
# from skyvern.forge.sdk.api.aws import aws_client
from skyvern.forge.sdk.core.aiohttp_helper import aiohttp_delete, aiohttp_get_json, aiohttp_post
from skyvern.forge.sdk.schemas.credentials import (
    CredentialItem,
    CredentialType,
    CreditCardCredential,
    PasswordCredential,
)

LOG = structlog.get_logger()

# Esta URL não será realmente usada nas funções modificadas, mas a variável é referenciada.
BITWARDEN_SERVER_BASE_URL = f"{settings.BITWARDEN_SERVER or 'http://localhost'}:{settings.BITWARDEN_SERVER_PORT or 8002}"


class BitwardenItemType(IntEnum):
    LOGIN = 1
    SECURE_NOTE = 2
    CREDIT_CARD = 3
    IDENTITY = 4

# As funções get_bitwarden_item_type_code, get_list_response_item_from_bitwarden_item,
# is_valid_email, BitwardenConstants, BitwardenQueryResult, RunCommandResult
# podem permanecer as mesmas, pois são definições de tipo ou helpers que não fazem chamadas de rede.
# Se alguma delas for chamada por código que não estamos "dummyficando", elas precisam estar aqui.
# Para simplificar, vamos mantê-las.

def get_bitwarden_item_type_code(item_type: BitwardenItemType) -> int:
    if item_type == BitwardenItemType.LOGIN:
        return 1
    elif item_type == BitwardenItemType.SECURE_NOTE:
        return 2
    elif item_type == BitwardenItemType.CREDIT_CARD:
        return 3
    elif item_type == BitwardenItemType.IDENTITY:
        return 4
    # Adicionado um else para cobrir todos os caminhos, embora improvável de ser chamado com esta modificação
    return 0 


def get_list_response_item_from_bitwarden_item(item: dict) -> CredentialItem:
    # Esta função provavelmente não será chamada se não listarmos itens do Bitwarden.
    # Mas a mantemos para integridade estrutural.
    if item.get("type") == BitwardenItemType.LOGIN and "login" in item:
        login = item["login"]
        totp = BitwardenService.extract_totp_secret(login.get("totp", ""))
        return CredentialItem(
            item_id=item.get("id", "dummy_login_id"),
            credential=PasswordCredential(
                username=login.get("username", ""),
                password=login.get("password", ""),
                totp=totp,
            ),
            name=item.get("name", "Dummy Login Item"),
            credential_type=CredentialType.PASSWORD,
        )
    elif item.get("type") == BitwardenItemType.CREDIT_CARD and "card" in item:
        card = item["card"]
        return CredentialItem(
            item_id=item.get("id", "dummy_cc_id"),
            credential=CreditCardCredential(
                card_holder_name=card.get("cardholderName", ""),
                card_number=card.get("number", ""),
                card_exp_month=card.get("expMonth", ""),
                card_exp_year=card.get("expYear", ""),
                card_cvv=card.get("code", ""),
                card_brand=card.get("brand", ""),
            ),
            name=item.get("name", "Dummy Credit Card"),
            credential_type=CredentialType.CREDIT_CARD,
        )
    else:
        # Retornar um item dummy genérico para evitar quebrar se chamado inesperadamente
        LOG.warning(f"get_list_response_item_from_bitwarden_item chamada com tipo de item não suportado ou dados ausentes: {item.get('type')}")
        return CredentialItem(
            item_id=item.get("id", "dummy_unknown_id"),
            credential=PasswordCredential(username="dummy", password="dummy", totp=""), # Genérico
            name=item.get("name", "Dummy Unknown Item"),
            credential_type=CredentialType.PASSWORD, # Genérico
        )


def is_valid_email(email: str | None) -> bool:
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


class BitwardenConstants(StrEnum):
    BW_ORGANIZATION_ID = "BW_ORGANIZATION_ID"
    BW_COLLECTION_IDS = "BW_COLLECTION_IDS"
    CLIENT_ID = "BW_CLIENT_ID"
    CLIENT_SECRET = "BW_CLIENT_SECRET"
    MASTER_PASSWORD = "BW_MASTER_PASSWORD"
    URL = "BW_URL"
    BW_COLLECTION_ID = "BW_COLLECTION_ID"
    IDENTITY_KEY = "BW_IDENTITY_KEY"
    BW_ITEM_ID = "BW_ITEM_ID"
    USERNAME = "BW_USERNAME"
    PASSWORD = "BW_PASSWORD"
    TOTP = "BW_TOTP"
    CREDIT_CARD_HOLDER_NAME = "BW_CREDIT_CARD_HOLDER_NAME"
    CREDIT_CARD_NUMBER = "BW_CREDIT_CARD_NUMBER"
    CREDIT_CARD_EXPIRATION_MONTH = "BW_CREDIT_CARD_EXPIRATION_MONTH"
    CREDIT_CARD_EXPIRATION_YEAR = "BW_CREDIT_CARD_EXPIRATION_YEAR"
    CREDIT_CARD_CVV = "BW_CREDIT_CARD_CVV"
    CREDIT_CARD_BRAND = "BW_CREDIT_CARD_BRAND"
    SKYVERN_AUTH_BITWARDEN_ORGANIZATION_ID = "SKYVERN_AUTH_BITWARDEN_ORGANIZATION_ID"
    SKYVERN_AUTH_BITWARDEN_MASTER_PASSWORD = "SKYVERN_AUTH_BITWARDEN_MASTER_PASSWORD"
    SKYVERN_AUTH_BITWARDEN_CLIENT_ID = "SKYVERN_AUTH_BITWARDEN_CLIENT_ID"
    SKYVERN_AUTH_BITWARDEN_CLIENT_SECRET = "SKYVERN_AUTH_BITWARDEN_CLIENT_SECRET"


class BitwardenQueryResult(BaseModel):
    credential: dict[str, str]
    uris: list[str]


class RunCommandResult(BaseModel):
    stdout: str
    stderr: str
    returncode: int


class BitwardenService:
    # --- INÍCIO DAS MODIFICAÇÕES DUMMY ---

    @staticmethod
    async def run_command(
        command: list[str], additional_env: dict[str, str] | None = None, timeout: int = 60
    ) -> RunCommandResult:
        LOG.warning(f"BITWARDEN DUMMY: run_command chamado com: {' '.join(command)}. Retornando sucesso dummy.")
        # Retorna um resultado de sucesso falso, como se o comando tivesse funcionado sem saída.
        return RunCommandResult(stdout="", stderr="", returncode=0)

    @staticmethod
    def _extract_session_key(unlock_cmd_output: str) -> str | None:
        LOG.warning("BITWARDEN DUMMY: _extract_session_key chamado. Retornando chave de sessão dummy.")
        return "dummy_session_key_1234567890"

    @staticmethod
    async def get_secret_value_from_url(*args, **kwargs) -> dict[str, str]:
        LOG.warning("BITWARDEN DUMMY: get_secret_value_from_url chamado. Retornando credencial dummy.")
        return {
            BitwardenConstants.USERNAME: "dummy_user",
            BitwardenConstants.PASSWORD: "dummy_password",
            BitwardenConstants.TOTP: "",
        }

    @staticmethod
    def extract_totp_secret(totp_value: str) -> str:
        # Esta função é um helper e pode ser mantida como está, pois não faz chamadas de rede.
        if not totp_value:
            return ""
        if totp_value.startswith("otpauth://"):
            try:
                query = urllib.parse.urlparse(totp_value).query
                params = dict(urllib.parse.parse_qsl(query))
                return params.get("secret", "")
            except Exception:
                LOG.error("Falha ao parsear TOTP URI (mantido do original)", totp_value=totp_value, exc_info=False)
                return ""
        return totp_value
    
    @staticmethod
    async def _get_secret_value_from_url(*args, **kwargs) -> dict[str, str]:
        LOG.warning("BITWARDEN DUMMY: _get_secret_value_from_url chamado. Retornando credencial dummy.")
        return {
            BitwardenConstants.USERNAME: "dummy_user_internal",
            BitwardenConstants.PASSWORD: "dummy_password_internal",
            BitwardenConstants.TOTP: "",
        }

    @staticmethod
    async def get_sensitive_information_from_identity(*args, **kwargs) -> dict[str, str]:
        LOG.warning("BITWARDEN DUMMY: get_sensitive_information_from_identity chamado. Retornando info dummy.")
        # Retorna um dicionário com chaves esperadas, mas valores dummy
        identity_fields = kwargs.get("identity_fields", [])
        return {field: f"dummy_{field}_value" for field in identity_fields}

    @staticmethod
    async def _get_sensitive_information_from_identity(*args, **kwargs) -> dict[str, str]:
        LOG.warning("BITWARDEN DUMMY: _get_sensitive_information_from_identity (internal) chamado. Retornando info dummy.")
        identity_fields = kwargs.get("identity_fields", [])
        return {field: f"dummy_{field}_value_internal" for field in identity_fields}

    @staticmethod
    async def login(client_id: str, client_secret: str) -> None:
        LOG.warning("BITWARDEN DUMMY: login chamado. Nenhuma ação real.")
        pass

    @staticmethod
    async def unlock(master_password: str) -> str:
        LOG.warning("BITWARDEN DUMMY: unlock chamado. Retornando chave de sessão dummy.")
        return "dummy_session_key_for_unlock_12345"

    @staticmethod
    async def sync() -> None:
        LOG.warning("BITWARDEN DUMMY: sync chamado. Nenhuma ação real.")
        pass

    @staticmethod
    async def logout() -> None:
        LOG.warning("BITWARDEN DUMMY: logout chamado. Nenhuma ação real.")
        pass
    
    @staticmethod
    async def _get_credit_card_data(*args, **kwargs) -> dict[str, str]:
        LOG.warning("BITWARDEN DUMMY: _get_credit_card_data chamado. Retornando dados de CC dummy.")
        return {
            BitwardenConstants.CREDIT_CARD_HOLDER_NAME: "Dummy Holder",
            BitwardenConstants.CREDIT_CARD_NUMBER: "0000000000000000",
            BitwardenConstants.CREDIT_CARD_EXPIRATION_MONTH: "01",
            BitwardenConstants.CREDIT_CARD_EXPIRATION_YEAR: "2030",
            BitwardenConstants.CREDIT_CARD_CVV: "123",
            BitwardenConstants.CREDIT_CARD_BRAND: "DummyCard",
        }

    @staticmethod
    async def get_credit_card_data(*args, **kwargs) -> dict[str, str]:
        LOG.warning("BITWARDEN DUMMY: get_credit_card_data chamado. Retornando dados de CC dummy.")
        return await BitwardenService._get_credit_card_data()


    @staticmethod
    async def _unlock_using_server(master_password: str) -> None:
        LOG.warning(f"BITWARDEN DUMMY: _unlock_using_server chamado para o servidor {BITWARDEN_SERVER_BASE_URL}. Nenhuma chamada de rede real será feita.")
        # Não faz nada para evitar a chamada HTTP para /status ou /unlock
        pass

    @staticmethod
    async def _get_login_item_by_id_using_server(item_id: str) -> PasswordCredential:
        LOG.warning(f"BITWARDEN DUMMY: _get_login_item_by_id_using_server chamado para item {item_id}. Retornando credencial dummy.")
        return PasswordCredential(username="dummy_user_from_server", password="dummy_password_from_server", totp="")

    @staticmethod
    async def _create_login_item_using_server(
        bw_organization_id: str,
        collection_id: str,
        name: str,
        credential: PasswordCredential,
    ) -> str:
        LOG.warning(f"BITWARDEN DUMMY: _create_login_item_using_server chamado para nome {name}. Retornando ID de item dummy.")
        LOG.info(f"DADOS DA CREDENCIAL (NÃO SALVOS): {credential.model_dump_json(exclude_none=True)}")
        return f"dummy_login_item_id_{name.replace(' ', '_')}"

    @staticmethod
    async def _create_credit_card_item_using_server(
        bw_organization_id: str,
        collection_id: str,
        name: str,
        credential: CreditCardCredential,
    ) -> str:
        LOG.warning(f"BITWARDEN DUMMY: _create_credit_card_item_using_server chamado para nome {name}. Retornando ID de item dummy.")
        LOG.info(f"DADOS DO CARTÃO (NÃO SALVOS): {credential.model_dump_json(exclude_none=True)}")
        return f"dummy_cc_item_id_{name.replace(' ', '_')}"

    @staticmethod
    async def create_credential_item(
        collection_id: str, # Receberá "dummy_collection_id_..."
        name: str,
        credential: PasswordCredential | CreditCardCredential,
    ) -> str:
        LOG.warning(f"BITWARDEN DUMMY: create_credential_item chamado para coleção '{collection_id}', nome '{name}'.")
        LOG.info(f"DADOS DA CREDENCIAL (NÃO SERÃO SALVOS DE FORMA SEGURA/FUNCIONAL): {credential.model_dump_json(exclude_none=True)}")
        # Retorna um ID de item falso. O item não será salvo no Bitwarden.
        return f"dummy_created_item_id_{name.replace(' ', '_')}_{str(time.time())[-5:]}"


    # Funções para obter segredos de autenticação do Skyvern com Bitwarden
    # Modificadas para retornar valores dummy e não tentar AWS se as env vars não estiverem setadas.
    @staticmethod
    async def _get_skyvern_auth_master_password() -> str:
        master_password = settings.SKYVERN_AUTH_BITWARDEN_MASTER_PASSWORD
        if not master_password:
            LOG.warning("BITWARDEN DUMMY: SKYVERN_AUTH_BITWARDEN_MASTER_PASSWORD não definida, retornando dummy.")
            return "dummy_master_password_from_settings" # Evita erro "not set"
        return master_password

    @staticmethod
    async def _get_skyvern_auth_organization_id() -> str:
        bw_organization_id = settings.SKYVERN_AUTH_BITWARDEN_ORGANIZATION_ID
        if not bw_organization_id:
            LOG.warning("BITWARDEN DUMMY: SKYVERN_AUTH_BITWARDEN_ORGANIZATION_ID não definida, retornando dummy.")
            return "dummy_org_id_from_settings"
        return bw_organization_id

    @staticmethod
    async def _get_skyvern_auth_client_id() -> str:
        client_id = settings.SKYVERN_AUTH_BITWARDEN_CLIENT_ID
        if not client_id:
            LOG.warning("BITWARDEN DUMMY: SKYVERN_AUTH_BITWARDEN_CLIENT_ID não definida, retornando dummy.")
            return "dummy_client_id_from_settings"
        return client_id

    @staticmethod
    async def _get_skyvern_auth_client_secret() -> str:
        client_secret = settings.SKYVERN_AUTH_BITWARDEN_CLIENT_SECRET
        if not client_secret:
            LOG.warning("BITWARDEN DUMMY: SKYVERN_AUTH_BITWARDEN_CLIENT_SECRET não definida, retornando dummy.")
            return "dummy_client_secret_from_settings"
        return client_secret

    @staticmethod
    async def create_collection(
        name: str,
    ) -> str:
        LOG.warning(f"BITWARDEN DUMMY: create_collection chamado para nome '{name}'. Retornando ID de coleção dummy.")
        # Não tenta mais chamar _get_skyvern_auth_secrets ou _unlock_using_server aqui diretamente
        # pois create_credential_item já os chamaria (e eles são dummy).
        # Apenas retorna um ID falso.
        return f"dummy_collection_id_for_{name.replace(' ', '_')}"

    @staticmethod
    async def _create_collection_using_server(bw_organization_id: str, name: str) -> str:
        LOG.warning(f"BITWARDEN DUMMY: _create_collection_using_server chamado para org {bw_organization_id}, nome {name}. Retornando ID de coleção dummy.")
        return f"dummy_collection_id_server_for_{name.replace(' ', '_')}"


    @staticmethod
    async def _get_skyvern_auth_secrets() -> Tuple[str, str, str, str]:
        LOG.warning("BITWARDEN DUMMY: _get_skyvern_auth_secrets chamado. Retornando todas as credenciais dummy.")
        # Esta função agora é o ponto central para fornecer os dummies.
        master_password = settings.SKYVERN_AUTH_BITWARDEN_MASTER_PASSWORD or "dummy_master_password_default"
        bw_organization_id = settings.SKYVERN_AUTH_BITWARDEN_ORGANIZATION_ID or "dummy_org_id_default"
        client_id = settings.SKYVERN_AUTH_BITWARDEN_CLIENT_ID or "dummy_client_id_default"
        client_secret = settings.SKYVERN_AUTH_BITWARDEN_CLIENT_SECRET or "dummy_client_secret_default"
        
        # Logar se alguma variável de ambiente específica do Bitwarden não estiver definida,
        # para que você saiba que os defaults dummy estão sendo usados.
        if not settings.SKYVERN_AUTH_BITWARDEN_MASTER_PASSWORD:
            LOG.info("SKYVERN_AUTH_BITWARDEN_MASTER_PASSWORD não definida, usando default dummy.")
        if not settings.SKYVERN_AUTH_BITWARDEN_ORGANIZATION_ID:
            LOG.info("SKYVERN_AUTH_BITWARDEN_ORGANIZATION_ID não definida, usando default dummy.")
        if not settings.SKYVERN_AUTH_BITWARDEN_CLIENT_ID:
            LOG.info("SKYVERN_AUTH_BITWARDEN_CLIENT_ID não definida, usando default dummy.")
        if not settings.SKYVERN_AUTH_BITWARDEN_CLIENT_SECRET:
            LOG.info("SKYVERN_AUTH_BITWARDEN_CLIENT_SECRET não definida, usando default dummy.")
            
        return master_password, bw_organization_id, client_id, client_secret

    # As funções abaixo provavelmente não serão chamadas se você só estiver tentando "Add Credential"
    # e as funções acima já retornam valores dummy. Mas, por segurança, podemos torná-las dummy também.

    @staticmethod
    async def get_items_by_item_ids(item_ids: list[str]) -> list[CredentialItem]:
        LOG.warning(f"BITWARDEN DUMMY: get_items_by_item_ids chamado para IDs: {item_ids}. Retornando lista vazia.")
        return []

    @staticmethod
    async def _get_items_by_item_ids_using_server(item_ids: list[str]) -> list[CredentialItem]:
        LOG.warning(f"BITWARDEN DUMMY: _get_items_by_item_ids_using_server chamado. Retornando lista vazia.")
        return []

    @staticmethod
    async def get_collection_items(collection_id: str) -> list[CredentialItem]:
        LOG.warning(f"BITWARDEN DUMMY: get_collection_items chamado para coleção {collection_id}. Retornando lista vazia.")
        return []

    @staticmethod
    async def _get_collection_items_using_server(collection_id: str) -> list[CredentialItem]:
        LOG.warning(f"BITWARDEN DUMMY: _get_collection_items_using_server chamado. Retornando lista vazia.")
        return []

    @staticmethod
    async def get_credential_item(item_id: str) -> CredentialItem:
        LOG.warning(f"BITWARDEN DUMMY: get_credential_item chamado para item {item_id}. Retornando item dummy.")
        return CredentialItem(
            item_id=item_id,
            credential=PasswordCredential(username="dummy", password="dummy", totp=""),
            name="Dummy Item Retrieved",
            credential_type=CredentialType.PASSWORD,
        )

    @staticmethod
    async def _get_credential_item_by_id_using_server(item_id: str) -> CredentialItem:
        LOG.warning(f"BITWARDEN DUMMY: _get_credential_item_by_id_using_server chamado. Retornando item dummy.")
        return CredentialItem(
            item_id=item_id,
            credential=PasswordCredential(username="dummy_server", password="dummy_server_pass", totp=""),
            name="Dummy Server Item Retrieved",
            credential_type=CredentialType.PASSWORD,
        )

    @staticmethod
    async def delete_credential_item(item_id: str) -> None:
        LOG.warning(f"BITWARDEN DUMMY: delete_credential_item chamado para item {item_id}. Nenhuma ação real.")
        pass

    @staticmethod
    async def _delete_credential_item_using_server(item_id: str) -> None:
        LOG.warning(f"BITWARDEN DUMMY: _delete_credential_item_using_server chamado. Nenhuma ação real.")
        pass

    # --- FIM DAS MODIFICAÇÕES DUMMY ---
