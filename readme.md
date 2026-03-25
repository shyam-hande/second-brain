# 🧠 Second Brain - Personal AI Knowledge Assistant

A multi-agent AI system that acts as your personal second brain.
Store notes, recipes, meeting transcriptions, and any knowledge —
then chat with it, search it, and let it remember things about you.

Built with **Pydantic AI**, **ChromaDB**, **Logfire**, and **Anthropic Claude**.

---

## 📋 Table of Contents

- [What It Does](#what-it-does)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [Using the CLI](#using-the-cli)
- [Adding Your Own Content](#adding-your-own-content)
- [Running Evaluations](#running-evaluations)
- [Observability](#observability)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## What It Does

| Feature | Description |
|---|---|
| 🔍 **RAG Search** | Searches your personal notes/recipes before answering |
| 🧠 **Memory** | Remembers facts about you across sessions |
| 🤖 **Multi-Agent** | Specialized agents collaborate to give better answers |
| 🔒 **PII Guardrails** | Automatically removes sensitive info before storing |
| 📊 **Evaluations** | Proves the system works better than a plain chatbot |
| 🔭 **Observability** | Full tracing of every agent call with Logfire |

---

## System Architecture

```
You (CLI)
    ↓
Orchestrator Agent          ← decides which agents to call
    ↓           ↓           ↓
Research      Synthesis   Memory
Agent         Agent       Agent
(ChromaDB     (combines   (TinyDB
 RAG search)   findings)   persistence)
    ↓
PII Guardrail               ← cleans all text before storage
    ↓
Logfire Observability       ← traces every operation
```

---

## Prerequisites

- Python 3.11 or higher
- An Anthropic API key
- ~2GB disk space (for embedding models)
- Internet connection (first run only, to download models)

---

## Installation

### Step 1 - Clone or download the project

```bash
cd /your/projects/folder
# project folder should already exist as second-brain
cd second-brain
```

### Step 2 - Create virtual environment

```bash
python -m venv venv
```

### Step 3 - Activate virtual environment

```bash
# Mac / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 4 - Install dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ First install takes 3-5 minutes.
> `sentence-transformers` downloads a 90MB embedding model.

### Step 5 - Set up your API key

Create a `.env` file in the project root:

```bash
# .env
ANTHROPIC_API_KEY=your_actual_api_key_here
```

> Never commit this file. It is already in `.gitignore`.

---

## Configuration

All settings live in `src/config.py`.
They can be overridden via environment variables or the `.env` file.

| Setting | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | required | Your Anthropic API key |
| `model_name` | `claude-sonnet-4-20250514` | Claude model to use |
| `chroma_db_path` | `./data/chroma_db` | Vector store location |
| `embedding_model` | `all-MiniLM-L6-v2` | Local embedding model |
| `top_k_results` | `3` | Number of RAG results |
| `memory_db_path` | `./data/memory.json` | Memory storage file |
| `max_conversation_history` | `20` | Messages to keep in context |

---

## Running the System

### Always activate venv first!

```bash
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

---

### 1. Health Check (recommended first run)

Verifies all components are working before you start:

```bash
python health_check.py
```

Expected output:
```
✅ Configuration      - Model: claude-sonnet-4-20250514
✅ RAG / Vector Store - 45 chunks in vector store
✅ Memory Store       - 12 memories | 3 conversations
✅ PII Guardrails     - Detected and redacted 2 PII items
✅ Base Agent         - Response: 'OK'
✅ Research Agent     - 3 findings | Sources: [...]
✅ Orchestrator       - Agents used: [...] | Time: 4.2s
✅ Observability      - Logfire tracing active
✅ Evaluation         - Scorer works | Sample score: 0.875
```

---

### 2. Ingest Your Documents

Load your notes and documents into the knowledge base:

```bash
python ingest_documents.py
```

Expected output:
```
📄 Loaded 47 chunks from 3 directories
✅ Added 47 new chunks to vector store

🔍 TEST SEARCH
Query: 'pasta recipe'
  → [0.89] pasta_carbonara.md: 400g spaghetti, 200g guanciale...
```

> Run this again whenever you add new files to `data/`.

---

### 3. Launch the Second Brain

```bash
python main.py
```

Expected output:
```
Starting up systems...
📚 Knowledge base: 47 chunks loaded
💾 Memory: 12 memories loaded
🔑 Session: a3f8b2c1...

╭─────────────────────────────────────╮
│  🧠 Second Brain                    │
│  Your personal AI knowledge         │
│  assistant                          │
│                                     │
│  Type /help to see all commands     │
│  Type /quit to exit                 │
╰─────────────────────────────────────╯

You:
```

---

## Using the CLI

### All Commands

| Command | What it does | Example |
|---|---|---|
| `/chat <message>` | Full multi-agent response | `/chat What recipes do I have?` |
| `/search <query>` | Direct knowledge base search | `/search carbonara ingredients` |
| `/memory` | Show all stored memories | `/memory` |
| `/memory <keyword>` | Search memories by keyword | `/memory python` |
| `/remember <fact>` | Manually save a memory | `/remember I prefer bullet points` |
| `/profile` | Show your user profile | `/profile` |
| `/ingest` | Reload documents | `/ingest` |
| `/stats` | Show system statistics | `/stats` |
| `/eval` | Run quick evaluation | `/eval` |
| `/clear` | Clear the screen | `/clear` |
| `/quit` | Exit (saves memories) | `/quit` |

> 💡 **Tip:** You can also just type a message without a slash command
> and it will automatically use the full multi-agent system.

---

### Example Session

```
You: /chat What pasta recipes do I have?

🧠 Second Brain
─────────────────────────────────────────────
You have a **Pasta Carbonara** recipe! Here are the details:

**Ingredients:**
- 400g spaghetti
- 200g guanciale (or pancetta)
- 4 egg yolks
- 100g Pecorino Romano
...

🤖 Agents: orchestrator, research, synthesis
📁 Sources: pasta_carbonara.md
🎯 Confidence: high
⏱️  Time: 4.1s
─────────────────────────────────────────────

You: /remember I prefer metric measurements in recipes

✅ Remembered: 'I prefer metric measurements in recipes'

You: /search python virtual environment

Found 2 results:
┌─────────────────────────────────────────────┐
│ 1. python_tips.md (notes) score: 0.91       │
│ Always use python -m venv venv not          │
│ virtualenv for consistency...               │
└─────────────────────────────────────────────┘

You: /stats

📊 System Statistics
─────────────────────────────────────────
Knowledge Base   total_chunks      47
Memory Store     total_memories    15
Agent Metrics    total_calls       8
Agent Metrics    avg_response      3.2s
─────────────────────────────────────────

You: /quit
💭 Saving session memories...
  ✅ Saved 3 new memories from this session
👋 Goodbye! Your memories have been saved.
```

---

## Adding Your Own Content

Drop any `.md` or `.txt` file into the appropriate folder:

```
data/
├── notes/              ← general notes, learning, ideas
├── recipes/            ← cooking recipes
└── transcriptions/     ← meeting notes, voice transcriptions
```

Then reload the knowledge base:

```bash
# Option 1: Run the script directly
python ingest_documents.py

# Option 2: Use the CLI command while running
/ingest
```

### Example file formats

**Notes** (`data/notes/my_notes.md`):
```markdown
# My Learning Notes

## Topic One
Key point about topic one.
More details here.

## Topic Two
Another key concept.
```

**Recipes** (`data/recipes/my_recipe.md`):
```markdown
# Recipe Name

## Ingredients
- Item one
- Item two

## Steps
1. First step
2. Second step
```

---

## Running Evaluations

Evaluations prove that RAG + multi-agent is better than a plain chatbot.

### Quick eval (inside CLI)

```bash
# While main.py is running
/eval
```

Output:
```
Baseline: score=0.612 pass_rate=50%
RAG:      score=0.847 pass_rate=100%
✅ RAG improves score by 0.235 (38.4%)
```

### Full evaluation suite

```bash
python run_evals.py
```

Output:
```
📊 System Comparison
┌─────────────────┬───────┬───────────┬───────────┬─────────────┐
│ System          │ Cases │ Pass Rate │ Avg Score │ Avg Latency │
├─────────────────┼───────┼───────────┼───────────┼─────────────┤
│ Baseline        │   3   │    50%    │   0.612   │    2.1s     │
│ RAG System      │   5   │   100%    │   0.847   │    3.8s     │
│ Multi-Agent     │   3   │   100%    │   0.891   │    8.2s     │
└─────────────────┴───────┴───────────┴───────────┴─────────────┘

💡 Key Insights:
  📚 RAG is 38.4% better than baseline
  🤖 Multi-Agent is 45.6% better than baseline
  ⏱️  Multi-Agent is 4.4s slower than RAG (trade-off for quality)

🏆 Best performing system: Multi-Agent System
```

Results are saved to `eval_results_YYYYMMDD_HHMMSS.json`.

### Generate full evidence report

```bash
python generate_evidence.py
```

This runs all demonstrations and saves a complete JSON evidence report.

---

## Observability

The system uses **Logfire** for observability.
All agent calls are automatically traced.

### What is traced

- Every agent call (input, output, duration)
- Vector store searches (query, results, scores)
- Memory operations (save, retrieve, extract)
- PII detection events (types found, count redacted)
- Multi-agent pipeline (which agents ran, in what order)

### Viewing traces in console

Traces appear automatically in your terminal when running any script.
Look for lines like:

```
13:45:01 second-brain  chat_async                     message='What recipes...'
13:45:01 second-brain    pydantic_ai.agent             claude-sonnet-4-20250514
13:45:01 second-brain      vector_search              query='pasta' top_k=3
13:45:03 second-brain    pydantic_ai.agent             completed
13:45:03 second-brain  chat_async                     completed 2.3s
```

### Viewing the agent metrics

```bash
# While in CLI
/stats

# Or in Python
python -c "
from src.observability.metrics import agent_metrics
import json
print(json.dumps(agent_metrics.summary(), indent=2))
"
```

### Sending to Logfire cloud (optional)

If you want a visual dashboard, create a free account at
[logfire.pydantic.dev](https://logfire.pydantic.dev) then update
`src/agents/base_agent.py`:

```python
logfire.configure(
    service_name="second-brain",
    send_to_logfire=True,   # ← change to True
    token="your_logfire_token",
)
```

---

## Project Structure

```
second-brain/
│
├── main.py                     ← Entry point - run this!
├── ingest_documents.py         ← Load docs into knowledge base
├── run_evals.py                ← Full evaluation suite
├── generate_evidence.py        ← Generate evidence report
├── health_check.py             ← System health verification
├── requirements.txt            ← Python dependencies
├── .env                        ← API keys (never commit!)
├── .gitignore                  ← Git ignore rules
│
├── src/
│   ├── config.py               ← Central configuration
│   │
│   ├── agents/
│   │   ├── base_agent.py       ← Simple Claude agent
│   │   ├── research_agent.py   ← Searches knowledge base
│   │   ├── synthesis_agent.py  ← Combines findings
│   │   └── orchestrator.py     ← Multi-agent director
│   │
│   ├── rag/
│   │   ├── document_loader.py  ← Reads & chunks .md files
│   │   ├── vector_store.py     ← ChromaDB vector search
│   │   └── rag_agent.py        ← RAG-powered chat
│   │
│   ├── memory/
│   │   ├── models.py           ← Memory data models
│   │   ├── memory_store.py     ← TinyDB local storage
│   │   ├── memory_agent.py     ← Extracts facts from chat
│   │   └── session.py          ← Session lifecycle
│   │
│   ├── guardrails/
│   │   ├── pii_detector.py     ← Regex PII detection
│   │   └── guardrail.py        ← Cleans text middleware
│   │
│   ├── evaluation/
│   │   ├── models.py           ← Eval data structures
│   │   ├── scorer.py           ← Numeric scoring (0-1)
│   │   ├── dataset.py          ← Test cases
│   │   └── evaluator.py        ← Runs comparisons
│   │
│   ├── observability/
│   │   ├── tracer.py           ← Logfire setup
│   │   └── metrics.py          ← Custom metrics tracker
│   │
│   └── cli/
│       ├── display.py          ← Rich formatting helpers
│       ├── commands.py         ← Slash command handlers
│       └── app.py              ← Main CLI loop
│
├── data/
│   ├── notes/                  ← Your markdown notes
│   ├── recipes/                ← Your recipes
│   ├── transcriptions/         ← Meeting notes etc
│   ├── chroma_db/              ← Vector store (auto-created)
│   └── memory.json             ← Memory store (auto-created)
│
└── tests/
    ├── verify_step2.py         ← Agent verification
    ├── verify_step3.py         ← Observability verification
    ├── verify_step4.py         ← RAG verification
    ├── verify_step5.py         ← Memory verification
    ├── verify_step6.py         ← PII verification
    ├── verify_step7.py         ← Multi-agent verification
    ├── verify_step8.py         ← Eval verification
    ├── verify_step9.py         ← CLI verification
    └── verify_step10.py        ← End-to-end verification
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'logfire'`

Your virtual environment is not active:

```bash
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

---

### `ANTHROPIC_API_KEY not set`

Create or check your `.env` file:

```bash
cat .env
# Should show: ANTHROPIC_API_KEY=sk-ant-...
```

---

### `Model not found` error

Check available models with:

```bash
python -c "
import anthropic, os
from dotenv import load_dotenv
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
for m in client.models.list().data:
    print(m.id)
"
```

Then update `model_name` in `src/config.py`.

---

### Vector store is empty

Run the ingestion script:

```bash
python ingest_documents.py
```

Make sure you have `.md` or `.txt` files in `data/notes/`,
`data/recipes/`, or `data/transcriptions/`.

---

### `asyncio.run() cannot be called from a running event loop`

Use `chat_async()` instead of `chat()` inside async functions:

```python
# Inside async def - use this:
response, history = await chat_async("your message")

# Outside async (plain scripts) - use this:
response, history = chat("your message")
```

---

### Slow first response

Normal! First run downloads the embedding model (~90MB).
Subsequent runs use the cached model and are much faster.

---

### ChromaDB errors

Delete the vector store and re-ingest:

```bash
rm -rf data/chroma_db
python ingest_documents.py
```

---

### Memory store issues

Reset the memory store (this clears all memories):

```bash
rm data/memory.json
python main.py
```

---

## Quick Reference Card

```bash
# Setup (one time)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your_key" > .env

# Every time you open a new terminal
source venv/bin/activate

# Daily workflow
python health_check.py        # verify everything works
python ingest_documents.py    # load new documents
python main.py                # start your second brain

# Evaluation
python run_evals.py           # full comparison
python generate_evidence.py   # evidence report

# Inside the CLI
/chat What do I know about X?
/search keyword
/memory
/remember important fact
/stats
/quit
```

---

## Built With

| Library | Purpose |
|---|---|
| `pydantic-ai` | AI agent framework |
| `anthropic` | Claude LLM provider |
| `chromadb` | Local vector database |
| `sentence-transformers` | Local text embeddings |
| `tinydb` | Local JSON memory store |
| `logfire` | Observability & tracing |
| `rich` | Beautiful CLI output |
| `pydantic-settings` | Configuration management |
| `python-dotenv` | Environment variables |