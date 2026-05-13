import json
import os
import re
from datetime import datetime

import psycopg2
from loguru import logger


def _convert_date_to_iso(date_str: str) -> str:
    """Converte data de DD/MM/YYYY para YYYY-MM-DD (formato ISO)."""
    if not date_str:
        return date_str
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return date_str


class NotasCorretagemLoader:
    """Loader para salvar notas de corretagem no PostgreSQL de forma estruturada.
    Usa schema 'dw' para dados de negócio e 'staging' para dados brutos.
    Suporta idempotência (upsert) para evitar duplicatas.
    """

    def __init__(self, db_config: dict | None = None):
        self.db_config = db_config or {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "pdf_db"),
            "user": os.getenv("DB_USER", "weather_user"),
            "password": os.getenv("DB_PASSWORD", "weather_pass")
        }
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("Conectado ao PostgreSQL")
        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Conexão fechada")

    def _parse_nota_data(self, text_content: str) -> dict:
        """Parse do texto extraído para extrair campos estruturados."""
        data = {}

        cliente_match = re.search(r"Cliente:\s*(.+?)(?:\s+Conta|$)", text_content)
        if cliente_match:
            data["cliente"] = cliente_match.group(1).strip()

        conta_match = re.search(r"Conta Liquidação:\s*(\d+)", text_content)
        if conta_match:
            data["conta_liquidacao"] = conta_match.group(1)

        cidade_match = re.search(r"Cidade:\s*(.+?)(?:\s+Número|$)", text_content)
        if cidade_match:
            data["cidade"] = cidade_match.group(1).strip()

        nota_match = re.search(r"Número da Fatura:\s*(\d+)", text_content)
        if nota_match:
            data["numero_fatura"] = nota_match.group(1)

        nota_pos = text_content.find("Nº NOTA")
        if nota_pos != -1:
            remaining = text_content[nota_pos + 7:]
            match = re.search(r"(\d+)\s+(\d{2}/\d{2}/)\s*%?(\d{4})", remaining)
            if match:
                data["nota_numero"] = int(match.group(1))
                raw_date = match.group(2) + match.group(3)
                data["data_pregao"] = _convert_date_to_iso(raw_date)

        corretora_match = re.search(r"(Alpha Investimentos|Corretora.*)", text_content, re.IGNORECASE)
        if corretora_match:
            data["corretora"] = corretora_match.group(1).strip()

        return data

    def _parse_operacoes(self, text_content: str) -> list:
        """Parse das operações de compra/venda."""
        operacoes = []
        linhas = text_content.split("\n")

        for linha in linhas:
            pattern = r"(V|C)\s+([A-Z]{3,5}\d)\s+(\w+)\s+(\d{2}/\d{2}/\d{4})\s+(\d+)\s+([\d,]+)\s+([\d,]+)"
            match = re.search(pattern, linha)
            if match:
                operacoes.append({
                    "operacao": match.group(1),
                    "mercadoria": match.group(2),
                    "tipo": match.group(3),
                    "vencimento": match.group(4),
                    "quantidade": int(match.group(5)),
                    "cotacao": float(match.group(6).replace(",", ".")),
                    "taxa_op": float(match.group(7).replace(",", "."))
                })

        return operacoes

    def _parse_taxas(self, text_content: str) -> dict:
        """Parse das taxas e impostos."""
        taxas = {}

        irrf_match = re.search(r"IRRF\s+([\d,]+)", text_content)
        if irrf_match:
            taxas["irrf"] = float(irrf_match.group(1).replace(",", "."))

        ajuste_match = re.search(r"Ajuste\s+([\d,]+)", text_content)
        if ajuste_match:
            taxas["ajuste"] = float(ajuste_match.group(1).replace(",", "."))

        corretagem_match = re.search(r"Taxa Corretagem\s+([\d,]+)", text_content)
        if corretagem_match:
            taxas["taxa_corretagem"] = float(corretagem_match.group(1).replace(",", "."))

        registro_match = re.search(r"Taxa Registro/Bolsa\s+([\d,]+)", text_content)
        if registro_match:
            taxas["taxa_registro"] = float(registro_match.group(1).replace(",", "."))

        return taxas

    def _check_nota_exists(self, cur, corretora: str, conta: str, numero_fatura: str, data_pregao: str) -> int | None:
        """Verifica se a nota já existe (idempotência). Retorna o ID se existir."""
        cur.execute("""
            SELECT id FROM dw.notas_corretagem
            WHERE corretora = %s
              AND conta_liquidacao = %s
              AND numero_fatura = %s
              AND data_pregao = %s
        """, (corretora, conta, numero_fatura, data_pregao))

        result = cur.fetchone()
        return result[0] if result else None

    def load(self, extraction_result: dict) -> int | None:
        """Salva os dados extraídos no PostgreSQL com idempotência."""
        if not self.conn:
            self.connect()

        try:
            with self.conn.cursor() as cur:
                parsed_data = self._parse_nota_data(
                    extraction_result.get("text_pages", [{}])[0].get("text_content", "")
                )
                operacoes = self._parse_operacoes(
                    extraction_result.get("text_pages", [{}])[0].get("text_content", "")
                )
                taxas = self._parse_taxas(
                    extraction_result.get("text_pages", [{}])[0].get("text_content", "")
                )

                corretora = parsed_data.get("corretora")
                conta = parsed_data.get("conta_liquidacao")
                numero_fatura = parsed_data.get("numero_fatura")
                data_pregao = parsed_data.get("data_pregao")

                existing_id = self._check_nota_exists(cur, corretora, conta, numero_fatura, data_pregao)

                if existing_id:
                    logger.warning(f"Nota já existe com ID: {existing_id}. Atualizando...")
                    nota_id = existing_id
                    upload_date = extraction_result.get("upload_date")
                    cur.execute("""
                        UPDATE dw.notas_corretagem SET
                            file_name = %s,
                            cliente = %s,
                            cidade = %s,
                            nota_numero = %s,
                            file_size = %s,
                            processed_date = CURRENT_TIMESTAMP,
                            status = %s,
                            error_message = NULL,
                            upload_date = COALESCE(upload_date, %s)
                        WHERE id = %s
                    """, (
                        extraction_result.get("file_name"),
                        parsed_data.get("cliente"),
                        parsed_data.get("cidade"),
                        parsed_data.get("nota_numero"),
                        extraction_result.get("file_size"),
                        "success",
                        upload_date,
                        nota_id
                    ))
                else:
                    upload_date = extraction_result.get("upload_date")
                    cur.execute("""
                        INSERT INTO dw.notas_corretagem (
                            file_name, corretora, cliente, conta_liquidacao,
                            cidade, numero_fatura, nota_numero, data_pregao,
                            file_size, status, upload_date
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                    """, (
                        extraction_result.get("file_name"),
                        corretora,
                        parsed_data.get("cliente"),
                        conta,
                        parsed_data.get("cidade"),
                        numero_fatura,
                        parsed_data.get("nota_numero"),
                        data_pregao,
                        extraction_result.get("file_size"),
                        "success",
                        upload_date
                    ))
                    nota_id = cur.fetchone()[0]
                    logger.info(f"Nota inserida com ID: {nota_id}")

                cur.execute("DELETE FROM dw.operacoes WHERE nota_id = %s", (nota_id,))
                for op in operacoes:
                    cur.execute("""
                        INSERT INTO dw.operacoes (
                            nota_id, operacao, mercadoria, tipo,
                            vencimento, quantidade, cotacao, taxa_op
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        nota_id, op["operacao"], op["mercadoria"], op["tipo"],
                        op["vencimento"], op["quantidade"], op["cotacao"], op["taxa_op"]
                    ))
                logger.info(f"Inseridas {len(operacoes)} operações")

                cur.execute("DELETE FROM dw.taxas WHERE nota_id = %s", (nota_id,))
                if taxas:
                    cur.execute("""
                        INSERT INTO dw.taxas (nota_id, irrf, ajuste, taxa_corretagem, taxa_registro)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        nota_id,
                        taxas.get("irrf"),
                        taxas.get("ajuste"),
                        taxas.get("taxa_corretagem"),
                        taxas.get("taxa_registro")
                    ))
                    logger.info("Taxas inseridas")

                cur.execute("DELETE FROM staging.dados_brutos WHERE nota_id = %s", (nota_id,))
                cur.execute("""
                    INSERT INTO staging.dados_brutos (nota_id, text_content, table_data)
                    VALUES (%s, %s, %s)
                """, (
                    nota_id,
                    extraction_result.get("text_pages", [{}])[0].get("text_content"),
                    json.dumps(extraction_result.get("tables", []))
                ))

                self.conn.commit()
                logger.info("Dados salvos com sucesso!")
                return nota_id

        except psycopg2.IntegrityError as e:
            logger.error(f"Violação de constraint (duplicata): {e}")
            self.conn.rollback()
            return None
        except Exception as e:
            logger.error(f"Erro ao salvar: {e}")
            self.conn.rollback()
            return None

    def load_preview(self, extraction_result: dict) -> dict:
        """Mostra o que seria salvo sem inserir no banco."""
        text_content = extraction_result.get("text_pages", [{}])[0].get("text_content", "")

        parsed_data = self._parse_nota_data(text_content)
        operacoes = self._parse_operacoes(text_content)
        taxas = self._parse_taxas(text_content)

        return {
            "nota_corretagem": {
                "file_name": extraction_result.get("file_name"),
                "corretora": parsed_data.get("corretora"),
                "cliente": parsed_data.get("cliente"),
                "conta_liquidacao": parsed_data.get("conta_liquidacao"),
                "cidade": parsed_data.get("cidade"),
                "numero_fatura": parsed_data.get("numero_fatura"),
                "nota_numero": parsed_data.get("nota_numero"),
                "data_pregao": parsed_data.get("data_pregao"),
            },
            "operacoes": operacoes,
            "taxas": taxas,
            "idempotency_key": (
                f"{parsed_data.get('corretora')}_"
                f"{parsed_data.get('conta_liquidacao')}_"
                f"{parsed_data.get('numero_fatura')}_"
                f"{parsed_data.get('data_pregao')}"
            )
        }
