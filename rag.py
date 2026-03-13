import os
import uuid
from datetime import datetime
from typing import List, Dict, Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from config import settings, SYSTEM_PROMPT, refresh_settings
from storage import init_db, insert_document


def _ensure_dirs() -> None:
    os.makedirs(settings.storage_dir, exist_ok=True)
    os.makedirs(settings.uploads_dir, exist_ok=True)


def _embeddings():
    return FastEmbedEmbeddings(model_name=settings.embed_model)


def _llm(model_name: str):
    refresh_settings()
    if not settings.groq_api_key:
        raise RuntimeError("Missing GROQ_API_KEY")
    return ChatGroq(
        model_name=model_name,
        groq_api_key=settings.groq_api_key,
        temperature=0.2,
    )


def _invoke_with_fallback(messages):
    models = [
        settings.groq_model,
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
    ]
    tried = set()
    last_error = None
    for model in models:
        if model in tried:
            continue
        tried.add(model)
        try:
            return _llm(model).invoke(messages)
        except Exception as exc:
            last_error = exc
            msg = str(exc).lower()
            if "decommissioned" in msg or "invalid_request_error" in msg or "model" in msg:
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError("No Groq model available")


def ingest_document(file_path: str, filename: str) -> Dict[str, Any]:
    _ensure_dirs()
    init_db()

    loader = PyPDFLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(docs)

    if not chunks:
        raise RuntimeError("No extractable text found in PDF")

    doc_id = uuid.uuid4().hex
    vectorstore = FAISS.from_documents(chunks, _embeddings())
    vectorstore.save_local(os.path.join(settings.storage_dir, doc_id))

    insert_document(doc_id, filename, datetime.utcnow().isoformat())

    return {
        "doc_id": doc_id,
        "chunks": len(chunks),
        "pages": len(docs),
    }


def chat_without_docs(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    chat_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in messages:
        if m["role"] == "user":
            chat_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            chat_messages.append(AIMessage(content=m["content"]))

    response = _invoke_with_fallback(chat_messages)
    return {"answer": response.content, "citations": []}


def chat_with_docs(doc_id: str, question: str) -> Dict[str, Any]:
    path = os.path.join(settings.storage_dir, doc_id)
    if not os.path.exists(path):
        raise FileNotFoundError("Index not found for this doc_id")

    vectorstore = FAISS.load_local(path, _embeddings(), allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": settings.top_k})

    docs = retriever.get_relevant_documents(question)
    context = "\n\n".join([
        f"[page {d.metadata.get('page', 'n/a')}] {d.page_content}" for d in docs
    ])

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        "Use only the context below to answer. Provide citations with page numbers.\n\n"
        f"Question: {question}\n\nContext:\n{context}"
    )

    response = _invoke_with_fallback([HumanMessage(content=prompt)])

    citations = [{"page": d.metadata.get("page")} for d in docs]
    return {"answer": response.content, "citations": citations}
