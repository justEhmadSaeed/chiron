"""
Pinecone Retriever
====================
Namespacing strategy:
  - Adversarial RAG search cache : namespace = "rag_{experiment_id}"
  - Adversarial agent memory      : namespace = "memory_{experiment_id}"
  - Hypothesis index              : namespace = "hypotheses"  (shared, one doc per hypothesis)
"""

from __future__ import annotations

import time
import uuid
import logging
from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from chiron_backend.common.config import get_settings

logger = logging.getLogger("research_agent")
settings = get_settings()

_EMBEDDING_DIM = 3072
_HYPOTHESIS_NAMESPACE = "hypotheses"

# ---------------------------------------------------------------------------
#  Pinecone client init
# ---------------------------------------------------------------------------

_pc: Pinecone | None = None
_pinecone_index = None


def _get_index():
    global _pc, _pinecone_index
    if _pinecone_index is not None:
        return _pinecone_index

    if not settings.pinecone_api_key:
        logger.warning("Pinecone API key not set — retriever disabled.")
        return None

    _pc = Pinecone(api_key=settings.pinecone_api_key)
    index_name = settings.pinecone_index_name

    existing = _pc.list_indexes().names()
    if index_name in existing:
        info = _pc.describe_index(index_name)
        if info.dimension != _EMBEDDING_DIM:
            logger.warning(f"Index '{index_name}' has wrong dimension ({info.dimension}). Recreating...")
            _pc.delete_index(index_name)
            while index_name in _pc.list_indexes().names():
                time.sleep(1)
            existing = []

    if index_name not in existing:
        logger.info(f"Creating Pinecone index '{index_name}' (dim={_EMBEDDING_DIM})...")
        _pc.create_index(
            name=index_name,
            dimension=_EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not _pc.describe_index(index_name).status["ready"]:
            time.sleep(1)

    _pinecone_index = _pc.Index(index_name)
    return _pinecone_index


_embedder: GoogleGenerativeAIEmbeddings | None = None


def _get_embedder() -> GoogleGenerativeAIEmbeddings:
    global _embedder
    if _embedder is None:
        _embedder = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.gemini_api_key,
        )
    return _embedder


# ---------------------------------------------------------------------------
#  RAG: Tavily search results → Pinecone → retrieve top-k chunks
# ---------------------------------------------------------------------------

def store_and_retrieve_rag_chunks(
    query_text: str,
    raw_search_results: list[dict],
    experiment_id: str,
    top_k: int = 5,
) -> list[str]:
    """
    Chunks Tavily results, upserts them into a per-run RAG namespace,
    then retrieves the top-k semantically relevant chunks.
    Namespace: rag_{experiment_id}
    """
    index = _get_index()
    if not index:
        return []

    embedder = _get_embedder()
    namespace = f"rag_{experiment_id}"
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    timestamp = int(time.time())

    docs: list[str] = []
    metadata: list[dict] = []
    ids: list[str] = []

    for i, res in enumerate(raw_search_results):
        content = res.get("raw_content") or res.get("content", "")
        if not content:
            continue
        chunks = splitter.split_text(content)
        for j, chunk in enumerate(chunks):
            docs.append(chunk)
            metadata.append({
                "url": res.get("url", ""),
                "title": res.get("title", ""),
                "score": float(res.get("score", 0.0)),
                "published_date": res.get("published_date", ""),
                "experiment_id": experiment_id,
                "text": chunk,
            })
            ids.append(f"rag_{experiment_id}_{timestamp}_{i}_{j}")

    if not docs:
        logger.warning(f"[RAG:{namespace}] No content to index.")
        return []

    logger.info(f"[RAG:{namespace}] Upserting {len(docs)} chunks...")
    embeddings: list = []
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
        vector=query_emb, top_k=top_k, include_metadata=True, namespace=namespace
    )

    retrieved: list[str] = []
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        retrieved.append(
            f"Title: {meta.get('title', 'N/A')}\n"
            f"Source URL: {meta.get('url', 'N/A')}\n"
            f"Publish Date: {meta.get('published_date', 'N/A')}\n"
            f"Tavily Score: {meta.get('score', 'N/A')}\n"
            f"Content: {meta.get('text', '')}"
        )

    logger.info(f"[RAG:{namespace}] Retrieved {len(retrieved)} chunks.")
    return retrieved


