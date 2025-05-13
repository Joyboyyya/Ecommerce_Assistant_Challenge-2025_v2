import pandas as pd
from typing import List, Dict, Any, Optional


import pandas as pd
import numpy as np

def format_product_results(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format product results for API response."""
    formatted_results = []

    for product in products:
        # Format price
        price = product.get('price')
        if price is not None and not pd.isna(price):
            product['price'] = round(float(price), 2)
        else:
            product['price'] = None

        # Format rating
        rating = product.get('average_rating')
        if rating is not None and not pd.isna(rating):
            product['average_rating'] = round(float(rating), 1)
        else:
            product['average_rating'] = None

        # Clean features
        if 'features' in product and isinstance(product['features'], str) and '\n' in product['features']:
            product['features'] = [f.strip() for f in product['features'].split('\n') if f.strip()]

        # ✅ Replace any remaining NaN/inf in the entire dict
        cleaned_product = {
            k: (None if isinstance(v, float) and (pd.isna(v) or np.isinf(v)) else v)
            for k, v in product.items()
        }

        formatted_results.append(cleaned_product)

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