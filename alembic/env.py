from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# Tente importar sua Base declarativa dos modelos SQLAlchemy do Skyvern.
# Ajuste o caminho do import se necessário.
# Exemplo: from skyvern.forge.sdk.db.models import Base
# Se não conseguir importar, autogenerate pode ser limitado.
target_metadata = None
try:
    from skyvern.forge.sdk.db.models import Base # Tente este caminho comum
    target_metadata = Base.metadata
    print("ALEMBIC/ENV.PY: Base metadata importada com sucesso de skyvern.forge.sdk.db.models.")
except ImportError:
    print("ALEMBIC/ENV.PY: Não foi possível importar Base de skyvern.forge.sdk.db.models. Autogenerate pode ser limitado. target_metadata = None.")
    pass


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_db_url_from_env():
    db_url = os.environ.get("DATABASE_STRING")

    if not db_url:
        print("ALEMBIC/ENV.PY: DATABASE_STRING não encontrada no ambiente. Tentando ler de alembic.ini sqlalchemy.url...")
        db_url = config.get_main_option("sqlalchemy.url")
        if not db_url:
            raise ValueError(
                "DATABASE_STRING environment variable not set and sqlalchemy.url not found in alembic.ini"
            )
        print(f"ALEMBIC/ENV.PY: Usando sqlalchemy.url de alembic.ini: {db_url}")
    else:
        print(f"ALEMBIC/ENV.PY: Usando DATABASE_STRING da variável de ambiente: {db_url}")

    if db_url.startswith("postgresql+psycopg_async://"):
        db_url = db_url.replace("postgresql+psycopg_async://", "postgresql+psycopg://", 1)
        print(f"ALEMBIC/ENV.PY: Convertido para URL síncrona (de psycopg_async): {db_url}")
    elif db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        print(f"ALEMBIC/ENV.PY: Convertido para URL síncrona (de asyncpg): {db_url}")
    
    if not (db_url.startswith("postgresql+psycopg://") or db_url.startswith("postgresql://")):
        print(f"ALEMBIC/ENV.PY WARNING: URL do DB '{db_url}' não parece ser um dialeto psycopg síncrono padrão. Verifique.")

    return db_url

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
    connectable_url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(connectable_url)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
