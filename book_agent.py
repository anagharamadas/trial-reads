import os
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from book_summariser import get_summary
from library_manager import library_management_system


def _headers():
    """Rebuild the project's Bearer-token headers dict from the env API key.

    The feature modules expect a `headers` dict and re-extract the key by
    stripping the `Bearer ` prefix; we keep that convention here so the
    existing functions stay untouched.
    """
    return {"authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', '')}"}


@tool
def book_summary_tool(book_name: str, author_name: str = "") -> str:
    """Summarize the first three chapters of a specific published book, chapter by chapter.

    Use this when the user wants a summary or preview of a book they name. If the user does
    not give the author, supply it from your own knowledge of the book.
    """
    return get_summary(book_name, author_name, _headers())


@tool
def library_query_tool(query: str) -> str:
    """Answer questions about the USER'S OWN personal book collection and reading history.

    Use this for anything about what the user has read, is currently reading, wants to buy,
    or finished and when (e.g. "how many books have I completed", "which books am I reading",
    "what's in my collection"). This answers from the user's private library spreadsheet via text-to-SQL.
    """
    return library_management_system(query, _headers())


SYSTEM_PROMPT = (
    "You are TrialReads, a reading assistant with two tools. Use book_summary_tool to summarize "
    "a specific published book the user names. Use library_query_tool for any question about the "
    "user's OWN collection or reading history. Pick exactly one tool based on the query; if the "
    "request is neither, answer directly."
)


def build_agent(api_key: str):
    """Build a ReAct agent that decides which tool to call from a free-text query."""
    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini", openai_api_key=api_key)
    return create_react_agent(
        model=llm,
        tools=[book_summary_tool, library_query_tool],
        prompt=SYSTEM_PROMPT,
    )


def run_agent(agent, user_text: str):
    """Run one turn through the agent.

    Returns (reply_text, summary_args) where summary_args is
    {"book_name": ..., "author_name": ...} if book_summary_tool was invoked this turn
    (used to enable the post-summary recommendation button), otherwise None.
    """
    result = agent.invoke({"messages": [{"role": "user", "content": user_text}]})
    msgs = result["messages"]

    summary_args = None
    for m in msgs:
        for tc in getattr(m, "tool_calls", []) or []:
            if tc.get("name") == "book_summary_tool":
                summary_args = tc.get("args")

    reply = msgs[-1].content
    return reply, summary_args