# ---------------------------------------------------------------------------
#  Agent memory: store full adversarial reasoning per experiment run
# ---------------------------------------------------------------------------

def store_agent_memory(
    experiment_id: str,
    hypothesis_text: str,
    reasoning: str,
    signal: str,
    novelty_score: float,
    references_summary: str,
) -> None:
    """
    Stores the full adversarial agent reasoning for a hypothesis run.
    Namespace: memory_{experiment_id}
    Vector ID: experiment_id (one memory doc per run, upserted = idempotent)
    """
    index = _get_index()
    if not index:
        return

    namespace = f"memory_{experiment_id}"
    doc = (
        f"Hypothesis: {hypothesis_text}\n"
        f"Signal: {signal}\n"
        f"Novelty Score: {novelty_score}\n"
        f"References: {references_summary}\n"
        f"Agent Reasoning: {reasoning}"
    )
    emb = _get_embedder().embed_documents([doc])[0]
    index.upsert(
        vectors=[{
            "id": experiment_id,
            "values": emb,
            "metadata": {
                "hypothesis": hypothesis_text,
                "signal": signal,
                "novelty_score": novelty_score,
                "text": doc,
            },
        }],
        namespace=namespace,
    )
    logger.info(f"[Memory:{namespace}] Stored full reasoning for experiment '{experiment_id}'.")


def retrieve_agent_memory(experiment_id: str, query_text: str, top_k: int = 2) -> list[str]:
    """
    Retrieves relevant past reasonings from the experiment's memory namespace.
    """
    index = _get_index()
    if not index:
        return []

    namespace = f"memory_{experiment_id}"
    query_emb = _get_embedder().embed_query(query_text)
    try:
        results = index.query(
            vector=query_emb, top_k=top_k, include_metadata=True, namespace=namespace
        )
        return [
            m["metadata"]["text"]
            for m in results.get("matches", [])
            if m.get("metadata", {}).get("text")
        ]
    except Exception as e:
        logger.error(f"[Memory:{namespace}] Retrieval error: {e}")
        return []


# ---------------------------------------------------------------------------
#  Hypothesis index: one vector per hypothesis, keyed by experiment UUID
# ---------------------------------------------------------------------------

def store_hypothesis_vector(experiment_id: str, hypothesis_text: str) -> None:
    """
    Stores the hypothesis text as a single vector in the shared 'hypotheses' namespace.
    Vector ID = experiment_id, so each document is uniquely tied to its Firebase UUID.
    Safe to call multiple times — Pinecone upsert is idempotent.
    Namespace: hypotheses
    """
    index = _get_index()
    if not index:
        return

    emb = _get_embedder().embed_documents([hypothesis_text])[0]
    index.upsert(
        vectors=[{
            "id": experiment_id,
            "values": emb,
            "metadata": {
                "hypothesis": hypothesis_text,
                "experiment_id": experiment_id,
            },
        }],
        namespace=_HYPOTHESIS_NAMESPACE,
    )
    logger.info(f"[Hypothesis Index] Stored hypothesis for experiment '{experiment_id}'.")


def find_similar_hypotheses(query_hypothesis: str, top_k: int = 3) -> list[dict]:
    """
    Retrieves the most semantically similar past hypotheses from the index.
    Returns a list of dicts with 'experiment_id', 'hypothesis', and 'score'.
    """
    index = _get_index()
    if not index:
        return []

    query_emb = _get_embedder().embed_query(query_hypothesis)
    try:
        results = index.query(
            vector=query_emb, top_k=top_k, include_metadata=True, namespace=_HYPOTHESIS_NAMESPACE
        )
        return [
            {
                "experiment_id": m.get("id"),
                "hypothesis": m.get("metadata", {}).get("hypothesis", ""),
                "score": m.get("score", 0.0),
            }
            for m in results.get("matches", [])
        ]
    except Exception as e:
        logger.error(f"[Hypothesis Index] Query error: {e}")
        return []
