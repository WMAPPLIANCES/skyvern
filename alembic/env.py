# Conteúdo para: alembic/env.py

from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# Importar seus modelos SQLAlchemy para que o Alembic os reconheça para autogenerate
# Você PRECISA ajustar este import para o caminho correto dos seus modelos no Skyvern.
# Se o Skyvern usa um Base declarativo central, importe-o.
# Exemplo: from skyvern.models import Base  # Ou skyvern.db.models, etc.
# Se não, você pode precisar importar todos os seus modelos individualmente ou
# configurar target_metadata de outra forma (ver documentação do Alembic).
# Por enquanto, vamos deixar como None, o que significa que 'autogenerate' pode não funcionar
# perfeitamente sem mais configuração, mas 'alembic upgrade head' ainda deve aplicar migrações existentes.
target_metadata = None
# try:
#     from skyvern.forge.sdk.db.models import Base # Tente um caminho comum
#     target_metadata = Base.metadata
# except ImportError:
#     print("ALEMBIC/ENV.PY: Não foi possível importar Base de skyvern.forge.sdk.db.models. Autogenerate pode ser limitado.")
#     pass


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_db_url_from_env():
    """
    Obtém a URL do banco de dados da variável de ambiente DATABASE_STRING
    e a ajusta para uso síncrono pelo Alembic.
    """
    db_url = os.environ.get("DATABASE_STRING")

    if not db_url:
        # Fallback para sqlalchemy.url do alembic.ini se DATABASE_STRING não estiver definida
        # (Não ideal, pois queremos que a variável de ambiente seja a fonte da verdade)
        print("ALEMBIC/ENV.PY: DATABASE_STRING não encontrada no ambiente. Tentando ler de alembic.ini sqlalchemy.url...")
        db_url = config.get_main_option("sqlalchemy.url")
        if not db_url:
            raise ValueError(
                "DATABASE_STRING environment variable not set and sqlalchemy.url not found in alembic.ini"
            )
        print(f"ALEMBIC/ENV.PY: Usando sqlalchemy.url de alembic.ini: {db_url}")
    else:
        print(f"ALEMBIC/ENV.PY: Usando DATABASE_STRING da variável de ambiente: {db_url}")

    # Garante que estamos usando um dialeto síncrono para o Alembic
    # Isso é crucial se a DATABASE_STRING usa um dialeto async como psycopg_async ou asyncpg
    if db_url.startswith("postgresql+psycopg_async://"):
        db_url = db_url.replace("postgresql+psycopg_async://", "postgresql+psycopg://", 1)
        print(f"ALEMBIC/ENV.PY: Convertido para URL síncrona (de psycopg_async): {db_url}")
    elif db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        print(f"ALEMBIC/ENV.PY: Convertido para URL síncrona (de asyncpg): {db_url}")
    
    # Se já for postgresql:// ou postgresql+psycopg://, está bom.
    if not (db_url.startswith("postgresql+psycopg://") or db_url.startswith("postgresql://")):
        print(f"ALEMBIC/ENV.PY WARNING: URL do DB '{db_url}' não parece ser um dialeto psycopg síncrono padrão. Verifique.")

    return db_url

# Atualizar a configuração do Alembic para usar a URL do banco de dados da variável de ambiente
# Isso garante que tanto run_migrations_offline quanto run_migrations_online usem a URL correta.
effective_db_url = get_db_url_from_env()
if effective_db_url:
    config.set_main_option("sqlalchemy.url", effective_db_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Usar a URL que já foi processada e definida em config.get_main_option
    connectable_url = config.get_main_option("sqlalchemy.url")
    
    # Criar uma engine SÍNCRONA para o Alembic
    connectable = create_engine(connectable_url)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
