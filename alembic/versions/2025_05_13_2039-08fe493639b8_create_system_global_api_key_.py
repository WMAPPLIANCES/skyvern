"""create_system_global_api_key_organization

Revision ID: 08fe493639b8
Revises: 07cb499ecbce
Create Date: 2025-05-13 20:39:52.378864+00:00 
# A data de criação acima é um exemplo, o seu arquivo terá a data/hora exata da geração.
# Mantenha a 'Create Date' que o Alembic gerou no seu arquivo.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime
# Importar o tipo JSONB se você estiver usando PostgreSQL e o campo for JSONB.
# Se for um JSON genérico, pode ser apenas sqlalchemy.JSON.
# Verifique a definição do seu modelo Organization para bw_collection_ids.
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
# Estes valores DEVEM CORRESPONDER aos que o Alembic gerou no nome do arquivo e no cabeçalho do arquivo.
revision: str = '08fe493639b8' # ID desta revisão
down_revision: Union[str, None] = '07cb499ecbce' # ID da revisão anterior (última que rodou com sucesso)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Definição da tabela 'organizations' para a inserção.
# Certifique-se de que os nomes das colunas e tipos correspondem EXATAMENTE
# à sua tabela 'organizations' no banco de dados, conforme definido pelo seu modelo Pydantic
# e pelas migrações anteriores do Skyvern.
organizations_table_def = sa.Table('organizations', sa.MetaData(),
    sa.Column('organization_id', sa.String, primary_key=True),
    sa.Column('organization_name', sa.String, nullable=False),
    sa.Column('webhook_callback_url', sa.String, nullable=True),
    sa.Column('max_steps_per_run', sa.Integer, nullable=True),
    sa.Column('max_retries_per_step', sa.Integer, nullable=True),
    sa.Column('domain', sa.String, nullable=True),
    sa.Column('bw_organization_id', sa.String, nullable=True),
    sa.Column('bw_collection_ids', JSONB, nullable=True), # Assumindo JSONB para listas no PostgreSQL
    sa.Column('created_at', sa.DateTime, nullable=False),
    sa.Column('modified_at', sa.DateTime, nullable=False)
    # Adicione mais colunas aqui se o seu modelo Organization tiver outros campos obrigatórios
    # que não são opcionais e não têm valores padrão.
)

SYSTEM_ORG_ID = "SYSTEM_GLOBAL_API_KEY_ORG"
SYSTEM_ORG_NAME = "System Global API Key Access"

def upgrade() -> None:
    """
    Aplica a migração: insere a organização do sistema se ela não existir.
    """
    bind = op.get_bind() # Obtém a conexão atual que o Alembic está usando
    session = sa.orm.Session(bind=bind) # Cria uma sessão SQLAlchemy ligada a essa conexão

    # Verifica se a organização do sistema já existe para evitar erros de chave duplicada
    existing_org = session.execute(
        sa.select(organizations_table_def.c.organization_id)
        .where(organizations_table_def.c.organization_id == SYSTEM_ORG_ID)
    ).first()

    if not existing_org:
        # Se não existir, insere a nova organização do sistema
        op.bulk_insert(organizations_table_def,
            [
                {
                    'organization_id': SYSTEM_ORG_ID,
                    'organization_name': SYSTEM_ORG_NAME,
                    'webhook_callback_url': None,
                    'max_steps_per_run': 1000,  # Exemplo de valor padrão, ajuste se necessário
                    'max_retries_per_step': 5,    # Exemplo de valor padrão, ajuste se necessário
                    'domain': None,
                    'bw_organization_id': None,
                    'bw_collection_ids': None,  # Ou [] se o campo for JSONB e aceitar lista vazia e for preferível
                    'created_at': datetime.utcnow(),
                    'modified_at': datetime.utcnow()
                    # Certifique-se de que todos os campos NOT NULL sem valor padrão no DB estão aqui
                }
            ]
        )
        print(f"INFO: [Alembic Migration {revision}] Inserida a organização do sistema: ID={SYSTEM_ORG_ID}")
    else:
        print(f"INFO: [Alembic Migration {revision}] Organização do sistema já existe: ID={SYSTEM_ORG_ID}. Nenhuma ação de inserção realizada.")
    
    # Não é estritamente necessário chamar session.commit() aqui quando se usa op.bulk_insert,
    # pois o Alembic gerencia a transação principal da migração.
    # No entanto, se você fizesse outras operações com a sessão (ex: session.add()), um commit seria necessário.

def downgrade() -> None:
    """
    Reverte a migração: remove a organização do sistema.
    Use com cuidado em ambientes de produção.
    """
    op.execute(
        organizations_table_def.delete().where(organizations_table_def.c.organization_id == SYSTEM_ORG_ID)
    )
    print(f"INFO: [Alembic Migration {revision}] Removida a organização do sistema: ID={SYSTEM_ORG_ID}")
