# AI Concepts I Am Learning

## Large Language Models (LLMs)
LLMs are neural networks trained on massive text datasets.
They predict the next token based on context.
Examples: Claude, GPT-4, Gemini.

## RAG - Retrieval Augmented Generation
RAG combines a vector database with an LLM.
First retrieve relevant documents, then generate an answer.
This grounds the LLM in real data and reduces hallucination.

## Vector Embeddings
Embeddings convert text into lists of numbers (vectors).
Similar text has similar vectors.
Used for semantic search - find meaning not just keywords.

## Multi-Agent Systems
Multiple AI agents work together, each specializing in one task.
Patterns: orchestrator, pipeline, peer-to-peer.
Benefits: modularity, specialization, parallelism.

## Pydantic AI
A Python framework for building production AI agents.
Uses Pydantic models for structured inputs and outputs.
Supports multiple LLM providers including Anthropic.