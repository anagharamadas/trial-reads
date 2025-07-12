import os
from langchain_openai import ChatOpenAI
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate  # type: ignore
import re
def get_summary(book_name, author_name, headers):
    
    


    auth_header = headers.get("authorization", "")

    # If the header follows the 'Bearer <token>' format, split and get the token
    if auth_header.startswith("Bearer "):
        api_key = auth_header.split(" ", 1)[1]
    else:
        api_key = auth_header  # fallback if not in Bearer format


    # prompt = ChatPromptTemplate.from_messages([("system", content)])
    chat = ChatOpenAI(
        temperature=0, 
        openai_api_key=api_key,
        model="gpt-4o-mini"
        )
    internal_reasoning_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("human", "Summarise the book {book_name} by the author {author_name}.")
        ])
    final_response_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Provide a concise answer."),
        ("human", "Summarise the book{book_name} chapter by chapter of first 3 chaptersin 250 words each?")
    ])
    # Create a chain for internal reasoning
    internal_chain = internal_reasoning_prompt | chat

    # Create a chain for the final response
    final_chain = final_response_prompt | chat


    internal_response = internal_chain.invoke({"book_name": book_name, "author_name": author_name})
    final_response = final_chain.invoke({"book_name": book_name})

    cleaned_output = re.sub(r'<think>.*?</think>', '', final_response.content, flags=re.DOTALL)


    # Display the answer
    return cleaned_output

    


