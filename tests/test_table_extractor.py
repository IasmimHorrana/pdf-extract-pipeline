"""
Teste do TableExtractor ajustado.
"""

from src.extractors.table_extractor import TableExtractor
from src.utils.logging_config import setup_logging

setup_logging()

pdf_path = "samples/Notas_Corretagem_Final-1.pdf"

print("=== Teste 1: Detecção Automática ===")
extractor = TableExtractor()
results = extractor.extract(pdf_path)

print(f"Tabelas encontradas: {len(results)}")
for r in results:
    print(f"  Página {r.page_number}: {r.table_count} tabelas, accuracy {r.accuracy}%")
    print(f"  Dados: {r.table_data[:3]}...")

print("\n=== Teste 2: Como DataFrame ===")
df = extractor.extract_dataframe(pdf_path)
if df is not None:
    print(df.to_string())

print("\n=== Teste 3: Como Dict ===")
data = extractor.extract_as_dict(pdf_path)
print(f"Keys: {data[0].keys() if data else 'vazio'}")
