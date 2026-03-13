# PolicyNavigator — LangChain RAG + Groq

A single-repo policy research assistant with a black-and-white ChatGPT-style interface. It supports:
- **General chat** (no documents)
- **Grounded Q&A** over uploaded PDFs with citations

## Why This Project Fits PoT
Policies of Thought values rigorous, evidence-based analysis. This tool makes legislation and policy documents searchable, with citations that allow verification.

## Architecture
1. **Upload** a PDF
2. **Parse & Chunk** into page-aware segments
3. **Embed** locally with a free model (`sentence-transformers`)
4. **Index** with FAISS
5. **Retrieve** relevant chunks on each query
6. **Generate** answers with Groq using retrieved context

## Why These Models
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` is free, fast, and reliable for semantic search.
- **Generator:** Groq-hosted Llama 3 (fast, low-latency) suitable for real-time chat.

## Cloud Readiness
Deployable on any Python cloud platform (Render, Railway, Fly.io, or Docker). Use a persistent volume for `storage/` to keep FAISS indices.

## Setup (uv)

1) Create `.env`:
```
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama3-70b-8192
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
STORAGE_DIR=storage
UPLOADS_DIR=data/uploads
CHUNK_SIZE=900
CHUNK_OVERLAP=150
TOP_K=5
```

2) Install dependencies with `uv`:
```
uv venv
uv pip install -r pyproject.toml
```

3) Run:
```
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/` for the UI.

## API
- `POST /upload` — upload a PDF, returns `doc_id`
- `POST /chat` — chat with or without `doc_id`
- `GET /health` — basic health

## Deployment (single service)

### Render
1. Push repo to GitHub
2. Create Web Service
3. Build command: `uv pip install -r pyproject.toml`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`
5. Add env vars
6. Add persistent disk for `storage/`

### Railway
1. Push repo to GitHub
2. Create project from repo
3. Add env vars
4. Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`

### Docker
```
docker build -t policynavigator .
docker run --env-file .env -p 8000:8000 policynavigator
```

## Notes
- If no PDF is uploaded, the assistant still works as a general chat.
- To enable citations, upload a PDF and use the returned `doc_id`.
