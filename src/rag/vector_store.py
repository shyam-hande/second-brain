# src/rag/vector_store.py
import chromadb
from chromadb.utils import embedding_functions
import logfire
from src.config import settings
from src.rag.document_loader import Document


class VectorStore:
    """
    Manages document storage and semantic search using ChromaDB.
    
    ChromaDB stores documents as vectors (lists of numbers).
    Similar documents have similar vectors.
    Searching = finding vectors close to your query vector.
    """

    def __init__(self, collection_name: str = "second_brain"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_fn = None
        self._setup()

    def _setup(self):
        """Initialize ChromaDB and embedding function."""
        # Create local persistent ChromaDB
        # All data saved to disk at chroma_db_path
        self.client = chromadb.PersistentClient(
            path=settings.chroma_db_path
        )

        # Sentence transformer converts text → vectors
        # all-MiniLM-L6-v2 is small, fast, runs locally
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},  # cosine similarity
        )

        logfire.info(
            "vector_store_ready",
            collection=self.collection_name,
            existing_docs=self.collection.count(),
        )
        print(f"✅ Vector store ready | Existing docs: {self.collection.count()}")

    def add_documents(self, documents: list[Document]) -> int:
        """
        Add documents to the vector store.
        Skips documents that already exist (by doc_id).
        Returns count of newly added documents.
        """
        if not documents:
            return 0

        # Get existing IDs to avoid duplicates
        existing = self.collection.get()
        existing_ids = set(existing["ids"])

        # Filter out already stored documents
        new_docs = [d for d in documents if d.doc_id not in existing_ids]

        if not new_docs:
            print("ℹ️  All documents already in vector store")
            return 0

        # Prepare data for ChromaDB
        ids = [d.doc_id for d in new_docs]
        texts = [d.content for d in new_docs]
        metadatas = [d.metadata for d in new_docs]

        # Add to collection (embeddings created automatically)
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )

        logfire.info("documents_added", count=len(new_docs))
        print(f"✅ Added {len(new_docs)} new chunks to vector store")
        return len(new_docs)

    def search(self, query: str, top_k: int = None) -> list[dict]:
        """
        Search for documents similar to the query.
        
        Returns list of results with content and metadata.
        """
        top_k = top_k or settings.top_k_results

        if self.collection.count() == 0:
            logfire.warning("search_on_empty_collection")
            return []

        with logfire.span("vector_search", query=query, top_k=top_k):
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, self.collection.count()),
            )

        # Format results nicely
        formatted = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "relevance_score": round(1 - results["distances"][0][i], 3),
                })

        logfire.info(
            "search_completed",
            query=query,
            results_found=len(formatted),
        )

        return formatted

    def get_stats(self) -> dict:
        """Get statistics about the vector store."""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection_name,
            "embedding_model": settings.embedding_model,
        }

    def clear(self):
        """Clear all documents from the store."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
        )
        print("🗑️  Vector store cleared")


# Global instance
vector_store = VectorStore()