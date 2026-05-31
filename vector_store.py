import os
from typing import List, Dict, Any, Tuple

# Try importing chromadb
try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

class VectorStore:
    """
    Manages vector storage and retrieval.
    - Persistent Client: Persists embeddings in a local folder './chroma_db' using chromadb.
    - Fallback Client: If chromadb is unavailable, falls back to a clean, fast in-memory similarity calculator.
    """
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        self.use_chroma = HAS_CHROMADB
        self.in_memory_store: List[Dict[str, Any]] = []
        
        if self.use_chroma:
            try:
                # Initialize persistent chroma client
                self.client = chromadb.PersistentClient(path=self.db_path)
                # Create or get collection
                self.collection = self.client.get_or_create_collection(
                    name="document_chunks",
                    metadata={"hnsw:space": "cosine"} # Use cosine similarity
                )
                print("[DB STATUS] Persistent Chroma Vector DB Initialized.")
            except Exception as e:
                print(f"[DB WARNING] Failed to initialize Chroma DB: {e}. Falling back to In-Memory Vector Store.")
                self.use_chroma = False
        else:
            print("[DB STATUS] Chroma DB module not installed. Running In-Memory Vector Store.")

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Adds text chunks and their pre-computed embeddings to the database."""
        if not chunks or not embeddings:
            return

        if self.use_chroma:
            try:
                ids = [c["chunk_id"] for c in chunks]
                documents = [c["text"] for c in chunks]
                metadatas = [{"source_file": c["source_file"], "page_number": c["page_number"]} for c in chunks]
                
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
            except Exception as e:
                print(f"[DB WARNING] Failed to add to Chroma DB: {e}. Indexing to in-memory store instead.")
                self._add_to_in_memory(chunks, embeddings)
        else:
            self._add_to_in_memory(chunks, embeddings)

    def _add_to_in_memory(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        for chunk, embedding in zip(chunks, embeddings):
            self.in_memory_store.append({
                "chunk": chunk,
                "embedding": embedding
            })

    def query(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Retrieves top_k most similar chunks for the query embedding.
        Returns a list of tuples: (similarity_score, chunk_dictionary).
        """
        if self.use_chroma:
            try:
                # Query Chroma DB
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )
                
                # Format response to match (similarity, chunk_dict)
                retrieved = []
                if results and results["ids"] and results["ids"][0]:
                    ids = results["ids"][0]
                    documents = results["documents"][0]
                    metadatas = results["metadatas"][0]
                    # Chroma distances are distance metric (lower is better, for cosine, distance = 1 - similarity)
                    # We convert distance back to similarity: similarity = 1 - distance
                    distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids)
                    
                    for idx in range(len(ids)):
                        sim = 1.0 - distances[idx]
                        chunk_dict = {
                            "chunk_id": ids[idx],
                            "text": documents[idx],
                            "source_file": metadatas[idx]["source_file"],
                            "page_number": metadatas[idx]["page_number"]
                        }
                        retrieved.append((sim, chunk_dict))
                return retrieved
            except Exception as e:
                print(f"[DB WARNING] Chroma query failed: {e}. Falling back to in-memory search.")
                return self._query_in_memory(query_embedding, top_k)
        else:
            return self._query_in_memory(query_embedding, top_k)

    def _query_in_memory(self, query_embedding: List[float], top_k: int) -> List[Tuple[float, Dict[str, Any]]]:
        scored_chunks = []
        for item in self.in_memory_store:
            chunk = item["chunk"]
            emb = item["embedding"]
            
            # Since our embeddings are L2 normalized, cosine similarity is just the dot product
            if len(query_embedding) != len(emb):
                sim = 0.0
            else:
                sim = sum(q * e for q, e in zip(query_embedding, emb))
            scored_chunks.append((sim, chunk))
            
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return scored_chunks[:top_k]

    def clear(self):
        """Clears the collection database."""
        if self.use_chroma:
            try:
                self.client.delete_collection("document_chunks")
                self.collection = self.client.get_or_create_collection("document_chunks", metadata={"hnsw:space": "cosine"})
            except Exception:
                pass
        self.in_memory_store = []
