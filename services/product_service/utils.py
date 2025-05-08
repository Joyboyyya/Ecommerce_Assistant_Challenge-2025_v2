import pandas as pd
from typing import List, Dict, Any, Optional

def format_product_results(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format product results for API response."""
    formatted_results = []
    
    for product in products:
        # Format price to two decimal places
        if 'price' in product and product['price'] is not None:
            product['price'] = round(float(product['price']), 2)
            
        # Format rating to one decimal place
        if 'average_rating' in product and product['average_rating'] is not None:
            product['average_rating'] = round(float(product['average_rating']), 1)
            
        # Clean up features text if present
        if 'features' in product and product['features']:
            # Split by newlines if necessary
            if isinstance(product['features'], str) and '\n' in product['features']:
                product['features'] = [f.strip() for f in product['features'].split('\n') if f.strip()]
        
        formatted_results.append(product)
        
    return formatted_results

def get_top_rated_products(df: pd.DataFrame, category: Optional[str] = None, 
                          min_rating: float = 4.5, top_k: int = 5) -> List[Dict[str, Any]]:
    """Get top-rated products, optionally filtered by category."""
    # Make a copy to avoid modifying the original
    filtered_df = df.copy()
    
    # Filter by category if provided
    if category:
        category_lower = category.lower()
        filtered_df = filtered_df[
            filtered_df['main_category'].str.lower().str.contains(category_lower, na=False)
        ]
        
    # Filter by minimum rating
    filtered_df = filtered_df[filtered_df['average_rating'] >= min_rating]
    
    # Sort by rating (descending) 
    filtered_df = filtered_df.sort_values(
        by=['average_rating'], 
        ascending=[False]
    )
    
    # Get top k results
    top_products = filtered_df.head(top_k)
    
    # Convert to list of dictionaries
    return top_products.to_dict(orient='records')