import os
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

from book_agent import build_agent, run_agent
from recommendation_system import recommendation_system, generate_amazon_link

load_dotenv()

st.title("Trial Reads: Book Summarizer & Library Manager")
st.caption(
    "Ask anything in one place — the assistant figures out whether to summarize a book "
    "or answer questions about your personal library."
)

# The OpenAI API key is read from the environment (loaded from .env by load_dotenv above),
# never from the UI. The recommendation system expects the Bearer-token headers dict, and the
# book_agent tools / library_manager read os.environ["OPENAI_API_KEY"] directly.
openai_api_key = os.environ.get("OPENAI_API_KEY")

if not openai_api_key:
    st.error("OPENAI_API_KEY is not set. Add it to a .env file in the project root.")
    st.stop()

headers = {"authorization": f"Bearer {openai_api_key}"}

# Helper functions for library management
DB_PATH = "data/library.db"
TABLE_NAME = "library"


def load_library_df():
    """Load the library table from SQLite into a DataFrame."""
    engine = create_engine(f"sqlite:///{DB_PATH}")
    df = pd.read_sql_table(TABLE_NAME, engine)
    return df


def save_library_df(df):
    """Save a DataFrame to the library table in SQLite (replace mode)."""
    engine = create_engine(f"sqlite:///{DB_PATH}")
    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)


# Build the agent once per session (the key is fixed for the process lifetime).
if "agent" not in st.session_state:
    st.session_state.agent = build_agent(openai_api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []


def _render_recommendations(rec_result):
    """Render a recommendations message (markdown + Amazon purchase buttons)."""
    st.markdown(rec_result["original_response"])
    recommendations = rec_result["recommendations"]
    if recommendations:
        st.subheader("\U0001f6d2 Purchase Links:")
        for i, rec in enumerate(recommendations, 1):
            if "title" in rec and "author" in rec:
                amazon_link = generate_amazon_link(rec["title"], rec["author"])
                with st.container():
                    st.write(f"**{i}.** {rec['title']} by {rec['author']}")
                    if "reason" in rec:
                        st.write(f"*{rec['reason']}*")
                    st.link_button("\U0001f6d2 Buy on Amazon", amazon_link)
                    st.divider()


# Create tabs: Chat and My Library
chat_tab, library_tab = st.tabs(["💬 Chat", "📚 My Library"])

# ===== CHAT TAB =====
with chat_tab:
    # Index of the most recent summary message (to attach the recommendation button to it).
    last_summary_idx = None
    for i, msg in enumerate(st.session_state.messages):
        if msg.get("kind") == "summary":
            last_summary_idx = i

    # Render the chat history.
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            kind = msg.get("kind", "text")
            if kind == "recommendations":
                _render_recommendations(msg["data"])
            else:
                st.write(msg["content"])

            # Offer a recommendation button under the latest summary, unless it has already
            # produced recommendations.
            if kind == "summary" and i == last_summary_idx and not msg.get("recommended"):
                if st.button("Get Book Recommendations", key=f"rec_btn_{i}"):
                    try:
                        rec_result = recommendation_system(msg["book"], msg["author"], headers)
                        st.session_state.messages[i]["recommended"] = True
                        st.session_state.messages.append(
                            {"role": "assistant", "kind": "recommendations", "data": rec_result}
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating recommendations: {str(e)}")

    # Chat input.
    if prompt := st.chat_input("Ask for a book summary or about your library..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        try:
            reply, summary_args = run_agent(st.session_state.agent, prompt)
            if summary_args:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "kind": "summary",
                        "content": reply,
                        "book": summary_args.get("book_name", ""),
                        "author": summary_args.get("author_name", ""),
                    }
                )
            else:
                st.session_state.messages.append(
                    {"role": "assistant", "kind": "text", "content": reply}
                )
        except Exception as e:
            st.session_state.messages.append(
                {"role": "assistant", "kind": "text", "content": f"An error occurred: {str(e)}"}
            )
        st.rerun()

# ===== MY LIBRARY TAB =====
with library_tab:
    st.subheader("Manage Your Library")

    # Load library data into session state if not already loaded
    if "library_df" not in st.session_state:
        st.session_state.library_df = load_library_df()

    # Define column configuration for the data editor
    column_config = {
        "Book": st.column_config.TextColumn("Book", required=True),
        "Author": st.column_config.TextColumn("Author"),
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=["Yet to Buy", "Reading", "Ready to Start", "Finished"],
        ),
        "Year": st.column_config.NumberColumn("Year", min_value=1900, max_value=2100),
    }

    # Editable data grid
    edited_df = st.data_editor(
        st.session_state.library_df,
        column_config=column_config,
        num_rows="dynamic",
        key="library_editor",
    )

    # Buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Changes", key="save_btn"):
            # Validation: no blank Book values
            if edited_df["Book"].isna().any() or (edited_df["Book"] == "").any():
                st.error("❌ All books must have a title (Book column cannot be blank).")
            else:
                # Warning: Finished books should have a Year
                finished_without_year = (edited_df["Status"] == "Finished") & edited_df["Year"].isna()
                if finished_without_year.any():
                    st.warning(
                        "⚠️ Some books marked as 'Finished' do not have a Year value. "
                        "Consider adding the year they were finished."
                    )

                # Save to database
                try:
                    save_library_df(edited_df)
                    st.session_state.library_df = edited_df
                    st.success("✓ Changes saved successfully!")
                except Exception as e:
                    st.error(f"Error saving changes: {str(e)}")

    with col2:
        if st.button("🔄 Refresh", key="refresh_btn"):
            st.session_state.library_df = load_library_df()
            st.rerun()
