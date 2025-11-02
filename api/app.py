import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
from llm.chains.data_extraction import DataExtractionChain
from llm.chains.date_classifier import DateClassifierChain
from llm.graphs.multi_agent_graph import MultiAgentGraph
from mcp_client import MCPClient
from langchain_community.document_loaders.parsers.pdf import PyMuPDFParser
from langchain_core.document_loaders import Blob

mcp_client = None
extraction_chain = None
classifier_chain = None
multi_agent_graph = None

# Run during initialisation of the backend.
# Code snippet credits to Claude
@asynccontextmanager
async def lifespan(app):
    global mcp_client, extraction_chain, classifier_chain, multi_agent_graph

    mcp_client = MCPClient("mcp_servers/data_extraction.py")
    await mcp_client.connect()

    extraction_chain = DataExtractionChain(
        model="gemini-2.0-flash",
        mcp_client=mcp_client
    )

    classifier_chain = DateClassifierChain(
        model="gemini-2.0-flash"
    )

    multi_agent_graph = MultiAgentGraph(model="gemini-2.0-flash")

    yield
    await mcp_client.close()

app = FastAPI(lifespan=lifespan)

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
async def extract(file=File(...), fields=Form(...)):
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

        extracted = await extraction_chain.extract(description, output_type, text)

        # If a date was extracted, classify it
        status = None
        if extracted.is_a_date_retrieval and extracted.value:
            classified = await classifier_chain.classify(
                normalised_date=extracted.value,
                reference_date="2024-01-01"
            )
            status = classified.classification

        results.append({
            "pages": pages_str,
            "description": description,
            "output_type": output_type,
            "original_text": extracted.original_text,
            "extracted": extracted.value,
            "reason": extracted.reason,
            "status": status
        })

    return {"results": results}


@app.post("/multi-agent-query")
async def multi_agent_query(file=File(...), query=Form(...)):
    text_by_page = read_pdf(file)

    async def event_generator():
        async for update in multi_agent_graph.run_stream(query=query, pdf_text=text_by_page):
            yield f"data: {json.dumps(update)}\n\n"
            await asyncio.sleep(0)
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
