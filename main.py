from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
from typing import Dict
from dotenv import load_dotenv
import groq

from config import settings, refresh_settings
from rag import ingest_document, chat_without_docs, chat_with_docs

load_dotenv()

app = FastAPI(title="PolicyNavigator - LangChain RAG")

os.makedirs(settings.uploads_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_path = os.path.join(settings.uploads_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = ingest_document(file_path, file.filename)
        return {"status": "ok", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(payload: Dict):
    try:
        doc_id = payload.get("doc_id")
        messages = payload.get("messages", [])

        if doc_id:
            question = messages[-1]["content"] if messages else ""
            result = chat_with_docs(doc_id, question)
        else:
            result = chat_without_docs(messages)

        return {"status": "ok", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    refresh_settings()
    groq_ok = False
    groq_error = None
    try:
        if settings.groq_api_key:
            client = groq.Groq(api_key=settings.groq_api_key)
            client.models.list()
            groq_ok = True
    except Exception as e:
        groq_error = str(e)

    return {
        "status": "ok",
        "groq_key_set": bool(settings.groq_api_key),
        "groq_model": settings.groq_model,
        "embed_model": settings.embed_model,
        "storage_dir": settings.storage_dir,
        "groq_ok": groq_ok,
        "groq_error": groq_error,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
