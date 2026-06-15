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

`app.py` is the single entry point and orchestrator. It renders the UI, builds a **LangGraph `StateGraph`** keyed on `AgentState`, and routes via `route_agent` to one of **two** graph-routed feature modules (`book_summariser`, `library_manager`) based on the radio-button `agent_choice`. The API key is captured from a password text input, wrapped into a `headers` dict (`{"accept", "content-type", "authorization": "Bearer <key>"}` — only the `authorization` token is ever consumed downstream), and threaded through the graph state into each module.

**Recommendations bypass the graph.** `recommendation_system` is the third feature but is *not* routed through the `StateGraph`. It is invoked directly from a Streamlit button inside the Book Summarizer flow, gated by `st.session_state.summary_generated` (only shown after a summary succeeds). It reads book/author/headers back out of `st.session_state`.

Key threading convention: every feature module receives `headers` and re-extracts the API key by stripping the `Bearer ` prefix (see the identical block at the top of `book_summariser.py`, `recommendation_system.py`, `library_manager.py`). When adding a module, follow this same extraction pattern rather than passing the raw key.

The three feature modules:

- **`book_summariser.py`** — `get_summary(book_name, author_name, headers)`. Builds two `ChatPromptTemplate | ChatOpenAI` chains (`gpt-4o-mini`, temp 0): an "internal reasoning" chain and a final chapter-by-chapter summary chain. **Caveat:** the two are *not* actually chained — `internal_response` is computed and then discarded; only the final chain's output (which receives just `book_name`) is returned. The final prompt also has typos (`chaptersin`, no space before `250`). Strips any `<think>...</think>` blocks from output via regex (the `gpt-4o-mini` model never emits these, so it's currently a no-op).
- **`recommendation_system.py`** — `recommendation_system(...)` wraps a single-node LangGraph that asks the LLM for exactly 5 recommendations in a fixed `"N. [Title] by [Author]\n   Reason: ..."` format. `parse_recommendations()` relies on that exact format to extract title/author/reason; `generate_amazon_link()` builds an Amazon search URL. Returns `{"original_response", "recommendations"}`. **Changing the prompt format will break the parser**, and vice versa — keep them in sync.
- **`library_manager.py`** — `library_management_system(user_query, headers)`. A LlamaIndex RAG pipeline over a persistent **ChromaDB** at `./chroma_db` (collection `library_manager`). On first run (empty collection) it ingests every file in `data/` (currently `data/Books.pdf`) with `SentenceSplitter` + `OpenAIEmbedding` (`text-embedding-3-small`); subsequent runs reuse the persisted vectors. Queries use `tree_summarize`. The README describes this as a CSV-based reading-history chatbot, but the actual ingest source is the PDF(s) under `data/`.

### Dependency pinning caveat

`requirements.txt` pins `chromadb==0.4.15` and `protobuf==3.20.3` for compatibility; `library_manager.py` also sets `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` at runtime to avoid a protobuf incompatibility. Be cautious upgrading these.

### Persisted artifacts

`chroma_db/` (the vector store) and `data/Books.pdf` are committed to the repo. Deleting `chroma_db/` forces a full re-embed (and OpenAI cost) on the next Library Manager query.