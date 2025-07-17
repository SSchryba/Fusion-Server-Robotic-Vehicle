"""
Quantum Knowledge Ingestor for Autonomous AI Agent Framework

Scrapes documentation and tutorials from quantum computing libraries,
processes them into embeddings, and stores in vector database for
knowledge retrieval and fusion updates.
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import json
import re
from pathlib import Path

# Web scraping imports
try:
    import requests
    from bs4 import BeautifulSoup
    import aiohttp
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False
    # Create dummy BeautifulSoup for type hints
    class BeautifulSoup:
        pass

# Vector database imports
try:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of documentation"""
    id: str
    title: str
    content: str
    url: str
    source: str  # 'qiskit', 'cirq', 'pennylane', 'dwave'
    doc_type: str  # 'tutorial', 'api', 'example', 'guide'
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class QuantumKnowledgeIngestor:
    """
    Ingests quantum computing documentation and stores it in vector database
    for semantic search and knowledge retrieval.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the knowledge ingestor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Storage configuration
        self.data_dir = Path("quantum_agent/memory")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Vector database setup
        self.embedding_model = None
        self.faiss_index = None
        self.chromadb_client = None
        self.collection = None
        
        # Document tracking
        self.processed_urls: Set[str] = set()
        self.document_chunks: List[DocumentChunk] = []
        
        # Source configurations
        self.quantum_sources = {
            'qiskit': {
                'base_url': 'https://qiskit.org/documentation/',
                'patterns': [
                    'https://qiskit.org/documentation/tutorials/',
                    'https://qiskit.org/documentation/apidoc/',
                    'https://qiskit.org/documentation/getting_started.html'
                ]
            },
            'cirq': {
                'base_url': 'https://quantumai.google/cirq/',
                'patterns': [
                    'https://quantumai.google/cirq/tutorials/',
                    'https://quantumai.google/cirq/docs/',
                    'https://quantumai.google/cirq/examples/'
                ]
            },
            'pennylane': {
                'base_url': 'https://pennylane.ai/qml/',
                'patterns': [
                    'https://pennylane.ai/qml/demos/',
                    'https://docs.pennylane.ai/',
                    'https://pennylane.ai/qml/whatisqml.html'
                ]
            },
            'dwave': {
                'base_url': 'https://docs.ocean.dwavesys.com/',
                'patterns': [
                    'https://docs.ocean.dwavesys.com/en/stable/getting_started.html',
                    'https://docs.ocean.dwavesys.com/en/stable/examples/',
                    'https://docs.ocean.dwavesys.com/en/stable/docs_index.html'
                ]
            }
        }
        
        self._initialize_components()
        
        logger.info("Quantum Knowledge Ingestor initialized")
        
    def _initialize_components(self):
        """Initialize vector database and embedding components."""
        try:
            if VECTOR_DB_AVAILABLE:
                # Initialize sentence transformer
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Initialize FAISS index
                embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
                self.faiss_index = faiss.IndexFlatIP(embedding_dim)  # Inner product index
                
                logger.info("FAISS vector database initialized")
                
            if CHROMADB_AVAILABLE:
                # Initialize ChromaDB
                self.chromadb_client = chromadb.PersistentClient(
                    path=str(self.data_dir / "chromadb")
                )
                
                try:
                    self.collection = self.chromadb_client.get_collection("quantum_knowledge")
                except:
                    self.collection = self.chromadb_client.create_collection(
                        name="quantum_knowledge",
                        metadata={"description": "Quantum computing knowledge base"}
                    )
                    
                logger.info("ChromaDB initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            
    async def ingest_all_sources(self) -> Dict[str, Any]:
        """
        Ingest documentation from all quantum computing sources.
        
        Returns:
            Dictionary with ingestion results
        """
        if not SCRAPING_AVAILABLE:
            raise ImportError("Web scraping libraries are required")
            
        logger.info("Starting comprehensive quantum knowledge ingestion")
        
        results = {
            'total_processed': 0,
            'sources': {},
            'errors': []
        }
        
        for source_name, source_config in self.quantum_sources.items():
            try:
                logger.info(f"Ingesting {source_name} documentation...")
                
                source_result = await self._ingest_source(source_name, source_config)
                results['sources'][source_name] = source_result
                results['total_processed'] += source_result['processed_count']
                
            except Exception as e:
                error_msg = f"Failed to ingest {source_name}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                
        # Save processed documents
        await self._save_knowledge_base()
        
        logger.info(f"Knowledge ingestion completed: {results['total_processed']} documents processed")
        
        return results
        
    async def _ingest_source(self, source_name: str, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest documentation from a specific source."""
        processed_count = 0
        urls_discovered = set()
        
        # Discover URLs to process
        for pattern in source_config['patterns']:
            discovered = await self._discover_urls(pattern, source_name)
            urls_discovered.update(discovered)
            
        # Process each discovered URL
        for url in urls_discovered:
            if url not in self.processed_urls:
                try:
                    chunks = await self._process_url(url, source_name)
                    self.document_chunks.extend(chunks)
                    processed_count += len(chunks)
                    self.processed_urls.add(url)
                    
                    # Small delay to be respectful
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"Failed to process {url}: {e}")
                    
        return {
            'processed_count': processed_count,
            'urls_discovered': len(urls_discovered),
            'urls_processed': len([u for u in urls_discovered if u in self.processed_urls])
        }
        
    async def _discover_urls(self, start_url: str, source_name: str) -> Set[str]:
        """Discover URLs to scrape from a starting URL."""
        urls = set()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(start_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find all links
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            
                            # Convert relative URLs to absolute
                            if href.startswith('/'):
                                base_url = self.quantum_sources[source_name]['base_url']
                                href = base_url.rstrip('/') + href
                            elif href.startswith('../'):
                                continue  # Skip relative parent URLs for now
                            elif not href.startswith('http'):
                                continue  # Skip other relative URLs
                                
                            # Filter relevant URLs based on source
                            if self._is_relevant_url(href, source_name):
                                urls.add(href)
                                
        except Exception as e:
            logger.warning(f"Failed to discover URLs from {start_url}: {e}")
            
        return urls
        
    def _is_relevant_url(self, url: str, source_name: str) -> bool:
        """Check if URL is relevant for documentation."""
        url_lower = url.lower()
        
        # General filters
        if any(ext in url_lower for ext in ['.pdf', '.zip', '.tar.gz', '.jpg', '.png']):
            return False
            
        if any(skip in url_lower for skip in ['github.com', 'twitter.com', 'linkedin.com']):
            return False
            
        # Source-specific filters
        if source_name == 'qiskit':
            return any(pattern in url_lower for pattern in [
                'qiskit.org/documentation',
                'tutorial',
                'getting_started',
                'apidoc'
            ])
        elif source_name == 'cirq':
            return any(pattern in url_lower for pattern in [
                'quantumai.google/cirq',
                'tutorial',
                'example',
                'docs'
            ])
        elif source_name == 'pennylane':
            return any(pattern in url_lower for pattern in [
                'pennylane.ai',
                'demo',
                'tutorial',
                'qml'
            ])
        elif source_name == 'dwave':
            return any(pattern in url_lower for pattern in [
                'docs.ocean.dwavesys.com',
                'example',
                'getting_started'
            ])
            
        return False
        
    async def _process_url(self, url: str, source_name: str) -> List[DocumentChunk]:
        """Process a single URL and extract documentation chunks."""
        chunks = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title
                        title = self._extract_title(soup)
                        
                        # Extract and chunk content
                        content_chunks = self._extract_content_chunks(soup, url, source_name)
                        
                        for i, chunk_content in enumerate(content_chunks):
                            if len(chunk_content.strip()) > 100:  # Only meaningful chunks
                                chunk_id = f"{source_name}_{hash(url)}_{i}"
                                
                                chunk = DocumentChunk(
                                    id=chunk_id,
                                    title=title,
                                    content=chunk_content,
                                    url=url,
                                    source=source_name,
                                    doc_type=self._classify_document_type(url, title),
                                    metadata={
                                        'word_count': len(chunk_content.split()),
                                        'chunk_index': i,
                                        'total_chunks': len(content_chunks)
                                    }
                                )
                                
                                # Generate embedding
                                if self.embedding_model:
                                    chunk.embedding = self.embedding_model.encode(chunk_content).tolist()
                                    
                                chunks.append(chunk)
                                
        except Exception as e:
            logger.warning(f"Failed to process URL {url}: {e}")
            
        return chunks
        
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML."""
        # Try various title sources
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
            
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
            
        return "Untitled Document"
        
    def _extract_content_chunks(self, soup: BeautifulSoup, url: str, source_name: str) -> List[str]:
        """Extract and chunk content from HTML."""
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
            
        # Extract main content areas
        content_selectors = [
            'main',
            '.content',
            '.documentation',
            '.tutorial-content',
            'article',
            '.rst-content'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
                
        if not main_content:
            main_content = soup.find('body')
            
        if not main_content:
            return []
            
        # Extract text and split into chunks
        text = main_content.get_text()
        
        # Clean text
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'\n+', '\n', text)  # Normalize newlines
        
        # Split into chunks (by paragraphs or sections)
        chunks = []
        paragraphs = text.split('\n')
        
        current_chunk = ""
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # If adding this paragraph would make chunk too long, start new chunk
            if len(current_chunk) + len(paragraph) > 1000 and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += " " + paragraph if current_chunk else paragraph
                
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks
        
    def _classify_document_type(self, url: str, title: str) -> str:
        """Classify document type based on URL and title."""
        url_lower = url.lower()
        title_lower = title.lower()
        
        if any(term in url_lower for term in ['tutorial', 'getting_started']):
            return 'tutorial'
        elif any(term in url_lower for term in ['api', 'reference']):
            return 'api'
        elif any(term in url_lower for term in ['example', 'demo']):
            return 'example'
        elif any(term in title_lower for term in ['guide', 'how to']):
            return 'guide'
        else:
            return 'documentation'
            
    async def _save_knowledge_base(self):
        """Save processed knowledge to vector databases."""
        if not self.document_chunks:
            logger.warning("No document chunks to save")
            return
            
        logger.info(f"Saving {len(self.document_chunks)} document chunks to knowledge base")
        
        try:
            # Save to FAISS
            if self.faiss_index and self.embedding_model:
                embeddings = []
                metadata = []
                
                for chunk in self.document_chunks:
                    if chunk.embedding:
                        embeddings.append(chunk.embedding)
                        metadata.append({
                            'id': chunk.id,
                            'title': chunk.title,
                            'url': chunk.url,
                            'source': chunk.source,
                            'doc_type': chunk.doc_type
                        })
                        
                if embeddings:
                    embeddings_array = np.array(embeddings).astype('float32')
                    self.faiss_index.add(embeddings_array)
                    
                    # Save FAISS index
                    faiss.write_index(self.faiss_index, str(self.data_dir / "quantum_kb.faiss"))
                    
                    # Save metadata
                    with open(self.data_dir / "quantum_kb_metadata.json", 'w') as f:
                        json.dump(metadata, f, indent=2)
                        
                    logger.info(f"Saved {len(embeddings)} embeddings to FAISS")
                    
            # Save to ChromaDB
            if self.collection:
                documents = []
                metadatas = []
                ids = []
                embeddings = []
                
                for chunk in self.document_chunks:
                    documents.append(chunk.content)
                    metadatas.append({
                        'title': chunk.title,
                        'url': chunk.url,
                        'source': chunk.source,
                        'doc_type': chunk.doc_type,
                        'created_at': chunk.created_at.isoformat()
                    })
                    ids.append(chunk.id)
                    if chunk.embedding:
                        embeddings.append(chunk.embedding)
                        
                if documents:
                    # Add to collection in batches
                    batch_size = 100
                    for i in range(0, len(documents), batch_size):
                        batch_docs = documents[i:i+batch_size]
                        batch_metadata = metadatas[i:i+batch_size]
                        batch_ids = ids[i:i+batch_size]
                        batch_embeddings = embeddings[i:i+batch_size] if embeddings else None
                        
                        self.collection.add(
                            documents=batch_docs,
                            metadatas=batch_metadata,
                            ids=batch_ids,
                            embeddings=batch_embeddings
                        )
                        
                    logger.info(f"Saved {len(documents)} documents to ChromaDB")
                    
            # Save raw data
            raw_data = []
            for chunk in self.document_chunks:
                chunk_data = {
                    'id': chunk.id,
                    'title': chunk.title,
                    'content': chunk.content,
                    'url': chunk.url,
                    'source': chunk.source,
                    'doc_type': chunk.doc_type,
                    'metadata': chunk.metadata,
                    'created_at': chunk.created_at.isoformat()
                }
                raw_data.append(chunk_data)
                
            with open(self.data_dir / "quantum_knowledge_raw.json", 'w') as f:
                json.dump(raw_data, f, indent=2)
                
            logger.info("Knowledge base saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save knowledge base: {e}")
            
    def search_knowledge(self, query: str, limit: int = 10, source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search the quantum knowledge base.
        
        Args:
            query: Search query
            limit: Maximum results to return
            source_filter: Filter by source (qiskit, cirq, pennylane, dwave)
            
        Returns:
            List of relevant documents
        """
        results = []
        
        try:
            if self.collection:
                # Use ChromaDB for search
                where_clause = {"source": source_filter} if source_filter else None
                
                search_results = self.collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where=where_clause
                )
                
                if search_results['documents']:
                    for i, doc in enumerate(search_results['documents'][0]):
                        result = {
                            'content': doc,
                            'metadata': search_results['metadatas'][0][i],
                            'id': search_results['ids'][0][i],
                            'distance': search_results['distances'][0][i] if search_results.get('distances') else None
                        }
                        results.append(result)
                        
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            
        return results
        
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        if not self.document_chunks:
            return {'total_documents': 0}
            
        source_counts = {}
        doc_type_counts = {}
        total_words = 0
        
        for chunk in self.document_chunks:
            source_counts[chunk.source] = source_counts.get(chunk.source, 0) + 1
            doc_type_counts[chunk.doc_type] = doc_type_counts.get(chunk.doc_type, 0) + 1
            total_words += chunk.metadata.get('word_count', 0)
            
        return {
            'total_documents': len(self.document_chunks),
            'total_words': total_words,
            'processed_urls': len(self.processed_urls),
            'source_distribution': source_counts,
            'document_type_distribution': doc_type_counts,
            'faiss_index_size': self.faiss_index.ntotal if self.faiss_index else 0,
            'chromadb_available': CHROMADB_AVAILABLE and self.collection is not None
        }
        
    def export_embeddings(self, output_path: str) -> Dict[str, Any]:
        """Export embeddings for fusion system integration."""
        try:
            embeddings_data = {
                'timestamp': datetime.now().isoformat(),
                'embedding_model': 'all-MiniLM-L6-v2',
                'total_documents': len(self.document_chunks),
                'embeddings': []
            }
            
            for chunk in self.document_chunks:
                if chunk.embedding:
                    embedding_entry = {
                        'id': chunk.id,
                        'content': chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                        'source': chunk.source,
                        'doc_type': chunk.doc_type,
                        'embedding': chunk.embedding,
                        'metadata': chunk.metadata
                    }
                    embeddings_data['embeddings'].append(embedding_entry)
                    
            with open(output_path, 'w') as f:
                json.dump(embeddings_data, f, indent=2)
                
            logger.info(f"Exported {len(embeddings_data['embeddings'])} embeddings to {output_path}")
            
            return {
                'success': True,
                'output_path': output_path,
                'exported_count': len(embeddings_data['embeddings']),
                'file_size_mb': os.path.getsize(output_path) / 1024 / 1024
            }
            
        except Exception as e:
            logger.error(f"Failed to export embeddings: {e}")
            return {'success': False, 'error': str(e)} 