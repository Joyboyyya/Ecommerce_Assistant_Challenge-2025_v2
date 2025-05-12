import os
import logging
from langchain_cohere import ChatCohere
from langchain_core.tools import tool

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "PEy1tsUjWmM66wjbm8SgFAHulAHZOHlLI0kiiIRM")
COHERE_MODEL = os.getenv("COHERE_MODEL", "command-r")

# Singleton pattern for LLM client
_llm_client = None

def create_llm_client():
    """
    Create and configure the LLM client.
    
    Returns:
        Configured ChatCohere instance with tools
    """
    global _llm_client
    
    # Return existing client if already initialized
    if _llm_client is not None:
        return _llm_client
    
    logger.info(f"Initializing Cohere LLM client with model: {COHERE_MODEL}")
    
    # Initialize ChatCohere with API key
    try:
        llm = ChatCohere(
            cohere_api_key=COHERE_API_KEY,
            model=COHERE_MODEL,
            temperature=0.7,  # Adjust based on needs
        )
        
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
        
        # Bind tools to the LLM
        llm_with_tools = llm.bind_tools(tools)
        
        logger.info(f"Successfully initialized LLM client with {len(tools)} tools")
        
        # Store in singleton
        _llm_client = llm_with_tools
        
        return llm_with_tools
        
    except Exception as e:
        logger.error(f"Error initializing LLM client: {str(e)}")
        raise