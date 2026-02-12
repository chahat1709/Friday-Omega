import chromadb
import uuid
import time
import json
import os
# Fix Unicode Error in Windows
os.environ["PYTHONUTF8"] = "1"
from concurrent.futures import ThreadPoolExecutor

class AdaptiveEngine:
    def __init__(self, persist_path="friday_memory_vdb"):
        print("[AdaptiveEngine] Initializing Vector Memory (ChromaDB)...")
        try:
            # Use persistent storage
            self.client = chromadb.PersistentClient(path=persist_path)
            # self.client = chromadb.Client() 
            self.collection = self.client.get_or_create_collection(name="user_interactions")
            self.feedback_collection = self.client.get_or_create_collection(name="user_feedback")
            self.executor = ThreadPoolExecutor(max_workers=1)
            print("[AdaptiveEngine] Memory System Online.")
        except Exception as e:
            print(f"[AdaptiveEngine] Init Error: {e}")
            raise e

    def remember_interaction(self, user_query, ai_response, metadata=None):
        """
        Asynchronously stores the interaction in vector DB.
        """
        def _store():
            try:
                doc_id = str(uuid.uuid4())
                meta = metadata or {}
                meta['timestamp'] = time.time()
                meta['type'] = 'conversation'
                
                # We embed the "Combined Context" but primarily search by User Query usually
                text_to_embed = f"User: {user_query}\nAI: {ai_response}"
                
                self.collection.add(
                    documents=[text_to_embed],
                    metadatas=[meta],
                    ids=[doc_id]
                )
                # print(f"[Memory] Stored I/O: {doc_id}")
            except Exception as e:
                print(f"[Memory] Store Error: {e}")

        self.executor.submit(_store)

    def recall_context(self, query, n_results=3):
        """
        Retrieves relevant past interactions to provide context.
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            context_snippets = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    context_snippets.append(f"[Past Interaction {i+1}]: {doc}")
            
            return "\n".join(context_snippets)
        except Exception as e:
            print(f"[Memory] Recall Error: {e}")
            return ""

    def process_feedback(self, result_type, details):
        """
        Stores user feedback (Positive/Negative) to adjust future behavior.
        """
        def _store_feedback():
            try:
                doc_id = str(uuid.uuid4())
                self.feedback_collection.add(
                    documents=[details],
                    metadatas=[{"type": result_type, "timestamp": time.time()}],
                    ids=[doc_id]
                )
            except Exception as e:
                print(f"[Memory] Feedback Store Error: {e}")
        
        self.executor.submit(_store_feedback)
