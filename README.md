# HTX AI Engineering Take Home Test

## Quick Start

### Prerequisites
- Docker and Docker Compose in machine
- `.env` file with LLM API key

### Setup

1. **Clone repository**
```bash
git clone https://github.com/leezhanpeng/htx-ai-engineering-take-home-test.git
cd htx-ai-engineering-take-home-test
```

2. **Add .env into /api folder**

Expected `api/.env` structure:
```env
LLM_API_KEY=<KEY>
LLM_BASE_URL=<URL>
```

3. **Start the application**

In root, run:

```bash
docker compose up --build
```

4. **Access the dashboard**
- Dashboard: http://localhost:8501
- API endpoint is located at http://localhost:8000

## System Design

### Overview

The system is designed as a microservices architecture with three main components:

1. **Frontend (Streamlit Dashboard)** - User interface for document upload and query interaction
2. **Backend (FastAPI)** - API layer handling requests and orchestrating LLM workflows
3. **LLM Layer** - Multi-agent system and extraction chains powered by LangChain/LangGraph

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard (Port 8501)              │
│  ┌──────────────────────┐  ┌──────────────────────────────┐     │
│  │  Field Extraction    │  │  Multi-Agent Analysis        │     │
│  │  - PDF Upload        │  │  - PDF Upload                │     │
│  │  - Field Config      │  │  - Query Input               │     │
│  │  - Results Display   │  │  - Real-time Streaming       │     │
│  └──────────┬───────────┘  └───────────┬──────────────────┘     │
└─────────────┼──────────────────────────┼────────────────────────┘
              │                          │
              │    HTTP POST             │    HTTP POST (SSE)
              ▼                          ▼
┌───────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Port 8000)                │
│  ┌──────────────────────┐  ┌──────────────────────────────┐   │
│  │  /extract            │  │  /multi-agent-query          │   │
│  │  - PDF Processing    │  │  - PDF Text Extraction       │   │
│  │  - Field Extraction  │  │  - Graph Execution           │   │
│  │  - MCP Tool Binding  │  │  - Event Streaming           │   │
│  └──────────┬───────────┘  └───────────┬──────────────────┘   │
└─────────────┼──────────────────────────┼──────────────────────┘
              │                          │
              ▼                          ▼
┌────────────────────────────────────────────────────────────────┐
│                        LLM Layer                               │
│                                                                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │               Data Extraction Chain                       │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐     │ │
│  │  │ LLM Call │→ │Tool Call?│→ │ MCP Tool Execution   │     │ │
│  │  │          │← │(Optional)│← │ (Date Normaliser)    │     │ │
│  │  └──────────┘  └──────────┘  └──────────────────────┘     │ │
│  │                        │                                  │ │
│  │                        ▼                                  │ │
│  │              ┌──────────────────┐                         │ │
│  │              │ Structured Output│                         │ │
│  │              └──────────────────┘                         │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │             Multi-Agent Graph (LangGraph)                 │ │
│  │                                                           │ │
│  │              ┌──────────────────┐                         │ │
│  │              │  Supervisor      │                         │ │
│  │              │  (Route Query)   │                         │ │
│  │              └────────┬─────────┘                         │ │
│  │                       │                                   │ │
│  │         ┌─────────────┼─────────────┐                     │ │
│  │         ▼             ▼             ▼                     │ │
│  │   ┌─────────┐   ┌──────────┐  ┌───────────┐               │ │
│  │   │ Revenue │   │   Both   │  │Expenditure│               │ │
│  │   │  Only   │   │  Agents  │  │   Only    │               │ │
│  │   └────┬────┘   └─────┬────┘  └──────┬────┘               │ │
│  │        │              │              │                    │ │
│  │        ▼              ▼              ▼                    │ │
│  │   ┌──────────┐   ┌──────────┐  ┌───────────┐              │ │
│  │   │ Revenue  │   │ Revenue  │  │Expenditure│              │ │
│  │   │  Agent   │   │  Agent   │  │  Agent    │              │ │
│  │   └────┬─────┘   └────┬─────┘  └─────┬─────┘              │ │
│  │        │              │              │                    │ │
│  │        │              ▼              │                    │ │
│  │        │        ┌───────────┐        │                    │ │
│  │        │        │Expenditure│        │                    │ │
│  │        │        │  Agent    │        │                    │ │
│  │        │        └────┬──────┘        │                    │ │
│  │        │             │               │                    │ │
│  │        └─────────────┼───────────────┘                    │ │
│  │                      ▼                                    │ │
│  │              ┌──────────────┐                             │ │
│  │              │  Supervisor  │                             │ │
│  │              │ (Synthesise) │                             │ │
│  │              └──────────────┘                             │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘

