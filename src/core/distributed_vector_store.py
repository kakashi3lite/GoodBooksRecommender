"""
Enhanced vector store implementation with distributed and scaling optimizations.
Supports hierarchical FAISS indices, sharding, and distributed vector databases.
"""

import asyncio
import pickle
import logging
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
import torch

# Optional distributed vector DB imports
try:
    from pymilvus import connections, Collection, DataType, CollectionSchema, FieldSchema
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

from src.core.logging import StructuredLogger
from src.core.exceptions import GoodBooksException
from src.config import Config

logger = StructuredLogger(__name__)

@dataclass
class VectorStoreConfig:
    """Configuration for vector store scaling and optimization."""
    vector_db_type: str = "faiss"  # faiss, milvus, pinecone
    enable_sharding: bool = True
    shard_size: int = 50000  # Number of vectors per shard
    enable_hierarchical: bool = True
    use_gpu: bool = False
    index_type: str = "ivf_hnsw"  # flat, ivf, hnsw, ivf_hnsw
    nlist: int = 1024  # Number of clusters for IVF
    m: int = 32  # Number of connections for HNSW
    efConstruction: int = 200
    efSearch: int = 128
    enable_compression: bool = True
    compression_bits: int = 8
    enable_async_operations: bool = True
    max_workers: int = 4

