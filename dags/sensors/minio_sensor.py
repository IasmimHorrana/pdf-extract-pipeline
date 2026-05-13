import sys
from pathlib import Path

from airflow.sensors.base import BaseSensorOperator
from airflow.utils.context import Context

sys.path.insert(0, "/opt/airflow/src")

from dags.hooks.minio_hook import MinIOHook
from utils.logging_config import get_logger

logger = get_logger("MinIOSensor")


class MinIONewFileSensor(BaseSensorOperator):
    """
    Sensor que detecta novos arquivos PDF no bucket MinIO.

    Comportamento:
    - Verifica a cada poke_interval (default 60s)
    - Só detecta arquivos que não estão na lista de processados (tracked_files)
    - Armazena lista de arquivos já detectados na pasta .sensor_state/
    - Ao marcar como processado, adiciona à lista tracked_files
    """

    template_fields = ("bucket", "prefix", "processed_marker")

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        processed_marker: str = "processed/",
        minio_conn_id: str = "minio_default",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.bucket = bucket
        self.prefix = prefix
        self.processed_marker = processed_marker
        self.minio_conn_id = minio_conn_id
        self.hook = MinIOHook(minio_conn_id=self.minio_conn_id)

    def poke(self, context: Context) -> bool:
        """Verifica se há novos arquivos não processados."""
        logger.info(f"Verificando bucket '{self.bucket}' prefixo '{self.prefix}'")

        objects = self.hook.list_objects(self.bucket, self.prefix)

        if not objects:
            logger.debug("Nenhum arquivo encontrado")
            return False

        tracked = self._get_tracked_files()
        new_files = []

        for obj in objects:
            key = obj["Key"]
            if not key.endswith(".pdf"):
                continue
            if self.processed_marker in key:
                continue
            if key in tracked:
                continue
            new_files.append(key)

        if new_files:
            logger.info(f"Encontrados {len(new_files)} novos arquivos: {new_files}")
            context["ti"].xcom_push(key="new_files", value=new_files)
            return True

        logger.debug("Nenhum arquivo novo encontrado")
        return False

    def _get_tracked_files(self) -> set:
        """Retorna conjunto de arquivos já processados."""
        state_file = Path(f".sensor_state/{self.bucket}_{self.prefix.replace('/', '_')}.txt")
        if state_file.exists():
            with open(state_file) as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def mark_processed(self, file_key: str):
        """Marca arquivo como processado."""
        state_file = Path(f".sensor_state/{self.bucket}_{self.prefix.replace('/', '_')}.txt")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, "a") as f:
            f.write(f"{file_key}\n")
        logger.debug(f"Arquivo marcado como processado: {file_key}")
