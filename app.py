import streamlit as st
from book_summariser import get_summary
from library_manager import library_management_system
from recommendation_system import recommendation_system
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from typing import Dict, Any, TypedDict

load_dotenv()

# Define the state schema as a TypedDict
class AgentState(TypedDict):
    agent_choice: str
    book_name: str
    author_name: str
    user_query: str
    openai_api_key: str
    headers: Dict
    summary: str
    response: str
    error: str

# Routing function to determine which agent to use
def route_agent(state: AgentState) -> str:
    """Route to the appropriate agent based on user choice"""
    if state.get("agent_choice") == "Book Summarizer":
        return "get_summary"
    elif state.get("agent_choice") == "Library Manager":
        return "library_management_system"
    else:
        return "end"

# Agent execution functions
def execute_book_summarizer(state: AgentState) -> AgentState:
    """Execute the book summarizer agent"""
    book_name = state.get("book_name")
    author_name = state.get("author_name")
    headers = state.get("headers")
    
    if book_name and author_name and headers:
        try:
            summary = get_summary(book_name, author_name, headers)
            return {"summary": summary, "agent_choice": state.get("agent_choice")}
        except Exception as e:
            return {"error": f"Error generating summary: {str(e)}"}
    return {"error": "Missing required fields for book summarizer"}

def execute_library_manager(state: AgentState) -> AgentState:
    """Execute the library manager agent"""
    user_query = state.get("user_query")
    headers = state.get("headers")
    
    if user_query and headers:
        try:
            response = library_management_system(user_query, headers)
            return {"response": response, "agent_choice": state.get("agent_choice")}
        except Exception as e:
            return {"error": f"Error retrieving information: {str(e)}"}
    return {"error": "Missing required fields for library manager"}

def start_node(state: AgentState) -> AgentState:
    """Start node that passes through the state"""
    return state

def end_node(state: AgentState) -> AgentState:
    """End node that passes through the state"""
    return state

st.title("AI Assistant: Book Summarizer & Knowledge Retriever")

agent_choice = st.radio(
    "Choose the AI agent you want to use:",
    ("Book Summarizer", "Library Manager")
)

openai_api_key = st.text_input("Enter your Open API key:", type="password")

if not openai_api_key:
    st.error("Please enter your Open API key.")
else:
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {openai_api_key}"
    }
    
    llm = ChatOpenAI(
        temperature=0, 
        openai_api_key=openai_api_key,
        model="gpt-4o-mini"
    )
    
    # Create the graph
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("start", start_node)
    builder.add_node("get_summary", execute_book_summarizer)
    builder.add_node("library_management_system", execute_library_manager)
    builder.add_node("end", end_node)
    
    # Add edge from START to start node
    builder.add_edge(START, "start")
    
    # Add conditional edges based on agent choice
    builder.add_conditional_edges(
        "start",
        route_agent,
        {
            "get_summary": "get_summary",
            "library_management_system": "library_management_system",
            "end": "end"
        }
    )
    
    # Add edges to end
    builder.add_edge("get_summary", END)
    builder.add_edge("library_management_system", END)
    
    # Compile the graph
    graph = builder.compile()
    
    # Initialize state with agent choice
    initial_state = {
        "agent_choice": agent_choice,
        "headers": headers,
        "book_name": "",
        "author_name": "",
        "user_query": "",
        "openai_api_key": openai_api_key,
        "summary": "",
        "response": "",
        "error": ""
    }
    
    if agent_choice == "Book Summarizer":
        book_name = st.text_input("Enter the book name:")
        author_name = st.text_input("Enter the author name:")
        
        if st.button("Get Summary"):
            if not book_name or not author_name:
                st.error("Please fill in all fields.")
            else:
                # Update state with book details
                initial_state["book_name"] = book_name
                initial_state["author_name"] = author_name
                
                # Execute the graph
                result = graph.invoke(initial_state)
                
                if "summary" in result:
                    st.subheader("Summary:")
                    st.write(result["summary"])
                    
                    # Store the summary and headers in session state for recommendations
                    st.session_state.summary_generated = True
                    st.session_state.summary_headers = headers
                    st.session_state.summary_book_name = book_name
                    st.session_state.summary_author_name = author_name
                else:
                    st.error(result.get("error", "An error occurred"))
        
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
        user_query = st.text_input("Enter your query for the knowledge base:")
        
        if st.button("Retrieve Information"):
            if not user_query:
                st.error("Please enter your query.")
            else:
                # Update state with user query
                initial_state["user_query"] = user_query
                
                # Execute the graph
                result = graph.invoke(initial_state)
                
                if "response" in result:
                    st.subheader("Response:")
                    st.write(result["response"])
                else:
                    st.error(result.get("error", "An error occurred"))               