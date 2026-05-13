import boto3
from airflow.hooks.base import BaseHook
from botocore.config import Config
from botocore.exceptions import ClientError
from loguru import logger


class MinIOHook(BaseHook):
    """Hook para conexão com MinIO/S3."""

    conn_name_attr = "minio_conn_id"
    conn_type = "http"

    def __init__(self, minio_conn_id: str = "minio_default"):
        super().__init__()
        self.minio_conn_id = minio_conn_id
        self._client = None

    def get_conn(self):
        """Retorna cliente boto3 configurado."""
        if self._client is None:
            conn = self.get_connection(self.minio_conn_id)
            logger.info(f"Connection encontrada: host={conn.host}, port={conn.port}, login={conn.login}")

            if not conn.host:
                raise ValueError(f"Connection '{self.minio_conn_id}' não tem host configurado!")

            endpoint = f"http://{conn.host}:{conn.port}"
            logger.info(f"Conectando ao MinIO: {endpoint}")

            self._client = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=conn.login,
                aws_secret_access_key=conn.password,
                aws_session_token=None,
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                ),
                region_name="us-east-1",
            )

        return self._client

    def list_objects(self, bucket: str, prefix: str = "") -> list[dict]:
        """Lista objetos no bucket com prefixo."""
        client = self.get_conn()
        try:
            response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            return response.get("Contents", [])
        except ClientError as e:
            logger.error(f"Erro ao listar objetos em {bucket}: {e}")
            return []

    def download_file(self, bucket: str, key: str, local_path: str) -> bool:
        """Download arquivo do MinIO para local."""
        client = self.get_conn()
        try:
            client.download_file(bucket, key, local_path)
            logger.info(f"Download concluído: {key} -> {local_path}")
            return True
        except ClientError as e:
            logger.error(f"Erro ao baixar {key}: {e}")
            return False

    def upload_file(self, bucket: str, key: str, local_path: str) -> bool:
        """Upload arquivo local para MinIO."""
        client = self.get_conn()
        try:
            client.upload_file(local_path, bucket, key)
            logger.info(f"Upload concluído: {local_path} -> {key}")
            return True
        except ClientError as e:
            logger.error(f"Erro ao subir {key}: {e}")
            return False

    def get_object_metadata(self, bucket: str, key: str) -> dict | None:
        """Retorna metadados do objeto."""
        client = self.get_conn()
        try:
            return client.head_object(Bucket=bucket, Key=key)
        except ClientError:
            return None

    def delete_object(self, bucket: str, key: str) -> bool:
        """Deleta objeto do bucket."""
        client = self.get_conn()
        try:
            client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Objeto deletado: {key}")
            return True
        except ClientError as e:
            logger.error(f"Erro ao deletar {key}: {e}")
            return False

    def move_object(self, bucket: str, source_key: str, dest_key: str) -> bool:
        """Move/copia objeto de source_key para dest_key e deleta o original."""
        client = self.get_conn()
        try:
            client.copy(
                CopySource={"Bucket": bucket, "Key": source_key},
                Bucket=bucket,
                Key=dest_key
            )
            client.delete_object(Bucket=bucket, Key=source_key)
            logger.info(f"Arquivo movido: {source_key} -> {dest_key}")
            return True
        except ClientError as e:
            logger.error(f"Erro ao mover {source_key} para {dest_key}: {e}")
            return False
