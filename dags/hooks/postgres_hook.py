import psycopg2
from airflow.hooks.base import BaseHook
from loguru import logger


class PostgresHook(BaseHook):
    """Hook para conexão com PostgreSQL usando credentials do Airflow."""

    conn_name_attr = "postgres_conn_id"
    conn_type = "postgres"

    def __init__(self, postgres_conn_id: str = "postgres_default"):
        super().__init__()
        self.postgres_conn_id = postgres_conn_id
        self._conn = None

    def get_conn(self):
        """Retorna conexão psycopg2."""
        if self._conn is None or self._conn.closed:
            conn = self.get_connection(self.postgres_conn_id)
            self._conn = psycopg2.connect(
                host=conn.host,
                port=conn.port or 5432,
                database=conn.schema or "pdf_db",
                user=conn.login,
                password=conn.password,
            )
            logger.info(f"Conectado ao PostgreSQL ({conn.host}:{conn.port}/{conn.schema})")
        return self._conn

    def get_records(self, sql: str, params: tuple | None = None) -> list:
        """Executa SELECT e retorna resultados."""
        conn = self.get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def run(self, sql: str, params: tuple | None = None) -> None:
        """Executa SQL (INSERT, UPDATE, DELETE)."""
        conn = self.get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()

    def run_many(self, sql: str, data: list[tuple]) -> None:
        """Executa SQL com múltiplos valores (executemany)."""
        conn = self.get_conn()
        with conn.cursor() as cur:
            cur.executemany(sql, data)
        conn.commit()

    def close(self) -> None:
        """Fecha conexão."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            logger.info("Conexão PostgreSQL fechada")
