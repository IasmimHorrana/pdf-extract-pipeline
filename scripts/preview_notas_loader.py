"""
Preview do NotasCorretagemLoader - Visualiza dados estruturados antes de salvar.
"""

import json

from src.extractors import PDFExtractor
from src.loaders.notas_corretagem_loader import NotasCorretagemLoader
from src.utils.logging_config import setup_logging

setup_logging()

pdf_path = "samples/Notas_Corretagem_Final-1.pdf"

print("=" * 60)
print("PREVIEW - NOTAS DE CORRETAGEM (DATA WAREHOUSE)")
print("=" * 60)

extractor = PDFExtractor()
result = extractor.extract(pdf_path)

extraction_data = extractor.extract_to_dict(pdf_path)

loader = NotasCorretagemLoader()
preview = loader.load_preview(extraction_data)

print("\n--- 1. nota_corretagem ---")
print(json.dumps(preview["nota_corretagem"], indent=2, ensure_ascii=False))

print("\n--- 2. operacoes ---")
for op in preview["operacoes"]:
    print(json.dumps(op, indent=2, ensure_ascii=False))
    print("---")

print("\n--- 3. taxas ---")
print(json.dumps(preview["taxas"], indent=2, ensure_ascii=False))

print("\n" + "=" * 60)
print("RESUMO")
print("=" * 60)
print("Tabela 'notas_corretagem': 1 registro")
print(f"Tabela 'operacoes': {len(preview['operacoes'])} registro(s)")
print("Tabela 'taxas': 1 registro (se houver taxas)")
print("Tabela 'dados_brutos': 1 registro (backup)")
