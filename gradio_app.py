# gradio_app.py
"""
Gradio Web UI for Second Brain - Compatible with Gradio 6.0+
Run with: python gradio_app.py
Then open: http://localhost:7860
"""
import asyncio
import concurrent.futures
import gradio as gr
import logfire
from datetime import datetime

# Setup observability
logfire.configure(
    service_name="second-brain-gradio",
    send_to_logfire=False,
)
logfire.instrument_pydantic_ai()


# ── Helper to run async in sync context ───────────────────────────────────────
def run_async(coro):
    """Run async coroutine from sync Gradio handlers."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ── Startup ────────────────────────────────────────────────────────────────────
def startup():
    """Load documents into vector store on startup."""
    try:
        from src.rag.document_loader import load_all_documents
        from src.rag.vector_store import vector_store
        docs = load_all_documents()
        if docs:
            vector_store.add_documents(docs)
            print(f"✅ Loaded {len(docs)} chunks into knowledge base")
        else:
            print("⚠️  No documents found in data/ folders")
    except Exception as e:
        print(f"⚠️  Startup warning: {e}")


# ── Session storage ────────────────────────────────────────────────────────────
_session_messages = []

def _save_to_session(user_msg: str, assistant_msg: str):
    _session_messages.append(f"User: {user_msg}")
    _session_messages.append(f"Assistant: {assistant_msg}")


# ── TAB 1: Chat ────────────────────────────────────────────────────────────────
def chat_handler(message: str, history: list) -> tuple:
    """
    Handle chat using full multi-agent system.
    Gradio 6.0 history format:
      [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    if not message.strip():
        return "", history

    with logfire.span("gradio_chat", message=message):
        try:
            async def _run():
                from src.agents.orchestrator_agent import orchestrator
                return await orchestrator.process(message)

            response = run_async(_run())
            answer = response.answer

            # Build metadata footer
            metadata_parts = []
            if response.sources:
                metadata_parts.append(
                    f"📁 **Sources:** {', '.join(response.sources)}"
                )
            if response.agents_used:
                metadata_parts.append(
                    f"🤖 **Agents:** {', '.join(response.agents_used)}"
                )
            if response.confidence:
                metadata_parts.append(
                    f"🎯 **Confidence:** {response.confidence}"
                )
            if response.processing_time_seconds:
                metadata_parts.append(
                    f"⏱️ **Time:** {response.processing_time_seconds}s"
                )
            if response.used_memory:
                metadata_parts.append("💾 **Used memory:** yes")

            if metadata_parts:
                answer += "\n\n---\n" + " | ".join(metadata_parts)

            if response.follow_up_suggestions:
                answer += "\n\n💡 **Follow-ups:**\n"
                for s in response.follow_up_suggestions:
                    answer += f"- {s}\n"

            _save_to_session(message, response.answer)

            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": answer})
            return "", history

        except Exception as e:
            logfire.error("gradio_chat_error", error=str(e))
            history.append({"role": "user", "content": message})
            history.append(
                {"role": "assistant", "content": f"❌ Error: {str(e)}"}
            )
            return "", history


# ── TAB 2: Search ──────────────────────────────────────────────────────────────
def search_handler(query: str) -> str:
    """Direct vector search - no LLM."""
    if not query.strip():
        return "Please enter a search query."

    try:
        from src.rag.vector_store import vector_store
        results = vector_store.search(query, top_k=4)

        if not results:
            return "No results found in knowledge base."

        output = f"## 🔍 Results for: '{query}'\n\n"
        for i, result in enumerate(results, 1):
            filename = result["metadata"].get("filename", "unknown")
            category = result["metadata"].get("category", "")
            score = result["relevance_score"]
            content = result["content"][:300]
            output += f"### {i}. {filename} `[{category}]` — Score: `{score}`\n\n"
            output += f"{content}...\n\n---\n\n"

        return output

    except Exception as e:
        return f"❌ Search error: {str(e)}"


# ── TAB 3: Memory ──────────────────────────────────────────────────────────────
def get_memories(filter_keyword: str = "") -> str:
    """Get stored memories."""
    try:
        from src.memory.memory_store import memory_store

        if filter_keyword and filter_keyword.strip():
            memories = memory_store.search_memories(filter_keyword)
            title = f"Memories matching '{filter_keyword}'"
        else:
            memories = memory_store.get_all_memories()
            title = "All Stored Memories"

        if not memories:
            return "No memories stored yet. Have a conversation first!"

        output = f"## 💾 {title} ({len(memories)} total)\n\n"
        for m in memories:
            stars = "⭐" * m.importance
            date = m.created_at[:10] if m.created_at else "unknown"
            output += f"**[{m.type.upper()}]** {stars} — `{date}`\n\n"
            output += f"> {m.content}\n\n---\n\n"

        return output

    except Exception as e:
        return f"❌ Error: {str(e)}"


def save_memory_handler(content: str) -> str:
    """Manually save a memory."""
    if not content.strip():
        return "Please enter something to remember."

    try:
        from src.memory.memory_store import memory_store
        from src.memory.models import MemoryType
        from src.guardrails.guardrail import pii_guardrail

        clean_content = pii_guardrail.process_for_storage(content)
        memory = memory_store.save_memory(
            content=clean_content,
            memory_type=MemoryType.FACT,
            importance=4,
            tags=["manual", "gradio"],
        )

        msg = f"✅ Remembered: '{clean_content}'"
        if clean_content != content:
            msg += "\n⚠️ PII was detected and removed before saving."
        return msg

    except Exception as e:
        return f"❌ Error: {str(e)}"


def extract_session_memories() -> str:
    """Extract memories from current session."""
    if not _session_messages:
        return "No conversation yet. Chat first!"

    try:
        async def _run():
            from src.memory.memory_agent import extract_and_save_memories
            conversation = "\n".join(_session_messages)
            return await extract_and_save_memories(conversation)

        saved = run_async(_run())
        return f"✅ Extracted and saved {saved} memories from this session!"

    except Exception as e:
        return f"❌ Error: {str(e)}"


# ── TAB 4: Documents ───────────────────────────────────────────────────────────
def ingest_handler() -> str:
    """Reload documents into the knowledge base."""
    try:
        from src.rag.document_loader import load_all_documents
        from src.rag.vector_store import vector_store

        docs = load_all_documents()

        if not docs:
            return (
                "❌ No documents found!\n\n"
                "Add .md or .txt files to:\n"
                "- data/notes/\n"
                "- data/recipes/\n"
                "- data/transcriptions/"
            )

        added = vector_store.add_documents(docs)
        stats = vector_store.get_stats()

        return (
            f"✅ Ingestion complete!\n\n"
            f"- Chunks processed: {len(docs)}\n"
            f"- Newly added: {added}\n"
            f"- Total in knowledge base: {stats['total_chunks']}\n"
            f"- Embedding model: {stats['embedding_model']}"
        )

    except Exception as e:
        return f"❌ Ingestion error: {str(e)}"


# ── TAB 5: Stats & Eval ────────────────────────────────────────────────────────
def get_stats() -> str:
    """Get system statistics."""
    try:
        from src.memory.memory_store import memory_store
        from src.rag.vector_store import vector_store
        from src.observability.metrics import agent_metrics
        from src.guardrails.guardrail import pii_guardrail
        from src.agents.orchestrator_agent import orchestrator

        kb = vector_store.get_stats()
        mem = memory_store.get_stats()
        ag = agent_metrics.summary()
        guard = pii_guardrail.get_stats()
        orch = orchestrator.get_stats()

        output = "## 📊 System Statistics\n\n"

        output += "### 📚 Knowledge Base\n"
        output += f"- Total chunks: `{kb['total_chunks']}`\n"
        output += f"- Collection: `{kb['collection_name']}`\n"
        output += f"- Embedding model: `{kb['embedding_model']}`\n\n"

        output += "### 💾 Memory Store\n"
        output += f"- Total memories: `{mem['total_memories']}`\n"
        output += f"- Conversations: `{mem['total_conversations']}`\n"
        output += f"- Has profile: `{mem['has_profile']}`\n"
        output += f"- By type: `{mem['memory_types']}`\n\n"

        output += "### 🤖 Agent Metrics\n"
        output += f"- Total calls: `{ag['total_calls']}`\n"
        output += f"- Avg response time: `{ag['avg_response_time_seconds']}s`\n"
        output += f"- Fastest: `{ag['fastest_seconds']}s`\n"
        output += f"- Slowest: `{ag['slowest_seconds']}s`\n"
        output += f"- Confidence: `{ag['confidence_distribution']}`\n\n"

        output += "### 🔒 PII Guardrail\n"
        output += f"- Messages checked: `{guard['total_checked']}`\n"
        output += f"- PII items redacted: `{guard['total_pii_items_redacted']}`\n"
        output += f"- Strict mode: `{guard['strict_mode']}`\n\n"

        output += "### 🎯 Orchestrator\n"
        output += f"- Total queries: `{orch['total_queries']}`\n"
        output += f"- Total time: `{orch['total_time_seconds']}s`\n"
        output += f"- Avg per query: `{orch['avg_time_seconds']}s`\n"

        return output

    except Exception as e:
        return f"❌ Stats error: {str(e)}"


def run_quick_eval() -> str:
    """Run a quick mini evaluation."""
    try:
        async def _run():
            from src.evaluation.evaluator import (
                evaluate_system, run_baseline, run_rag_system,
            )
            from src.evaluation.dataset import (
                BASELINE_EVAL_CASES, RAG_EVAL_CASES
            )
            base = await evaluate_system(
                "Baseline", BASELINE_EVAL_CASES[:2], run_baseline
            )
            rag = await evaluate_system(
                "RAG", RAG_EVAL_CASES[:2], run_rag_system
            )
            return base, rag

        base, rag = run_async(_run())

        output = "## 📊 Quick Evaluation Results\n\n"
        output += "| System | Score | Pass Rate | Latency |\n"
        output += "|--------|-------|-----------|--------|\n"
        output += (
            f"| Baseline | `{base.avg_score:.3f}` | "
            f"`{base.pass_rate:.0%}` | `{base.avg_latency:.1f}s` |\n"
        )
        output += (
            f"| RAG | `{rag.avg_score:.3f}` | "
            f"`{rag.pass_rate:.0%}` | `{rag.avg_latency:.1f}s` |\n\n"
        )

        improvement = rag.avg_score - base.avg_score
        if improvement > 0:
            pct = improvement / base.avg_score * 100
            output += (
                f"✅ **RAG improves score by "
                f"{improvement:.3f} ({pct:.1f}%)**\n\n"
            )
        else:
            output += "⚠️ Scores similar. Try adding more documents!\n\n"

        output += (
            "💡 Run `python run_evals.py` for the full evaluation suite."
        )
        return output

    except Exception as e:
        return f"❌ Eval error: {str(e)}"

# ── MCP Chat handler ───────────────────────────────────────────────────────────
def mcp_chat_handler(message: str, history: list) -> tuple:
    """Handle MCP agent chat."""
    if not message.strip():
        return "", history
    try:
        async def _run():
            from src.agents.mcp_agent import mcp_chat
            return await mcp_chat(message)

        response = run_async(_run())
        answer = response.answer

        # Show which tools were used
        if response.tools_used:
            answer += (
                f"\n\n---\n"
                f"🔌 **MCP Tools used:** "
                f"{', '.join(response.tools_used)}\n"
                f"🎯 **Confidence:** {response.confidence}"
            )

        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": answer})
        return "", history

    except Exception as e:
        history.append({"role": "user", "content": message})
        history.append(
            {"role": "assistant", "content": f"❌ MCP Error: {e}"}
        )
        return "", history


# ── Build UI ───────────────────────────────────────────────────────────────────
def build_ui():
    """Build the complete Gradio UI - Gradio 6.0 compatible."""

    # In Gradio 6.0 - NO theme or css in gr.Blocks()
    with gr.Blocks(title="🧠 Second Brain") as app:

        gr.Markdown("""
        # 🧠 Second Brain
        ### Your Personal AI-Powered Knowledge Assistant
        *Powered by Claude + RAG + Multi-Agent + Memory*
        ---
        """)

        with gr.Tabs():

            # ── Tab 1: Chat ────────────────────────────────────────
            with gr.Tab("💬 Chat"):
                gr.Markdown("""
                Chat using the full **multi-agent system**.
                Searches your knowledge base and uses your memories.
                """)

                # Gradio 6.0 - no 'type' argument needed
                chatbot = gr.Chatbot(
                    label="Second Brain Chat",
                    height=500,
                    show_label=True,
                )

                with gr.Row():
                    chat_input = gr.Textbox(
                        placeholder="Ask anything... e.g. 'What pasta recipes do I have?'",
                        label="Your message",
                        scale=4,
                        lines=2,
                    )
                    send_btn = gr.Button(
                        "Send 🚀",
                        variant="primary",
                        scale=1,
                    )

                with gr.Row():
                    clear_btn = gr.Button("🗑️ Clear Chat", scale=1)
                    save_mem_btn = gr.Button(
                        "💾 Save Session Memories",
                        scale=1,
                        variant="secondary",
                    )

                memory_status = gr.Textbox(
                    label="Memory Status",
                    interactive=False,
                    lines=2,
                )

                gr.Examples(
                    examples=[
                        "What pasta recipes do I have?",
                        "What Python tips do I have in my notes?",
                        "Summarize my AI concepts notes",
                        "What do you know about me?",
                        "What productivity tips do I have?",
                        "Tell me about the walrus operator in Python",
                    ],
                    inputs=chat_input,
                    label="💡 Try these questions",
                )

                send_btn.click(
                    fn=chat_handler,
                    inputs=[chat_input, chatbot],
                    outputs=[chat_input, chatbot],
                )
                chat_input.submit(
                    fn=chat_handler,
                    inputs=[chat_input, chatbot],
                    outputs=[chat_input, chatbot],
                )
                clear_btn.click(
                    fn=lambda: ([], ""),
                    outputs=[chatbot, memory_status],
                )
                save_mem_btn.click(
                    fn=extract_session_memories,
                    outputs=memory_status,
                )

            # ── Tab 2: Search ──────────────────────────────────────
            with gr.Tab("🔍 Search"):
                gr.Markdown("""
                **Direct vector search** of your knowledge base.
                Pure semantic similarity — no LLM involved.
                """)

                with gr.Row():
                    search_input = gr.Textbox(
                        placeholder="Search your knowledge base...",
                        label="Search query",
                        scale=4,
                    )
                    search_btn = gr.Button(
                        "Search 🔍",
                        variant="primary",
                        scale=1,
                    )

                search_output = gr.Markdown()

                gr.Examples(
                    examples=[
                        "carbonara ingredients",
                        "python list comprehension",
                        "virtual environment",
                        "second brain productivity",
                        "AI agents",
                        "meeting action items",
                    ],
                    inputs=search_input,
                    label="💡 Try these searches",
                )

                search_btn.click(
                    fn=search_handler,
                    inputs=search_input,
                    outputs=search_output,
                )
                search_input.submit(
                    fn=search_handler,
                    inputs=search_input,
                    outputs=search_output,
                )

            # ── Tab 3: Memory ──────────────────────────────────────
            with gr.Tab("💾 Memory"):
                gr.Markdown("""
                View and manage your **persistent memories**.
                Facts the system learned about you across all sessions.
                """)

                with gr.Row():
                    memory_filter = gr.Textbox(
                        placeholder="Filter by keyword (blank = show all)...",
                        label="Filter",
                        scale=4,
                    )
                    view_mem_btn = gr.Button(
                        "View 👁️",
                        variant="primary",
                        scale=1,
                    )

                memories_output = gr.Markdown()

                gr.Markdown("### ➕ Add Memory Manually")
                with gr.Row():
                    new_memory_input = gr.Textbox(
                        placeholder="e.g. I prefer concise answers with bullet points",
                        label="New memory",
                        scale=4,
                    )
                    add_mem_btn = gr.Button(
                        "Remember ✅",
                        variant="secondary",
                        scale=1,
                    )

                add_memory_status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=2,
                )

                view_mem_btn.click(
                    fn=get_memories,
                    inputs=memory_filter,
                    outputs=memories_output,
                )
                memory_filter.submit(
                    fn=get_memories,
                    inputs=memory_filter,
                    outputs=memories_output,
                )
                add_mem_btn.click(
                    fn=save_memory_handler,
                    inputs=new_memory_input,
                    outputs=add_memory_status,
                )
                app.load(
                    fn=lambda: get_memories(""),
                    outputs=memories_output,
                )

            # ── Tab 4: Documents ───────────────────────────────────
            with gr.Tab("📄 Documents"):
                gr.Markdown("""
                **Manage your knowledge base.**

                Add `.md` or `.txt` files to:
                - `data/notes/` — general notes
                - `data/recipes/` — cooking recipes
                - `data/transcriptions/` — meeting notes

                Then click **Ingest Documents**.
                """)

                ingest_btn = gr.Button(
                    "📚 Ingest Documents",
                    variant="primary",
                    size="lg",
                )
                ingest_output = gr.Markdown()

                ingest_btn.click(
                    fn=ingest_handler,
                    outputs=ingest_output,
                )

            # ── Tab 5: Stats & Eval ────────────────────────────────
            with gr.Tab("📊 Stats & Eval"):
                gr.Markdown("""
                **System statistics and evaluation.**
                """)

                with gr.Row():
                    stats_btn = gr.Button(
                        "📊 Refresh Stats",
                        variant="primary",
                    )
                    eval_btn = gr.Button(
                        "🧪 Run Quick Eval",
                        variant="secondary",
                    )

                stats_output = gr.Markdown()
                eval_output = gr.Markdown()

                gr.Markdown("""
                ---
                💡 Full eval: `python run_evals.py`
                💡 Evidence: `python generate_evidence.py`
                """)

                stats_btn.click(fn=get_stats, outputs=stats_output)
                eval_btn.click(fn=run_quick_eval, outputs=eval_output)
                app.load(fn=get_stats, outputs=stats_output)

            # ── Tab 6: MCP Agent ───────────────────────────────────
            # ── Tab 6: MCP Agent ───────────────────────────────────
            with gr.Tab("🔌 MCP Agent"):
                gr.Markdown("""
                ## 🔌 MCP-Powered Agent

                This agent connects to your Second Brain via
                **Model Context Protocol (MCP)**.

                Unlike the Chat tab where the orchestrator
                explicitly directs agents, here the agent
                **autonomously decides** which tools to call.

                ### Available MCP Tools
                | Tool | Purpose |
                |------|---------|
                | `search_knowledge_base` | Semantic search notes |
                | `get_all_sources` | List all documents |
                | `get_memory_context` | Load your preferences |
                | `save_memory` | Persist important facts |
                | `check_pii` | Detect sensitive info |
                """)

                mcp_chatbot = gr.Chatbot(
                    label="MCP Agent Chat",
                    height=450,
                )

                with gr.Row():
                    mcp_input = gr.Textbox(
                        placeholder=(
                            "Ask the MCP agent... "
                            "e.g. 'What documents do you have?'"
                        ),
                        label="Your message",
                        scale=4,
                        lines=2,
                    )
                    mcp_send = gr.Button(
                        "Send 🔌",
                        variant="primary",
                        scale=1,
                    )

                mcp_clear = gr.Button("🗑️ Clear")

                gr.Examples(
                    examples=[
                        "What documents do you have access to?",
                        "Search my notes for carbonara recipe",
                        "What do you remember about me?",
                        "Remember this: I prefer dark mode",
                        "Check this for PII: my email is test@test.com",
                    ],
                    inputs=mcp_input,
                    label="💡 Try these",
                )

                gr.Markdown("""
                ---
                💡 **MCP vs Multi-Agent:**
                - **Multi-Agent** (Chat tab): Orchestrator explicitly 
                  directs Research → Synthesis → Memory agents
                - **MCP Agent** (this tab): One agent autonomously 
                  picks and calls tools as needed
                """)

                mcp_send.click(
                    fn=mcp_chat_handler,
                    inputs=[mcp_input, mcp_chatbot],
                    outputs=[mcp_input, mcp_chatbot],
                )
                mcp_input.submit(
                    fn=mcp_chat_handler,
                    inputs=[mcp_input, mcp_chatbot],
                    outputs=[mcp_input, mcp_chatbot],
                )
                mcp_clear.click(
                    fn=lambda: ([], ""),
                    outputs=[mcp_chatbot, mcp_input],
                )

    return app


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧠 Starting Second Brain Gradio UI...")
    print("Loading documents...")
    startup()

    app = build_ui()

    print("\n✅ Starting server...")
    print("📌 Open in browser: http://localhost:7860\n")

    # In Gradio 6.0 - theme and css go in launch()
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
    )