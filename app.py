import os
import streamlit as st
from dotenv import load_dotenv

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
