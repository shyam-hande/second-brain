# ingest_documents.py
"""
Run this script to load your documents into the vector store.
Run it again whenever you add new documents!
"""
from src.rag.document_loader import load_all_documents
from src.rag.vector_store import vector_store
import logfire

logfire.configure(service_name="second-brain", send_to_logfire=False)


def main():
    print("=" * 50)
    print("📚 DOCUMENT INGESTION")
    print("=" * 50)

    # Step 1: Show current state
    stats_before = vector_store.get_stats()
    print(f"\nBefore: {stats_before['total_chunks']} chunks in store")

    # Step 2: Load documents from disk
    print("\nLoading documents from disk...")
    documents = load_all_documents()

    if not documents:
        print("❌ No documents found! Check your data/ folders")
        return

    print(f"Found {len(documents)} chunks to process")

    # Step 3: Add to vector store
    print("\nAdding to vector store...")
    added = vector_store.add_documents(documents)

    # Step 4: Show final state
    stats_after = vector_store.get_stats()
    print(f"\nAfter: {stats_after['total_chunks']} chunks in store")
    print(f"Newly added: {added} chunks")

    # Step 5: Quick test search
    print("\n" + "=" * 50)
    print("🔍 TEST SEARCH")
    print("=" * 50)

    test_queries = [
        "pasta recipe",
        "python tips",
        "virtual environment",
    ]

    for query in test_queries:
        results = vector_store.search(query, top_k=2)
        print(f"\nQuery: '{query}'")
        if results:
            for r in results:
                print(f"  → [{r['relevance_score']}] {r['metadata']['filename']}: "
                      f"{r['content'][:80]}...")
        else:
            print("  → No results found")

    print("\n✅ Ingestion complete!")


if __name__ == "__main__":
    main()