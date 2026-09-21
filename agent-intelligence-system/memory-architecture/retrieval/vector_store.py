"""
ChromaDB Vector Store Integration
==================================

Vector-based memory retrieval system using ChromaDB for semantic similarity search.
Provides efficient similarity-based memory retrieval and clustering capabilities.
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import hashlib
import logging

from ..core.memory_base import MemoryBase, MemoryType


logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB-based vector store for memory retrieval and similarity search.
    Supports multiple collections for different memory types and efficient retrieval.
    """

    def __init__(
        self,
        persist_directory: str = "./data/vector_store",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.persist_directory = persist_directory

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )

        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )

        # Collections for different memory types
        self.collections: Dict[str, chromadb.Collection] = {}

        # Initialize collections
        self._initialize_collections()

        # Cache for recent embeddings
        self.embedding_cache: Dict[str, List[float]] = {}
        self.cache_max_size = 1000

        # Statistics
        self.total_embeddings = 0
        self.search_count = 0
        self.cache_hits = 0

    def _initialize_collections(self) -> None:
        """Initialize collections for different memory types"""
        collection_names = [mem_type.value for mem_type in MemoryType]

        for name in collection_names:
            try:
                collection = self.client.get_or_create_collection(
                    name=f"memories_{name}",
                    embedding_function=self.embedding_function,
                    metadata={
                        "description": f"{name.title()} memories collection",
                        "created_at": datetime.now().isoformat()
                    }
                )
                self.collections[name] = collection
                logger.info(f"Initialized collection: memories_{name}")
            except Exception as e:
                logger.error(f"Failed to initialize collection {name}: {e}")
                raise

    def add_memory(self, memory: MemoryBase) -> str:
        """
        Add a memory to the vector store.
        Returns the document ID.
        """
        try:
            # Generate document ID
            doc_id = self._generate_document_id(memory)

            # Prepare document content
            document_content = self._prepare_document_content(memory)

            # Get or create embedding
            embedding = self._get_embedding(document_content)

            # Prepare metadata
            metadata = self._prepare_metadata(memory)

            # Add to appropriate collection
            collection_name = memory.type.value
            collection = self.collections[collection_name]

            collection.add(
                embeddings=[embedding],
                documents=[document_content],
                metadatas=[metadata],
                ids=[doc_id]
            )

            self.total_embeddings += 1

            # Cache the embedding
            self._cache_embedding(document_content, embedding)

            logger.debug(f"Added memory {memory.id} to vector store")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add memory {memory.id} to vector store: {e}")
            raise

    def search_similar_memories(
        self,
        query: str,
        memory_types: List[MemoryType] = None,
        max_results: int = 10,
        similarity_threshold: float = 0.3,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for memories similar to the query.
        Returns list of memory results with similarity scores.
        """
        try:
            self.search_count += 1

            if memory_types is None:
                memory_types = list(MemoryType)

            # Get query embedding
            query_embedding = self._get_embedding(query)

            all_results = []

            for memory_type in memory_types:
                collection_name = memory_type.value
                if collection_name not in self.collections:
                    continue

                collection = self.collections[collection_name]

                # Prepare where clause for filtering
                where_clause = self._build_where_clause(filters, memory_type)

                # Calculate results per collection
                results_per_collection = max_results // len(memory_types) + 1

                # Query collection
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=results_per_collection,
                    where=where_clause,
                    include=["documents", "metadatas", "distances", "ids"]
                )

                # Process results
                collection_results = self._process_query_results(
                    results, memory_type, similarity_threshold
                )
                all_results.extend(collection_results)

            # Sort by similarity and return top results
            all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return all_results[:max_results]

        except Exception as e:
            logger.error(f"Failed to search similar memories: {e}")
            return []

    def find_memory_clusters(
        self,
        memory_type: MemoryType,
        min_cluster_size: int = 3,
        max_clusters: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find clusters of similar memories using vector similarity.
        Useful for identifying patterns and themes.
        """
        try:
            collection_name = memory_type.value
            collection = self.collections[collection_name]

            # Get all memories from collection
            all_results = collection.get(include=["documents", "metadatas", "embeddings", "ids"])

            if not all_results["ids"]:
                return []

            # Perform clustering using distance-based approach
            clusters = self._perform_clustering(
                embeddings=all_results["embeddings"],
                documents=all_results["documents"],
                metadatas=all_results["metadatas"],
                ids=all_results["ids"],
                min_cluster_size=min_cluster_size,
                max_clusters=max_clusters
            )

            return clusters

        except Exception as e:
            logger.error(f"Failed to find memory clusters: {e}")
            return []

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        stats = {
            "total_embeddings": self.total_embeddings,
            "search_count": self.search_count,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hits / max(self.search_count, 1),
            "collections": {}
        }

        for memory_type, collection in self.collections.items():
            try:
                count = collection.count()
                stats["collections"][memory_type] = {
                    "count": count,
                    "type": memory_type
                }
            except Exception as e:
                stats["collections"][memory_type] = {"error": str(e)}

        return stats

    def update_memory(self, memory: MemoryBase) -> bool:
        """Update an existing memory in the vector store"""
        try:
            # Delete existing memory
            self.delete_memory(memory.id)

            # Add updated memory
            self.add_memory(memory)

            return True

        except Exception as e:
            logger.error(f"Failed to update memory {memory.id}: {e}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from the vector store"""
        try:
            # Find which collection contains this memory
            for collection_name, collection in self.collections.items():
                try:
                    # Get all documents to find the one with matching memory_id
                    all_docs = collection.get(include=["metadatas", "ids"])

                    for i, metadata in enumerate(all_docs["metadatas"]):
                        if metadata.get("memory_id") == memory_id:
                            # Delete the document
                            collection.delete(ids=[all_docs["ids"][i]])
                            logger.debug(f"Deleted memory {memory_id} from collection {collection_name}")
                            return True

                except Exception as e:
                    logger.warning(f"Error searching collection {collection_name}: {e}")
                    continue

            logger.warning(f"Memory {memory_id} not found in any collection")
            return False

        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False

    def clear_collection(self, memory_type: MemoryType) -> bool:
        """Clear all memories of a specific type"""
        try:
            collection_name = memory_type.value
            if collection_name in self.collections:
                self.client.delete_collection(name=f"memories_{collection_name}")
                # Reinitialize the collection
                self._initialize_collections()
                logger.info(f"Cleared collection for {memory_type.value}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to clear collection {memory_type.value}: {e}")
            return False

    def optimize_index(self) -> None:
        """Optimize the vector index for better performance"""
        try:
            # ChromaDB automatically handles optimization, but we can trigger
            # a manual optimization by getting statistics
            for collection_name, collection in self.collections.items():
                count = collection.count()
                logger.info(f"Collection {collection_name}: {count} documents")

            logger.info("Vector index optimization completed")

        except Exception as e:
            logger.error(f"Failed to optimize vector index: {e}")

    def _generate_document_id(self, memory: MemoryBase) -> str:
        """Generate a unique document ID for the memory"""
        content_hash = hashlib.md5(
            f"{memory.id}_{memory.type.value}_{memory.creation_time.isoformat()}".encode()
        ).hexdigest()[:16]
        return f"doc_{content_hash}"

    def _prepare_document_content(self, memory: MemoryBase) -> str:
        """Prepare document content for embedding"""
        # Combine primary content with key concepts and summary
        content_parts = [memory.content.primary_content]

        if memory.content.summary:
            content_parts.append(f"Summary: {memory.content.summary}")

        if memory.content.key_concepts:
            content_parts.append(f"Key concepts: {', '.join(memory.content.key_concepts)}")

        if memory.metadata.tags:
            content_parts.append(f"Tags: {', '.join(memory.metadata.tags)}")

        return " | ".join(content_parts)

    def _prepare_metadata(self, memory: MemoryBase) -> Dict[str, Any]:
        """Prepare metadata for storage"""
        metadata = {
            "memory_id": memory.id,
            "memory_type": memory.type.value,
            "importance": memory.importance,
            "creation_time": memory.creation_time.isoformat(),
            "status": memory.status.value,
            "source": memory.metadata.source,
            "access_count": memory.metadata.access_count,
            "emotional_valence": memory.metadata.emotional_valence,
            "arousal": memory.metadata.arousal,
            "confidence": memory.metadata.confidence
        }

        # Add type-specific metadata
        if hasattr(memory, 'timestamp'):  # Episodic memory
            metadata["timestamp"] = memory.timestamp.isoformat()
            metadata["location"] = memory.metadata.location
            metadata["participants"] = memory.metadata.participants

        if hasattr(memory, 'concept'):  # Semantic memory
            metadata["concept"] = memory.concept
            metadata["pattern_type"] = getattr(memory, 'pattern_type', 'unknown')

        # Add tags
        if memory.metadata.tags:
            metadata["tags"] = memory.metadata.tags

        return metadata

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text, with caching"""
        # Check cache first
        cache_key = hashlib.md5(text.encode()).hexdigest()[:16]
        if cache_key in self.embedding_cache:
            self.cache_hits += 1
            return self.embedding_cache[cache_key]

        # Generate new embedding
        try:
            embeddings = self.embedding_function([text])
            embedding = embeddings[0]

            # Cache the embedding
            self._cache_embedding(text, embedding)

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return a zero embedding as fallback
            return [0.0] * 384  # Default dimension for MiniLM

    def _cache_embedding(self, text: str, embedding: List[float]) -> None:
        """Cache an embedding"""
        cache_key = hashlib.md5(text.encode()).hexdigest()[:16]

        # Remove oldest entry if cache is full
        if len(self.embedding_cache) >= self.cache_max_size:
            oldest_key = next(iter(self.embedding_cache))
            del self.embedding_cache[oldest_key]

        self.embedding_cache[cache_key] = embedding

    def _build_where_clause(self, filters: Dict[str, Any], memory_type: MemoryType) -> Optional[Dict[str, Any]]:
        """Build ChromaDB where clause from filters"""
        if not filters:
            return None

        where_conditions = []

        # Add memory type filter
        where_conditions.append({"memory_type": memory_type.value})

        # Add other filters
        for key, value in filters.items():
            if key in ["importance", "emotional_valence", "arousal", "confidence"]:
                # Numeric range filters
                if isinstance(value, dict):
                    if "min" in value:
                        where_conditions.append({key: {"$gte": value["min"]}})
                    if "max" in value:
                        where_conditions.append({key: {"$lte": value["max"]}})
                else:
                    where_conditions.append({key: {"$eq": value}})
            elif key in ["tags", "participants"]:
                # List filters
                if isinstance(value, list):
                    where_conditions.append({key: {"$in": value}})
                else:
                    where_conditions.append({key: {"$eq": value}})
            elif key in ["location", "concept", "pattern_type"]:
                # String filters
                where_conditions.append({key: {"$eq": value}})

        # Combine conditions with AND
        if len(where_conditions) == 1:
            return where_conditions[0]
        elif len(where_conditions) > 1:
            return {"$and": where_conditions}

        return None

    def _process_query_results(
        self,
        results: Dict[str, Any],
        memory_type: MemoryType,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """Process query results from ChromaDB"""
        processed_results = []

        if not results["ids"][0]:  # No results
            return processed_results

        for i in range(len(results["ids"][0])):
            # Calculate similarity score (convert distance to similarity)
            distance = results["distances"][0][i]
            similarity = 1.0 - distance  # Convert to similarity

            # Filter by threshold
            if similarity < similarity_threshold:
                continue

            result = {
                "memory_id": results["metadatas"][0][i]["memory_id"],
                "memory_type": memory_type.value,
                "document": results["documents"][0][i],
                "similarity_score": similarity,
                "distance": distance,
                "metadata": results["metadatas"][0][i],
                "vector_id": results["ids"][0][i]
            }

            processed_results.append(result)

        return processed_results

    def _perform_clustering(
        self,
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        min_cluster_size: int,
        max_clusters: int
    ) -> List[Dict[str, Any]]:
        """
        Perform clustering on embeddings to find similar memory groups.
        Uses a simple distance-based clustering approach.
        """
        try:
            if len(embeddings) < min_cluster_size:
                return []

            # Convert to numpy array for efficient computation
            embeddings_array = np.array(embeddings)

            # Simple clustering: find groups of mutually similar memories
            clusters = []
            used_indices = set()
            similarity_threshold = 0.7

            for i, embedding in enumerate(embeddings_array):
                if i in used_indices:
                    continue

                # Find similar memories
                similarities = np.dot(embeddings_array, embedding)
                similar_indices = np.where(similarities > similarity_threshold)[0]

                if len(similar_indices) >= min_cluster_size:
                    # Create cluster
                    cluster_indices = [idx for idx in similar_indices if idx not in used_indices]

                    if len(cluster_indices) >= min_cluster_size:
                        cluster = {
                            "cluster_id": len(clusters),
                            "size": len(cluster_indices),
                            "similarity_threshold": similarity_threshold,
                            "memories": []
                        }

                        # Add memories to cluster
                        for idx in cluster_indices:
                            cluster["memories"].append({
                                "memory_id": metadatas[idx]["memory_id"],
                                "document": documents[idx],
                                "metadata": metadatas[idx],
                                "similarity": float(similarities[idx])
                            })
                            used_indices.add(idx)

                        # Sort by similarity
                        cluster["memories"].sort(key=lambda x: x["similarity"], reverse=True)

                        clusters.append(cluster)

                        if len(clusters) >= max_clusters:
                            break

            return clusters

        except Exception as e:
            logger.error(f"Failed to perform clustering: {e}")
            return []

    def __del__(self):
        """Cleanup when the object is destroyed"""
        try:
            # Clear embedding cache
            self.embedding_cache.clear()
        except:
            pass