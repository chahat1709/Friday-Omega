import chromadb
import uuid
import logging
from typing import List, Dict, Any

class MemoryRAG:
    """
    Vector Memory System (RAG).
    Prevents LLM Context Collapse by chunking massive tool output (e.g., 50k lines of XML)
    into a searchable semantic vector space.
    """
    def __init__(self, persist_path="friday_memory_vdb"):
        self.persist_path = persist_path
        try:
            self.client = chromadb.PersistentClient(path=self.persist_path)
            self.collection = self.client.get_or_create_collection(name="tactical_memory")
            logging.info("[MemoryRAG] Vector database initialized.")
        except Exception as e:
            logging.error(f"[MemoryRAG] Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collection = None

    def store(self, agent_id: str, tool_name: str, text: str, mission_id: str = "global"):
        """Chunks and stores heavy output into the vector db."""
        if not self.collection or not text:
            return None
        
        # Simple chunking strategy: split by 1000 chars roughly
        chunk_size = 1000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            doc_id = f"{mission_id}_{agent_id}_{tool_name}_{uuid.uuid4().hex[:8]}"
            ids.append(doc_id)
            documents.append(chunk)
            metadatas.append({"agent": agent_id, "tool": tool_name, "mission": mission_id})
            
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return f"Stored {len(chunks)} chunks in Vector Memory."
        except Exception as e:
            logging.error(f"[MemoryRAG] Storage error: {e}")
            return f"Storage error: {e}"

    def search(self, query: str, n_results: int = 3, mission_id: str = None) -> str:
        """Searches the vector database for relevant chunks based on a semantic query."""
        if not self.collection:
            return "Error: Database offline."
            
        try:
            where_clause = {"mission": mission_id} if mission_id else None
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
            
            if not results['documents'] or not results['documents'][0]:
                return "Memory search yielded no relevant results."
                
            out = f"--- RAG RESULTS FOR: '{query}' ---\n"
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                out += f"[Intel from {meta['agent']} via {meta['tool']}]: {doc}\n"
            return out
            
        except Exception as e:
            logging.error(f"[MemoryRAG] Search error: {e}")
            return f"Memory search failed: {e}"

memory_rag = MemoryRAG()
