from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List, Optional, Dict, Any

from models import OrderResponse, OrderDetailResponse, ProductOrderResponse, HighPriorityOrderResponse
from api_client import OrderApiClient

# Initialize FastAPI app
app = FastAPI(
    title="Order Service",
    description="Service for retrieving order information",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize API client
MOCK_API_URL = os.environ.get("MOCK_API_URL", "http://localhost:8001")
api_client = OrderApiClient(base_url=MOCK_API_URL)

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Order Service API", "status": "running"}

@app.get("/customer/{customer_id}", response_model=OrderResponse)
def get_customer_orders(customer_id: int):
    """Get all orders for a specific customer."""
    orders = api_client.get_customer_orders(customer_id)
    
    # Check if error response
    if isinstance(orders, dict) and "error" in orders:
        raise HTTPException(status_code=404, detail=orders["error"])
    
    return {
        "customer_id": customer_id,
        "orders": orders,
        "count": len(orders)
    }

@app.get("/customer/{customer_id}/recent", response_model=OrderDetailResponse)
def get_recent_order(customer_id: int):
    """Get the most recent order for a specific customer."""
    orders = api_client.get_customer_orders(customer_id)
    
    # Check if error response
    if isinstance(orders, dict) and "error" in orders:
        raise HTTPException(status_code=404, detail=orders["error"])
    
    if not orders:
        raise HTTPException(status_code=404, detail=f"No orders found for customer ID {customer_id}")
    
    # Return the first order (most recent due to sorting)
    return {
        "customer_id": customer_id,
        "order": orders[0]
    }

@app.get("/customer/{customer_id}/product", response_model=ProductOrderResponse)
def get_orders_by_product(
    customer_id: int,
    product_keyword: str = Query(..., description="Keyword to search in product name or category")
):
    """Get orders containing a specific product for a customer."""
    orders = api_client.get_customer_orders(customer_id)
    
    # Check if error response
    if isinstance(orders, dict) and "error" in orders:
        raise HTTPException(status_code=404, detail=orders["error"])
    
    # Filter orders by product keyword
    filtered_orders = [
        order for order in orders 
        if (isinstance(order.get('Product', ''), str) and 
            product_keyword.lower() in order.get('Product', '').lower()) or 
           (isinstance(order.get('Product_Category', ''), str) and 
            product_keyword.lower() in order.get('Product_Category', '').lower())
    ]
    
    if not filtered_orders:
        raise HTTPException(
            status_code=404, 
            detail=f"No orders found with product containing '{product_keyword}' for customer ID {customer_id}"
        )
    
    return {
        "customer_id": customer_id,
        "product_keyword": product_keyword,
        "orders": filtered_orders,
        "count": len(filtered_orders)
    }

@app.get("/high-priority", response_model=HighPriorityOrderResponse)
def get_high_priority_orders(
    limit: int = Query(5, description="Maximum number of orders to return")
):
    """Get recent high-priority orders."""
    orders = api_client.get_orders_by_priority("Critical", limit)
    
    # Check if error response
    if isinstance(orders, dict) and "error" in orders:
        raise HTTPException(status_code=404, detail=orders["error"])
    
    return {
        "orders": orders,
        "count": len(orders)
    }

@app.get("/total-sales-by-category")
def get_total_sales_by_category():
    """Get total sales by product category."""
    data = api_client.get_total_sales_by_category()
    
    # Check if error response
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    
    return {"categories": data}

@app.get("/high-profit-products")
def get_high_profit_products(
    min_profit: float = Query(100.0, description="Minimum profit threshold")
):
    """Get high-profit products."""
    data = api_client.get_high_profit_products(min_profit)
    
    # Check if error response
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    
    return {"min_profit": min_profit, "products": data, "count": len(data)}

@app.get("/shipping-cost-summary")
def get_shipping_cost_summary():
    """Get shipping cost summary."""
    data = api_client.get_shipping_cost_summary()
    
    # Check if error response
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    
    return data

@app.get("/profit-by-gender")
def get_profit_by_gender():
    """Get total profit by customer gender."""
    data = api_client.get_profit_by_gender()
    
    # Check if error response
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    
    return {"genders": data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)