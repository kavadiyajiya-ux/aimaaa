import os
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = "chroma_db"
POLICIES_CSV = "policies.csv"

class PolicyMemory:
    def __init__(self):
        self.initialized = False
        self.use_fallback = False
        self.encoder = None
        self.collection = None
        self.client = None
        self.fallback_policies = []

    def init_db(self) -> None:
        """
        Loads policies, initializes ChromaDB and the sentence encoder.
        Falls back to keyword matching if dependencies fail to download/initialize.
        """
        if self.initialized:
            return

        # Pre-load policies for fallback list
        if os.path.exists(POLICIES_CSV):
            try:
                df = pd.read_csv(POLICIES_CSV)
                self.fallback_policies = df.to_dict('records')
            except Exception as e:
                print(f"[Memory] Error loading CSV: {e}")
                self.fallback_policies = []
        else:
            self.fallback_policies = []

        try:
            print("[Memory] Initializing local SentenceTransformer (all-MiniLM-L6-v2)...")
            # Set HF cache dir inside workspace to keep it localized
            os.environ["HF_HOME"] = os.path.join(os.getcwd(), ".hf_cache")
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            
            print("[Memory] Connecting to persistent ChromaDB client...")
            self.client = chromadb.PersistentClient(path=CHROMA_DIR)
            self.collection = self.client.get_or_create_collection("policies")
            
            # Populate DB if empty
            if self.collection.count() == 0 and self.fallback_policies:
                print("[Memory] Populating ChromaDB with policy documents...")
                ids = []
                documents = []
                embeddings = []
                metadatas = []
                
                for idx, row in enumerate(self.fallback_policies):
                    doc_text = f"[{row['category']}] {row['title']}: {row['content']}"
                    ids.append(str(row.get('policy_id', f"POL-{idx}")))
                    documents.append(doc_text)
                    metadatas.append({"category": row.get("category", "General"), "title": row.get("title", "")})
                    
                    # Encode using SentenceTransformer
                    emb = self.encoder.encode(doc_text).tolist()
                    embeddings.append(emb)
                    
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                print(f"[Memory] Successfully ingested {len(documents)} policies into ChromaDB.")
            
            self.initialized = True
            print("[Memory] ChromaDB Memory System is active.")
            
        except Exception as e:
            print(f"[Memory] Failed to start Vector Store: {e}")
            print("[Memory] Enabling high-fidelity keyword fallback engine.")
            self.use_fallback = True
            self.initialized = True

    def fallback_search(self, query: str, limit: int = 3) -> list[str]:
        """
        A high-fidelity keyword overlapping algorithm for finding policies when vector store is down.
        """
        query_words = set(re_tokenize(query.lower()))
        scored_policies = []
        
        for p in self.fallback_policies:
            content = str(p.get('content', ''))
            title = str(p.get('title', ''))
            category = str(p.get('category', ''))
            
            doc_text = f"[{category}] {title}: {content}"
            doc_words = re_tokenize(doc_text.lower())
            
            # Compute intersection weight
            score = 0
            for qw in query_words:
                if len(qw) < 3:
                    continue  # skip tiny words like 'a', 'in', 'to'
                if qw in category.lower():
                    score += 5
                if qw in title.lower():
                    score += 3
                if qw in content.lower():
                    score += 1
            
            # Exact matches on category names
            for cat in ["it", "hr", "payroll", "security", "operations"]:
                if cat in query.lower() and cat in category.lower():
                    score += 10
                    
            scored_policies.append((score, doc_text))
            
        # Sort by score descending and return
        scored_policies.sort(key=lambda x: x[0], reverse=True)
        return [text for score, text in scored_policies[:limit]]

    def search(self, query: str, limit: int = 3) -> list[str]:
        """
        Searches policy memory for the top N matches.
        """
        self.init_db()
        if self.use_fallback or not self.collection:
            return self.fallback_search(query, limit)
            
        try:
            # Query using ChromaDB
            query_emb = self.encoder.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_emb],
                n_results=limit
            )
            
            documents = results.get("documents", [[]])[0]
            if documents:
                return documents
            return self.fallback_search(query, limit)
        except Exception as e:
            print(f"[Memory Search Error] {e}. Falling back...")
            return self.fallback_search(query, limit)

def re_tokenize(text: str) -> list[str]:
    """Helper to split words and remove punctuation."""
    import re
    return re.findall(r'\b\w+\b', text)

# Global memory instance
policy_memory = PolicyMemory()

def retrieve_relevant_policies(query: str, limit: int = 3) -> list[str]:
    """
    Exposed functional API for retrieving policies.
    """
    return policy_memory.search(query, limit)
