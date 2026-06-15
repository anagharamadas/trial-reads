# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

TrialReads is a Streamlit app that uses LangChain/LangGraph, LlamaIndex, and OpenAI to (1) summarize the first three chapters of a book, (2) recommend similar books with Amazon purchase links, and (3) answer natural-language questions over a personal reading-history PDF via RAG.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app (serves on http://localhost:8501)
streamlit run app.py
```

There is no test suite, linter, or build step. The OpenAI API key is read from the environment — `app.py` calls `load_dotenv()`, so a `.env` file in the project root with `OPENAI_API_KEY=...` is required (copy `.env.example` to `.env` and fill it in). `.env` is gitignored and must never be committed; there is no UI field for the key.

## Architecture

`app.py` is the single entry point and orchestrator. It renders a **single chat UI** (`st.chat_input` + a message transcript in `st.session_state.messages`) and delegates every user turn to a **LangGraph ReAct agent** built in `book_agent.py`. There is no radio button and no manual feature routing — the agent's LLM decides, per message, which (if any) tool to call.

The OpenAI key is read once from the environment in `app.py` (`os.environ["OPENAI_API_KEY"]`, loaded from `.env` via `load_dotenv()`); if it is missing the app shows an error and `st.stop()`s. A `headers` dict (`{"authorization": "Bearer <key>"}`) is still constructed because the feature modules expect it (see the key-threading convention below), but there is no UI field for the key.

**The agent (`book_agent.py`).** `build_agent(api_key)` returns a `langgraph.prebuilt.create_react_agent` over `ChatOpenAI` (`gpt-4o-mini`, temp 0) with two `@tool`s and a `SYSTEM_PROMPT` instructing it to pick exactly one tool, or answer directly if neither fits. The agent is built **once per session** and cached in `st.session_state.agent`. The model chooses a tool primarily from each tool's **docstring**, so the docstrings are load-bearing — edit them deliberately.

- `book_summary_tool(book_name, author_name="")` → calls `get_summary(...)`. The docstring tells the model to supply the author from its own knowledge if the user omits it.
- `library_query_tool(query)` → calls `library_management_system(...)` (RAG over the user's personal library).

Both tools rebuild the `headers` dict internally via `_headers()` (from `os.environ["OPENAI_API_KEY"]`), preserving the legacy extraction convention so the feature functions stay untouched.

**`run_agent(agent, user_text)`** invokes the agent for one turn and returns `(reply_text, summary_args)`. It walks every message in the result looking for a `book_summary_tool` tool call; if found, `summary_args` is that call's `{"book_name", "author_name"}`, otherwise `None`. `app.py` uses this to tag the assistant message `kind="summary"` (vs `kind="text"`) and to remember which book/author to recommend against.

**Recommendations are not a tool.** `recommendation_system` is invoked directly from a Streamlit **button** rendered under the most recent summary message (gated on the message having `kind="summary"` and not yet `recommended`). It reads the book/author captured in `summary_args` and appends a `kind="recommendations"` message. It never goes through the agent.

Key threading convention: every feature module receives `headers` and re-extracts the API key by stripping the `Bearer ` prefix (see the identical block at the top of `book_summariser.py`, `recommendation_system.py`, `library_manager.py`). When adding a module, follow this same extraction pattern rather than passing the raw key; the agent's `_headers()` helper exists to keep feeding these functions the dict they expect.

The three feature modules:

- **`book_summariser.py`** — `get_summary(book_name, author_name, headers)`. Builds two `ChatPromptTemplate | ChatOpenAI` chains (`gpt-4o-mini`, temp 0): an "internal reasoning" chain and a final chapter-by-chapter summary chain. **Caveat:** the two are *not* actually chained — `internal_response` is computed and then discarded; only the final chain's output (which receives just `book_name`, so `author_name` never influences the result) is returned. The final prompt also has typos (`chaptersin`, no space before `250`). Strips any `<think>...</think>` blocks from output via regex (the `gpt-4o-mini` model never emits these, so it's currently a no-op).
- **`recommendation_system.py`** — `recommendation_system(...)` wraps a single-node LangGraph that asks the LLM for exactly 5 recommendations in a fixed `"N. [Title] by [Author]\n   Reason: ..."` format. `parse_recommendations()` relies on that exact format to extract title/author/reason; `generate_amazon_link()` builds an Amazon search URL. Returns `{"original_response", "recommendations"}`. **Changing the prompt format will break the parser**, and vice versa — keep them in sync.
- **`library_manager.py`** — `library_management_system(user_query, headers)`. A LlamaIndex RAG pipeline over a persistent **ChromaDB** at `./chroma_db` (collection `library_manager`). On first run (empty collection) it ingests every file in `data/` (currently `data/Books.pdf`) with `SentenceSplitter` + `OpenAIEmbedding` (`text-embedding-3-small`); subsequent runs reuse the persisted vectors. Queries use `tree_summarize`. The README describes this as a CSV-based reading-history chatbot, but the actual ingest source is the PDF(s) under `data/`.

### Dependency pinning caveat

`requirements.txt` pins `chromadb==0.4.15` and `protobuf==3.20.3` for compatibility; `library_manager.py` also sets `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` at runtime to avoid a protobuf incompatibility. Be cautious upgrading these.

### Persisted artifacts

`chroma_db/` (the vector store) and `data/Books.pdf` are committed to the repo. Deleting `chroma_db/` forces a full re-embed (and OpenAI cost) on the next Library Manager query.