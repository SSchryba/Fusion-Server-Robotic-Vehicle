"""
Vector Memory System for Autonomous AI Agent Framework

Uses ChromaDB to store and retrieve agent memories, interactions,
and learned experiences with semantic search capabilities.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    SentenceTransformer = None

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Memory:
    """Represents a single memory entry"""
    id: str
    content: str
    memory_type: str  # 'interaction', 'observation', 'learning', 'goal', 'plan'
    timestamp: datetime
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    importance: float = 0.5  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary for storage."""
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'importance': self.importance,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """Create memory from dictionary."""
        return cls(
            id=data['id'],
            content=data['content'],
            memory_type=data['memory_type'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {}),
            importance=data.get('importance', 0.5),
            access_count=data.get('access_count', 0),
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None
        )


class VectorMemory:
    """
    Vector-based memory system using ChromaDB for semantic storage and retrieval.
    """
    
    def __init__(self, config_manager):
        """
        Initialize the vector memory system.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.memory_config = config_manager.memory_config
        
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB and sentence-transformers are required for VectorMemory")
        
        # Initialize ChromaDB client
        self.client = None
        self.collection = None
        self.embedding_model = None
        
        # Memory management
        self.memories: Dict[str, Memory] = {}
        self.memory_index = 0
        
        # Setup paths
        self.data_path = Path(self.memory_config.persistence_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self._initialize_chromadb()
        self._initialize_embedding_model()
        self._load_existing_memories()
        
        logger.info(f"Vector memory system initialized with {len(self.memories)} existing memories")
        
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            if self.memory_config.persistence_enabled:
                settings = Settings(
                    persist_directory=str(self.data_path),
                    anonymized_telemetry=False
                )
                self.client = chromadb.PersistentClient(settings=settings)
            else:
                self.client = chromadb.EphemeralClient()
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=self.memory_config.collection_name
                )
                logger.info(f"Using existing ChromaDB collection: {self.memory_config.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.memory_config.collection_name,
                    metadata={"description": "Autonomous agent memories"}
                )
                logger.info(f"Created new ChromaDB collection: {self.memory_config.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
            
    def _initialize_embedding_model(self):
        """Initialize the sentence transformer embedding model."""
        try:
            self.embedding_model = SentenceTransformer(self.memory_config.embedding_model)
            logger.info(f"Loaded embedding model: {self.memory_config.embedding_model}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
            
    def _load_existing_memories(self):
        """Load existing memories from ChromaDB."""
        try:
            # Get all memories from collection
            result = self.collection.get()
            
            if result and result['ids']:
                for i, memory_id in enumerate(result['ids']):
                    metadata = result['metadatas'][i] if result['metadatas'] else {}
                    
                    # Reconstruct memory object
                    memory_data = json.loads(metadata.get('memory_data', '{}'))
                    if memory_data:
                        memory = Memory.from_dict(memory_data)
                        self.memories[memory_id] = memory
                        
                logger.info(f"Loaded {len(self.memories)} existing memories")
                
        except Exception as e:
            logger.warning(f"Failed to load existing memories: {e}")
            
    def store_memory(self, content: str, memory_type: str, 
                    metadata: Optional[Dict[str, Any]] = None,
                    importance: float = 0.5) -> str:
        """
        Store a new memory in the vector database.
        
        Args:
            content: The content to store
            memory_type: Type of memory ('interaction', 'observation', etc.)
            metadata: Additional metadata
            importance: Importance score (0.0 to 1.0)
            
        Returns:
            Memory ID
        """
        try:
            # Create memory ID
            memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.memory_index}"
            self.memory_index += 1
            
            # Create memory object
            memory = Memory(
                id=memory_id,
                content=content,
                memory_type=memory_type,
                timestamp=datetime.now(),
                metadata=metadata or {},
                importance=importance
            )
            
            # Generate embedding
            embedding = self.embedding_model.encode(content).tolist()
            memory.embedding = embedding
            
            # Store in ChromaDB
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    'memory_type': memory_type,
                    'timestamp': memory.timestamp.isoformat(),
                    'importance': importance,
                    'memory_data': json.dumps(memory.to_dict())
                }]
            )
            
            # Store in local cache
            self.memories[memory_id] = memory
            
            # Check memory limits
            self._enforce_memory_limits()
            
            logger.info(f"Stored memory: {memory_id} ({memory_type})")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
            
    def retrieve_memories(self, query: str, limit: int = 10, 
                         memory_types: Optional[List[str]] = None,
                         min_importance: float = 0.0) -> List[Memory]:
        """
        Retrieve memories similar to the query.
        
        Args:
            query: Search query
            limit: Maximum number of memories to return
            memory_types: Filter by memory types
            min_importance: Minimum importance threshold
            
        Returns:
            List of similar memories
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Build filter criteria
            where_filter = {}
            if memory_types:
                where_filter['memory_type'] = {'$in': memory_types}
            if min_importance > 0.0:
                where_filter['importance'] = {'$gte': min_importance}
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter if where_filter else None
            )
            
            memories = []
            if results and results['ids']:
                for i, memory_id in enumerate(results['ids'][0]):
                    if memory_id in self.memories:
                        memory = self.memories[memory_id]
                        memory.access_count += 1
                        memory.last_accessed = datetime.now()
                        memories.append(memory)
                        
            logger.info(f"Retrieved {len(memories)} memories for query: {query[:50]}...")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
            
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a specific memory by ID."""
        memory = self.memories.get(memory_id)
        if memory:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
        return memory
        
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_id: ID of memory to update
            updates: Dictionary of updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            memory = self.memories.get(memory_id)
            if not memory:
                logger.warning(f"Memory not found for update: {memory_id}")
                return False
                
            # Apply updates
            for key, value in updates.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
                    
            # Update metadata if content changed
            if 'content' in updates:
                # Regenerate embedding
                embedding = self.embedding_model.encode(memory.content).tolist()
                memory.embedding = embedding
                
                # Update ChromaDB
                self.collection.update(
                    ids=[memory_id],
                    embeddings=[embedding],
                    documents=[memory.content],
                    metadatas=[{
                        'memory_type': memory.memory_type,
                        'timestamp': memory.timestamp.isoformat(),
                        'importance': memory.importance,
                        'memory_data': json.dumps(memory.to_dict())
                    }]
                )
            else:
                # Update metadata only
                self.collection.update(
                    ids=[memory_id],
                    metadatas=[{
                        'memory_type': memory.memory_type,
                        'timestamp': memory.timestamp.isoformat(),
                        'importance': memory.importance,
                        'memory_data': json.dumps(memory.to_dict())
                    }]
                )
                
            logger.info(f"Updated memory: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            return False
            
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        try:
            if memory_id in self.memories:
                del self.memories[memory_id]
                
            self.collection.delete(ids=[memory_id])
            logger.info(f"Deleted memory: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False
            
    def get_memories_by_type(self, memory_type: str, limit: int = 100) -> List[Memory]:
        """Get all memories of a specific type."""
        memories = [
            memory for memory in self.memories.values()
            if memory.memory_type == memory_type
        ]
        
        # Sort by importance and recency
        memories.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        return memories[:limit]
        
    def get_recent_memories(self, hours: int = 24, limit: int = 50) -> List[Memory]:
        """Get recent memories within the specified time window."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_memories = [
            memory for memory in self.memories.values()
            if memory.timestamp > cutoff
        ]
        
        recent_memories.sort(key=lambda m: m.timestamp, reverse=True)
        return recent_memories[:limit]
        
    def _enforce_memory_limits(self):
        """Enforce memory limits by removing old/unimportant memories."""
        if len(self.memories) <= self.memory_config.max_memories:
            return
            
        # Sort memories by importance and access patterns
        sorted_memories = sorted(
            self.memories.values(),
            key=lambda m: (
                m.importance * 0.4 +
                m.access_count * 0.3 +
                (1.0 if m.last_accessed and m.last_accessed > datetime.now() - timedelta(days=7) else 0.0) * 0.3
            ),
            reverse=False  # Lowest scores first (for removal)
        )
        
        # Remove least important memories
        memories_to_remove = len(self.memories) - self.memory_config.max_memories
        for memory in sorted_memories[:memories_to_remove]:
            self.delete_memory(memory.id)
            
        logger.info(f"Removed {memories_to_remove} memories to enforce limits")
        
    def search_memories(self, query_filters: Dict[str, Any], limit: int = 50) -> List[Memory]:
        """
        Search memories with complex filters.
        
        Args:
            query_filters: Dictionary of search criteria
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        results = []
        
        for memory in self.memories.values():
            if self._matches_filters(memory, query_filters):
                results.append(memory)
                
        # Sort by relevance (importance + recency)
        results.sort(
            key=lambda m: m.importance * 0.6 + 
                         (1.0 - (datetime.now() - m.timestamp).days / 365.0) * 0.4,
            reverse=True
        )
        
        return results[:limit]
        
    def _matches_filters(self, memory: Memory, filters: Dict[str, Any]) -> bool:
        """Check if memory matches the given filters."""
        for key, value in filters.items():
            if key == 'memory_type' and memory.memory_type != value:
                return False
            elif key == 'min_importance' and memory.importance < value:
                return False
            elif key == 'max_age_days':
                age_days = (datetime.now() - memory.timestamp).days
                if age_days > value:
                    return False
            elif key == 'contains' and value.lower() not in memory.content.lower():
                return False
            elif key == 'metadata_key' and value not in memory.metadata:
                return False
                
        return True
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory system."""
        if not self.memories:
            return {'total_memories': 0}
            
        total_memories = len(self.memories)
        memory_types = {}
        importance_sum = 0.0
        access_count_sum = 0
        
        for memory in self.memories.values():
            memory_types[memory.memory_type] = memory_types.get(memory.memory_type, 0) + 1
            importance_sum += memory.importance
            access_count_sum += memory.access_count
            
        return {
            'total_memories': total_memories,
            'memory_types': memory_types,
            'average_importance': importance_sum / total_memories,
            'total_access_count': access_count_sum,
            'collection_name': self.memory_config.collection_name,
            'embedding_model': self.memory_config.embedding_model,
            'persistence_enabled': self.memory_config.persistence_enabled
        }
        
    def backup_memories(self, backup_path: Optional[str] = None) -> str:
        """Create a backup of all memories."""
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.data_path / f"backup_memories_{timestamp}.json"
        else:
            backup_path = Path(backup_path)
            
        try:
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'total_memories': len(self.memories),
                'memories': [memory.to_dict() for memory in self.memories.values()]
            }
            
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
                
            logger.info(f"Created memory backup: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
            
    def restore_memories(self, backup_path: str) -> int:
        """Restore memories from backup."""
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
                
            restored_count = 0
            for memory_data in backup_data.get('memories', []):
                try:
                    memory = Memory.from_dict(memory_data)
                    
                    # Store restored memory
                    if memory.embedding:
                        self.collection.add(
                            ids=[memory.id],
                            embeddings=[memory.embedding],
                            documents=[memory.content],
                            metadatas=[{
                                'memory_type': memory.memory_type,
                                'timestamp': memory.timestamp.isoformat(),
                                'importance': memory.importance,
                                'memory_data': json.dumps(memory.to_dict())
                            }]
                        )
                        
                        self.memories[memory.id] = memory
                        restored_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to restore memory {memory_data.get('id', 'unknown')}: {e}")
                    
            logger.info(f"Restored {restored_count} memories from backup")
            return restored_count
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            raise
            
    def clear_all_memories(self):
        """Clear all memories (use with caution)."""
        try:
            # Clear ChromaDB collection
            self.collection.delete()
            
            # Clear local cache
            self.memories.clear()
            
            # Recreate collection
            self.collection = self.client.create_collection(
                name=self.memory_config.collection_name,
                metadata={"description": "Autonomous agent memories"}
            )
            
            logger.warning("All memories have been cleared")
            
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            raise 