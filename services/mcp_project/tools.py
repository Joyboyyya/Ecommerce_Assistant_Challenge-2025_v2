
import json
import os
from typing import List, Dict, Any, Optional
import requests
from mcp.server.fastmcp import FastMCP
import getpass
import os


# def _set_env(var: str):
#     if not os.environ.get(var):
#         os.environ[var] = getpass.getpass(f"{var}: ")


# _set_env("COHERE_API_KEY")

import os
import logging
import requests
import pandas as pd

from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from datetime import date, datetime
from typing import Optional

import pytz
from langchain_core.runnables import RunnableConfig

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition

# ==========================================
# Configuration
# ==========================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service endpoints (can also be set via environment variables)
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001")
ORDER_SERVICE_URL   = os.getenv("ORDER_SERVICE_URL",   "http://localhost:8002")

# Initialize FastMCP server
mcp = FastMCP("Ecommerce")

# ==========================================
# Product Service Tools
# ==========================================

@mcp.tool()
def search_products(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for products based on a text query using RAG.

    Args:
        query: Search query string
        top_k: Number of results to return (default: 5)

    Returns:
        List of product dictionaries containing details like title, description, price, etc.
    """
    try:
        response = requests.get(
            f"{PRODUCT_SERVICE_URL}/search",
            params={"query": query, "top_k": top_k}
        )
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return []

@mcp.tool()
def search_product_by_category(category: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for products in a specific category.

    Args:
        category: Category to search in
        query: Search query string
        top_k: Number of results to return (default: 5)

    Returns:
        List of product dictionaries containing details like title, description, price, etc.
    """
    try:
        response = requests.get(
            f"{PRODUCT_SERVICE_URL}/search/category",
            params={"category": category, "query": query, "top_k": top_k}
        )
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        logger.error(f"Error searching products by category: {e}")
        return []

@mcp.tool()
def get_top_rated_products(category: Optional[str] = None,
                           min_rating: float = 4.5,
                           top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Get top-rated products, optionally filtered by category.

    Args:
        category: Category to filter by (optional)
        min_rating: Minimum rating threshold (default: 4.5)
        top_k: Number of results to return (default: 5)

    Returns:
        List of top-rated product dictionaries
    """
    try:
        params = {"min_rating": min_rating, "top_k": top_k}
        if category:
            params["category"] = category
        response = requests.get(f"{PRODUCT_SERVICE_URL}/top-rated", params=params)
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        logger.error(f"Error fetching top-rated products: {e}")
        return []


@mcp.tool()
def get_specific_instrument_details(instrument_type: str) -> List[Dict[str, Any]]:
    """
    Get information about a specific type of musical instrument.

    Args:
        instrument_type: Type of instrument (e.g., 'guitar', 'piano', 'drums')

    Returns:
        List of dictionaries containing instrument details
    """
    try:
        return search_products(instrument_type, top_k=3)
    except Exception as e:
        logger.error(f"Error fetching specific instrument details: {e}")
        return []

# ==========================================
# Order Service Tools
# ==========================================

@mcp.tool()
def get_customer_orders(customer_id: int) -> List[Dict[str, Any]]:
    """
    Get all orders for a specific customer.

    Args:
        customer_id: Customer ID

    Returns:
        List of dictionaries containing order information
    """
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/customer/{customer_id}")
        response.raise_for_status()
        return response.json().get("orders", [])
    except Exception as e:
        logger.error(f"Error fetching customer orders: {e}")
        return []

@mcp.tool()
def get_customer_recent_order(customer_id: int) -> Dict[str, Any]:
    """
    Get the most recent order for a specific customer.

    Args:
        customer_id: Customer ID

    Returns:
        Dictionary containing the most recent order details
    """
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/customer/{customer_id}/recent")
        response.raise_for_status()
        return response.json().get("order", {})
    except Exception as e:
        logger.error(f"Error fetching recent order: {e}")
        return {}

@mcp.tool()
def get_customer_product_orders(customer_id: int,
                                product_keyword: str) -> List[Dict[str, Any]]:
    """
    Get orders containing a specific product for a customer.

    Args:
        customer_id: Customer ID
        product_keyword: Keyword to search in product name or category

    Returns:
        List of dictionaries containing matching order information
    """
    try:
        response = requests.get(
            f"{ORDER_SERVICE_URL}/customer/{customer_id}/product",
            params={"product_keyword": product_keyword}
        )
        response.raise_for_status()
        return response.json().get("orders", [])
    except Exception as e:
        logger.error(f"Error fetching product orders: {e}")
        return []

@mcp.tool()
def get_high_priority_orders(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get recent high-priority orders.

    Args:
        limit: Maximum number of orders to return (default: 5)

    Returns:
        List of dictionaries containing high-priority order information
    """
    try:
        response = requests.get(
            f"{ORDER_SERVICE_URL}/high-priority",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json().get("orders", [])
    except Exception as e:
        logger.error(f"Error fetching high-priority orders: {e}")
        return []

@mcp.tool()
def get_sales_by_category() -> List[Dict[str, Any]]:
    """
    Get total sales data aggregated by product category.

    Returns:
        List of dictionaries with category and sales data
    """
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/total-sales-by-category")
        response.raise_for_status()
        return response.json().get("categories", [])
    except Exception as e:
        logger.error(f"Error fetching sales by category: {e}")
        return []

@mcp.tool()
def get_high_profit_products(min_profit: float = 100.0) -> List[Dict[str, Any]]:
    """
    Get high-profit products.

    Args:
        min_profit: Minimum profit threshold (default: 100.0)

    Returns:
        List of dictionaries containing high-profit product order information
    """
    try:
        response = requests.get(
            f"{ORDER_SERVICE_URL}/high-profit-products",
            params={"min_profit": min_profit}
        )
        response.raise_for_status()
        return response.json().get("products", [])
    except Exception as e:
        logger.error(f"Error fetching high-profit products: {e}")
        return []

@mcp.tool()
def get_shipping_cost_summary() -> Dict[str, float]:
    """
    Get shipping cost summary (average, min, max).

    Returns:
        Dictionary with shipping cost statistics
    """
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/shipping-cost-summary")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching shipping cost summary: {e}")
        return {}

@mcp.tool()
def get_profit_by_gender() -> List[Dict[str, Any]]:
    """
    Get total profit aggregated by customer gender.

    Returns:
        List of dictionaries with gender and profit data
    """
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/profit-by-gender")
        response.raise_for_status()
        return response.json().get("genders", [])
    except Exception as e:
        logger.error(f"Error fetching profit by gender: {e}")
        return []

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
