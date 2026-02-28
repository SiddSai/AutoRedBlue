# using pymupdf4llm: https://pypi.org/project/pymupdf4llm/
# ^^^ parses a pdf paper into a md file
import pymupdf4llm
import os

# use as an intermediate function to use inside a concrete toolkit
def read_pdf(input_dir: str, input_name: str, store_dir: str) -> str:
    pdf_path = os.path.join(input_dir, f"{input_name}.pdf")

    base = os.path.basename(input_name)
    # if base.lower().endswith(".pdf"):
    #     base = base[:-4]
    md_path = os.path.join(store_dir, f"{base}.md")

    os.makedirs(store_dir, exist_ok=True)

    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()

    md_text = pymupdf4llm.to_markdown(pdf_path)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    return md_text