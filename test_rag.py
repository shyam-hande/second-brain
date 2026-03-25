# test_rag.py
import asyncio
from src.rag.rag_agent import rag_chat


async def main():
    print("=" * 60)
    print("RAG AGENT TEST")
    print("=" * 60)

    # These questions should be answered using YOUR documents
    questions = [
        "What pasta recipe do I have? List the ingredients.",
        "What Python tips do I have about list comprehensions?",
        "How do I make carbonara without cream?",
        "What is the walrus operator in Python?",
    ]

    for q in questions:
        print(f"\n❓ Question: {q}")
        response, _ = await rag_chat(q)
        print(f"💬 Answer: {response.answer}")
        print(f"📁 Sources used: {response.sources}")
        print(f"🧠 Used knowledge base: {response.used_knowledge_base}")
        print(f"🎯 Confidence: {response.confidence}")
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())