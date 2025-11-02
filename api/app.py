import io
import json
from fastapi import FastAPI, UploadFile, File, Form
from llm.chains.data_extraction import DataExtractionChain
from langchain_community.document_loaders.parsers.pdf import PyMuPDFParser
from langchain_core.document_loaders import Blob

app = FastAPI()
extraction_chain = DataExtractionChain(model="gemini-2.0-flash")

# Help from Claude in building this function
def read_pdf(file):
    pdf_bytes = file.file.read()
    blob = Blob.from_data(pdf_bytes, mime_type="application/pdf")
    
    parser = PyMuPDFParser()
    documents = parser.parse(blob)
    
    text_by_page = {}
    for i, doc in enumerate(documents, start=1):
        text_by_page[i] = doc.page_content
    
    return text_by_page


def parse_page_range(range_str, total_pages):
    pages = set()
    for part in range_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            start, end = int(start.strip()), int(end.strip())
            pages.update(range(start, min(end + 1, total_pages + 1)))
        else:
            page_num = int(part)
            if page_num <= total_pages:
                pages.add(page_num)
    return sorted(list(pages))


@app.post("/extract")
async def extract(file: UploadFile = File(...), fields: str = Form(...)):
    text_by_page = read_pdf(file)
    total_pages = len(text_by_page)
    fields_data = json.loads(fields)
    results = []
    
    for field in fields_data:
        pages_str = field.get("pages", "").strip()
        description = field.get("description", "").strip()
        output_type = field.get("output_type", "str").strip()
        
        if not pages_str:
            continue
        
        page_nums = parse_page_range(pages_str, total_pages)
        text = "\n---\n".join([f"[Page {p}]\n{text_by_page[p]}" for p in page_nums])

        extracted = extraction_chain.extract(description, output_type, text)
    
        results.append({
            "pages": pages_str,
            "description": description,
            "output_type": output_type,
            "extracted": extracted.value,
            "reason": extracted.reason
        })
    
    return {"results": results}
