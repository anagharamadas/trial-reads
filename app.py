import os
from langchain_community.chat_models import ChatPerplexity
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate  # type: ignore
import re

st.title("Explain My Model")
PPLX_API_KEY = st.text_input("Enter your API key: ", type="password")


os.environ["PPLX_API_KEY"] = PPLX_API_KEY




# User input for the question
book_name = st.text_input("Enter the book name:")
author_name = st.text_input("Enter the author name:")

if st.button("Get Summary"):
    if not PPLX_API_KEY:
         st.error("Please enter your Perplexity API key.")
    elif not book_name:
        st.error("Please enter the book name.")
    elif not author_name:
        st.error("Please enter the author name.")
    else:

        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {PPLX_API_KEY}"
        }

        try:
            # Make the API request
            # prompt = ChatPromptTemplate.from_messages([("system", content)])
            chat = ChatPerplexity(
                temperature=0, 
                pplx_api_key=os.environ["PPLX_API_KEY"],
                model="sonar-pro"
                )
            internal_reasoning_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant."),
                ("human", "Summarise the book {book_name} by the author {author_name}.")
                ])
            final_response_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant. Provide a concise answer."),
                ("human", "What is the final summary of the book {book_name}?")
            ])
            # Create a chain for internal reasoning
            internal_chain = internal_reasoning_prompt | chat

            # Create a chain for the final response
            final_chain = final_response_prompt | chat


            internal_response = internal_chain.invoke({"book_name": book_name, "author_name": author_name})
            final_response = final_chain.invoke({"book_name": book_name})

            cleaned_output = re.sub(r'<think>.*?</think>', '', final_response.content, flags=re.DOTALL)
           

            # Display the answer
            st.subheader("Summary:")
            st.write(final_response.content)

        except Exception as e:
            # Handle errors gracefully
            st.error(f"An error occurred: {str(e)}")

