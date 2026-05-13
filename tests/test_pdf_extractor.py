"""
Teste do PDFExtractor (wrapper text + table).
"""

from src.extractors import PDFExtractor
from src.utils.logging_config import setup_logging

setup_logging()

pdf_path = "samples/Notas_Corretagem_Final-1.pdf"

print("=== Teste PDFExtractor ===\n")

extractor = PDFExtractor()
result = extractor.extract(pdf_path)

print(f"Arquivo: {result.file_name}")
print(f"Páginas: {result.total_pages}")
print(f"Tabelas: {result.total_tables}")
print(f"Sucesso: {result.success}")

print("\n--- Texto (primeira página) ---")
if result.text_pages:
    print(result.text_pages[0]["text_content"][:300])

print("\n--- Tabelas ---")
for t in result.tables:
    print(f"  Página {t['page_number']}: {t['extraction_method']}, accuracy {t['accuracy']}%")

print("\n--- Dict output ---")
data = extractor.extract_to_dict(pdf_path)
print(f"Keys: {data.keys()}")
