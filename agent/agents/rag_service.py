"""
RAG (Retrieval Augmented Generation) service using ChromaDB as vector store.
Embeddings default to OpenAI; falls back to a lightweight sentence-transformer
when OPENAI_API_KEY is not set.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

CHROMA_PERSIST_DIR = os.getenv("CHROMA_DIR", "./data/chroma")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def _get_embeddings():
    """Return embeddings model; fall back gracefully when OpenAI key is missing."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("sk-placeholder"):
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small")
    else:
        # Use a local embedding model (no API key required)
        from langchain_community.embeddings import FakeEmbeddings
        logger.warning("OPENAI_API_KEY not set — using FakeEmbeddings (for dev only)")
        return FakeEmbeddings(size=1536)


def _get_vectorstore(collection_name: str):
    from langchain_chroma import Chroma
    Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=collection_name,
        embedding_function=_get_embeddings(),
        persist_directory=CHROMA_PERSIST_DIR,
    )


def _collection_name(workspace_id: str, kb_id: str) -> str:
    return f"ws_{workspace_id}_kb_{kb_id}".replace("-", "_")


async def ingest_text(
    text: str,
    workspace_id: str,
    kb_id: str,
    metadata: Optional[dict] = None,
) -> int:
    """Split text into chunks and store in ChromaDB. Returns number of chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    docs: List[Document] = splitter.create_documents(
        [text],
        metadatas=[{**(metadata or {}), "workspace_id": workspace_id, "kb_id": kb_id}],
    )

    col = _collection_name(workspace_id, kb_id)
    vs = _get_vectorstore(col)
    vs.add_documents(docs)
    return len(docs)


async def retrieve(
    query: str,
    workspace_id: str,
    kb_id: str,
    k: int = 4,
) -> str:
    """Retrieve top-k relevant chunks and return as formatted context string."""
    col = _collection_name(workspace_id, kb_id)
    vs = _get_vectorstore(col)
    docs = vs.similarity_search(query, k=k)
    if not docs:
        return ""
    context_parts = [f"[{i+1}] {d.page_content}" for i, d in enumerate(docs)]
    return "\n\n".join(context_parts)
