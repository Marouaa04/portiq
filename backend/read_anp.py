import os
from pypdf import PdfReader

files = os.listdir("documents")
anp = [f for f in files if "Tableau" in f][0]
reader = PdfReader("documents/" + anp)

for i in range(1, 8):
    print(f"\n========== PAGE {i+1} ==========")
    text = reader.pages[i].extract_text()
    print(text[:800])