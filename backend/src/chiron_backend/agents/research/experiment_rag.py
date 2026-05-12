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
from chiron_backend.agents.research.retriever import PineconeInferenceEmbedder
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


def _get_embedder() -> PineconeInferenceEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = PineconeInferenceEmbedder(
            model=settings.embedding_model,
            api_key=settings.pinecone_api_key,
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

    grouped_docs: dict[int, list[str]] = {}
    grouped_metadata: dict[int, list[dict]] = {}
    grouped_ids: dict[int, list[str]] = {}
    timestamp = int(time.time())

    for i, res in enumerate(raw_search_results):
        content = res.get("content", "")
        if not content:
            continue
        chunks = splitter.split_text(content)
        
        grouped_docs[i] = []
        grouped_metadata[i] = []
        grouped_ids[i] = []
        
        for j, chunk in enumerate(chunks):
            grouped_docs[i].append(chunk)
            grouped_metadata[i].append({
                "url": res.get("url", ""),
                "title": res.get("title", ""),
                "score": float(res.get("score", 0.0)),
                "text": chunk,
            })
            grouped_ids[i].append(f"{namespace}_{timestamp}_{i}_{j}")

    docs: list[str] = []
    metadata: list[dict] = []
    ids: list[str] = []
    
    MAX_CHUNKS = 400
    if grouped_docs:
        sources = list(grouped_docs.keys())
        pointers = {s: 0 for s in sources}
        total_extracted = 0
        
        while total_extracted < MAX_CHUNKS:
            added_in_round = False
            for s in sources:
                if pointers[s] < len(grouped_docs[s]):
                    docs.append(grouped_docs[s][pointers[s]])
                    metadata.append(grouped_metadata[s][pointers[s]])
                    ids.append(grouped_ids[s][pointers[s]])
                    pointers[s] += 1
                    total_extracted += 1
                    added_in_round = True
                
                if total_extracted >= MAX_CHUNKS:
                    break
            
            if not added_in_round:
                break

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
