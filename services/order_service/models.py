from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class OrderBase(BaseModel):
    """Base model for order information."""
    Order_Date: str
    Time: Optional[str] = None
    Aging: Optional[float] = None
    Customer_Id: int
    Gender: Optional[str] = None
    Device_Type: Optional[str] = None
    Customer_Login_type: Optional[str] = None
    Product_Category: str
    Product: str
    Sales: float
    Quantity: Optional[float] = None
    Discount: Optional[float] = None
    Profit: Optional[float] = None
    Shipping_Cost: float
    Order_Priority: str
    Payment_method: Optional[str] = None
    
class OrderResponse(BaseModel):
    """Model for order response."""
    customer_id: int
    orders: List[Dict[str, Any]]
    count: int
    
class OrderDetailResponse(BaseModel):
    """Model for detailed order response."""
    customer_id: int
    order: Dict[str, Any]
    
class ProductOrderResponse(BaseModel):
    """Model for product order response."""
    customer_id: int
    product_keyword: str
    orders: List[Dict[str, Any]]
    count: int
    
class HighPriorityOrderResponse(BaseModel):
    """Model for high priority order response."""
    orders: List[Dict[str, Any]]
    count: int
    
class OrderFilterParams(BaseModel):
    """Model for order filtering parameters."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gender: Optional[str] = None
    device_type: Optional[str] = None
    product_category: Optional[str] = None
    order_priority: Optional[str] = None
    payment_method: Optional[str] = None
    min_sales: Optional[float] = None
    max_sales: Optional[float] = None
    
class OrderAnalytics(BaseModel):
    """Model for order analytics response."""
    total_orders: int
    total_sales: float
    average_order_value: float
    total_profit: Optional[float] = None
    total_shipping_cost: float
    orders_by_priority: Dict[str, int]
    orders_by_category: Dict[str, int]
    orders_by_payment_method: Optional[Dict[str, int]] = None
    orders_by_gender: Optional[Dict[str, int]] = None