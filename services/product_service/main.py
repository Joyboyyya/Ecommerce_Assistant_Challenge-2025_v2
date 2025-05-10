from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from vector_store import ProductVectorStore
from models import ProductSearchResponse, ProductCategoryResponse
from utils import format_product_results, get_top_rated_products

# print(f"Product_URL: {os.environ.get(r'PRODUCT_SERVICE_URL')}")

# Initialize FastAPI app
app = FastAPI(
    title="Product Search Service",
    description="Service for searching and retrieving product information",
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

# Initialize vector store
vector_store = ProductVectorStore()

# Data paths
DATA_DIR = os.environ.get("DATA_DIR", "../../new_data")
PRODUCT_DATA_PATH = os.path.join(DATA_DIR, os.environ.get("PRODUCT_DATA_FILE", "Product_Information_Dataset.csv"))
INDEX_DIR = os.environ.get("INDEX_DIR", "../../new_data/preprocessed_data")
# Create index directory if it doesn't exist
os.makedirs(INDEX_DIR, exist_ok=True)
INDEX_PATH = os.path.join(INDEX_DIR, "product_index.faiss")
PRODUCT_PICKLE_PATH = os.path.join(INDEX_DIR, "product_data.pkl")

# Ensure directories exist
os.makedirs(INDEX_DIR, exist_ok=True)

# Check if index exists, otherwise build it
if os.path.exists(INDEX_PATH) and os.path.exists(PRODUCT_PICKLE_PATH):
    print(f"Loading existing index from {INDEX_PATH}")
    vector_store.load_index(INDEX_PATH, PRODUCT_PICKLE_PATH)
else:
    print(f"Building new index from {PRODUCT_DATA_PATH}")
    # Load and preprocess data
    vector_store.load_data(PRODUCT_DATA_PATH)
    # Create embeddings
    vector_store.create_embeddings()
    # Build index
    vector_store.build_index()
    # Save index for future use
    vector_store.save_index(INDEX_PATH, PRODUCT_PICKLE_PATH)

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Product Search Service API", "status": "running"}

@app.get("/search", response_model=ProductSearchResponse)
def search_products(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, description="Number of results to return")
):
    """Search for products based on a text query."""
    results = vector_store.search(query, top_k)
    
    if not results:
        # Return empty results rather than an error
        return {"query": query, "results": [], "count": 0}
    
    # Format results
    formatted_results = format_product_results(results)
    
    return {
        "query": query,
        "results": formatted_results,
        "count": len(formatted_results)
    }

@app.get("/search/category", response_model=ProductCategoryResponse)
def search_by_category(
    category: str = Query(..., description="Category to search in"),
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, description="Number of results to return")
):
    """Search for products in a specific category."""
    results = vector_store.search_by_category(query, category, top_k)
    
    if not results:
        # Return empty results rather than an error
        return {"category": category, "results": [], "count": 0}
    
    # Format results
    formatted_results = format_product_results(results)
    
    return {
        "category": category,
        "results": formatted_results,
        "count": len(formatted_results)
    }

@app.get("/top-rated")
def top_rated_products(
    category: Optional[str] = Query(None, description="Category filter (optional)"),
    min_rating: float = Query(4.5, description="Minimum rating"),
    top_k: int = Query(5, description="Number of results to return")
):
    """Get top-rated products, optionally filtered by category."""
    # Get top-rated products
    results = get_top_rated_products(
        vector_store.product_df, 
        category=category,
        min_rating=min_rating,
        top_k=top_k
    )
    
    # Format results
    formatted_results = format_product_results(results)
    
    return {
        "category": category or "all",
        "min_rating": min_rating,
        "results": formatted_results,
        "count": len(formatted_results)
    }

@app.get("/product/{product_id}")
def get_product(product_id: int):
    """Get product details by ID."""
    product = vector_store.get_product_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
    
    # Format product
    formatted_product = format_product_results([product])[0]
    
    return formatted_product

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)