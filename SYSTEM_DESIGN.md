# XYZ System — RAG Document Reconstruction & Schema Migration

**Document Type:** System Design & Architecture Overview  
**Version:** 1.0.0  
**Project:** POC — Automated Legacy Document Migration  
**Date:** 2026-05-31  

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Business Goals & Success Criteria](#2-business-goals--success-criteria)
3. [High-Level Architecture](#3-high-level-architecture)
4. [What Was Built — POC](#4-what-was-built--poc)
   - [System Components](#41-system-components)
   - [Data Flow](#42-data-flow)
   - [Technology Stack](#43-technology-stack)
5. [File-by-File Breakdown](#5-file-by-file-breakdown)
6. [How the Requirement is Satisfied](#6-how-the-requirement-is-satisfied)
7. [Current Limitations of the POC](#7-current-limitations-of-the-poc)
8. [Scalability Improvements — Production Roadmap](#8-scalability-improvements--production-roadmap)
   - [Chunking Strategy](#81-chunking-strategy)
   - [Vector Database](#82-vector-database)
   - [Multi-Document & Multi-Format Support](#83-multi-document--multi-format-support)
   - [LLM & Retrieval Improvements](#84-llm--retrieval-improvements)
   - [API & Interface Layer](#85-api--interface-layer)
   - [Observability & Monitoring](#86-observability--monitoring)
9. [POC vs Production — Comparison Table](#9-poc-vs-production--comparison-table)
10. [Conclusion](#10-conclusion)

---

## 1. Problem Statement

Organizations often maintain large sets of legacy documents — manuals, policies, regulatory guides, technical specifications — that are actively used in existing systems. When a **new system (XYZ)** is being developed, it typically requires:

- The **same underlying information**, but in a **different format or schema**
- Extraction of **specific fields or sections** that the old document wasn't structured around
- Addition of **new metadata, warnings, FAQs, or mappings** that weren't present originally

Doing this **manually** is:
- **Time-consuming** — a 300-page document can take days to manually reformat
- **Inconsistent** — different team members interpret and map content differently
- **Not scalable** — impossible to repeat across hundreds of documents
- **Error-prone** — critical sections can be missed or misinterpreted

### The Core Need

> *"Automatically read old documents, extract the relevant information, make the necessary changes or mappings, and generate data/documents that can be directly used by the new system — reducing manual effort and improving consistency."*

---

## 2. Business Goals & Success Criteria

| Goal | Success Criteria |
|---|---|
| Automate document extraction | System reads PDFs without manual copying |
| Semantic retrieval | Finds the **right sections** even without exact keyword matches |
| Structured output | Output matches a predefined schema for the new system (XYZ) |
| Reduce manual effort | 1 analyst + 1 query → full upgraded document in seconds |
| Consistency | Same query always produces structurally consistent output |
| Fallback resilience | System never crashes — works even without API keys |

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LEGACY DOCUMENT SYSTEM                          │
│                                                                     │
│   [sample1.pdf]    [sample2.pdf]    [... more PDFs]                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                     ┌───────▼────────┐
                     │  PDF Parsing   │  (pypdf — page by page)
                     └───────┬────────┘
                             │ Text Chunks (1 per page)
                     ┌───────▼────────┐
                     │   Embeddings   │  (Gemini gemini-embedding-2)
                     │  Generation    │  3072-dim dense vectors
                     └───────┬────────┘
                             │ Vectors
                     ┌───────▼────────┐
                     │  Chroma        │  Persistent local vector DB
                     │  Vector DB     │  Cosine similarity index
                     └───────┬────────┘
                             │
          ┌──────────────────┴──────────────────────┐
          │                                         │
   ┌──────▼──────┐                        ┌────────▼────────┐
   │   Existing  │                        │  NEW REQUIREMENTS│
   │   Knowledge │                        │  (User Query)   │
   │   Chunks    │                        │                 │
   └──────┬──────┘                        └────────┬────────┘
          │                                         │
          └──────────────┬──────────────────────────┘
                         │  Context + Requirements
                ┌────────▼─────────┐
                │  Gemini LLM      │  gemini-2.5-flash
                │  (Prompt Engine) │  Structured JSON output
                └────────┬─────────┘
                         │
                ┌────────▼─────────┐
                │ Pydantic Schema  │  Validates output structure
                │ Validation       │
                └────────┬─────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
   ┌──────▼──────┐              ┌───────▼──────┐
   │  Markdown   │              │  Styled PDF  │
   │  (.md)      │              │  (ReportLab) │
   └─────────────┘              └──────────────┘
          │                             │
          └──────────────┬──────────────┘
                         │
              ┌──────────▼───────────┐
              │  NEW SYSTEM (XYZ)    │
              │  Consumes V2 Output  │
              └──────────────────────┘
```

---

## 4. What Was Built — POC

### 4.1 System Components

The POC is built as a **modular Python pipeline** with 5 core modules:

| Module | File | Role |
|---|---|---|
| Data Schemas | `schemas.py` | Defines the structure of all data objects |
| Embedding Engine | `embeddings.py` | Converts text to dense vectors |
| Vector Store | `vector_store.py` | Stores and retrieves vectors |
| Pipeline Orchestrator | `pipeline.py` | End-to-end RAG + LLM + output compilation |
| CLI Interface | `main.py` | User-facing interactive terminal interface |

### 4.2 Data Flow

```
1. INGEST PHASE
   PDF File
     → pypdf reads page-by-page
     → Each page = one DocumentChunk (chunk_id, source_file, page_number, text)
     → Gemini embeddings converts each chunk's text into a 3072-dim vector
     → Vectors + metadata stored in Chroma DB on disk

2. QUERY PHASE
   User types new requirement
     → Query text converted to embedding vector
     → Vector compared against all stored chunks (cosine similarity)
     → Top 4 most relevant pages retrieved with similarity scores

3. GENERATION PHASE
   Retrieved pages (old knowledge) + New requirement (user query)
     → Combined into a structured prompt
     → Sent to Gemini 2.5 Flash
     → Response validated against Pydantic GeneratedDocument schema
     → Compiled into Markdown + PDF output files
```

### 4.3 Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.10+ | Core implementation |
| PDF Parsing | `pypdf` | Extract text from legacy PDFs |
| Embeddings | `google-genai` / `gemini-embedding-2` | Dense semantic vectors |
| Vector DB | `chromadb` (persistent) | Store and search embeddings |
| LLM | `gemini-2.5-flash` | Generate structured upgraded documents |
| Schema Validation | `pydantic` v2 | Enforce strict output structure |
| PDF Output | `reportlab` | Styled PDF compilation |
| Config | `python-dotenv` | API key management |

---

## 5. File-by-File Breakdown

### `schemas.py` — The Data Blueprint

Defines **4 Pydantic models** that enforce the shape of all data:

```
DocumentChunk
  ├── chunk_id        → Unique ID (e.g. CK-3A9F2B)
  ├── source_file     → Original PDF filename
  ├── page_number     → Which page this came from
  └── text            → Raw extracted text

UpgradedSection
  ├── heading         → Section title in the new document
  ├── content         → Restructured content for XYZ system
  └── source_pages    → Which old pages this was synthesized from

FAQItem
  ├── question        → Auto-generated user-facing question
  └── answer          → Auto-generated concise answer

GeneratedDocument  (The complete V2 output)
  ├── title           → Document title
  ├── version         → "2.0.0"
  ├── overview        → Executive summary of changes
  ├── sections        → List of UpgradedSections
  ├── safety_directives → List of warning/caution strings
  └── faq             → List of FAQItems
```

---

### `embeddings.py` — The Fingerprinter

Converts raw text into numeric vectors for semantic search.

**Live Mode** (when `GEMINI_API_KEY` is set):
- Calls `models/gemini-embedding-2` via Google GenAI SDK
- Returns a **3072-dimensional** dense vector
- Captures deep semantic meaning — finds relevant pages even without exact keyword matches

**Offline/Mock Mode** (no API key):
- Uses an MD5 hash-based bag-of-words approach
- Returns a **128-dimensional** normalized vector
- Still functional for demo purposes

---

### `vector_store.py` — The Smart Filing Cabinet

Manages storage and retrieval of all chunk embeddings.

**Primary Mode** (Chroma DB installed):
- Initializes a persistent `PersistentClient` at `./chroma_db`
- Uses **cosine similarity** (`hnsw:space: cosine`) for retrieval
- Data survives between runs — no need to re-embed every time

**Fallback Mode** (Chroma not installed):
- Uses in-memory list with manual dot-product cosine similarity
- Slightly slower at scale but functionally identical

Key methods:
- `add_chunks()` — stores text chunks + their embeddings
- `query()` — finds top-K most similar chunks for a query
- `clear()` — resets the collection

---

### `pipeline.py` — The Orchestrator

The core business logic. Contains 5 main functions:

1. **`ingest_document(file_path, vector_store)`**
   - Reads the PDF using `pypdf`
   - Skips pages with fewer than 30 characters (blank/header pages)
   - Generates a unique `chunk_id` per page using MD5 hash
   - Calls `get_embedding()` for each chunk
   - Stores all chunks in the vector store

2. **`retrieve_context(query, vector_store, top_k=4)`**
   - Converts the user's query to an embedding
   - Queries the vector store for top 4 matches
   - Returns list of `(similarity_score, chunk_dict)` tuples

3. **`generate_upgraded_document(query, chunks, source_filename)`**
   - Builds a structured prompt combining:
     - Retrieved old document pages (with similarity scores)
     - User's new requirement
   - Calls `gemini-2.5-flash` with `response_schema=GeneratedDocument`
   - Falls back to smart offline mock generator if API call fails

4. **`compile_markdown(doc)`**
   - Converts `GeneratedDocument` → formatted `.md` string
   - Includes headers, source references, safety warnings, FAQ

5. **`compile_pdf(doc, output_path)`**
   - Uses ReportLab with custom paragraph styles (Indigo/Slate theme)
   - Generates sections, warning boxes (red background), FAQ entries
   - Saves a professionally styled PDF

---

### `main.py` — The CLI Interface

Interactive command-line entry point:

1. Creates `.env` template if missing
2. Shows a banner with API key status (Live vs Offline)
3. Scans both root directory and `data/` folder for PDF files
4. Displays a numbered file selection menu
5. Runs ingestion with a visual progress bar
6. Enters a loop:
   - Takes a new requirement query from the user
   - Retrieves top 4 relevant pages (prints snippets + scores)
   - Calls pipeline to generate upgraded document
   - Saves outputs to `data/upgraded_document.md` and `.pdf`
   - Prints a full summary
   - Asks if the user wants another query on the same document

---

## 6. How the Requirement is Satisfied

| Business Requirement | Implementation |
|---|---|
| *"Automatically read old documents"* | `pypdf` reads every page of every PDF automatically |
| *"Extract relevant information"* | Semantic vector search retrieves only the most relevant pages |
| *"Make necessary changes or mappings"* | User types new requirement → LLM maps old content to new schema |
| *"Generate documents for new system"* | Outputs structured JSON (Pydantic) + Markdown + PDF |
| *"Reduce manual effort"* | Entire pipeline runs with a single command: `python main.py` |
| *"Improve consistency"* | Pydantic schema validation enforces identical structure every time |

### End-to-End Example

**Old Document:** `sample1.pdf` (US Constitution — 85 pages)

**New Requirement typed by user:**
```
"Extract Article II sections about the President's duties, map them 
to Executive power and add safety warning about constitutional limits."
```

**System Output:**
- Retrieved Pages 20, 41, 61, 59 (most constitutionally relevant)
- Generated:
  - Title: `UPGRADED GOVERNANCE & LEGISLATIVE FRAMEWORK (XYZ V2)`
  - 2 restructured sections with source page references
  - 2 safety directives (critical warnings)
  - 2 auto-generated FAQ pairs
- Saved: `data/upgraded_document.md` + `data/upgraded_document.pdf`

---

## 7. Current Limitations of the POC

| Limitation | Impact |
|---|---|
| **Page-level chunking** | One chunk = entire page. Pages with mixed content reduce retrieval precision |
| **Local Chroma DB only** | Single machine, no concurrent users, no cloud backup |
| **PDF only** | Cannot process Word, Excel, HTML, or database records |
| **No re-ranking** | Retrieved chunks are not re-scored before sending to LLM |
| **Single document session** | Can only query one document per session run |
| **No caching** | Identical queries re-run the full pipeline each time |
| **CLI only** | Not accessible via API or web browser |
| **No multi-user support** | One user at a time |
| **Fixed output schema** | Pydantic schema is hardcoded, not configurable per use case |
| **No ingestion deduplication** | Re-ingesting the same PDF creates duplicate chunks in the DB |

---

## 8. Scalability Improvements — Production Roadmap

### 8.1 Chunking Strategy

**Current:** 1 chunk = 1 full page (can be 800+ words)

**Improved:** Token-based sliding window chunking

```
Page Text (1000 tokens)
  → Chunk 1: tokens 0–400
  → Chunk 2: tokens 300–700   ← 100 token overlap
  → Chunk 3: tokens 600–1000
```

**Benefits:**
- Smaller, more focused chunks → higher retrieval precision
- Overlap prevents splitting context across chunk boundaries
- Works well with LLM context window limits

**Libraries:** `langchain.text_splitter.RecursiveCharacterTextSplitter`, `tiktoken`

---

### 8.2 Vector Database

**Current:** Local Chroma DB (`./chroma_db`)

**Improved Options for Production:**

| Option | Best For | Scale |
|---|---|---|
| **Pinecone** | Fully managed cloud, zero ops | Millions of vectors |
| **Weaviate** | Self-hosted + GraphQL API | Enterprise, custom schemas |
| **Qdrant** | High-performance, filterable metadata | High query throughput |
| **pgvector** (PostgreSQL) | Already using PostgreSQL | Moderate scale, SQL familiar |

**Additional improvements:**
- Add **metadata filters** (filter by document name, date, department, etc.)
- Enable **hybrid search** (combine keyword BM25 + semantic vector search)

---

### 8.3 Multi-Document & Multi-Format Support

**Current:** One PDF at a time

**Improved:**
- Support `.docx` (python-docx), `.xlsx` (openpyxl), `.html` (BeautifulSoup), `.txt`, `.json`, database exports
- **Auto-ingestion pipeline**: Watch a folder or S3 bucket — any new file dropped triggers automatic ingestion
- **Batch processing**: Ingest 100 PDFs in parallel using async or multiprocessing
- **Deduplication**: Hash each chunk before inserting — skip if already indexed

```python
# Production ingestion example
async def batch_ingest(file_list):
    tasks = [ingest_document(f, vector_store) for f in file_list]
    await asyncio.gather(*tasks)
```

---

### 8.4 LLM & Retrieval Improvements

**Current:** Top 4 pages by cosine similarity → direct to LLM

**Improved retrieval pipeline:**

```
User Query
    ↓
Bi-encoder (Gemini Embeddings)  → fast approximate retrieval (top 20)
    ↓
Cross-encoder re-ranking        → precise re-scoring of top 20
    ↓
Top 4 re-ranked chunks          → sent to LLM
```

**Additional LLM improvements:**
- **Query expansion**: Rewrite user query into multiple sub-queries for broader retrieval
- **Hypothetical Document Embeddings (HyDE)**: Generate a hypothetical answer first, embed it, then search
- **Response caching**: Cache LLM responses for identical queries (Redis / in-memory)
- **Multi-turn conversation**: Allow follow-up queries that build on previous context
- **Streaming responses**: Stream the LLM output token by token instead of waiting for full response

---

### 8.5 API & Interface Layer

**Current:** CLI only (`python main.py`)

**Improved:** REST API using FastAPI

```python
# Expose pipeline as an API
POST /api/ingest          → Upload and ingest a PDF
POST /api/query           → Submit a new requirement query
GET  /api/documents       → List all ingested documents
GET  /api/outputs/{id}    → Download generated Markdown/PDF
```

**Full production stack:**
```
Frontend (React / Next.js)
    ↓
FastAPI REST API
    ↓
RAG Pipeline (pipeline.py — refactored as service)
    ↓
Cloud Vector DB (Pinecone / Weaviate)
    ↓
Gemini LLM API
    ↓
Output Storage (S3 / GCS bucket)
```

**Multi-user support:**
- JWT authentication
- Per-user document namespaces in the vector DB
- Role-based access (Admin can manage docs, User can only query)

---

### 8.6 Observability & Monitoring

**Current:** Print statements only

**Production:**

| Concern | Solution |
|---|---|
| **Logging** | Structured JSON logs (Python `logging` + Cloud Logging) |
| **Tracing** | LangSmith / Langfuse — trace every LLM call end-to-end |
| **Cost tracking** | Monitor Gemini API token usage per query |
| **Retrieval quality** | Log similarity scores + user feedback (thumbs up/down) |
| **Latency monitoring** | Track embedding time, retrieval time, LLM generation time |
| **Alerts** | Alert if LLM fallback rate exceeds threshold |

---

## 9. POC vs Production — Comparison Table

| Feature | POC (Current) | Production (Target) |
|---|---|---|
| **Document formats** | PDF only | PDF, Word, Excel, HTML, JSON, DB |
| **Chunking** | Page-level (coarse) | Token-level sliding window (precise) |
| **Vector DB** | Local Chroma DB | Pinecone / Weaviate (cloud, distributed) |
| **Retrieval** | Cosine similarity only | Hybrid search + cross-encoder re-ranking |
| **LLM** | gemini-2.5-flash | gemini-2.5-flash + caching + streaming |
| **Interface** | CLI terminal | REST API + Web Dashboard |
| **Users** | Single user | Multi-user with authentication |
| **Concurrency** | Sequential | Async / parallel batch processing |
| **Document volume** | 1–5 PDFs | Thousands of documents |
| **Ingestion trigger** | Manual | Automated (folder watch / S3 event) |
| **Output schema** | Fixed Pydantic model | Configurable per use case |
| **Monitoring** | Print statements | Structured logs + LLM tracing + alerts |
| **Deployment** | Local machine | Docker + Cloud Run / Kubernetes |
| **Deduplication** | None | Hash-based chunk deduplication |

---

## 10. Conclusion

### What Was Achieved in the POC

This POC successfully demonstrates the **complete end-to-end pipeline** for automated legacy document migration:

1. ✅ Legacy PDFs are automatically read and semantically indexed
2. ✅ New requirements are taken as natural language input
3. ✅ Relevant knowledge is retrieved using AI-powered semantic search
4. ✅ Gemini LLM synthesizes old knowledge + new requirements into a structured V2 document
5. ✅ Output is validated against a strict Pydantic schema for consistency
6. ✅ Final documents are generated in both Markdown and styled PDF formats
7. ✅ System works fully offline (fallback mode) — no hard dependency on API availability

### What the Production System Adds

The architecture is deliberately modular so each component can be upgraded independently:
- Swap **Chroma → Pinecone** without touching the LLM or pipeline logic
- Swap **CLI → FastAPI** without touching the vector store or embeddings
- Add **new document formats** without changing the retrieval or generation logic

This means the POC is not a throwaway prototype — it is a **working foundation** that can grow into a production-grade document intelligence system.

> **POC Disclaimer:** This system was built entirely with a **Proof of Concept mindset**. The scope was based solely on the high-level requirement provided — no detailed field mappings, target schemas, or integration specifications were defined at this stage. Design and implementation decisions were made to demonstrate the core concept end-to-end as quickly and clearly as possible. Further refinements, extended scenarios, and production-grade features would be scoped and built in subsequent phases based on detailed client requirements.

---

*Generated for client presentation. System built using Google Gemini APIs, ChromaDB, and Python.*
