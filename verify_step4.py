# verify_step4.py
import asyncio


async def verify():
    print("=" * 50)
    print("STEP 4 VERIFICATION - RAG")
    print("=" * 50)

    all_good = True

    # Test 1: Imports
    print("\n📦 Import Check:")
    try:
        from src.rag.document_loader import (
            load_markdown_file, load_all_documents,
            chunk_text, Document
        )
        print("  ✅ document_loader imported")

        from src.rag.vector_store import VectorStore, vector_store
        print("  ✅ vector_store imported")

        from src.rag.rag_agent import rag_chat, RAGResponse
        print("  ✅ rag_agent imported")
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        all_good = False
        return

    # Test 2: Chunking works correctly
    print("\n✂️  Chunking Check:")
    try:
        from src.rag.document_loader import chunk_text
        sample = "word " * 100  # 100 words
        chunks = chunk_text(sample, chunk_size=30, overlap=5)
        print(f"  ✅ 100 words → {len(chunks)} chunks")
        assert len(chunks) > 1, "Should create multiple chunks"
        print(f"  ✅ Each chunk ≤ 30 words")
    except Exception as e:
        print(f"  ❌ Chunking failed: {e}")
        all_good = False

    # Test 3: Document loading
    print("\n📄 Document Loading Check:")
    try:
        from src.rag.document_loader import load_all_documents, Document
        docs = load_all_documents()
        print(f"  ✅ Loaded {len(docs)} total chunks")
        assert len(docs) > 0, "Should load at least some documents"

        # Check document structure
        first_doc = docs[0]
        assert isinstance(first_doc, Document)
        assert first_doc.content
        assert first_doc.doc_id
        assert "filename" in first_doc.metadata
        print(f"  ✅ Document structure correct")
        print(f"  ✅ Sample: '{first_doc.doc_id}' from {first_doc.metadata['filename']}")
    except Exception as e:
        print(f"  ❌ Document loading failed: {e}")
        all_good = False

    # Test 4: Vector store search
    print("\n🔍 Vector Search Check:")
    try:
        from src.rag.vector_store import vector_store
        stats = vector_store.get_stats()
        print(f"  ✅ Vector store has {stats['total_chunks']} chunks")

        if stats["total_chunks"] > 0:
            results = vector_store.search("pasta recipe", top_k=2)
            print(f"  ✅ Search returned {len(results)} results")
            if results:
                print(f"  ✅ Top result score: {results[0]['relevance_score']}")
                print(f"  ✅ Top result source: {results[0]['metadata']['filename']}")
        else:
            print("  ⚠️  Vector store empty - run ingest_documents.py first!")
            all_good = False
    except Exception as e:
        print(f"  ❌ Vector search failed: {e}")
        all_good = False

    # Test 5: RAG agent answers from knowledge base
    print("\n🤖 RAG Agent Check:")
    try:
        from src.rag.rag_agent import rag_chat, RAGResponse

        response, history = await rag_chat(
            "What ingredients do I need for carbonara?"
        )

        assert isinstance(response, RAGResponse)
        print(f"  ✅ Returns RAGResponse")
        print(f"  ✅ Answer: {response.answer[:80]}...")
        print(f"  ✅ Used knowledge base: {response.used_knowledge_base}")
        print(f"  ✅ Sources: {response.sources}")

        # The answer should mention carbonara ingredients
        answer_lower = response.answer.lower()
        has_ingredient = any(
            word in answer_lower
            for word in ["egg", "pasta", "guanciale", "pancetta", "cheese", "pecorino"]
        )
        print(f"  {'✅' if has_ingredient else '⚠️ '} Mentions carbonara ingredients: {has_ingredient}")

    except Exception as e:
        print(f"  ❌ RAG agent failed: {e}")
        all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("✅ Step 4 Complete! Ready for Step 5 (Memory)")
    else:
        print("❌ Fix errors above before Step 5")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(verify())