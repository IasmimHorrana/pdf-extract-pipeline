"""
Teste real do NotasCorretagemLoader - insere no banco.
"""

import os

import psycopg2

from src.extractors import PDFExtractor
from src.loaders.notas_corretagem_loader import NotasCorretagemLoader
from src.utils.logging_config import setup_logging

os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "pdf_db"
os.environ["DB_USER"] = "weather_user"
os.environ["DB_PASSWORD"] = "weather_pass"

setup_logging()

pdf_path = "samples/Notas_Corretagem_Final-1.pdf"

print("=" * 60)
print("TESTE REAL - INSERÇÃO NO BANCO")
print("=" * 60)

extractor = PDFExtractor()
result = extractor.extract(pdf_path)
extraction_data = extractor.extract_to_dict(pdf_path)

loader = NotasCorretagemLoader()
nota_id = loader.load(extraction_data)

if nota_id:
    print(f"\n✓ Sucesso! Nota inserida com ID: {nota_id}")
else:
    print("\n✗ Erro ao inserir")

loader.close()

print("\n" + "=" * 60)
print("VERIFICANDO DADOS NO BANCO")
print("=" * 60)

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="pdf_db",
    user="weather_user",
    password="weather_pass"
)

cur = conn.cursor()

cur.execute("SELECT id, cliente, conta_liquidacao, corretora FROM notas_corretagem WHERE id = %s", (nota_id,))
nota = cur.fetchone()
print(f"\nnotas_corretagem: {nota}")

cur.execute("SELECT id, operacao, mercadoria, quantidade, cotacao FROM operacoes WHERE nota_id = %s", (nota_id,))
operacoes = cur.fetchall()
print(f"operacoes ({len(operacoes)}):")
for op in operacoes:
    print(f"  {op}")

cur.execute("SELECT irrf, ajuste, taxa_corretagem, taxa_registro FROM taxas WHERE nota_id = %s", (nota_id,))
taxas = cur.fetchone()
print(f"taxas: {taxas}")

conn.close()
print("\n✓ Teste concluído com sucesso!")
