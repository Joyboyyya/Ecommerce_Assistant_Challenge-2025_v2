import requests
import pandas as pd
from typing import List, Dict, Any, Optional, Union
import logging
import os
import dotenv
from dotenv import load_dotenv
from pathlib import Path
import logging

# Load environment variables from .env file
# Use relative path from the current file
# current_dir = Path(__file__).resolve().parent
# project_root = current_dir.parent.parent  # Go up two levels to project root
# dotenv_path = project_root / ".env"

# # Load .env file if it exists
# if dotenv_path.exists():
#     load_dotenv(dotenv_path=str(dotenv_path))
# else:
#     # Fall back to trying a .env in the current directory
#     load_dotenv()

# raw = os.environ.get("MOCK_API_URL")
# logger = logging.getLogger("your_module_name")
# logger.debug("RAW os.environ['MOCK_API_URL']: %r", raw)
# assert raw == "http://localhost:8000", "Env var was not read correctly!"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderApiClient:
    """Client for interacting with the order mock API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize with API base URL."""
        # base_url = "http://localhost:8000"
        self.base_url = base_url
        logger.info(f"Initialized OrderApiClient with base URL: {base_url}")
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders from the dataset."""
        try:
            response = requests.get(f"{self.base_url}/data")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved {len(data)} orders from the database")
            return data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching all orders: {str(e)}")
            return {"error": f"Error fetching all orders: {str(e)}"}
        
    def get_customer_orders(self, customer_id: int) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """
        Get all orders for a specific customer.
        
        Args:
            customer_id: The customer ID to look up
            
        Returns:
            List of order dictionaries or error dictionary
        """
        try:
            logger.info(f"Fetching orders for customer ID: {customer_id}")
            response = requests.get(f"{self.base_url}/data/customer/{customer_id}")
            response.raise_for_status()
            
            data = response.json()
            
            # Check if error response from API
            if isinstance(data, dict) and "error" in data:
                logger.warning(f"API returned error: {data['error']}")
                return data
            
            # Process data with pandas for easier manipulation
            if data:
                df = pd.DataFrame(data)
                # Convert date strings to datetime objects
                if 'Order_Date' in df.columns:
                    df['Order_Date'] = pd.to_datetime(df['Order_Date'])
                    # Sort by date (most recent first)
                    df = df.sort_values('Order_Date', ascending=False)
                    # Convert datetime back to string for JSON serialization
                    df['Order_Date'] = df['Order_Date'].dt.strftime('%Y-%m-%d')
                
                logger.info(f"Found {len(df)} orders for customer ID: {customer_id}")
                return df.to_dict(orient='records')
            else:
                logger.warning(f"No orders found for customer ID: {customer_id}")
                return {"error": f"No orders found for customer ID {customer_id}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from API: {str(e)}")
            return {"error": f"Error fetching data from API: {str(e)}"}
            
    def get_orders_by_product_category(self, category: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """
        Get orders for a specific product category.
        
        Args:
            category: Product category to filter by
            
        Returns:
            List of order dictionaries or error dictionary
        """
        try:
            logger.info(f"Fetching orders for product category: {category}")
            response = requests.get(f"{self.base_url}/data/product-category/{category}")
            response.raise_for_status()
            
            data = response.json()
            
            # Check if error response from API
            if isinstance(data, dict) and "error" in data:
                logger.warning(f"API returned error: {data['error']}")
                return data
            
            logger.info(f"Found {len(data)} orders for category: {category}")
            return data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching orders by category: {str(e)}")
            return {"error": f"Error fetching orders by category: {str(e)}"}
            
    def get_orders_by_priority(self, priority: str, limit: int = 5) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """
        Get orders with a specific priority.

        Args:
            priority: Order priority to filter by (e.g., "Critical", "High", "Medium", "Low")
            limit: Maximum number of orders to return

        Returns:
            List of order dictionaries or error dictionary
        """
        try:
            logger.info(f"Fetching orders with priority: {priority}")
            response = requests.get(f"{self.base_url}/data/order-priority/{priority}")
            response.raise_for_status()

            data = response.json()

            # Check if error response from API
            if isinstance(data, dict) and "error" in data:
                logger.warning(f"API returned error: {data['error']}")
                return data

            # Process data with pandas for easier manipulation
            if data:
                df = pd.DataFrame(data)
                # Convert date strings to datetime objects
                if 'Order_Date' in df.columns:
                    df['Order_Date'] = pd.to_datetime(df['Order_Date'])
                    # Sort by date (most oldest first)
                    df = df.sort_values(['Order_Date','Time'], ascending=[False,False])
                    # Convert datetime back to string for JSON serialization
                    df['Order_Date'] = df['Order_Date'].dt.strftime('%Y-%m-%d')

                # Limit number of results
                df = df.head(limit)

                logger.info(f"Found {len(df)} orders with priority: {priority}")
                return df.to_dict(orient='records')
            else:
                logger.warning(f"No orders found with priority: {priority}")
                return {"error": f"No orders found with priority {priority}"}

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching orders by priority: {str(e)}")
            return {"error": f"Error fetching orders by priority: {str(e)}"}
    
    def get_total_sales_by_category(self) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """
        Get total sales aggregated by product category.
        
        Returns:
            List of dictionaries with category and sales data or error dictionary
        """
        try:
            logger.info("Fetching total sales by category")
            response = requests.get(f"{self.base_url}/data/total-sales-by-category")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved sales data for {len(data)} categories")
            return data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sales by category: {str(e)}")
            return {"error": f"Error fetching sales by category: {str(e)}"}
    
    def get_high_profit_products(self, min_profit: float = 100.0) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """
        Get high-profit products.
        
        Args:
            min_profit: Minimum profit threshold
            
        Returns:
            List of high-profit product orders or error dictionary
        """
        try:
            logger.info(f"Fetching high-profit products (min profit: {min_profit})")
            response = requests.get(f"{self.base_url}/data/high-profit-products?min_profit={min_profit}")
            response.raise_for_status()
            
            data = response.json()
            
            # Check if error response from API
            if isinstance(data, dict) and "error" in data:
                logger.warning(f"API returned error: {data['error']}")
                return data
            
            logger.info(f"Found {len(data)} high-profit products")
            return data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching high-profit products: {str(e)}")
            return {"error": f"Error fetching high-profit products: {str(e)}"}
    
    def get_shipping_cost_summary(self) -> Dict[str, Any]:
        """
        Get shipping cost summary (average, min, max).
        
        Returns:
            Dictionary with shipping cost summary or error dictionary
        """
        try:
            logger.info("Fetching shipping cost summary")
            response = requests.get(f"{self.base_url}/data/shipping-cost-summary")
            response.raise_for_status()
            
            data = response.json()
            logger.info("Retrieved shipping cost summary")
            return data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching shipping cost summary: {str(e)}")
            return {"error": f"Error fetching shipping cost summary: {str(e)}"}
    
    def get_profit_by_gender(self) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """
        Get total profit aggregated by customer gender.
        
        Returns:
            List of dictionaries with gender and profit data or error dictionary
        """
        try:
            logger.info("Fetching profit by gender")
            response = requests.get(f"{self.base_url}/data/profit-by-gender")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved profit data for {len(data)} genders")
            return data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching profit by gender: {str(e)}")
            return {"error": f"Error fetching profit by gender: {str(e)}"}