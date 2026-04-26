import time
import uuid
import logging
from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from chiron_backend.common.config import get_settings

logger = logging.getLogger("research_agent")
settings = get_settings()

# Initialize Pinecone client
if settings.pinecone_api_key:
    pc = Pinecone(api_key=settings.pinecone_api_key)
    
    # Auto-create the index if it doesn't exist, or recreate if wrong dimension
    index_name = settings.pinecone_index_name
    
    if index_name in pc.list_indexes().names():
        info = pc.describe_index(index_name)
        if info.dimension != 3072:
            logger.warning(f"Pinecone index '{index_name}' has wrong dimension ({info.dimension}). Deleting and recreating with 3072...")
            pc.delete_index(index_name)
            while index_name in pc.list_indexes().names():
                time.sleep(1)
                
    if index_name not in pc.list_indexes().names():
        logger.info(f"Creating Pinecone index '{index_name}' (dimension 3072)...")
        pc.create_index(
            name=index_name,
            dimension=3072, # Gemini embeddings are 3072 dims
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        # Wait for index to be ready
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)
            
    pinecone_index = pc.Index(index_name)
else:
    logger.warning("Pinecone API key not found. Retriever will fail if called.")
    pc = None
    pinecone_index = None

# Hardcode the text-embedding-004 model explicitly as requested
gemini_embedder = GoogleGenerativeAIEmbeddings(model=settings.embedding_model, google_api_key=settings.gemini_api_key)

def store_and_retrieve_rag_chunks(query_text: str, raw_search_results: list[dict], top_k: int = 3) -> list[str]:
    """
    Takes raw Tavily search results (dict with 'url' and 'content'),
    chunks the content, embeds it into Pinecone, and returns the top-K semantic matches for the query.
    """
    if not pinecone_index:
        logger.error("Pinecone index not initialized.")
        return []

    # 1. Combine and chunk raw text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    docs = []
    metadata = []
    ids = []
    
    timestamp = int(time.time())
    
    for i, res in enumerate(raw_search_results):
        content = res.get('content', '')
        url = res.get('url', '')
        title = res.get('title', 'Unknown Title')
        score = res.get('score', 0.0)
        pub_date = res.get('published_date', 'Unknown Date')
        
        if not content:
            continue
        
        chunks = text_splitter.split_text(content)
        for j, chunk in enumerate(chunks):
            docs.append(chunk)
            # Store the text chunk in metadata so we can retrieve it later
            metadata.append({
                "url": url, 
                "title": title, 
                "score": score, 
                "published_date": pub_date, 
                "source_index": i,
                "text": chunk
            })
            ids.append(f"doc_{timestamp}_{i}_chunk_{j}")
            
    if not docs:
        return []

    # 2. Namespace in Pinecone
    namespace = "tavily_search_cache"
        
    logger.info(f"Pinecone: Storing {len(docs)} new document chunks from Tavily.")
    
    # 3. Add chunks to Pinecone
    embeddings = []
    batch_size = 50
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i:i + batch_size]
        batch_emb = gemini_embedder.embed_documents(batch_docs)
        embeddings.extend(batch_emb)
    
    vectors = []
    for i in range(len(docs)):
        vectors.append({
            "id": ids[i],
            "values": embeddings[i],
            "metadata": metadata[i]
        })
        
    # Upsert in batches of 100
    for i in range(0, len(vectors), 100):
        pinecone_index.upsert(vectors=vectors[i:i+100], namespace=namespace)
    
    # 4. Query the collection 
    query_emb = gemini_embedder.embed_query(query_text)
    
    results = pinecone_index.query(
        vector=query_emb,
        top_k=top_k, # Pinecone handles if we ask for more than available natively
        include_metadata=True,
        namespace=namespace
    )
    
    # 5. Format the retrieved chunks for the LLM
    retrieved_chunks = []
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        chunk_text = f"Title: {meta.get('title', 'N/A')}\nSource URL: {meta.get('url', 'N/A')}\nPublish Date: {meta.get('published_date', 'N/A')}\nTavily Relevance Score: {meta.get('score', 'N/A')}\nContent: {meta.get('text', '')}"
        retrieved_chunks.append(chunk_text)
            
    return retrieved_chunks


def store_agent_memory(agent_id: str, hypothesis_text: str, reasoning: str, status: str):
    """
    Stores the adversarial agent's reasoning into a specific Pinecone namespace for long-term memory.
    """
    if not pinecone_index:
        return

    namespace = f"memory_{agent_id}"
    doc = f"Past Hypothesis Evaluated: {hypothesis_text}\nConclusion Status: {status}\nAgent Reasoning: {reasoning}"
    emb = gemini_embedder.embed_documents([doc])[0]
    
    pinecone_index.upsert(
        vectors=[{
            "id": str(uuid.uuid4()),
            "values": emb,
            "metadata": {"status": status, "text": doc}
        }],
        namespace=namespace
    )

def retrieve_agent_memory(agent_id: str, query_text: str, top_k: int = 2) -> list[str]:
    """
    Retrieves the most relevant past reasonings from the agent's memory.
    """
    if not pinecone_index:
        return []

    namespace = f"memory_{agent_id}"
    query_emb = gemini_embedder.embed_query(query_text)
    
    try:
        results = pinecone_index.query(
            vector=query_emb,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace
        )
        
        retrieved = []
        for match in results.get("matches", []):
            meta = match.get("metadata", {})
            if "text" in meta:
                retrieved.append(meta["text"])
        return retrieved
    except Exception as e:
        logger.error(f"Pinecone memory retrieval error: {e}")
        return []
