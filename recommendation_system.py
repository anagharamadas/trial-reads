import os
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv
import streamlit as st
import urllib.parse
import re


load_dotenv()


class State(TypedDict):
    book_name: str
    author_name: str
    response: str

def generate_amazon_link(book_title: str, author_name: str) -> str:
    """Generate Amazon search link for a book"""
    search_query = f"{book_title} {author_name}"
    encoded_query = urllib.parse.quote(search_query)
    return f"https://www.amazon.com/s?k={encoded_query}"

def parse_recommendations(response_text: str) -> List[Dict[str, str]]:
    """Parse the AI response to extract book recommendations"""
    recommendations = []
    
    # Split by numbered recommendations (1., 2., etc.)
    lines = response_text.split('\n')
    current_book = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a new numbered recommendation
        if re.match(r'^\d+\.', line):
            # Save previous book if exists
            if current_book:
                recommendations.append(current_book)
            current_book = {}
            
            # Extract book title and author from the line
            # Remove the number and dot
            content = re.sub(r'^\d+\.\s*', '', line)
            
            # Try to extract title and author (assuming format: "Title by Author")
            if ' by ' in content:
                parts = content.split(' by ', 1)
                current_book['title'] = parts[0].strip()
                current_book['author'] = parts[1].strip()
            else:
                current_book['title'] = content
                current_book['author'] = ''
                
        elif current_book and line:
            # This might be additional info (reason, etc.)
            if 'reason' not in current_book:
                current_book['reason'] = line
            else:
                current_book['reason'] += ' ' + line
    
    # Add the last book
    if current_book:
        recommendations.append(current_book)
    
    return recommendations

def system_prompt(book_name: str, author_name: str) -> str:
    return f"""
    You are a helpful assistant who can find books similar to the one the user is looking for.
    You will be given a book name and author name.
    You will need to find books similar to the one the user is looking for.
    
    Book: {book_name}
    Author: {author_name}
    
    Please provide exactly 5 book recommendations that are similar to this book. 
    Format each recommendation as follows:
    
    1. [Book Title] by [Author Name]
       Reason: [Brief explanation of why it's similar]
    
    2. [Book Title] by [Author Name]
       Reason: [Brief explanation of why it's similar]
    
    Continue for all 5 recommendations. Make sure to include both the book title and author name for each recommendation.
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


def recommendation_system(book_name: str, author_name: str, headers: Dict[str, str]) -> Dict[str, Any]:
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
    
    response_text = result["response"]
    
    # Parse recommendations and add Amazon links
    recommendations = parse_recommendations(response_text)
    
    return {
        "original_response": response_text,
        "recommendations": recommendations
    }
