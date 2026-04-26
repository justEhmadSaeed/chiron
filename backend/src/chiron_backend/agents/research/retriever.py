import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from chiron_backend.common.config import get_settings
import logging

# Suppress ChromaDB's aggressive telemetry logger warnings entirely
logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("chromadb.telemetry").setLevel(logging.ERROR)

settings = get_settings()

# Initialize ChromaDB client
try:
    if settings.chroma_api_key and settings.chroma_tenant and settings.chroma_database:
        chroma_client = chromadb.CloudClient(
            tenant=settings.chroma_tenant,
            database=settings.chroma_database,
            api_key=settings.chroma_api_key,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    else:
        print("Warning: Chroma Cloud config missing. Falling back to EphemeralClient.")
        chroma_client = chromadb.EphemeralClient(settings=ChromaSettings(anonymized_telemetry=False))
except Exception as e:
    print(f"Warning: Could not connect to Chroma Cloud ({e}). Falling back to EphemeralClient for testing.")
    chroma_client = chromadb.EphemeralClient(settings=ChromaSettings(anonymized_telemetry=False))

# Hardcode the text-embedding-004 model explicitly as requested
gemini_embedder = GoogleGenerativeAIEmbeddings(model=settings.embedding_model, google_api_key=settings.gemini_api_key)

def store_and_retrieve_rag_chunks(query_text: str, raw_search_results: list[dict], top_k: int = 3) -> list[str]:
    """
    Takes raw Tavily search results (dict with 'url' and 'content'),
    chunks the content, embeds it into ChromaDB, and returns the top-K semantic matches for the query.
    """
    # 1. Combine and chunk raw text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    docs = []
    metadata = []
    ids = []
    
    for i, res in enumerate(raw_search_results):
        content = res.get('content', '')
        url = res.get('url', '')
        title = res.get('title', 'Unknown Title')
        score = res.get('score', 0.0)
        pub_date = res.get('published_date', 'Unknown Date')
        
        if not content:
            continue
        
        import time
        timestamp = int(time.time())
        chunks = text_splitter.split_text(content)
        for j, chunk in enumerate(chunks):
            docs.append(chunk)
            metadata.append({"url": url, "title": title, "score": score, "published_date": pub_date, "source_index": i})
            ids.append(f"doc_{timestamp}_{i}_chunk_{j}")
            
    if not docs:
        return []

    # 2. Create/get a collection in ChromaDB
    collection_name = "tavily_search_cache"
        
    logger = logging.getLogger("research_agent")
    logger.info(f"ChromaDB: Storing {len(docs)} new document chunks from Tavily.")
    collection = chroma_client.get_or_create_collection(name=collection_name)
    
    # 3. Add chunks to ChromaDB
    # We embed via Gemini explicitly so Chroma doesn't silently try downloading the default PyTorch `all-MiniLM-L6-v2` transformer model to disk on the first query!
    # Batch the embedding requests to avoid "Payload too large" gRPC errors
    embeddings = []
    batch_size = 50
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i:i + batch_size]
        batch_emb = gemini_embedder.embed_documents(batch_docs)
        embeddings.extend(batch_emb)
    
    collection.add(
        documents=docs,
        embeddings=embeddings,
        metadatas=metadata,
        ids=ids
    )
    
    # 4. Query the collection 
    query_emb = gemini_embedder.embed_query(query_text)
    
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=min(top_k, len(docs))
    )
    
    # 5. Format the retrieved chunks for the LLM
    retrieved_chunks = []
    if results and results.get('documents') and results['documents'][0]:
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            chunk_text = f"Title: {meta.get('title', 'N/A')}\nSource URL: {meta.get('url', 'N/A')}\nPublish Date: {meta.get('published_date', 'N/A')}\nTavily Relevance Score: {meta.get('score', 'N/A')}\nContent: {doc}"
            retrieved_chunks.append(chunk_text)
            
    return retrieved_chunks

import uuid

def store_agent_memory(agent_id: str, hypothesis_text: str, reasoning: str, status: str):
    """
    Stores the adversarial agent's reasoning into a specific ChromaDB collection for long-term memory.
    """
    collection_name = f"memory_{agent_id}"
    try:
        collection = chroma_client.get_or_create_collection(name=collection_name)
    except Exception:
        try:
            collection = chroma_client.create_collection(name=collection_name)
        except Exception:
            collection = chroma_client.get_collection(name=collection_name)
            
    doc = f"Past Hypothesis Evaluated: {hypothesis_text}\nConclusion Status: {status}\nAgent Reasoning: {reasoning}"
    emb = gemini_embedder.embed_documents([doc])[0]
    
    collection.add(
        documents=[doc],
        embeddings=[emb],
        metadatas=[{"status": status}],
        ids=[str(uuid.uuid4())]
    )

def retrieve_agent_memory(agent_id: str, query_text: str, top_k: int = 2) -> list[str]:
    """
    Retrieves the most relevant past reasonings from the agent's memory.
    """
    collection_name = f"memory_{agent_id}"
    try:
        collection = chroma_client.get_collection(name=collection_name)
        if collection.count() == 0:
            return []
    except Exception:
        return [] # Collection doesn't exist yet
        
    query_emb = gemini_embedder.embed_query(query_text)
    
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=min(top_k, collection.count())
    )
    
    if results and results.get('documents') and results['documents'][0]:
        return results['documents'][0]
    return []