class DistributedVectorStore:
    """
    Distributed vector store with support for multiple backends and scaling optimizations.
    """
    
    def __init__(self, config: VectorStoreConfig, store_path: Optional[str] = None):
        """
        Initialize distributed vector store.
        
        Args:
            config: Vector store configuration
            store_path: Path to save/load the vector store
        """
        self.config = config
        self.store_path = Path(store_path) if store_path else Path("models/distributed_vector_store")
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.encoder = None
        self.dimension = 384  # Default for all-MiniLM-L6-v2
        self.shards = {}
        self.metadata_store = {}
        self.shard_mapping = {}  # Maps book_id to shard_id
        
        # Threading support
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self.lock = threading.RLock()
        
        # Initialize based on backend
        self._init_backend()
        self._init_encoder()
    
    def _init_backend(self) -> None:
        """Initialize the appropriate vector database backend."""
        if self.config.vector_db_type == "milvus" and MILVUS_AVAILABLE:
            self._init_milvus()
        elif self.config.vector_db_type == "pinecone" and PINECONE_AVAILABLE:
            self._init_pinecone()
        else:
            self._init_faiss()
            
    def _init_encoder(self) -> None:
        """Initialize the sentence transformer encoder."""
        try:
            device = 'cuda' if torch.cuda.is_available() and self.config.use_gpu else 'cpu'
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
            self.dimension = self.encoder.get_sentence_embedding_dimension()
            
            logger.info("Encoder initialized",
                       model="all-MiniLM-L6-v2",
                       device=device,
                       dimension=self.dimension)
        except Exception as e:
            logger.error("Failed to initialize encoder", error=str(e))
            raise
    
    def _init_faiss(self) -> None:
        """Initialize FAISS backend with optimizations."""
        self.backend_type = "faiss"
        logger.info("Initialized FAISS backend", config=self.config.__dict__)
    
    def _init_milvus(self) -> None:
        """Initialize Milvus backend."""
        try:
            # Connect to Milvus
            connections.connect("default", host="localhost", port="19530")
            
            # Define collection schema
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
                FieldSchema(name="book_id", dtype=DataType.INT64),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=1000)
            ]
            
            schema = CollectionSchema(fields, "GoodBooks vector collection")
            self.collection = Collection("goodbooks_vectors", schema)
            
            # Create index
            index_params = {
                "metric_type": "IP",  # Inner product for cosine similarity
                "index_type": "IVF_FLAT",
                "params": {"nlist": self.config.nlist}
            }
            self.collection.create_index("embedding", index_params)
            
            self.backend_type = "milvus"
            logger.info("Initialized Milvus backend")
            
        except Exception as e:
            logger.warning(f"Milvus initialization failed, falling back to FAISS: {str(e)}")
            self._init_faiss()
    
    def _init_pinecone(self) -> None:
        """Initialize Pinecone backend."""
        try:
            config = Config()
            api_key = getattr(config, 'PINECONE_API_KEY', None)
            environment = getattr(config, 'PINECONE_ENVIRONMENT', 'us-east-1-aws')
            
            if not api_key:
                raise ValueError("Pinecone API key not configured")
            
            pinecone.init(api_key=api_key, environment=environment)
            
            index_name = "goodbooks-vectors"
            
            # Create index if it doesn't exist
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    pod_type="p1.x1"  # Smallest pod for development
                )
            
            self.index = pinecone.Index(index_name)
            self.backend_type = "pinecone"
            logger.info("Initialized Pinecone backend")
            
        except Exception as e:
            logger.warning(f"Pinecone initialization failed, falling back to FAISS: {str(e)}")
            self._init_faiss()
    
    def _create_optimized_faiss_index(self, num_vectors: int) -> faiss.Index:
        """Create optimized FAISS index based on configuration and data size."""
        try:
            if self.config.index_type == "flat":
                index = faiss.IndexFlatIP(self.dimension)
                
            elif self.config.index_type == "ivf":
                quantizer = faiss.IndexFlatIP(self.dimension)
                nlist = min(self.config.nlist, max(1, num_vectors // 100))
                index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
                
            elif self.config.index_type == "hnsw":
                index = faiss.IndexHNSWFlat(self.dimension, self.config.m)
                index.hnsw.efConstruction = self.config.efConstruction
                index.hnsw.efSearch = self.config.efSearch
                
            elif self.config.index_type == "ivf_hnsw":
                # Hierarchical index for large datasets
                quantizer = faiss.IndexHNSWFlat(self.dimension, self.config.m)
                quantizer.hnsw.efConstruction = self.config.efConstruction
                nlist = min(self.config.nlist, max(1, num_vectors // 50))
                index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
                
            else:
                logger.warning(f"Unknown index type {self.config.index_type}, using IVF")
                quantizer = faiss.IndexFlatIP(self.dimension)
                nlist = min(self.config.nlist, max(1, num_vectors // 100))
                index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            
            # Add compression if enabled
            if self.config.enable_compression:
                compressed_index = faiss.IndexIVFPQ(
                    index.quantizer, self.dimension, index.nlist,
                    self.dimension // 8, self.config.compression_bits
                )
                index = compressed_index
            
            # GPU support if available
            if self.config.use_gpu and faiss.get_num_gpus() > 0:
                gpu_resources = faiss.StandardGpuResources()
                index = faiss.index_cpu_to_gpu(gpu_resources, 0, index)
                logger.info("Using GPU acceleration for FAISS")
            
            logger.info("Created optimized FAISS index",
                       index_type=self.config.index_type,
                       num_vectors=num_vectors,
                       compression=self.config.enable_compression,
                       gpu=self.config.use_gpu and faiss.get_num_gpus() > 0)
            
            return index
            
        except Exception as e:
            logger.error("Failed to create optimized index", error=str(e))
            # Fallback to simple flat index
            return faiss.IndexFlatIP(self.dimension)
    
    async def build_from_books_async(self, books_df: pd.DataFrame) -> None:
        """
        Build vector store from books DataFrame with sharding support.
        
        Args:
            books_df: DataFrame with book metadata
        """
        try:
            logger.info("Building distributed vector store", 
                       num_books=len(books_df),
                       sharding=self.config.enable_sharding)
            
            # Validate input
            required_columns = ['book_id', 'title', 'authors']
            missing_columns = set(required_columns) - set(books_df.columns)
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Prepare text content
            texts = await self._prepare_book_texts_async(books_df)
            
            if self.config.enable_sharding and len(books_df) > self.config.shard_size:
                await self._build_sharded_index(books_df, texts)
            else:
                await self._build_single_index(books_df, texts)
            
            # Save metadata and configuration
            await self._save_metadata(books_df)
            
            logger.info("Vector store build completed successfully")
            
        except Exception as e:
            logger.error("Failed to build vector store", error=str(e))
            raise
    
    async def _build_sharded_index(self, books_df: pd.DataFrame, texts: List[str]) -> None:
        """Build sharded index for large datasets."""
        num_shards = (len(books_df) + self.config.shard_size - 1) // self.config.shard_size
        
        logger.info(f"Building {num_shards} shards with {self.config.shard_size} vectors each")
        
        tasks = []
        for shard_id in range(num_shards):
            start_idx = shard_id * self.config.shard_size
            end_idx = min((shard_id + 1) * self.config.shard_size, len(books_df))
            
            shard_books = books_df.iloc[start_idx:end_idx]
            shard_texts = texts[start_idx:end_idx]
            
            task = self._build_shard(shard_id, shard_books, shard_texts)
            tasks.append(task)
        
        # Build shards in parallel
        await asyncio.gather(*tasks)
        
        # Update shard mapping
        for shard_id in range(num_shards):
            start_idx = shard_id * self.config.shard_size
            end_idx = min((shard_id + 1) * self.config.shard_size, len(books_df))
            
            for idx in range(start_idx, end_idx):
                book_id = books_df.iloc[idx]['book_id']
                self.shard_mapping[book_id] = shard_id
    
    async def _build_shard(self, shard_id: int, books_df: pd.DataFrame, texts: List[str]) -> None:
        """Build a single shard of the vector index."""
        try:
            # Generate embeddings for this shard
            embeddings = await self._generate_embeddings_async(texts)
            
            if self.backend_type == "faiss":
                # Create FAISS index for this shard
                index = self._create_optimized_faiss_index(len(embeddings))
                
                # Normalize for cosine similarity
                faiss.normalize_L2(embeddings)
                
                # Train if needed
                if hasattr(index, 'train') and not index.is_trained:
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor, index.train, embeddings
                    )
                
                # Add vectors
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, index.add, embeddings
                )
                
                self.shards[shard_id] = index
                
                # Save shard to disk
                shard_path = self.store_path / f"shard_{shard_id}.index"
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, faiss.write_index, index, str(shard_path)
                )
            
            elif self.backend_type == "milvus":
                # Insert into Milvus collection
                entities = [
                    [int(row['book_id']) * 1000 + i for i, row in books_df.iterrows()],  # Unique IDs
                    [int(row['book_id']) for _, row in books_df.iterrows()],
                    embeddings.tolist(),
                    [json.dumps({"title": row['title'], "authors": row['authors']}) 
                     for _, row in books_df.iterrows()]
                ]
                
                self.collection.insert(entities)
                self.collection.flush()
            
            elif self.backend_type == "pinecone":
                # Upsert to Pinecone
                vectors = []
                for i, (_, row) in enumerate(books_df.iterrows()):
                    vectors.append({
                        'id': f"book_{row['book_id']}_{shard_id}_{i}",
                        'values': embeddings[i].tolist(),
                        'metadata': {
                            'book_id': int(row['book_id']),
                            'title': row['title'],
                            'authors': row['authors'],
                            'shard_id': shard_id
                        }
                    })
                
                # Batch upsert
                batch_size = 100
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i + batch_size]
                    self.index.upsert(vectors=batch)
            
            # Store metadata for this shard
            shard_metadata = {}
            for i, (_, row) in enumerate(books_df.iterrows()):
                internal_id = i
                shard_metadata[internal_id] = {
                    'book_id': int(row['book_id']),
                    'title': row['title'],
                    'authors': row['authors'],
                    'original_text': texts[i]
                }
            
            self.metadata_store[shard_id] = shard_metadata
            
            logger.info(f"Built shard {shard_id} with {len(books_df)} vectors")
            
        except Exception as e:
            logger.error(f"Failed to build shard {shard_id}", error=str(e))
            raise
    
    async def _build_single_index(self, books_df: pd.DataFrame, texts: List[str]) -> None:
        """Build a single index for smaller datasets."""
        embeddings = await self._generate_embeddings_async(texts)
        
        if self.backend_type == "faiss":
            index = self._create_optimized_faiss_index(len(embeddings))
            
            faiss.normalize_L2(embeddings)
            
            if hasattr(index, 'train') and not index.is_trained:
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, index.train, embeddings
                )
            
            await asyncio.get_event_loop().run_in_executor(
                self.executor, index.add, embeddings
            )
            
            self.shards[0] = index
            
            # Save to disk
            index_path = self.store_path / "single.index"
            await asyncio.get_event_loop().run_in_executor(
                self.executor, faiss.write_index, index, str(index_path)
            )
        
        # Store metadata
        metadata = {}
        for i, (_, row) in enumerate(books_df.iterrows()):
            metadata[i] = {
                'book_id': int(row['book_id']),
                'title': row['title'],
                'authors': row['authors'],
                'original_text': texts[i]
            }
            self.shard_mapping[row['book_id']] = 0
        
        self.metadata_store[0] = metadata
    
    async def search_async(self, 
                          query: str, 
                          k: int = 10,
                          filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar books across all shards.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_criteria: Optional filtering criteria
            
        Returns:
            List of similar books with scores
        """
        try:
            # Generate query embedding
            query_embedding = await self._generate_query_embedding(query)
            
            if self.backend_type == "faiss":
                return await self._search_faiss(query_embedding, k, filter_criteria)
            elif self.backend_type == "milvus":
                return await self._search_milvus(query_embedding, k, filter_criteria)
            elif self.backend_type == "pinecone":
                return await self._search_pinecone(query_embedding, k, filter_criteria)
            else:
                raise ValueError(f"Unsupported backend: {self.backend_type}")
                
        except Exception as e:
            logger.error("Search failed", error=str(e))
            raise
    
    async def _search_faiss(self, 
                           query_embedding: np.ndarray, 
                           k: int,
                           filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search using FAISS backend."""
        all_results = []
        
        if self.config.enable_sharding and len(self.shards) > 1:
            # Search across all shards in parallel
            tasks = []
            for shard_id, index in self.shards.items():
                task = self._search_shard(shard_id, index, query_embedding, k * 2)  # Get more from each shard
                tasks.append(task)
            
            shard_results = await asyncio.gather(*tasks)
            
            # Combine and re-rank results
            for results in shard_results:
                all_results.extend(results)
            
            # Sort by score and take top k
            all_results.sort(key=lambda x: x['score'], reverse=True)
            all_results = all_results[:k]
        else:
            # Single shard search
            shard_id = 0
            index = self.shards[shard_id]
            all_results = await self._search_shard(shard_id, index, query_embedding, k)
        
        # Apply filters if specified
        if filter_criteria:
            all_results = self._apply_filters(all_results, filter_criteria)
        
        return all_results[:k]
    
    async def _search_shard(self, 
                           shard_id: int, 
                           index: faiss.Index, 
                           query_embedding: np.ndarray, 
                           k: int) -> List[Dict[str, Any]]:
        """Search a single FAISS shard."""
        try:
            # Normalize query for cosine similarity
            faiss.normalize_L2(query_embedding.reshape(1, -1))
            
            # Perform search
            scores, indices = await asyncio.get_event_loop().run_in_executor(
                self.executor, index.search, query_embedding.reshape(1, -1), k
            )
            
            results = []
            shard_metadata = self.metadata_store.get(shard_id, {})
            
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx >= 0 and idx in shard_metadata:  # Valid result
                    metadata = shard_metadata[idx]
                    results.append({
                        'book_id': metadata['book_id'],
                        'title': metadata['title'],
                        'authors': metadata['authors'],
                        'score': float(score),
                        'shard_id': shard_id,
                        'rank': i + 1
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed for shard {shard_id}", error=str(e))
            return []
    
    async def _search_milvus(self, 
                            query_embedding: np.ndarray, 
                            k: int,
                            filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search using Milvus backend."""
        try:
            search_params = {"metric_type": "IP", "params": {"nprobe": 10}}
            
            results = self.collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=k,
                output_fields=["book_id", "metadata"]
            )
            
            search_results = []
            for hit in results[0]:
                metadata = json.loads(hit.entity.get('metadata'))
                search_results.append({
                    'book_id': hit.entity.get('book_id'),
                    'title': metadata.get('title', ''),
                    'authors': metadata.get('authors', ''),
                    'score': float(hit.score),
                    'rank': len(search_results) + 1
                })
            
            return search_results
            
        except Exception as e:
            logger.error("Milvus search failed", error=str(e))
            return []
    
    async def _search_pinecone(self, 
                              query_embedding: np.ndarray, 
                              k: int,
                              filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search using Pinecone backend."""
        try:
            query_response = self.index.query(
                vector=query_embedding.tolist(),
                top_k=k,
                include_metadata=True,
                filter=filter_criteria
            )
            
            results = []
            for match in query_response['matches']:
                metadata = match['metadata']
                results.append({
                    'book_id': metadata['book_id'],
                    'title': metadata['title'],
                    'authors': metadata['authors'],
                    'score': float(match['score']),
                    'rank': len(results) + 1
                })
            
            return results
            
        except Exception as e:
            logger.error("Pinecone search failed", error=str(e))
            return []
    
    async def _prepare_book_texts_async(self, books_df: pd.DataFrame) -> List[str]:
        """Prepare text content for embedding generation."""
        def prepare_text(row):
            parts = [str(row['title'])]
            
            if 'authors' in row and pd.notna(row['authors']):
                parts.append(f"by {row['authors']}")
            
            if 'description' in row and pd.notna(row['description']):
                parts.append(str(row['description'])[:500])  # Limit description length
            
            if 'tags' in row and pd.notna(row['tags']):
                parts.append(f"Tags: {row['tags']}")
            
            return " ".join(parts)
        
        # Parallel text preparation
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.executor, prepare_text, row)
            for _, row in books_df.iterrows()
        ]
        
        texts = await asyncio.gather(*tasks)
        return texts
    
    async def _generate_embeddings_async(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts in batches."""
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Generate embeddings in executor to avoid blocking
            embeddings = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.encoder.encode, batch_texts
            )
            
            all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings)
    
    async def _generate_query_embedding(self, query: str) -> np.ndarray:
        """Generate embedding for a search query."""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, self.encoder.encode, [query]
        )[0]
    
    def _apply_filters(self, results: List[Dict[str, Any]], filter_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filtering criteria to search results."""
        filtered = []
        
        for result in results:
            include = True
            
            # Example filters
            if 'min_score' in filter_criteria:
                if result['score'] < filter_criteria['min_score']:
                    include = False
            
            if 'author_contains' in filter_criteria:
                if filter_criteria['author_contains'].lower() not in result['authors'].lower():
                    include = False
            
            if include:
                filtered.append(result)
        
        return filtered
    
    async def _save_metadata(self, books_df: pd.DataFrame) -> None:
        """Save vector store metadata and configuration."""
        metadata = {
            'config': self.config.__dict__,
            'backend_type': self.backend_type,
            'dimension': self.dimension,
            'num_books': len(books_df),
            'num_shards': len(self.shards),
            'shard_mapping': self.shard_mapping,
            'created_at': datetime.now().isoformat()
        }
        
        metadata_path = self.store_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save detailed metadata
        detailed_metadata_path = self.store_path / "detailed_metadata.pkl"
        with open(detailed_metadata_path, 'wb') as f:
            pickle.dump(self.metadata_store, f)
    
    async def load_async(self) -> bool:
        """Load existing vector store from disk."""
        try:
            metadata_path = self.store_path / "metadata.json"
            
            if not metadata_path.exists():
                return False
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.backend_type = metadata['backend_type']
            self.dimension = metadata['dimension']
            self.shard_mapping = metadata['shard_mapping']
            
            # Load detailed metadata
            detailed_metadata_path = self.store_path / "detailed_metadata.pkl"
            if detailed_metadata_path.exists():
                with open(detailed_metadata_path, 'rb') as f:
                    self.metadata_store = pickle.load(f)
            
            # Load shards based on backend
            if self.backend_type == "faiss":
                await self._load_faiss_shards(metadata['num_shards'])
            
            logger.info("Vector store loaded successfully",
                       backend=self.backend_type,
                       num_shards=metadata['num_shards'],
                       num_books=metadata['num_books'])
            
            return True
            
        except Exception as e:
            logger.error("Failed to load vector store", error=str(e))
            return False
    
    async def _load_faiss_shards(self, num_shards: int) -> None:
        """Load FAISS shards from disk."""
        if num_shards == 1:
            # Single index
            index_path = self.store_path / "single.index"
            if index_path.exists():
                index = await asyncio.get_event_loop().run_in_executor(
                    self.executor, faiss.read_index, str(index_path)
                )
                self.shards[0] = index
        else:
            # Multiple shards
            for shard_id in range(num_shards):
                shard_path = self.store_path / f"shard_{shard_id}.index"
                if shard_path.exists():
                    index = await asyncio.get_event_loop().run_in_executor(
                        self.executor, faiss.read_index, str(shard_path)
                    )
                    self.shards[shard_id] = index
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics and health information."""
        return {
            'backend_type': self.backend_type,
            'num_shards': len(self.shards),
            'total_vectors': sum(len(self.metadata_store.get(shard_id, {})) for shard_id in self.shards.keys()),
            'dimension': self.dimension,
            'config': self.config.__dict__,
            'memory_usage_mb': sum(
                shard.ntotal * self.dimension * 4 / (1024 * 1024) 
                for shard in self.shards.values() 
                if hasattr(shard, 'ntotal')
            ) if self.backend_type == "faiss" else 0
        }
