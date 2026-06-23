"""Text-to-SQL library manager.

Replaces the former ChromaDB vector-RAG pipeline. The user's personal library
lives in a structured spreadsheet (`data/Books.xlsx`); we load it into a tiny
SQLite table on every run and let the LLM translate natural-language questions
into SQL via LlamaIndex's NLSQLTableQueryEngine. For tabular questions
(counts, filters, aggregates) this is exact, where cosine-similarity retrieval
could only ever be approximate.
"""

import logging
import os

import pandas as pd
from sqlalchemy import create_engine

from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.openai import OpenAI

logger = logging.getLogger(__name__)

EXCEL_PATH = "data/Books.xlsx"
DB_PATH = "data/library.db"
TABLE_NAME = "library"

# Canonical Status values, surfaced to the LLM so it filters on the exact
# spelling rather than guessing (e.g. "to buy" -> "Yet to Buy").
STATUS_VALUES = ["Yet to Buy", "Finished", "Reading", "Ready to Start"]

# Schema context handed to the text-to-SQL prompt. This is load-bearing: it
# teaches the model what each column means and how "books read in <year>" maps
# onto the data (Year is only populated for Finished books).
TABLE_CONTEXT = (
    "This table lists the user's personal book collection and reading history. "
    "Columns: "
    "Book (the book title); "
    "Author (the author's name, may be NULL); "
    f"Status (the reading state, exactly one of: {', '.join(repr(s) for s in STATUS_VALUES)}); "
    "Year (the integer year the user FINISHED the book; NULL unless Status is 'Finished'). "
    "To count books the user read or finished in a given year, filter "
    "Status = 'Finished' AND Year = <year>. "
    "To count books in a category such as 'yet to buy', filter on the exact Status value."
)


def _api_key_from_headers(headers):
    """Extract the OpenAI key from the project's Bearer-token headers dict."""
    auth_header = headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return auth_header  # fallback if not in Bearer format


def _build_engine():
    """Read the Excel sheet into a fresh SQLite table and return a SQLAlchemy engine.

    Rebuilt on every call so the answers always reflect the current spreadsheet.
    The sheet has a junk title row above the real header, so the header is on
    the second row (header=1).
    """
    df = pd.read_excel(EXCEL_PATH, header=1)
    # The real sheet has exactly these four columns, in order.
    df = df.iloc[:, :4]
    df.columns = ["Book", "Author", "Status", "Year"]

    # Tidy up: drop rows with no title, trim whitespace, coerce Year to a
    # nullable integer (it arrives as floats like 2025.0 because of the NULLs).
    df = df.dropna(subset=["Book"]).copy()
    for col in ["Book", "Author", "Status"]:
        df[col] = df[col].astype("string").str.strip()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")

    engine = create_engine(f"sqlite:///{DB_PATH}")
    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
    return engine


def library_management_system(user_query, headers):
    """Answer a natural-language question about the user's library via text-to-SQL.

    Keeps the original (user_query, headers) signature so the agent tool and the
    rest of the app are unchanged.
    """
    os.environ["OPENAI_API_KEY"] = _api_key_from_headers(headers)

    engine = _build_engine()
    sql_database = SQLDatabase(engine, include_tables=[TABLE_NAME])

    llm = OpenAI(model="gpt-4o-mini", temperature=0)
    query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database,
        tables=[TABLE_NAME],
        llm=llm,
        context_query_kwargs={TABLE_NAME: TABLE_CONTEXT},
    )

    response = query_engine.query(user_query)

    # Log the generated SQL so every answer is inspectable / debuggable.
    sql = response.metadata.get("sql_query") if response.metadata else None
    if sql:
        logger.info("Generated SQL: %s", sql)

    return str(response)
