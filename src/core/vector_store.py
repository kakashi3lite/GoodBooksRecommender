"""
FAISS vector store implementation for book metadata with RAG capabilities.
Provides semantic search over book content for explanations and recommendations.
"""

import asyncio
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
import torch

from src.core.logging import StructuredLogger
from src.core.exceptions import GoodBooksException

logger = StructuredLogger(__name__)

class VectorStoreError(GoodBooksException):
    """Raised when vector store operations fail"""
    pass

class BookVectorStore:
    """
    FAISS-based vector store for book metadata with semantic search capabilities.
    Supports both content-based and metadata-based retrieval for RAG applications.
    """
    
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2",
        dimension: int = 384,
        index_type: str = "flat",
        store_path: Optional[str] = None
    ):
        """
        Initialize the vector store.
        
        Args:
            model_name: SentenceTransformer model name for embeddings
            dimension: Embedding dimension
            index_type: FAISS index type ('flat', 'ivf', 'hnsw')
            store_path: Path to save/load the vector store
        """
        self.model_name = model_name
        self.dimension = dimension
        self.index_type = index_type
        self.store_path = Path(store_path) if store_path else Path("models/vector_store")
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.encoder = None
        self.index = None
        self.book_metadata: Dict[int, Dict[str, Any]] = {}
        self.id_to_book_id: Dict[int, int] = {}
        self.book_id_to_id: Dict[int, int] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize encoder
        self._init_encoder()
        
    def _init_encoder(self) -> None:
        """Initialize the sentence transformer encoder."""
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.encoder = SentenceTransformer(self.model_name, device=device)
            logger.info(
                "Sentence transformer initialized",
                model=self.model_name,
                device=device,
                dimension=self.dimension
            )
        except Exception as e:
            logger.error("Failed to initialize sentence transformer", error=str(e))
            raise VectorStoreError(f"Failed to initialize encoder: {str(e)}") from e
    
    def _create_index(self, num_vectors: int) -> faiss.Index:
        """Create FAISS index based on configuration."""
        try:
            if self.index_type == "flat":
                index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
            elif self.index_type == "ivf":
                quantizer = faiss.IndexFlatIP(self.dimension)
                nlist = min(100, max(1, num_vectors // 100))  # Adaptive nlist
                index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            elif self.index_type == "hnsw":
                index = faiss.IndexHNSWFlat(self.dimension, 32)
                index.hnsw.efConstruction = 200
                index.hnsw.efSearch = 128
            else:
                raise VectorStoreError(f"Unsupported index type: {self.index_type}")
            
            logger.info(
                "FAISS index created",
                index_type=self.index_type,
                dimension=self.dimension,
                num_vectors=num_vectors
            )
            return index
            
        except Exception as e:
            logger.error("Failed to create FAISS index", error=str(e))
            raise VectorStoreError(f"Failed to create index: {str(e)}") from e
    
    async def build_from_books_async(self, books_df: pd.DataFrame) -> None:
        """
        Build vector store from books DataFrame asynchronously.
        
        Args:
            books_df: DataFrame with book metadata including text content
            
        Raises:
            VectorStoreError: If building the vector store fails
        """
        try:
            logger.info("Starting vector store build", num_books=len(books_df))
            
            # Validate input
            required_columns = ['book_id', 'title', 'authors']
            missing_columns = set(required_columns) - set(books_df.columns)
            if missing_columns:
                raise VectorStoreError(f"Missing required columns: {missing_columns}")
            
            if books_df.empty:
                raise VectorStoreError("Books DataFrame cannot be empty")
            
            # Prepare text content for embedding
            texts = await self._prepare_book_texts_async(books_df)
            
            # Generate embeddings
            embeddings = await self._generate_embeddings_async(texts)
            
            # Create and populate index
            self.index = self._create_index(len(embeddings))
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to index
            if self.index_type == "ivf":
                # Train IVF index
                await asyncio.get_event_loop().run_in_executor(
                    self._executor, self.index.train, embeddings
                )
            
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self.index.add, embeddings
            )
            
            # Store metadata mappings
            self._build_metadata_mappings(books_df)
            
            # Save to disk
            await self.save_async()
            
            logger.info(
                "Vector store build completed",
                num_vectors=self.index.ntotal,
                index_type=self.index_type
            )
            
        except Exception as e:
            logger.error("Vector store build failed", error=str(e), exc_info=True)
            raise VectorStoreError(f"Failed to build vector store: {str(e)}") from e
    
    async def _prepare_book_texts_async(self, books_df: pd.DataFrame) -> List[str]:
        """Prepare text content from books for embedding generation."""
        texts = []
        
        for _, book in books_df.iterrows():
            # Combine multiple text fields
            text_parts = []
            
            # Title and authors are required
            text_parts.append(f"Title: {book['title']}")
            text_parts.append(f"Authors: {book['authors']}")
            
            # Add optional fields if available
            if 'description' in book and pd.notna(book['description']):
                text_parts.append(f"Description: {book['description'][:500]}")  # Truncate
            
            if 'all_tags' in book and pd.notna(book['all_tags']):
                text_parts.append(f"Tags: {book['all_tags']}")
            
            if 'genres' in book and pd.notna(book['genres']):
                text_parts.append(f"Genres: {book['genres']}")
            
            if 'average_rating' in book and pd.notna(book['average_rating']):
                text_parts.append(f"Rating: {book['average_rating']}")
            
            # Combine all text parts
            combined_text = " | ".join(text_parts)
            texts.append(combined_text)
        
        return texts
    
    async def _generate_embeddings_async(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts asynchronously."""
        try:
            logger.info("Generating embeddings", num_texts=len(texts))
            
            # Use thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self._executor,
                self._encode_texts,
                texts
            )
            
            logger.info(
                "Embeddings generated",
                shape=embeddings.shape,
                dtype=embeddings.dtype
            )
            
            return embeddings
            
        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            raise VectorStoreError(f"Failed to generate embeddings: {str(e)}") from e
    
    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        """Encode texts using sentence transformer."""
        # Batch processing for efficiency
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.encoder.encode(
                batch,
                normalize_embeddings=False,  # We'll normalize later
                show_progress_bar=False
            )
            all_embeddings.append(batch_embeddings)
        
        return np.vstack(all_embeddings).astype(np.float32)
    
    def _build_metadata_mappings(self, books_df: pd.DataFrame) -> None:
        """Build metadata mappings for book lookups."""
        self.book_metadata = {}
        self.id_to_book_id = {}
        self.book_id_to_id = {}
        
        for idx, (_, book) in enumerate(books_df.iterrows()):
            book_id = int(book['book_id'])
            
            # Store metadata
            self.book_metadata[idx] = {
                'book_id': book_id,
                'title': book['title'],
                'authors': book['authors'],
                'average_rating': book.get('average_rating', 0),
                'description': book.get('description', ''),
                'all_tags': book.get('all_tags', ''),
                'genres': book.get('genres', ''),
                'publication_year': book.get('publication_year', None)
            }
            
            # Store ID mappings
            self.id_to_book_id[idx] = book_id
            self.book_id_to_id[book_id] = idx
    
    async def semantic_search_async(
        self, 
        query: str, 
        k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search over book vectors.
        
        Args:
            query: Search query string
            k: Number of results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of search results with metadata and scores
            
        Raises:
            VectorStoreError: If search fails
        """
        try:
            if self.index is None:
                raise VectorStoreError("Vector store not initialized. Call build_from_books_async first.")
            
            logger.info("Performing semantic search", query=query[:100], k=k)
            
            # Generate query embedding
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                self._executor,
                lambda: self.encoder.encode([query], normalize_embeddings=False)
            )
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = await loop.run_in_executor(
                self._executor,
                self.index.search,
                query_embedding,
                k
            )
            
            # Process results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue
                
                if score < score_threshold:
                    continue
                
                metadata = self.book_metadata.get(idx, {})
                results.append({
                    'book_id': metadata.get('book_id'),
                    'title': metadata.get('title'),
                    'authors': metadata.get('authors'),
                    'similarity_score': float(score),
                    'metadata': metadata
                })
            
            logger.info("Semantic search completed", num_results=len(results))
            return results
            
        except Exception as e:
            logger.error("Semantic search failed", query=query[:100], error=str(e))
            raise VectorStoreError(f"Search failed: {str(e)}") from e
    
    async def get_similar_books_async(
        self, 
        book_id: int, 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get books similar to a given book ID.
        
        Args:
            book_id: ID of the book to find similarities for
            k: Number of similar books to return
            
        Returns:
            List of similar books with metadata and scores
        """
        try:
            if book_id not in self.book_id_to_id:
                logger.warning("Book not found in vector store", book_id=book_id)
                return []
            
            vector_id = self.book_id_to_id[book_id]
            
            # Get the book's vector
            book_vector = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: self.index.reconstruct(vector_id).reshape(1, -1)
            )
            
            # Search for similar vectors (k+1 to exclude the book itself)
            scores, indices = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self.index.search,
                book_vector,
                k + 1
            )
            
            # Process results, excluding the input book
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1 or idx == vector_id:  # Skip invalid indices and self
                    continue
                
                metadata = self.book_metadata.get(idx, {})
                results.append({
                    'book_id': metadata.get('book_id'),
                    'title': metadata.get('title'),
                    'authors': metadata.get('authors'),
                    'similarity_score': float(score),
                    'metadata': metadata
                })
            
            return results[:k]  # Return exactly k results
            
        except Exception as e:
            logger.error("Similar books search failed", book_id=book_id, error=str(e))
            return []
    
    async def save_async(self) -> None:
        """Save vector store to disk asynchronously."""
        try:
            logger.info("Saving vector store", path=str(self.store_path))
            
            # Save FAISS index
            index_path = self.store_path / "faiss.index"
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                faiss.write_index,
                self.index,
                str(index_path)
            )
            
            # Save metadata
            metadata_path = self.store_path / "metadata.pkl"
            metadata = {
                'book_metadata': self.book_metadata,
                'id_to_book_id': self.id_to_book_id,
                'book_id_to_id': self.book_id_to_id,
                'model_name': self.model_name,
                'dimension': self.dimension,
                'index_type': self.index_type
            }
            
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info("Vector store saved successfully")
            
        except Exception as e:
            logger.error("Failed to save vector store", error=str(e))
            raise VectorStoreError(f"Failed to save vector store: {str(e)}") from e
    
    async def load_async(self) -> bool:
        """
        Load vector store from disk asynchronously.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            index_path = self.store_path / "faiss.index"
            metadata_path = self.store_path / "metadata.pkl"
            
            if not (index_path.exists() and metadata_path.exists()):
                logger.info("Vector store files not found", path=str(self.store_path))
                return False
            
            logger.info("Loading vector store", path=str(self.store_path))
            
            # Load FAISS index
            self.index = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                faiss.read_index,
                str(index_path)
            )
            
            # Load metadata
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.book_metadata = metadata['book_metadata']
            self.id_to_book_id = metadata['id_to_book_id']
            self.book_id_to_id = metadata['book_id_to_id']
            
            # Verify consistency
            if (metadata['model_name'] != self.model_name or 
                metadata['dimension'] != self.dimension):
                logger.warning(
                    "Model configuration mismatch",
                    stored_model=metadata['model_name'],
                    current_model=self.model_name
                )
            
            logger.info(
                "Vector store loaded successfully",
                num_vectors=self.index.ntotal,
                num_books=len(self.book_metadata)
            )
            return True
            
        except Exception as e:
            logger.error("Failed to load vector store", error=str(e))
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            'num_vectors': self.index.ntotal if self.index else 0,
            'num_books': len(self.book_metadata),
            'dimension': self.dimension,
            'index_type': self.index_type,
            'model_name': self.model_name,
            'is_trained': self.index.is_trained if self.index else False
        }
    
    def __del__(self):
        """Cleanup thread pool executor."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)
