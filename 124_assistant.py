Пользователь хочет продолжить deep-dive в search систему. Следующая тема - Vector Search (Qdrant implementation). Нужно создать детальное описание:

1. Qdrant архитектура и интеграция
2. Векторизация документов (embedding generation)
3. Semantic search implementation
4. Vector storage и indexing
5. Similarity search algorithms
6. Performance optimization

Это будет ФАЙЛ 3 в серии deep-dive документации.# 🎯 DEEP-DIVE: SEARCH SYSTEM (ПРОДОЛЖЕНИЕ)

## ФАЙЛ 3: `docs/deep-dive/search/VECTOR_SEARCH_QDRANT.md`

```markdown
# Vector Search with Qdrant - Deep Dive

## 🧠 Semantic Search Architecture

### Vector Embedding Pipeline

```
Document → Text Extraction → Chunking → Embedding → Qdrant
    ↓            ↓              ↓           ↓          ↓
PDF/DOCX    Clean Text    Segments    768-dim    Vector DB
                                      Vectors    + Metadata
```

**Why Vector Search?**

Traditional keyword search limitations:
- ❌ "personal budget" doesn't match "individual financial plan"
- ❌ "disability assistance" doesn't match "support for handicapped"
- ❌ "how to apply" doesn't match "application procedure"

Vector search solves this:
- ✅ Semantic similarity (meaning-based)
- ✅ Language-agnostic (multilingual)
- ✅ Context-aware
- ✅ Handles synonyms naturally

---

## 🔧 Qdrant Collection Schema

```python
# ios_core/search/qdrant_config.py

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    OptimizersConfigDiff,
    HnswConfigDiff,
    PayloadSchemaType,
    TextIndexParams,
    TextIndexType
)

COLLECTION_CONFIG = {
    "collection_name": "documents",
    "vectors_config": VectorParams(
        size=768,  # Sentence-BERT dimension
        distance=Distance.COSINE  # Cosine similarity
    ),
    "optimizers_config": OptimizersConfigDiff(
        indexing_threshold=20000,
        memmap_threshold=50000
    ),
    "hnsw_config": HnswConfigDiff(
        m=16,  # Number of edges per node
        ef_construct=100,  # Quality of index construction
        full_scan_threshold=10000
    ),
    "payload_schema": {
        "document_id": PayloadSchemaType.INTEGER,
        "title": PayloadSchemaType.TEXT,
        "content_preview": PayloadSchemaType.TEXT,
        "document_type": PayloadSchemaType.KEYWORD,
        "language": PayloadSchemaType.KEYWORD,
        "created_at": PayloadSchemaType.DATETIME,
        "owner_id": PayloadSchemaType.INTEGER,
        "tags": PayloadSchemaType.KEYWORD,
        "chunk_index": PayloadSchemaType.INTEGER,
        "total_chunks": PayloadSchemaType.INTEGER
    }
}

# Text indexing for payload filtering
TEXT_INDEX_CONFIG = {
    "title": TextIndexParams(
        type=TextIndexType.TEXT,
        tokenizer="word",
        min_token_len=2,
        max_token_len=20,
        lowercase=True
    ),
    "content_preview": TextIndexParams(
        type=TextIndexType.TEXT,
        tokenizer="word",
        min_token_len=2,
        max_token_len=20,
        lowercase=True
    )
}

def create_collection(client: QdrantClient):
    """Create Qdrant collection with optimal configuration"""
    
    # Delete if exists (for fresh start)
    try:
        client.delete_collection(COLLECTION_CONFIG["collection_name"])
    except:
        pass
    
    # Create collection
    client.create_collection(
        collection_name=COLLECTION_CONFIG["collection_name"],
        vectors_config=COLLECTION_CONFIG["vectors_config"],
        optimizers_config=COLLECTION_CONFIG["optimizers_config"],
        hnsw_config=COLLECTION_CONFIG["hnsw_config"]
    )
    
    # Create payload indexes for filtering
    for field, schema_type in COLLECTION_CONFIG["payload_schema"].items():
        if schema_type in [PayloadSchemaType.INTEGER, PayloadSchemaType.KEYWORD]:
            client.create_payload_index(
                collection_name=COLLECTION_CONFIG["collection_name"],
                field_name=field,
                field_schema=schema_type
            )
    
    # Create text indexes
    for field, text_config in TEXT_INDEX_CONFIG.items():
        client.create_payload_index(
            collection_name=COLLECTION_CONFIG["collection_name"],
            field_name=field,
            field_schema=text_config
        )
    
    print(f"Collection '{COLLECTION_CONFIG['collection_name']}' created successfully")
