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
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chiron_backend.common.config import get_settings

logger = logging.getLogger("research_agent")
settings = get_settings()

_EMBEDDING_DIM = 1024
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


class PineconeInferenceEmbedder:
    def __init__(self, api_key: str, model: str):
        # We don't need the api_key passed explicitly if we reuse the global _pc
        # but for clean abstraction we initialize a new Pinecone client.
        from pinecone import Pinecone
        self.pc = Pinecone(api_key=api_key)
        self.model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = self.pc.inference.embed(
            model=self.model,
            inputs=texts,
            parameters={"input_type": "passage", "truncate": "END"}
        )
        return [data['values'] for data in response.data]

    def embed_query(self, text: str) -> list[float]:
        response = self.pc.inference.embed(
            model=self.model,
            inputs=[text],
            parameters={"input_type": "query", "truncate": "END"}
        )
        return response.data[0]['values']

_embedder: PineconeInferenceEmbedder | None = None


def _get_embedder() -> PineconeInferenceEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = PineconeInferenceEmbedder(
            model=settings.embedding_model,
            api_key=settings.pinecone_api_key,
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

    grouped_docs: dict[int, list[str]] = {}
    grouped_metadata: dict[int, list[dict]] = {}
    grouped_ids: dict[int, list[str]] = {}

    for i, res in enumerate(raw_search_results):
        content = res.get("raw_content") or res.get("content", "")
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
                "published_date": res.get("published_date", ""),
                "experiment_id": experiment_id,
                "text": chunk,
            })
            grouped_ids[i].append(f"rag_{experiment_id}_{timestamp}_{i}_{j}")

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

    BATCH_SIZE = 25
    BATCH_DELAY = 1.5
    embeddings: list = []
    for i in range(0, len(docs), BATCH_SIZE):
        if i > 0:
            time.sleep(BATCH_DELAY)
        batch = docs[i : i + BATCH_SIZE]
        for attempt in range(3):
            try:
                embeddings.extend(embedder.embed_documents(batch))
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = (attempt + 1) * 5
                    logger.warning(f"[RAG:{namespace}] Embedding 429, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

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
