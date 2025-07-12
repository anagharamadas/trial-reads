import streamlit as st
from book_summariser import get_summary
from library_manager import library_management_system
from recommendation_system import recommendation_system
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize Langfuse (optional - only if you have Langfuse keys)
# """ try:
#     langfuse = Langfuse(
#         public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
#         secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
#         host=os.getenv("LANGFUSE_HOST")
#     )
# except:
#     langfuse = None """

st.title("AI Assistant: Book Summarizer & Knowledge Retriever")

# trace = langfuse.trace(name="my-trace")
# span = trace.span(name="my-operation")
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
            
            # Store the summary and headers in session state for recommendations
            st.session_state.summary_generated = True
            st.session_state.summary_headers = headers
            st.session_state.summary_book_name = book_name
            st.session_state.summary_author_name = author_name
    
    # Show recommendation button only after summary is generated
    if st.session_state.get('summary_generated', False):
        st.divider()
        if st.button("Get Book Recommendations"):
            try:
                st.subheader("Book Recommendations:")
                recommendation_system_response = recommendation_system(
                    st.session_state.summary_book_name, 
                    st.session_state.summary_author_name, 
                    st.session_state.summary_headers
                )
                st.write(recommendation_system_response)
            except Exception as e:
                st.error(f"Error generating recommendations: {str(e)}")

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
# span.end()               