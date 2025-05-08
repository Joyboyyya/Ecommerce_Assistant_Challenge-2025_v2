from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ProductBase(BaseModel):
    """Base model for product information."""
    title: str
    description: Optional[str] = None
    features: Optional[str] = None
    price: Optional[float] = None
    average_rating: Optional[float] = None
    rating_number: Optional[int] = None
    main_category: Optional[str] = None
    categories: Optional[str] = None
    
class ProductSearchQuery(BaseModel):
    """Model for product search query."""
    query: str
    top_k: int = Field(5, description="Number of results to return")
    category: Optional[str] = None
    
class ProductSearchResponse(BaseModel):
    """Model for product search response."""
    query: str
    results: List[Dict[str, Any]]
    count: int
    
class ProductCategoryQuery(BaseModel):
    """Model for product category query."""
    category: str
    top_k: int = Field(5, description="Number of results to return")
    
class ProductCategoryResponse(BaseModel):
    """Model for product category response."""
    category: str
    results: List[Dict[str, Any]]
    count: int