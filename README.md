# RAG Document Reconstruction & Schema Migration POC

> **Proof of Concept** — Automated legacy document extraction, transformation, and V2 document generation using Google Gemini + ChromaDB.

---

## What This Does

This pipeline automatically:
1. Reads legacy PDF documents from an existing system
2. Chunks and embeds them into a Vector Database (ChromaDB)
3. Accepts new system requirements as a query
4. Retrieves the most relevant sections from the old documents
5. Uses Gemini LLM to generate a structured, upgraded V2 document
6. Outputs the result as both **Markdown** and a styled **PDF**

---

## Project Structure

```
POC_Clinet_2/
├── main.py              # Interactive CLI interface
├── pipeline.py          # Core RAG orchestration + LLM + output compilation
├── embeddings.py        # Gemini embedding engine (with offline fallback)
├── vector_store.py      # ChromaDB vector store wrapper (with in-memory fallback)
├── schemas.py           # Pydantic data models for structured output
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template (copy to .env)
├── SYSTEM_DESIGN.md     # Full system design & architecture documentation
└── data/
    ├── sample1.pdf      # Legacy document 1 (source)
    ├── sample2.pdf      # Legacy document 2 (source)
    ├── upgraded_document.md   # Generated output (created at runtime)
    └── upgraded_document.pdf  # Generated output (created at runtime)
```

---

## Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ichha10/POC_Document-parsing-and-intelligence.git
cd POC_Document-parsing-and-intelligence
```

### 2. Create a Virtual Environment (Recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Your API Key
```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Open `.env` and replace `your_gemini_api_key_here` with your actual key:
```
GEMINI_API_KEY=your_actual_key_here
```

> **Get a Gemini API Key:** Visit [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

> **No API Key?** The pipeline runs in **Offline / Mock Mode** automatically — no key required for a demo run.

---

## Running the Pipeline

```bash
python main.py
```

You will see an interactive CLI:
1. Select a PDF document to ingest
2. Type your new system requirement (e.g., *"Extract Article II sections about the President's duties..."*)
3. The system retrieves relevant pages, calls Gemini, and generates:
   - `data/upgraded_document.md`
   - `data/upgraded_document.pdf`

---

## Example Queries

**For `sample1.pdf` (US Constitution):**
```
Extract Article II sections about the President's duties, map them to Executive power
and add a safety warning about constitutional limits.
```

**For `sample2.pdf` (DHIS2 Manual):**
```
Extract pivot table creation steps, map them to XYZ dashboard schema,
and add a warning limit on query sizes.
```

---

## Technology Stack

| Component | Technology |
|---|---|
| PDF Parsing | `pypdf` |
| Embeddings | Google Gemini `gemini-embedding-2` |
| Vector Database | `chromadb` (persistent local) |
| LLM | Google Gemini `gemini-2.5-flash` |
| Schema Validation | `pydantic` v2 |
| PDF Output | `reportlab` |
| Config Management | `python-dotenv` |

---

## Architecture Overview

```
Legacy PDFs  →  Chunking  →  Embeddings  →  ChromaDB
                                                ↓
New Requirements (query)  →  Retriever  →  Relevant Chunks
                                                ↓
                                         Gemini LLM
                                                ↓
                                     Pydantic Validation
                                                ↓
                                  Markdown + PDF (V2 Output)
```

For the full system design, architecture decisions, scalability roadmap, and POC scope details, see [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md).

---

## Notes

- The `.env` file is excluded from version control via `.gitignore` — your API key is never committed.
- ChromaDB persists to `./chroma_db/` on first run — subsequent runs skip re-ingestion.
- The system works fully offline if no API key is provided (mock mode).
