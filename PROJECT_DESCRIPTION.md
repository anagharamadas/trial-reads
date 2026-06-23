# TrialReads — Application Description

> **Purpose of this document.** A complete, self-contained description of the TrialReads
> application (also called *BookSummaryGenerator*) — what it is, who it's for, what it does,
> how it works, and the technology it's built on. It is written to be loaded as **context for a
> Claude Project** so the assistant can answer questions about this application accurately. It is
> grounded in the actual source code; where a behavior is a runtime/LLM decision rather than a
> hard-coded fact, that is called out explicitly.

---

## 1. What TrialReads is

TrialReads is a **single-page conversational web app** that acts as a personal reading
assistant. The user types in **one chat box**, and the app figures out — per message — what the
user wants and responds. It does three things:

1. **Summarizes a book** the user names, chapter by chapter (first three chapters).
2. **Answers questions about the user's own library and reading history** (e.g. "how many books
   have I finished?", "what am I reading right now?", "how many did I finish in 2024?"), reading
   from the user's personal spreadsheet.
3. **Recommends similar books to buy**, with one-click Amazon search links, offered after a
   summary.

It is a **local Streamlit application** (runs on the user's machine at `http://localhost:8501`),
backed by **OpenAI's `gpt-4o-mini`** model for all language understanding and generation. There
is no separate backend server, no hosted database, no user accounts, and no message queue — it
is one Python process plus two data files on disk.

**Name note:** the repository/folder is `BookSummaryGenerator`; the product/UI name is
**TrialReads** ("Trial Reads: Book Summarizer & Library Manager"). They refer to the same app.

---

## 2. Who it's for & primary uses

- **An individual reader** who keeps a personal book list (a spreadsheet of books they own, are
  reading, have finished, or want to buy) and wants a fast, natural-language way to (a) preview a
  book before reading/buying it, (b) ask questions about their own reading history without
  writing formulas or filters, and (c) discover similar titles to purchase.

Typical uses:
- *"Summarize the first three chapters of Atomic Habits."* → a chapter-by-chapter preview.
- *"How many books have I finished?"* / *"Which books am I currently reading?"* / *"How many did
  I finish in 2024?"* → exact answers computed from the user's spreadsheet.
- After a summary, click **"Get Book Recommendations"** → 5 similar titles, each with a *Buy on
  Amazon* link.

---

## 3. Features & functionality (in detail)

### 3.1 Unified chat with automatic routing (no mode switches)
There is **one chat input and one transcript**. The user never picks a "mode." Behind the scenes
a **ReAct agent** (an LLM that can call tools) reads each message and decides, on its own,
whether to (a) summarize a book, (b) query the personal library, or (c) just answer directly in
conversation. This decision is made by the model at runtime based on the wording of the request.

### 3.2 Book summarization
- The user names a book (author optional). If the author is omitted, the agent supplies it from
  the model's own knowledge.
- The app returns a **concise, chapter-by-chapter summary of the first three chapters** (~250
  words per chapter), so the user can preview a book before committing to it or buying it.
- After a summary appears, a **"Get Book Recommendations"** button is shown under it.

### 3.3 Personal-library Q&A via **text-to-SQL** (the "Library Manager")
This is the most technically distinctive feature.

- The user's library lives in an **Excel spreadsheet** (`data/Books.xlsx`) with four columns:
  - **Book** — the title.
  - **Author** — the author (may be blank).
  - **Status** — exactly one of: **`Yet to Buy`**, **`Finished`**, **`Reading`**,
    **`Ready to Start`**.
  - **Year** — the year the book was *finished* (only filled in for `Finished` books; otherwise
    blank).
- When the user asks a question, the app **loads the spreadsheet into a small SQLite database**,
  then uses an LLM to **translate the natural-language question into a real SQL query**, runs
  that SQL, and phrases the result back in plain English.
- Because the answer is computed by **actual SQL** (counts, filters, aggregates), it is **exact**
  — e.g. "how many books did I finish in 2024?" becomes
  `SELECT COUNT(*) FROM library WHERE Status='Finished' AND Year=2024`. The previous version of
  this feature used vector similarity search (ChromaDB), which could only *approximate* such
  answers; it was replaced by this text-to-SQL approach precisely to make counts/filters exact.
- The database is **rebuilt from the spreadsheet on every question**, so answers always reflect
  the current contents of `Books.xlsx` — the user can edit the spreadsheet and immediately see
  updated answers. The generated SQL is logged so every answer is inspectable/debuggable.

### 3.4 Book recommendations with Amazon purchase links
- Triggered by the **button under the latest summary** (not by the chat/agent).
- Produces **exactly 5 recommendations** similar to the summarized book, each with a short reason.
- For each recommendation, the app generates an **Amazon search URL** (title + author,
  URL-encoded) and renders a **"Buy on Amazon"** link button. *No Amazon API is called* — these
  are plain search links the user can click.

### 3.5 Persistent conversation within a session
The chat transcript and the agent persist for the duration of a browser session (Streamlit
session state). Refreshing/restarting the app starts a fresh session.

---

## 4. Benefits

- **One natural-language interface for three jobs** — preview a book, interrogate your own
  reading history, and find similar books to buy, without switching tools or learning a query
  language.
- **Exact answers about your library** — because library questions compile to SQL, counts and
  filters are precise rather than fuzzy/approximate.
- **Always current** — the library database is regenerated from the spreadsheet on every query,
  so edits to the spreadsheet are reflected immediately; nothing to re-index.
- **Low operational footprint** — a single local process and two files; no server to run, no
  database to administer, no accounts. Easy to run on a laptop.
- **Transparent & debuggable** — the generated SQL is logged, so library answers can be verified.
- **Frictionless purchasing path** — recommendations come with ready-to-click Amazon search
  links.

---

## 5. How it works (architecture & request flow)

### 5.1 High-level shape
- **One Streamlit process** renders the UI and runs all logic in-process.
- **One external system:** the **OpenAI API** (`gpt-4o-mini`), used for summaries,
  recommendations, the agent's tool-selection reasoning, and natural-language→SQL translation.
- **"Amazon"** appears only as generated search-link URLs — there is no Amazon integration/API.
- **Two on-disk data files:** `data/Books.xlsx` (the source of truth for the library) and
  `data/library.db` (a throwaway SQLite database rebuilt from the spreadsheet on each library
  query).

### 5.2 The components (files)
- **`app.py`** — the single entry point. Renders the chat UI and history, reads the API key from
  the environment, builds the agent once per session, routes each user message to the agent, and
  renders the recommendation button + recommendation results.
- **`book_agent.py`** — builds a **LangGraph ReAct agent** over `gpt-4o-mini` with **two tools**
  (`book_summary_tool`, `library_query_tool`) and a system prompt telling it to pick exactly one
  tool per message, or to answer directly if neither applies. The model chooses a tool largely
  from each tool's description, so those descriptions are load-bearing.
- **`book_summariser.py`** — `get_summary(...)`: LangChain prompt→model chains that produce the
  chapter-by-chapter summary.
- **`library_manager.py`** — `library_management_system(...)`: the **LlamaIndex text-to-SQL**
  pipeline (read Excel → load into SQLite → `NLSQLTableQueryEngine` translates the question to
  SQL → run → answer). A "table context" string tells the model the exact `Status` values and
  the meaning of `Year`, which is what makes the generated SQL correct.
- **`recommendation_system.py`** — `recommendation_system(...)`: a **single-node LangGraph** that
  asks the model for 5 similarly-themed books in a fixed format, plus `parse_recommendations()`
  (which depends on that exact format) and `generate_amazon_link()` (builds the Amazon search
  URL). Invoked directly by the button, **not** through the agent.

### 5.3 What happens on a chat message (e.g. a library question)
1. The user types in the chat box; `app.py` hands the message to the agent.
2. The **agent asks the model which tool to use** (this is the runtime routing decision) and
   calls, say, the **library tool**.
3. The library tool **reads `Books.xlsx`, (re)builds the `library` table in SQLite**, and asks
   the model to **translate the question into SQL** using the table-context hints.
4. The generated SQL **runs against SQLite**; the row result is **phrased back into a sentence**
   by the model.
5. The agent produces the final reply; `app.py` renders it. If the message was a *book summary*,
   the reply is tagged so the recommendation button appears beneath it.

A single library question therefore involves a few OpenAI round-trips (tool selection →
NL-to-SQL → answer phrasing → the agent's final turn), which is the main source of latency/cost.

### 5.4 What happens on "Get Book Recommendations"
The button calls the recommendation module **directly** (bypassing the agent): the single-node
graph asks the model for 5 recommendations in the fixed format, the response is parsed into
title/author/reason, and each item is rendered with an Amazon search link.

---

## 6. Data model

`data/Books.xlsx` is the **source of truth** for the library. Practical notes:
- The sheet has a **junk title row above the real header**, so the real column header is on the
  **second row**. The first four columns are read as `Book, Author, Status, Year` (in that
  order).
- **Status** is constrained to four exact values: `Yet to Buy`, `Finished`, `Reading`,
  `Ready to Start`.
- **Year** holds the *finished* year and is only present for `Finished` books (blank otherwise);
  it is coerced to a nullable integer.
- On each library query this is loaded into a SQLite table named **`library`** (replacing any
  previous contents) at `data/library.db`. That `.db` file is a regenerated artifact — it is not
  source-controlled and can be deleted at any time; it will be rebuilt on the next query.

---

## 7. Technology stack

**Language & runtime**
- **Python** (developed/run in a conda environment named `langchain_env`, Python 3.12).

**UI / app framework**
- **Streamlit** — the web UI: chat input, message transcript, buttons, link buttons. Also
  provides per-session state (the agent and chat history).

**LLM & AI orchestration**
- **OpenAI `gpt-4o-mini`** — the single model used for everything (summaries, recommendations,
  agent reasoning/tool selection, and NL→SQL). Temperature 0 for deterministic tasks; ~0.1 for
  recommendations.
- **LangChain** (`langchain-openai`, `langchain-core`) — `ChatOpenAI` chat model wrapper and
  prompt templating (used by the summarizer and recommender).
- **LangGraph** — two distinct uses:
  - `create_react_agent` — the **ReAct agent** that routes each message to a tool
    (`book_agent.py`).
  - `StateGraph` — the **single-node graph** that generates recommendations
    (`recommendation_system.py`).
- **LlamaIndex** (`llama-index-core`, `llama-index-llms-openai`) — the **text-to-SQL** engine
  (`SQLDatabase` + `NLSQLTableQueryEngine`) that turns library questions into SQL.

**Data & storage**
- **pandas** + **openpyxl** — read the Excel spreadsheet (`data/Books.xlsx`).
- **SQLAlchemy** + **SQLite** — build and query the throwaway `library` table
  (`data/library.db`); SQLite is file-based and in-process (no DB server).

**Utilities**
- **python-dotenv** — loads `OPENAI_API_KEY` from a `.env` file.
- **urllib** (standard library) — builds the Amazon search URLs (no Amazon API/SDK).
- **ipykernel**, **requests** — present in the dependency list (dev/transitive); not central to
  the app's behavior.

**External systems**
- **OpenAI API** — the only external service the app calls.
- **Amazon** — link target only (generated search URLs); not integrated.

---

## 8. Configuration & how to run

- **Dependencies:** `pip install -r requirements.txt`.
- **API key:** the **OpenAI API key is read from the environment**, loaded from a `.env` file in
  the project root (`OPENAI_API_KEY=...`). There is **no UI field** for the key. If the key is
  missing, the app shows an error and stops. `.env` is gitignored and must never be committed.
- **Run:** `streamlit run app.py` → serves on `http://localhost:8501`.
- **No test suite, linter, or build step** exists in the repository.
- **Internal key convention:** every feature function receives a `headers` dict of the form
  `{"authorization": "Bearer <key>"}` and re-extracts the key by stripping the `Bearer ` prefix.
  This is a historical convention kept so the feature modules stay unchanged; functionally it is
  just the OpenAI key being threaded through.

---

## 9. Important behaviors, constraints & known quirks

These are accurate, code-grounded notes that help answer "why did it do X?" questions:

- **Routing is an LLM decision.** Which tool runs for a given message is decided by the model at
  runtime from the tool descriptions and system prompt — it is not hard-coded keyword routing.
  Ambiguous phrasing can therefore occasionally route to an unexpected tool.
- **Library answers are only as good as the spreadsheet.** They are computed by SQL over
  `Books.xlsx`. Correct, consistent `Status` spelling and `Year` values are what make answers
  exact. The four canonical `Status` values are explicitly given to the model.
- **The library DB is disposable and always rebuilt.** Edits to `Books.xlsx` are reflected on the
  next query; `data/library.db` is never the source of truth.
- **Recommendations are not part of the chat agent.** They come from a button and a separate
  single-node graph. The recommendation **output format is fixed**, and the parser depends on
  that exact `"N. Title by Author / Reason: ..."` format — changing the prompt format would break
  parsing, and vice versa.
- **Amazon links are search URLs only.** They open an Amazon search for "title author"; there is
  no price, availability, or purchase integration.
- **Summarizer quirks (as currently written).** The summarizer builds two prompt chains but only
  the final chapter-by-chapter chain's output is returned; an "internal reasoning" chain is
  computed and then discarded. The final summary prompt receives only the **book name** (so the
  author the user/agent provides does not actually influence the summary text), and that prompt
  contains minor typos (`chaptersin`, a missing space before `250`). Output is run through a
  regex that strips `<think>...</think>` blocks, which `gpt-4o-mini` never emits, so it's
  effectively a no-op. These do not crash the app but are worth knowing when explaining summary
  behavior.
- **No persistence beyond the session.** No accounts, no saved history across restarts; state
  lives in the Streamlit session.
- **Single user / local.** It is designed to run locally for one user; there is no
  multi-tenancy, auth, rate-limiting, or scaling layer.

---

## 10. One-line summary

**TrialReads is a local Streamlit chat assistant that, using OpenAI `gpt-4o-mini` orchestrated by
LangGraph/LangChain/LlamaIndex, summarizes books chapter-by-chapter, answers exact questions
about a user's personal reading spreadsheet via natural-language-to-SQL, and recommends similar
books with Amazon purchase links.**
