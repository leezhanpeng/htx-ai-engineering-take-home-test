import fitz
import json
from fastapi import FastAPI, UploadFile, File, Form
from llm.llm import LLM
from llm.prompts.data_extraction import DATA_EXTRACTION_SYSTEM_MESSAGE, DATA_EXTRACTION_USER_MESSAGE, get_format_class

app = FastAPI()
llm = LLM(model="gemini-2.0-flash")


def read_pdf(file):
    pdf_bytes = file.file.read()
    out = {}
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for i, page in enumerate(doc, start=1):
            out[i] = page.get_text("text")
    return out


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

        user_message = DATA_EXTRACTION_USER_MESSAGE.format(prompt=description, output_type=output_type, text=text)
        format_class = get_format_class(output_type)

        extracted = llm.generate_structured(
            [{"role": "system", "content": DATA_EXTRACTION_SYSTEM_MESSAGE}, {"role": "user", "content": user_message}],
            format_class
        )
        
        results.append({
            "pages": pages_str,
            "description": description,
            "output_type": output_type,
            "extracted": extracted.value,
            "reason": extracted.reason
        })
    
    return {"results": results}
