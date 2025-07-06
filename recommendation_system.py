import os
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv
import streamlit as st
load_dotenv()


class State(TypedDict):
    book_name: str
    author_name: str
    response: str

 

def system_prompt(book_name: str, author_name: str) -> str:
    return f"""
    You are a helpful assistant who can do a web search and find books similar to the one the user is looking for.
    You will be given a book name and author name.
    You will need to do a web search and find books similar to the one the user is looking for.
    You will need to return the book name and author name of the books you find.
    
    Book: {book_name}
    Author: {author_name}
    
    Please provide 5 book recommendations that are similar to this book. For each recommendation, include:
    1. Book title
    2. Author name
    3. Brief reason why it's similar
    """

def generate_response(state: State, api_key: str) -> Dict[str, Any]:
    book_name = state["book_name"]
    author_name = state["author_name"]
    chat = ChatOpenAI(
        temperature=0.1, 
        openai_api_key=api_key,
        model="gpt-4o-mini"
    )
    
    message = HumanMessage(content=system_prompt(book_name, author_name))
    response = chat.invoke([message])
    
    return {"response": response.content}

def recommendation_system(book_name: str, author_name: str, headers: Dict[str, str]) -> str:
    # Extract API key from headers
    auth_header = headers.get("authorization", "")
    
    # If the header follows the 'Bearer <token>' format, split and get the token
    if auth_header.startswith("Bearer "):
        api_key = auth_header.split(" ", 1)[1]
    else:
        api_key = auth_header  # fallback if not in Bearer format
    
    # Create the graph
    graph = StateGraph(State)
    
    # Create a custom node that includes the API key
    def generate_response_with_api_key(state: State) -> Dict[str, Any]:
        return generate_response(state, api_key)
    
    graph.add_node("generate_response", generate_response_with_api_key)
    graph.add_edge(START, "generate_response")
    graph.add_edge("generate_response", END)
    
    # Compile and run
    react_graph = graph.compile()
    result = react_graph.invoke({"book_name": book_name, "author_name": author_name})
    
    return result["response"]
