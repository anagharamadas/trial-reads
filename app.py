import streamlit as st
from book_summariser import get_summary
from library_manager import library_management_system

st.title("AI Assistant: Book Summarizer & Knowledge Retriever")

agent_choice = st.radio(
    "Choose the AI agent you want to use:",
    ("Book Summarizer", "Library Manager")
)

if agent_choice == "Book Summarizer":
    openai_api_key = st.text_input("Enter your Open API key:", type="password")
    book_name = st.text_input("Enter the book name:")
    author_name = st.text_input("Enter the author name:")
    if st.button("Get Summary"):
        if not openai_api_key or not book_name or not author_name:
            st.error("Please fill in all fields.")
        else:
            headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {openai_api_key}"
            }

            summary = get_summary(book_name, author_name, headers)
            st.subheader("Summary:")
            st.write(summary)

elif agent_choice == "Library Manager":
    openai_api_key = st.text_input("Enter your Open API key:", type="password")
    user_query = st.text_input("Enter your query for the knowledge base:")
    if st.button("Retrieve Information"):
        if not openai_api_key:
            st.error("Please enter your Open API key.")
        elif not user_query:
            st.error("Please enter your query.")
        else:
            headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {openai_api_key}"
            }
            rag_response = library_management_system(user_query, headers)
            st.subheader("Response:")
            st.write(rag_response)
