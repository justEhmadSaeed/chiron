"""
RAG Cache — Pinecone-backed per-agent retrieval
=================================================
Each agent gets its own namespace in Pinecone.
A cleanup step deletes all three namespaces once the pipeline finishes.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone

from chiron_backend.common.config import get_settings

logger = logging.getLogger("research_agent")
settings = get_settings()

# Agent-scoped Pinecone namespaces
PROTOCOL_NAMESPACE = "exp_protocol_architect"
PROCUREMENT_NAMESPACE = "exp_procurement_specialist"
RESOURCE_NAMESPACE = "exp_resource_manager"

ALL_NAMESPACES = [PROTOCOL_NAMESPACE, PROCUREMENT_NAMESPACE, RESOURCE_NAMESPACE]

_pinecone_index = None
_embedder = None


def _get_embedder() -> GoogleGenerativeAIEmbeddings:
    global _embedder
    if _embedder is None:
        _embedder = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.gemini_api_key,
        )
    return _embedder


def _get_index():
    global _pinecone_index
    if _pinecone_index is None:
        pc = Pinecone(api_key=settings.pinecone_api_key)
        _pinecone_index = pc.Index(settings.pinecone_index_name)
    return _pinecone_index


def store_and_retrieve(
    namespace: str,
    query_text: str,
    raw_search_results: list[dict[str, Any]],
    top_k: int = 3,
) -> list[str]:
    """
    Chunk and upsert raw Tavily search results into the given Pinecone namespace,
    then query and return the top-k semantically relevant chunks.
    """
    embedder = _get_embedder()
    index = _get_index()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    docs: list[str] = []
    metadata: list[dict] = []
    ids: list[str] = []
    timestamp = int(time.time())

    for i, res in enumerate(raw_search_results):
        content = res.get("content", "")
        if not content:
            continue
        chunks = splitter.split_text(content)
        for j, chunk in enumerate(chunks):
            docs.append(chunk)
            metadata.append({
                "url": res.get("url", ""),
                "title": res.get("title", ""),
                "score": res.get("score", 0.0),
                "text": chunk,
            })
            ids.append(f"{namespace}_{timestamp}_{i}_{j}")

    if not docs:
        logger.warning(f"[RAG:{namespace}] No content to index.")
        return []

    logger.info(f"[RAG:{namespace}] Upserting {len(docs)} chunks...")
    embeddings = []
    for i in range(0, len(docs), 50):
        embeddings.extend(embedder.embed_documents(docs[i : i + 50]))

    vectors = [
        {"id": ids[i], "values": embeddings[i], "metadata": metadata[i]}
        for i in range(len(docs))
    ]
    for i in range(0, len(vectors), 100):
        index.upsert(vectors=vectors[i : i + 100], namespace=namespace)

    query_emb = embedder.embed_query(query_text)
    results = index.query(
        vector=query_emb,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace,
    )

    retrieved: list[str] = []
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        retrieved.append(
            f"Title: {meta.get('title', 'N/A')}\n"
            f"URL: {meta.get('url', 'N/A')}\n"
            f"Content: {meta.get('text', '')}"
        )

    logger.info(f"[RAG:{namespace}] Retrieved {len(retrieved)} chunks.")
    return retrieved


def cleanup_namespaces() -> None:
    """Delete all three agent namespaces from Pinecone after the report is generated."""
    index = _get_index()
    for ns in ALL_NAMESPACES:
        try:
            index.delete(delete_all=True, namespace=ns)
            logger.info(f"  🗑  Cleaned up namespace '{ns}'.")
        except Exception:
            pass  # Namespace was never created — that's fine
