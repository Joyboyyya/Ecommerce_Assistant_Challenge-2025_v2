from datetime import datetime
import threading

from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict

from llm_client import create_llm_client

# Import tools
from tools import (
    search_products,
    search_product_by_category,
    get_top_rated_products,
    get_customer_orders,
    get_customer_recent_order,
    get_customer_product_orders,
    get_high_priority_orders,
    get_sales_by_category,
    get_high_profit_products,
    get_shipping_cost_summary,
    get_profit_by_gender,
)

# Global variables for singleton pattern
_graph_instance = None
_graph_lock = threading.Lock()

def create_chat_graph():
    """
    Create the LangGraph for the e-commerce assistant.
    
    Returns:
        Compiled LangGraph instance
    """
    # Initialize LLM client with tools
    llm_with_tools = create_llm_client()

    class MessagesState(TypedDict):
        messages: Annotated[list, add_messages]


    # Define tools for the LLM
    tools = [
            search_products,
            search_product_by_category,
            get_top_rated_products,
            get_customer_orders,
            get_customer_recent_order,
            get_customer_product_orders,
            get_high_priority_orders,
            get_sales_by_category,
            get_high_profit_products,
            get_shipping_cost_summary,
            get_profit_by_gender,
    ]
    
    # Define the assistant node (LLM with tools)
    def assistant(state: MessagesState):
        # Get current time for context
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create system message with time context
        sys_msg = SystemMessage(content=f"""
            You are a helpful customer support assistant for an E-Commerce Website.
            Use the provided tools to search for products, orders, and other information to assist the user's queries.
            When searching, be persistent. Expand your query bounds if the first search returns no results.
            If a search comes up empty, expand your search before giving up.
            Before ending the conversation, ask the user if they need help with anything else.
            You are not allowed to make up information. If there is any missing information, ask the user for it.
            
            Current time: {current_time}.
        """)
        
        # Invoke LLM with system message and conversation history
        return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}
    
    # Create graph builder
    builder = StateGraph(MessagesState)
    
    # Add nodes
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    
    # Define edges
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        # Route based on whether the assistant wants to use tools
        tools_condition,
    )
    builder.add_edge("tools", "assistant")
    
    # Set up memory for state persistence
    memory = MemorySaver()
    
    # Compile graph
    return builder.compile(checkpointer=memory)

def get_graph_instance():
    """
    Get or create the LangGraph instance (singleton pattern).
    
    Returns:
        The shared LangGraph instance
    """
    global _graph_instance
    
    # Use double-checked locking pattern for thread safety
    if _graph_instance is None:
        with _graph_lock:
            if _graph_instance is None:
                _graph_instance = create_chat_graph()
    
    return _graph_instance