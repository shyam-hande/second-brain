# src/rag/document_loader.py
import os
import re
from dataclasses import dataclass
from pathlib import Path
import logfire
from src.config import settings


@dataclass
class Document:
    """Represents a loaded document chunk."""
    content: str
    metadata: dict
    doc_id: str


def clean_text(text: str) -> str:
    """Remove extra whitespace and empty lines."""
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Why overlap? So we don't lose context at chunk boundaries.
    
    Example with chunk_size=10, overlap=3:
    "Hello World Python Code"
     chunk1: "Hello World"
     chunk2: "rld Python"   ← overlaps with chunk1
     chunk3: "hon Code"     ← overlaps with chunk2
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        # Move forward by chunk_size minus overlap
        start += chunk_size - overlap

        # Stop if we have covered everything
        if start >= len(words):
            break

    return chunks


def load_markdown_file(file_path: str) -> list[Document]:
    """
    Load a single markdown file and return chunks as Documents.
    """
    path = Path(file_path)

    if not path.exists():
        logfire.warning(f"File not found: {file_path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Clean the text
    text = clean_text(raw_text)

    # Extract title from first heading if available
    title = path.stem  # filename without extension
    first_line = text.split("\n")[0] if text else ""
    if first_line.startswith("#"):
        title = first_line.lstrip("#").strip()

    # Split into chunks
    chunks = chunk_text(text)

    # Create Document objects
    documents = []
    for i, chunk in enumerate(chunks):
        doc = Document(
            content=chunk,
            metadata={
                "source": str(path),
                "filename": path.name,
                "title": title,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "category": path.parent.name,  # notes, recipes, etc.
            },
            doc_id=f"{path.stem}_chunk_{i}",
        )
        documents.append(doc)

    logfire.info(
        "document_loaded",
        file=path.name,
        chunks=len(documents),
        title=title,
    )

    return documents


def load_all_documents() -> list[Document]:
    """
    Load all documents from all data directories.
    """
    all_docs = []
    directories = [
        settings.notes_path,
        settings.recipes_path,
        settings.transcriptions_path,
    ]

    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            continue

        # Find all markdown files
        md_files = list(dir_path.glob("*.md"))
        txt_files = list(dir_path.glob("*.txt"))
        all_files = md_files + txt_files

        for file_path in all_files:
            docs = load_markdown_file(str(file_path))
            all_docs.extend(docs)

    logfire.info("all_documents_loaded", total_chunks=len(all_docs))
    print(f"📄 Loaded {len(all_docs)} chunks from {len(directories)} directories")
    return all_docs