import os

import camelot
import matplotlib
import matplotlib.pyplot as plt
from PyPDF2 import PdfReader

matplotlib.use("Agg")

file_name = "Notas_Corretagem_Final-1"
path = os.path.abspath(f"samples/{file_name}.pdf")

print("=" * 60)
print("VISUALIZAÇÃO COMPLETA DO PDF")
print("=" * 60)

print("\n--- 1. TEXTO COMPLETO DO PDF ---")
reader = PdfReader(path)
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    print(f"\n--- Página {i+1} ---")
    print(text)
    print("-" * 40)

print("\n" + "=" * 60)
print("--- 2. TABELAS DETECTADAS ---")
print("=" * 60)

tables = camelot.read_pdf(path, flavor="stream", pages="all")
print(f"\nTotal de tabelas encontradas: {len(tables)}\n")

for i, table in enumerate(tables):
    print(f"\n=== Tabela {i+1} (Página {table.page}) ===")
    print(f"Accuracy: {table.parsing_report['accuracy']}%")
    print(f"Whitespace: {table.parsing_report['whitespace']}%")
    print("\nDados:")
    print(table.df.to_string())

    camelot.plot(table, kind="grid")
    plt.savefig(f"output/{file_name}_table_{i+1}_grid.png", dpi=150)
    print(f"\n[Imagem salva: output/{file_name}_table_{i+1}_grid.png]")

print("\n" + "=" * 60)
print("--- 3. IMAGENS DO PDF ---")
print("=" * 60)

print("Para visualizar as páginas como imagem, use um visualizador de PDF.")
print("O PDF tem", len(reader.pages), "página(s)")
print("Tamanho:", reader.pages[0].mediabox.width, "x", reader.pages[0].mediabox.height)