```

### Component Details

#### 1. Field Extraction System

**Workflow:**
1. User uploads PDF and defines fields to extract (page range, description, output type)
2. Backend extracts PDF text using PyMuPDF
3. For each field:
   - LLM analyses relevant pages and extracts information
   - If date-related, MCP tool `date_normaliser` is invoked
   - Date classifier determines status (Expired/Ongoing/Upcoming relative to 2024-01-01)
   - Final structured output includes: `original_text`, `extracted_value`, `reason`, `status` (for dates)

**Key Features:**
- LLM inference for key extraction
- Tool calling via Local MCP

#### 2. Multi-Agent Analysis System

**State Management:**
```python
AgentState:
  - query: str                         # User question
  - pdf_text: dict[int, str]           # PDF content by page
  - revenue_findings: dict | None      # Revenue agent results
  - expenditure_findings: dict | None  # Expenditure agent results
  - supervisor_decision: str           # Routing decision
  - final_answer: str                  # Synthesised response
```

**Agent Responsibilities:**

- **Supervisor Agent** (2 modes):
  - **Route Mode**: Analyses query and decides which agents to invoke
    - Keywords: revenue, income, taxes → Revenue Agent
    - Keywords: expenditure, spending, budget → Expenditure Agent
    - Ambiguous/Both → Both Agents
  - **Synthesise Mode**: Combines findings from agents into a complete answer

- **Revenue Agent**:
  - Extracts revenue streams, amounts, years, page references
  - Calculates total revenue
  - Provides confidence level with explanation
  - Output: `revenue_streams`, `total_revenue`, `key_insights`, `confidence_level`

- **Expenditure Agent**:
  - Extracts expenditure items, purposes, amounts
  - Calculates total expenditure
  - Provides confidence level with explanation
  - Output: `expenditure_items`, `total_expenditure`, `key_insights`, `confidence_level`

**Graph Execution Flow:**
1. Supervisor routes query → determines agent(s) to invoke
2. Agent(s) analyse extracted PDF texts → extract structured findings
3. Supervisor synthesises → generates final answer
4. Every step along the way is streamed to frontend

### API Endpoints

The backend exposes two main endpoints:

#### 1. POST `/extract`

Field extraction with optional tool calling for date normalisation.

**Request:**
- Parameters:
  - `file`: PDF file (binary)
  - `fields`: JSON string containing array of field definitions

**Field Definition Schema:**
```json
{
  "pages": "1-3,5",           // Page range (e.g., "1", "1-5", "1,3,5-7")
  "description": "string",     // What to extract
  "output_type": "str|int|float|list[str]|list[int]|list[float]"
}
```

**Response:**
```json
{
  "results": [
    {
      "pages": "5",
      "description": "Amount of Corporate Income Tax in 2023",
      "output_type": "float",
      "original_text": "Corporate Income Tax revenue increased to $23.5 billion",
      "extracted": 23.5,
      "reason": "Found explicit mention of Corporate Income Tax amount",
      "status": null  // "Expired" | "Ongoing" | "Upcoming" (only for dates)
    }
  ]
}
```

#### 2. POST `/multi-agent-query`

Multi-agent analysis with streaming.

**Request:**
- Parameters:
  - `file`: PDF file (binary)
  - `query`: User question (string)

**Response:**
- Streams JSON

**Event Types:**

1. **Routing Event**
```json
{
  "type": "routing",
  "decision": "revenue_only|expenditure_only|combined"
}
```

2. **Revenue Analysis Event**
```json
{
  "type": "revenue_analysis",
  "findings": {
    "revenue_streams": [
      {
        "category": "Corporate Income Tax",
        "amount": "23.5",
        "unit": "billion",
        "year": "2023",
        "page": 5
      }
    ],
    "total_revenue": {"amount": "102.3", "unit": "billion"},
    "key_insights": ["..."],
    "confidence_level": "high|medium|low",
    "confidence_explanation": "..."
  },
  "num_streams": 5,
  "confidence_level": "high"
}
```

3. **Expenditure Analysis Event**
```json
{
  "type": "expenditure_analysis",
  "findings": {
    "expenditure_items": [
      {
        "category": "Healthcare",
        "amount": "15.2",
        "unit": "billion",
        "year": "2024",
        "page": 12,
        "purpose": "Public hospital subsidies"
      }
    ],
    "total_expenditure": {"amount": "95.7", "unit": "billion"},
    "key_insights": ["..."],
    "confidence_level": "high|medium|low",
    "confidence_explanation": "..."
  },
  "num_items": 8,
  "confidence_level": "medium"
}
```

4. **Synthesis Event**
```json
{
  "type": "synthesis"
}
```

5. **Final Result Event**
```json
{
  "type": "final_result",
  "final_answer": "The key government revenue streams include...",
  "revenue_findings": {...},
  "expenditure_findings": {...}
}
```

6. **Complete Event**
```json
{
  "type": "complete"
}
```

**Streaming Behavior:**
- Events are sent as data arrives from the multi-agent graph
- Connection stays open until `complete` event is sent

## Features & Results

### Part 1 & 2: Document Extraction & Tool Calling

**Input:**
![Part 1 and 2 Input](media/Part1and2input.PNG)

**Part 1 Output:**
![Part 1 Output](media/Part1output.PNG)

**Part 2 Output:**

Note that specifically for date extraction, date normalisation tool will be called, and the status of the date is also included, relative to 2024-01-01
![Part 2 Output](media/Part2output.PNG)

### Part 3: Multi-Agent System

**Input:**
![Part 3 Input](media/Part3input.PNG)

**Output:**
![Part 3 Output](media/Part3output.PNG)

## Technology Stack

### Backend
- **FastAPI** for backend endpoints
- **LangChain and LangGraph** for LLM orchestration, structured outputs and multi-agent workflows
- **Python MCP Library** for tool integration
- **PyMuPDF** for PDF text extraction

### Frontend
- **Streamlit** to more intuitively show output of various tasks

### LLM Provider
- Mainly using **Google Gemini 2.0 Flash**
- Easily modifiable via environment keys, as we run it on OpenAI compatible endpoint

### Library Justifications

- **LangChain**: Easy initialisation of chains for multistep tasks.

- **LangGraph**: Purpose-built for multi-agent workflows + take home test requirement

- **FastAPI**: My go to for backend endpoints.

- **Streamlit**: Meant to quickly cook up a frontend so that output can be visualised intuitively.

- **PyMuPDF**: Theoretically, under perfect condition, we should use different libraries for different content structure, e.g. text, table, graph etc.

  - For simplicity, I decided to just pick one that is the fastest since the product is suppose to be lightweight, and at least performs as well as the rest if not better.

  - https://github.com/py-pdf/benchmarks suggests that PyMuPDF is fastest, and performance is good.
  - https://arxiv.org/pdf/2410.09871 paper suggests PyMuPDF is also well-performing, so it was chosen without much hesitation.

- **MCP (Model Context Protocol)**: One of the most standard library to initialise local MCPs.

## Project Structure

```
htx-ai-engineering-take-home-test/
├── api/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env
│   ├── .env.sample
│   ├── mcp_client.py
│   ├── mcp_servers/
│   │   ├── data_extraction.py
│   │   └── tools/
│   │       └── date_normaliser.py
│   └── llm/
│       ├── agents/
│       │   ├── supervisor.py
│       │   ├── revenue_agent.py
│       │   └── expenditure_agent.py
│       ├── chains/
│       │   ├── data_extraction.py
│       │   └── date_classifier.py
│       ├── graphs/
│       │   ├── multi_agent_graph.py
│       │   └── state.py
│       └── prompts/
│           ├── data_extraction.py
│           ├── date_classifier.py
│           └── agents/
│
├── dashboard/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md
```