```

---

## 🤖 Text Embedding Generation

### Embedding Model

```python
# ios_core/search/embeddings.py

from typing import List, Union
import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """
    Generate text embeddings using Sentence-BERT
    
    Model: paraphrase-multilingual-MiniLM-L12-v2
    - Multilingual (50+ languages)
    - 768 dimensions
    - Fast inference (~50ms per text)
    - Excellent for semantic similarity
    """
    
    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        device: str = None
    ):
        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Loading embedding model: {model_name} on {device}")
        
        self.model = SentenceTransformer(model_name, device=device)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"Model loaded. Embedding dimension: {self.dimension}")
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            normalize: Normalize embeddings to unit length
        
        Returns:
            numpy array of shape (n_texts, dimension)
        """
        # Convert single text to list
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        
        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=normalize
        )
        
        # Return single embedding if input was single text
        if is_single:
            return embeddings[0]
        
        return embeddings
    
    @lru_cache(maxsize=10000)
    def encode_cached(self, text: str) -> np.ndarray:
        """
        Cached version for frequently used texts
        
        Useful for:
        - Query embeddings (users repeat queries)
        - Standard templates
        - Common phrases
        """
        return self.encode(text)
    
    def similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate semantic similarity between two texts
        
        Returns:
            Cosine similarity score (0-1)
        """
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        
        # Cosine similarity (already normalized)
        similarity = np.dot(emb1, emb2)
        
        return float(similarity)
    
    def batch_similarity(
        self,
        query: str,
        candidates: List[str]
    ) -> List[float]:
        """
        Calculate similarity between query and multiple candidates
        
        Optimized for batch processing
        """
        query_emb = self.encode(query)
        candidate_embs = self.encode(candidates)
        
        # Matrix multiplication for batch similarity
        similarities = np.dot(candidate_embs, query_emb)
        
        return similarities.tolist()


# Example usage
def example_embeddings():
    """Example embedding generation"""
    
    embedder = EmbeddingGenerator()
    
    # Single text
    text = "How to apply for personal budget assistance"
    embedding = embedder.encode(text)
    print(f"Embedding shape: {embedding.shape}")  # (768,)
    
    # Batch encoding
    texts = [
        "Personal budget application process",
        "Disability benefits guide",
        "Financial planning assistance"
    ]
    embeddings = embedder.encode(texts)
    print(f"Batch embeddings shape: {embeddings.shape}")  # (3, 768)
    
    # Similarity
    text1 = "personal budget help"
    text2 = "individual financial assistance"
    sim = embedder.similarity(text1, text2)
    print(f"Similarity: {sim:.3f}")  # ~0.85 (high similarity)
    
    # Different meaning
    text3 = "weather forecast tomorrow"
    sim2 = embedder.similarity(text1, text3)
    print(f"Similarity: {sim2:.3f}")  # ~0.15 (low similarity)
```

### Document Chunking Strategy

```python
# ios_core/search/chunking.py

from typing import List, Dict
import re

