# product_service/vector_store.py

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import os
import pickle
from typing import List, Dict, Any, Optional

class ProductVectorStore:
    """
    Vector store for product information retrieval.
    Uses embeddings to perform semantic search on product data.
    """
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """Initialize the vector store with a model for embeddings."""
        # Initialize model, index, and other necessary components
        self.model_name = model_name
        self.model = SentenceTransformer(self.model_name)
        self.embeddings = None
        self.product_ids = None
    
    def load_data(self, file_path):
        """Load product data from CSV file."""
        
        try: 
            df = pd.read_csv(file_path)
            self.product_df = df

            print(f"Loaded {len(df)} products from {file_path}")

            return self.preprocess_data(df)
        
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def preprocess_data(self, df=None):
        """Preprocess product data for embedding generation."""
        if df is None: 
            df = self.product_df

        # Create a copy to avoid modifying the original
        processed_df = df.copy()
        
        # Generate product IDs if they don't exist
        if "product_id" not in processed_df.columns:
            processed_df["product_id"] = processed_df.index

        # Check for duplicate titles and remove duplicates
        duplicate_count = processed_df.duplicated(subset = ['title'], keep = 'first').sum()
        if duplicate_count > 0:
            print(f"Found {duplicate_count} duplicate products - keeping only first occurrences")
            processed_df = processed_df.drop_duplicates(subset = ['title'], keep = 'first')
        
        # Fill missing values in text fields
        text_columns = ['title', 'description', 'features', 'categories', 'details']
        for col in text_columns:
            if col in processed_df.columns:
                processed_df[col] = processed_df[col].fillna('')
        
        # Normalize text - lowercase, remove extra whitespace
        for col in text_columns:
            if col in processed_df.columns:
                processed_df[col] = processed_df[col].str.lower().str.strip()
        
        # Store processed dataframe
        self.product_df = processed_df
        self.product_ids = processed_df['product_id'].tolist()

        return processed_df

    
    def create_embeddings(self):
        """Generate embeddings for product data."""

        # Ensure we have data to embed
        if self.product_df is None or len(self.product_df) == 0:
            print("No data available for embedding generation")
            return None
        
        # Get all text columns 
        text_columns = ['main_category', 'title', 'features', 'description', 'categories', 'details']
        
        # Create text representations by combining all fields
        print("Creating text representations for embedding...")
        product_texts = []
        
        for _, row in self.product_df.iterrows():
            # Combine all text fields into one string
            text_parts = []
            for col in text_columns:
                if col in row and not pd.isna(row[col]) and row[col]:
                    text_parts.append(f"{col}: {row[col]}")
            
            # Add numeric information
            if 'average_rating' in row and not pd.isna(row['average_rating']):
                text_parts.append(f"rating: {row['average_rating']}")
            
            if 'price' in row and not pd.isna(row['price']):
                text_parts.append(f"price: {row['price']}")
    
            if ('imputed_columns' in row and row['imputed_columns'] != None and row['imputed_columns']!= []):
                text_parts.append(f"imputed_columns: {row['imputed_columns']}")
            
            # Combine all parts with spaces
            product_text = " ".join(text_parts)
            product_texts.append(product_text)
        
        # Generate embeddings
        print(f"Generating embeddings for {len(product_texts)} products...")
        try:
            embeddings = self.model.encode(product_texts)
            self.embeddings = embeddings
            
            print(f"Successfully created embeddings of shape {embeddings.shape}")
            return embeddings
        
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return None
    
    def build_index(self):
        """Build search index from embeddings."""
        # Check if embeddings exist
        if self.embeddings is None:
            print("No embeddings available. Call create_embeddings() first.")
            return None
        
        try:
            # Get embedding dimensions
            vector_dimension = self.embeddings.shape[1]
            
            # Create a new index with the correct dimensions
            self.index = faiss.IndexFlatL2(vector_dimension)
            
            # Add the embeddings to the index
            self.index.add(self.embeddings)
            
            print(f"Successfully built index with {self.index.ntotal} vectors")
            return self.index
        
        except Exception as e:
            print(f"Error building index: {e}")
            return None
    
    def save_index(self, index_path, data_path):
        """
        Save the FAISS index and product data to disk.

        Args:
            index_path: Path to save the FAISS index
            data_path: Path to save the product data

        Returns:
            bool: True if saving was successful, False otherwise
        """
        # Check if index exists
        if self.index is None:
            print("No index available to save. Call build_index() first.")
            return False

        try:
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            os.makedirs(os.path.dirname(data_path), exist_ok=True)

            # Save the FAISS index
            faiss.write_index(self.index, index_path)

            # Save the embeddings
            if self.embeddings is not None:
                embeddings_path = os.path.splitext(index_path)[0] + "_embeddings.npy"
                np.save(embeddings_path, self.embeddings)
                print(f"Embeddings saved to {embeddings_path}")

            # Save the product dataframe
            self.product_df.to_pickle(data_path)

            print(f"Index saved to {index_path}")
            print(f"Product data saved to {data_path}")
            return True

        except Exception as e:
            print(f"Error saving index: {e}")
            return False
    
    def load_index(self, index_path, data_path):
        """
        Load a FAISS index and product data from disk.

        Args:
            index_path: Path to the saved FAISS index
            data_path: Path to the saved product data

        Returns:
            bool: True if loading was successful, False otherwise
        """
        try:
            # Load the FAISS index
            self.index = faiss.read_index(index_path)

            # Load the embeddings if available
            embeddings_path = os.path.splitext(index_path)[0] + "_embeddings.npy"
            if os.path.exists(embeddings_path):
                self.embeddings = np.load(embeddings_path)
                print(f"Loaded embeddings of shape {self.embeddings.shape}")

            # Load the product dataframe
            self.product_df = pd.read_pickle(data_path)

            # Recreate product_ids
            if 'product_id' in self.product_df.columns:
                self.product_ids = self.product_df['product_id'].tolist()
            else:
                self.product_ids = list(range(len(self.product_df)))

            print(f"Loaded index with {self.index.ntotal} vectors")
            print(f"Loaded {len(self.product_df)} products")
            return True

        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    def search(self, query, top_k=5):
        """
        Search for products similar to the query.

        Args:
            query: Text query to search for
            top_k: Number of results to return

        Returns:
            List of dictionaries containing product information
        """
        # Check if index exists
        if self.index is None:
            print("No index available. Call build_index() first.")
            return []

        try:
            # Convert query to embedding
            query_embedding = self.model.encode([query])

            # Normalize the query embedding for cosine similarity
            faiss.normalize_L2(query_embedding)

            # Search the index
            distances, indices = self.index.search(query_embedding, top_k)

            # Fetch the actual product data
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.product_df):
                    # Get the product data
                    product = self.product_df.iloc[idx].to_dict()

                    # Add distance score (lower is better for L2 distance)
                    product['search_score'] = float(distances[0][i])

                    # Add to results
                    results.append(product)

            print(f"Found {len(results)} products matching the query: '{query}'")
            return results

        except Exception as e:
            print(f"Error searching index: {e}")
            return []
    
    def search_by_category(self, query, category, top_k=5):
        """
        Search for products within a specific category.
        
        Args:
            query: Text query to search for
            category: Category to filter by
            top_k: Number of results to return
        
        Returns:
            List of dictionaries containing product information
        """
        # First get more results than we need
        results = self.search(query, top_k=top_k*3)
        
        # Filter by category
        filtered_results = []
        for product in results:
            if 'main_category' in product and product['main_category'] == category:
                filtered_results.append(product)

        
        # Return the top k results
        return filtered_results[:top_k]

    def get_product_by_id(self, product_id):
        """
        Retrieve product details by ID.

        Args:
            product_id: ID of the product to retrieve

        Returns:
            Dictionary containing product information, or None if not found
        """
        # Check if we have product data
        if self.product_df is None: 
            print("No product data available.")
            return None

        try:
            # Find the product by ID
            if 'product_id' in self.product_df.columns:
                product = self.product_df[self.product_df['product_id'] == product_id]

                # If product found, return it as a dictionary
                if not product.empty:
                    return product.iloc[0].to_dict()

            # If we reach here, the product wasn't found
            print(f"Product with ID {product_id} not found.")
            return None

        except Exception as e:
            print(f"Error retrieving product: {e}")
            return None