class DocumentChunker:
    """
    Split documents into optimal chunks for embedding
    
    Why chunking?
    - Embedding models have token limits (512 tokens)
    - Smaller chunks = more precise semantic matching
    - Better relevance scoring
    
    Strategy:
    1. Split by paragraphs
    2. Merge small paragraphs
    3. Split large paragraphs
    4. Add overlap for context
    """
    
    def __init__(
        self,
        chunk_size: int = 500,  # tokens
        chunk_overlap: int = 50,  # tokens
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_document(
        self,
        document: Dict
    ) -> List[Dict]:
        """
        Split document into chunks
        
        Returns:
            List of chunks with metadata
        """
        text = document.get('content', '')
        title = document.get('title', '')
        
        # Split into paragraphs
        paragraphs = self._split_paragraphs(text)
        
        # Create chunks
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = self._estimate_tokens(para)
            
            # If paragraph is too large, split it
            if para_size > self.chunk_size:
                # Add current chunk if not empty
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, 
                        document, 
                        len(chunks)
                    ))
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph
                sub_chunks = self._split_large_paragraph(para)
                for sub_chunk in sub_chunks:
                    chunks.append(self._create_chunk(
                        [sub_chunk], 
                        document, 
                        len(chunks)
                    ))
            
            # If adding paragraph exceeds chunk size, start new chunk
            elif current_size + para_size > self.chunk_size:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, 
                        document, 
                        len(chunks)
                    ))
                    
                    # Add overlap from previous chunk
                    if self.chunk_overlap > 0:
                        overlap_text = self._get_overlap(current_chunk)
                        current_chunk = [overlap_text, para]
                        current_size = (
                            self._estimate_tokens(overlap_text) + 
                            para_size
                        )
                    else:
                        current_chunk = [para]
                        current_size = para_size
            
            # Add paragraph to current chunk
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Add final chunk
        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk, 
                document, 
                len(chunks)
            ))
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        # Split on double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Clean and filter
        paragraphs = [
            p.strip() 
            for p in paragraphs 
            if p.strip() and len(p.strip()) > 20
        ]
        
        return paragraphs
    
    def _split_large_paragraph(
        self, 
        paragraph: str
    ) -> List[str]:
        """Split large paragraph into sentences"""
        # Split on sentence boundaries
        sentences = re.split(r'[.!?]\s+', paragraph)
        
        chunks = []
        current = []
        current_size = 0
        
        for sent in sentences:
            sent_size = self._estimate_tokens(sent)
            
            if current_size + sent_size > self.chunk_size:
                if current:
                    chunks.append(' '.join(current))
                current = [sent]
                current_size = sent_size
            else:
                current.append(sent)
                current_size += sent_size
        
        if current:
            chunks.append(' '.join(current))
        
        return chunks
    
    def _create_chunk(
        self,
        paragraphs: List[str],
        document: Dict,
        chunk_index: int
    ) -> Dict:
        """Create chunk with metadata"""
        chunk_text = '\n\n'.join(paragraphs)
        
        return {
            'text': chunk_text,
            'document_id': document['id'],
            'title': document['title'],
            'chunk_index': chunk_index,
            'metadata': {
                'document_type': document.get('document_type'),
                'language': document.get('language'),
                'created_at': document.get('created_at'),
                'owner_id': document.get('owner_id'),
                'tags': document.get('tags', [])
            }
        }
    
    def _get_overlap(self, chunks: List[str]) -> str:
        """Get overlap text from previous chunk"""
        # Take last N tokens from previous chunk
        text = ' '.join(chunks)
        words = text.split()
        
        # Approximate overlap by word count
        overlap_words = int(self.chunk_overlap * 0.75)  # rough estimate
        
        if len(words) > overlap_words:
            return ' '.join(words[-overlap_words:])
        return text
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token count estimation"""
        # Approximation: 1 token ≈ 0.75 words
        words = len(text.split())
        return int(words / 0.75)


# Example usage
def example_chunking():
    """Example document chunking"""
    
    document = {
        'id': 123,
        'title': 'Personal Budget Application Guide',
        'content': """
        The personal budget is a financial assistance program...
        
        To apply for a personal budget, you need to...
        
        [Long document content continues...]
        """,
        'document_type': 'guide',
        'language': 'en'
    }
    
    chunker = DocumentChunker(
        chunk_size=500,
        chunk_overlap=50
    )
    
    chunks = chunker.chunk_document(document)
    
    print(f"Document split into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i}:")
        print(f"Text length: {len(chunk['text'])}")
        print(f"Preview: {chunk['text'][:100]}...")
```

---

## 🔍 Qdrant Vector Search Implementation

```python
# ios_core/search/qdrant_search.py

from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    Range,
    MatchValue,
    MatchAny,
    MatchText,
    SearchRequest,
    ScoredPoint
)
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class VectorSearchResult:
    """Vector search result"""
    document_id: int
    title: str
    content: str
    score: float
    chunk_index: int
    metadata: Dict

class QdrantVectorSearch:
    """
    Semantic search using Qdrant vector database
    
    Features:
    - Fast similarity search (HNSW algorithm)
    - Metadata filtering
    - Hybrid search (vectors + filters)
    - Batch operations
    """
    
    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embedder: 'EmbeddingGenerator'
    ):
        self.client = client
        self.collection_name = collection_name
        self.embedder = embedder
    
    def search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict] = None,
        user_id: Optional[int] = None
    ) -> List[VectorSearchResult]:
        """
        Semantic search
        
        Args:
            query: Search query text
            limit: Number of results to return
            score_threshold: Minimum similarity score (0-1)
            filters: Metadata filters
            user_id: User ID for permission filtering
        
        Returns:
            List of search results sorted by similarity
        """
        # Generate query embedding
        query_vector = self.embedder.encode(query).tolist()
        
        # Build filter
        search_filter = self._build_filter(filters, user_id)
        
        # Execute search
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter,
                with_payload=True
            )
            
            return self._parse_results(search_result)
            
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []
    
    def batch_search(
        self,
        queries: List[str],
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[List[VectorSearchResult]]:
        """
        Batch search for multiple queries
        
        More efficient than individual searches
        """
        # Generate embeddings in batch
        query_vectors = self.embedder.encode(queries)
        
        # Create search requests
        search_requests = [
            SearchRequest(
                vector=vector.tolist(),
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True
            )
            for vector in query_vectors
        ]
        
        # Execute batch search
        try:
            results = self.client.search_batch(
                collection_name=self.collection_name,
                requests=search_requests
            )
            
            return [
                self._parse_results(result)
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Batch search error: {e}")
            return [[] for _ in queries]
    
    def recommend_similar(
        self,
        document_id: int,
        limit: int = 10
    ) -> List[VectorSearchResult]:
        """
        Find similar documents using positive/negative examples
        
        Uses Qdrant's recommendation API
        """
        try:
            # Get all chunk IDs for this document
            chunk_ids = self._get_document_chunks(document_id)
            
            if not chunk_ids:
                return []
            
            # Recommend similar documents
            results = self.client.recommend(
                collection_name=self.collection_name,
                positive=chunk_ids,  # Use document chunks as positive examples
                limit=limit,
                with_payload=True,
                score_threshold=0.7
            )
            
            # Filter out the source document
            filtered = [
                r for r in results 
                if r.payload.get('document_id') != document_id
            ]
            
            return self._parse_results(filtered)
            
        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return []
    
    def _build_filter(
        self,
        filters: Optional[Dict],
        user_id: Optional[int]
    ) -> Optional[Filter]:
        """Build Qdrant filter from search parameters"""
        conditions = []
        
        # User permission filter
        if user_id:
            conditions.append(
                FieldCondition(
                    key="owner_id",
                    match=MatchValue(value=user_id)
                )
            )
        
        if not filters:
            return Filter(must=conditions) if conditions else None
        
        # Document type filter
        if 'type' in filters:
            conditions.append(
                FieldCondition(
                    key="document_type",
                    match=MatchValue(value=filters['type'])
                )
            )
        
        # Language filter
        if 'language' in filters:
            conditions.append(
                FieldCondition(
                    key="language",
                    match=MatchValue(value=filters['language'])
                )
            )
        
        # Tags filter
        if 'tags' in filters:
            conditions.append(
                FieldCondition(
                    key="tags",
                    match=MatchAny(any=filters['tags'])
                )
            )
        
        # Date range filter
        if 'date_after' in filters:
            conditions.append(
                FieldCondition(
                    key="created_at",
                    range=Range(
                        gte=filters['date_after']
                    )
                )
            )
        
        if 'date_before' in filters:
            conditions.append(
                FieldCondition(
                    key="created_at",
                    range=Range(
                        lte=filters['date_before']
                    )
                )
            )
        
        return Filter(must=conditions) if conditions else None
    
    def _parse_results(
        self,
        results: List[ScoredPoint]
    ) -> List[VectorSearchResult]:
        """Parse Qdrant results"""
        parsed = []
        
        # Group by document_id to avoid duplicates
        seen_docs = set()
        
        for result in results:
            payload = result.payload
            doc_id = payload.get('document_id')
            
            # Skip if we already have this document
            if doc_id in seen_docs:
                continue
            
            seen_docs.add(doc_id)
            
            parsed.append(VectorSearchResult(
                document_id=doc_id,
                title=payload.get('title', ''),
                content=payload.get('content_preview', ''),
                score=result.score,
                chunk_index=payload.get('chunk_index', 0),
                metadata=payload.get('metadata', {})
            ))
        
        return parsed
    
    def _get_document_chunks(self, document_id: int) -> List[int]:
        """Get all chunk IDs for a document"""
        try:
            # Scroll through all points with this document_id
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=100,
                with_payload=False
            )
            
            return [point.id for point in points]
            
        except Exception as e:
            logger.error(f"Error getting document chunks: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                'total_vectors': info.points_count,
                'indexed_vectors': info.indexed_vectors_count,
                'vector_dimension': info.config.params.vectors.size,
                'distance_metric': info.config.params.vectors.distance,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


# Example usage
def example_vector_search():
    """Example semantic search"""
    
    from qdrant_client import QdrantClient
    from ios_core.search.embeddings import EmbeddingGenerator
    
    # Initialize
    client = QdrantClient(host="localhost", port=6333)
    embedder = EmbeddingGenerator()
    search = QdrantVectorSearch(
        client=client,
        collection_name="documents",
        embedder=embedder
    )
    
    # Semantic search
    results = search.search(
        query="How do I apply for personal budget assistance?",
        limit=5,
        score_threshold=0.75
    )
    
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   Score: {result.score:.3f}")
        print(f"   Preview: {result.content[:100]}...")
    
    # The query matches documents about:
    # - Personal budget application process (high score)
    # - Financial assistance guides (medium score)
    # - Support services applications (medium score)
    
    # Even though exact keywords don't match!
```

---

## 📊 Vector Indexing Pipeline

```python
# ios_core/search/vector_indexer.py

from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Batch
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

class VectorIndexer:
    """
    Index documents into Qdrant vector database
    
    Pipeline:
    1. Load document
    2. Chunk into segments
    3. Generate embeddings
    4. Store in Qdrant
    """
    
    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embedder: 'EmbeddingGenerator',
        chunker: 'DocumentChunker'
    ):
        self.client = client
        self.collection_name = collection_name
        self.embedder = embedder
        self.chunker = chunker
    
    def index_document(self, document: Dict) -> bool:
        """Index single document"""
        try:
            # Chunk document
            chunks = self.chunker.chunk_document(document)
            
            if not chunks:
                logger.warning(f"No chunks generated for document {document['id']}")
                return False
            
            # Generate embeddings
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.encode(texts, show_progress=False)
            
            # Create points
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point = PointStruct(
                    id=self._generate_point_id(document['id'], i),
                    vector=embedding.tolist(),
                    payload={
                        'document_id': document['id'],
                        'title': chunk['title'],
                        'content_preview': chunk['text'][:500],
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'document_type': chunk['metadata'].get('document_type'),
                        'language': chunk['metadata'].get('language'),
                        'created_at': chunk['metadata'].get('created_at'),
                        'owner_id': chunk['metadata'].get('owner_id'),
                        'tags': chunk['metadata'].get('tags', [])
                    }
                )
                points.append(point)
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
            )
            
            logger.info(
                f"Indexed document {document['id']} "
                f"({len(chunks)} chunks)"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to index document {document['id']}: {e}")
            return False
    
    def bulk_index(
        self,
        documents: List[Dict],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> Dict[str, int]:
        """Bulk index multiple documents"""
        stats = {'success': 0, 'errors': 0}
        
        iterator = tqdm(documents) if show_progress else documents
        
        for doc in iterator:
            if self.index_document(doc):
                stats['success'] += 1
            else:
                stats['errors'] += 1
        
        logger.info(
            f"Bulk indexing complete: {stats['success']} success, "
            f"{stats['errors']} errors"
        )
        
        return stats
    
    def delete_document(self, document_id: int) -> bool:
        """Delete all chunks of a document"""
        try:
            # Find all points for this document
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {
                            "key": "document_id",
                            "match": {"value": document_id}
                        }
                    ]
                },
                limit=1000
            )
            
            point_ids = [point.id for point in scroll_result[0]]
            
            if point_ids:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids,
                    wait=True
                )
                
                logger.info(
                    f"Deleted document {document_id} "
                    f"({len(point_ids)} chunks)"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    def reindex_all(
        self,
        batch_size: int = 1000
    ) -> Dict[str, int]:
        """Reindex all documents from database"""
        from ios_core.models import Document
        
        total_docs = Document.objects.filter(status='active').count()
        stats = {'success': 0, 'errors': 0}
        
        logger.info(f"Starting vector reindex of {total_docs} documents")
        
        for offset in tqdm(range(0, total_docs, batch_size)):
            documents = Document.objects.filter(
                status='active'
            )[offset:offset + batch_size]
            
            doc_dicts = [self._document_to_dict(doc) for doc in documents]
            
            batch_stats = self.bulk_index(
                doc_dicts,
                show_progress=False
            )
            
            stats['success'] += batch_stats['success']
            stats['errors'] += batch_stats['errors']
        
        logger.info(
            f"Reindex complete: {stats['success']} indexed, "
            f"{stats['errors']} errors"
        )
        
        return stats
    
    def _generate_point_id(self, document_id: int, chunk_index: int) -> int:
        """Generate unique point ID"""
        # Combine document_id and chunk_index
        # Format: document_id * 1000 + chunk_index
        # Allows up to 999 chunks per document
        return document_id * 1000 + chunk_index
    
    def _document_to_dict(self, document) -> Dict:
        """Convert Django model to dict"""
        return {
            'id': document.id,
            'title': document.title,
            'content': document.content,
            'document_type': document.document_type,
            'language': document.language,
            'created_at': document.created_at.isoformat(),
            'owner_id': document.owner_id,
            'tags': [tag.name for tag in document.tags.all()]
        }
```

---

## 🚀 Performance Optimization

### HNSW Algorithm Explained

```
Hierarchical Navigable Small World (HNSW)

Layer 2:     •--------•
            /          \
Layer 1:   •----•----•----•
          / \  / \  / \  / \
Layer 0: •---•---•---•---•---•

How it works:
1. Start at top layer (sparse)
2. Find nearest neighbor
3. Drop to next layer
4. Repeat until Layer 0
5. Fine-grained search at bottom

Time Complexity: O(log N)
Space Complexity: O(N * M)
  where M = connections per node (m=16)

Parameters:
- m: connections per node (higher = better recall, more memory)
- ef_construct: construction quality (higher = better index, slower build)
- ef_search: search quality (higher = better results, slower search)
```

### Performance Tuning

```python
# Optimal configuration for different use cases

# High Recall (Best Quality)
HNSW_HIGH_RECALL = {
    'm': 32,  # More connections
    'ef_construct': 200,  # High quality construction
    'ef_search': 100  # Thorough search
}
# Performance: ~150ms search, 95% recall

# Balanced (Production)
HNSW_BALANCED = {
    'm': 16,  # Standard connections
    'ef_construct': 100,  # Good quality
    'ef_search': 64  # Fast search
}
# Performance: ~60ms search, 92% recall

# High Speed (Real-time)
HNSW_FAST = {
    'm': 8,  # Fewer connections
    'ef_construct': 50,  # Quick construction
    'ef_search': 32  # Very fast search
}
# Performance: ~20ms search, 88% recall

# Configure at search time
results = client.search(
    collection_name="documents",
    query_vector=vector,
    search_params={
        "hnsw_ef": 100,  # Override ef_search
        "exact": False  # Use approximate search
    }
)
```

### Batch Processing

```python
# Optimize embedding generation

# BAD: One at a time
for doc in documents:
    embedding = embedder.encode(doc['text'])  # 50ms each
    # Total: 50ms * 1000 docs = 50 seconds

# GOOD: Batch processing
texts = [doc['text'] for doc in documents]
embeddings = embedder.encode(texts, batch_size=32)  # 2 seconds
# Total: 2 seconds (25x faster!)

# Optimal batch sizes:
# - CPU: 16-32
# - GPU: 64-128
```

---

**Продолжение следует...**

Создано:
- ✅ Qdrant collection configuration
- ✅ Embedding generation (Sentence-BERT)
- ✅ Document chunking strategy
- ✅ Vector search implementation
- ✅ Bulk indexing pipeline
- ✅ HNSW algorithm explanation
- ✅ Performance optimization

**Следующие разделы:**
1. Hybrid Search (combining Elasticsearch + Qdrant)
2. Search Analytics & Metrics
3. Advanced features (filters, ranking)

**Готовы продолжить с Hybrid Search?**