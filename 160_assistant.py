Пользователь хочет продолжить с Task 3.2: Qdrant Service Implementation. Я продолжу с детальной реализацией сервиса Qdrant, который будет отвечать за векторный поиск.## ФАЙЛ 19 (продолжение): Qdrant Service и Hybrid Search

```markdown
# Phase Implementation Details (продолжение)

#### Task 3.2: Qdrant Service Implementation
**Assignee:** Backend Developer
**Time:** 3 days
**Priority:** Critical

```python
# search/services/qdrant_service.py

"""
Qdrant service for vector similarity search
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    SearchRequest, ScalarQuantization,
    OptimizersConfigDiff
)
from django.conf import settings
from sentence_transformers import SentenceTransformer
import logging
from typing import List, Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)

class QdrantService:
    """
    Service for Qdrant vector operations
    """
    
    def __init__(self):
        """Initialize Qdrant client and embedding model"""
        qdrant_config = settings.QDRANT_CONFIG
        
        self.client = QdrantClient(
            host=qdrant_config['host'],
            port=qdrant_config['port'],
            grpc_port=qdrant_config.get('grpc_port', 6334),
            prefer_grpc=qdrant_config.get('prefer_grpc', True),
            timeout=qdrant_config.get('timeout', 30)
        )
        
        self.collection_name = settings.SEARCH_CONFIG['qdrant']['collection_name']
        self.vector_size = settings.SEARCH_CONFIG['qdrant']['vector_size']
        
        # Initialize embedding model
        model_name = settings.SEARCH_CONFIG['embedding']['model']
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded")
    
    def create_collection(self, force: bool = False):
        """
        Create Qdrant collection with optimized settings
        
        Args:
            force: Force recreate if collection exists
        """
        try:
            if force and self.client.collection_exists(self.collection_name):
                logger.warning(f"Deleting existing collection: {self.collection_name}")
                self.client.delete_collection(self.collection_name)
            
            if self.client.collection_exists(self.collection_name):
                logger.info(f"Collection already exists: {self.collection_name}")
                return
            
            # Create collection with optimized settings
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                ),
                # Enable on-disk storage for large collections
                on_disk_payload=True,
                
                # Optimizer settings for better performance
                optimizers_config=OptimizersConfigDiff(
                    indexing_threshold=20000,  # Start indexing after 20k vectors
                    memmap_threshold=20000,    # Use memory mapping
                ),
                
                # Enable quantization for memory efficiency
                quantization_config=ScalarQuantization(
                    scalar=ScalarQuantization(
                        type='int8',
                        quantile=0.99,
                        always_ram=False
                    )
                ),
                
                # HNSW index parameters
                hnsw_config={
                    'm': 16,              # Number of connections per layer
                    'ef_construct': 100,  # Size of dynamic candidate list
                    'full_scan_threshold': 10000,
                    'on_disk': True       # Store HNSW graph on disk
                }
            )
            
            logger.info(f"Created collection: {self.collection_name}")
        
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector
        """
        try:
            # Add instruction prefix for e5 models
            if 'e5' in settings.SEARCH_CONFIG['embedding']['model'].lower():
                text = f"query: {text}"
            
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.vector_size
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
        
        Returns:
            List of embedding vectors
        """
        try:
            batch_size = settings.SEARCH_CONFIG['embedding'].get('batch_size', 32)
            
            # Add instruction prefix for e5 models
            if 'e5' in settings.SEARCH_CONFIG['embedding']['model'].lower():
                texts = [f"passage: {text}" for text in texts]
            
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100
            )
            
            return [emb.tolist() for emb in embeddings]
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [[0.0] * self.vector_size] * len(texts)
    
    def index_document(self, document, embedding: Optional[List[float]] = None) -> bool:
        """
        Index a single document
        
        Args:
            document: Document model instance
            embedding: Pre-computed embedding (optional)
        
        Returns:
            Success status
        """
        try:
            # Generate embedding if not provided
            if embedding is None:
                text = f"{document.title} {document.summary or document.content[:500]}"
                embedding = self.generate_embedding(text)
            
            # Create point
            point = PointStruct(
                id=str(document.id),
                vector=embedding,
                payload={
                    'title': document.title,
                    'document_type': document.document_type,
                    'category': document.category,
                    'legal_code': document.legal_code,
                    'paragraph': document.paragraph,
                    'tags': document.tags,
                    'created_at': document.created_at.isoformat(),
                    'is_active': document.is_active,
                    'view_count': document.view_count,
                    'click_count': document.click_count
                }
            )
            
            # Upsert point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"Indexed document in Qdrant: {document.id}")
            return True
        
        except Exception as e:
            logger.error(f"Error indexing document {document.id} in Qdrant: {e}")
            return False
    
    def bulk_index_documents(self, documents: List, batch_size: int = 100) -> Dict[str, int]:
        """
        Bulk index documents
        
        Args:
            documents: List of Document model instances
            batch_size: Batch size for processing
        
        Returns:
            Statistics dict
        """
        total_success = 0
        total_failed = 0
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                # Generate embeddings for batch
                texts = [
                    f"{doc.title} {doc.summary or doc.content[:500]}"
                    for doc in batch
                ]
                embeddings = self.generate_embeddings_batch(texts)
                
                # Create points
                points = []
                for doc, embedding in zip(batch, embeddings):
                    point = PointStruct(
                        id=str(doc.id),
                        vector=embedding,
                        payload={
                            'title': doc.title,
                            'document_type': doc.document_type,
                            'category': doc.category,
                            'legal_code': doc.legal_code,
                            'paragraph': doc.paragraph,
                            'tags': doc.tags,
                            'created_at': doc.created_at.isoformat(),
                            'is_active': doc.is_active,
                            'view_count': doc.view_count,
                            'click_count': doc.click_count
                        }
                    )
                    points.append(point)
                
                # Upsert batch
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                total_success += len(batch)
                logger.info(f"Indexed batch {i//batch_size + 1}: {len(batch)} documents")
            
            except Exception as e:
                logger.error(f"Error indexing batch {i//batch_size + 1}: {e}")
                total_failed += len(batch)
        
        logger.info(f"Bulk indexed {total_success} documents, {total_failed} failed")
        
        return {
            'success': total_success,
            'failed': total_failed,
            'total': len(documents)
        }
    
    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 20,
        score_threshold: float = 0.0
    ) -> List[Dict]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            filters: Optional filters dict
            limit: Maximum number of results
            score_threshold: Minimum similarity score
        
        Returns:
            List of search results
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Build filter
            search_filter = None
            if filters:
                conditions = []
                
                # Add is_active filter (always)
                conditions.append(
                    FieldCondition(
                        key='is_active',
                        match=MatchValue(value=True)
                    )
                )
                
                if 'document_type' in filters:
                    conditions.append(
                        FieldCondition(
                            key='document_type',
                            match=MatchValue(value=filters['document_type'])
                        )
                    )
                
                if 'category' in filters:
                    conditions.append(
                        FieldCondition(
                            key='category',
                            match=MatchValue(value=filters['category'])
                        )
                    )
                
                if 'legal_code' in filters:
                    conditions.append(
                        FieldCondition(
                            key='legal_code',
                            match=MatchValue(value=filters['legal_code'])
                        )
                    )
                
                if conditions:
                    search_filter = Filter(must=conditions)
            else:
                # Always filter for active documents
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key='is_active',
                            match=MatchValue(value=True)
                        )
                    ]
                )
            
            # Execute search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'score': result.score,
                    'payload': result.payload
                })
            
            logger.debug(f"Qdrant search returned {len(formatted_results)} results")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document from collection"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[document_id]
            )
            logger.debug(f"Deleted document from Qdrant: {document_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from Qdrant: {e}")
            return False
    
    def get_collection_info(self) -> Dict:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'points_count': info.points_count,
                'vectors_count': info.vectors_count,
                'indexed_vectors_count': info.indexed_vectors_count,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
```

---

#### Task 3.3: Hybrid Search Fusion Implementation
**Assignee:** Backend Developer
**Time:** 2 days
**Priority:** Critical

```python
# search/services/fusion.py

"""
Hybrid search fusion algorithms
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Unified search result"""
    document_id: str
    score: float
    source: str  # 'elasticsearch' or 'qdrant'
    rank: int
    payload: Dict

class FusionAlgorithm:
    """Base class for fusion algorithms"""
    
    def fuse(
        self,
        es_results: List[Dict],
        qdrant_results: List[Dict]
    ) -> List[SearchResult]:
        """
        Fuse results from Elasticsearch and Qdrant
        
        Args:
            es_results: Elasticsearch results
            qdrant_results: Qdrant results
        
        Returns:
            Fused and ranked results
        """
        raise NotImplementedError

class ReciprocalRankFusion(FusionAlgorithm):
    """
    Reciprocal Rank Fusion (RRF)
    
    Score = sum(1 / (k + rank_i)) for each source
    
    Paper: "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods"
    """
    
    def __init__(self, k: int = 60):
        """
        Initialize RRF
        
        Args:
            k: Constant to prevent division by small numbers (default: 60)
        """
        self.k = k
    
    def fuse(
        self,
        es_results: List[Dict],
        qdrant_results: List[Dict]
    ) -> List[SearchResult]:
        """Fuse using RRF algorithm"""
        
        # Build RRF scores
        rrf_scores = {}
        
        # Process Elasticsearch results
        for rank, result in enumerate(es_results, start=1):
            doc_id = result['id']
            score = 1.0 / (self.k + rank)
            
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = {
                    'score': 0.0,
                    'sources': [],
                    'es_rank': None,
                    'qdrant_rank': None,
                    'payload': result.get('source', {})
                }
            
            rrf_scores[doc_id]['score'] += score
            rrf_scores[doc_id]['sources'].append('elasticsearch')
            rrf_scores[doc_id]['es_rank'] = rank
        
        # Process Qdrant results
        for rank, result in enumerate(qdrant_results, start=1):
            doc_id = result['id']
            score = 1.0 / (self.k + rank)
            
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = {
                    'score': 0.0,
                    'sources': [],
                    'es_rank': None,
                    'qdrant_rank': None,
                    'payload': result.get('payload', {})
                }
            
            rrf_scores[doc_id]['score'] += score
            rrf_scores[doc_id]['sources'].append('qdrant')
            rrf_scores[doc_id]['qdrant_rank'] = rank
        
        # Sort by RRF score
        sorted_results = sorted(
            rrf_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        # Convert to SearchResult objects
        fused_results = []
        for rank, (doc_id, data) in enumerate(sorted_results, start=1):
            source = 'both' if len(data['sources']) > 1 else data['sources'][0]
            
            fused_results.append(
                SearchResult(
                    document_id=doc_id,
                    score=data['score'],
                    source=source,
                    rank=rank,
                    payload=data['payload']
                )
            )
        
        logger.debug(f"RRF fused {len(es_results)} ES + {len(qdrant_results)} Qdrant = {len(fused_results)} results")
        
        return fused_results

class WeightedFusion(FusionAlgorithm):
    """
    Weighted score fusion
    
    Score = w1 * score1 + w2 * score2
    """
    
    def __init__(self, es_weight: float = 0.5, qdrant_weight: float = 0.5):
        """
        Initialize weighted fusion
        
        Args:
            es_weight: Weight for Elasticsearch scores
            qdrant_weight: Weight for Qdrant scores
        """
        self.es_weight = es_weight
        self.qdrant_weight = qdrant_weight
        
        # Normalize weights
        total = es_weight + qdrant_weight
        self.es_weight /= total
        self.qdrant_weight /= total
    
    def fuse(
        self,
        es_results: List[Dict],
        qdrant_results: List[Dict]
    ) -> List[SearchResult]:
        """Fuse using weighted scores"""
        
        # Normalize scores to [0, 1]
        es_normalized = self._normalize_scores(es_results, 'score')
        qdrant_normalized = self._normalize_scores(qdrant_results, 'score')
        
        # Build combined scores
        combined_scores = {}
        
        # Process Elasticsearch results
        for result in es_normalized:
            doc_id = result['id']
            combined_scores[doc_id] = {
                'score': result['normalized_score'] * self.es_weight,
                'es_score': result['score'],
                'qdrant_score': 0.0,
                'source': 'elasticsearch',
                'payload': result.get('source', {})
            }
        
        # Process Qdrant results
        for result in qdrant_normalized:
            doc_id = result['id']
            
            if doc_id in combined_scores:
                combined_scores[doc_id]['score'] += result['normalized_score'] * self.qdrant_weight
                combined_scores[doc_id]['qdrant_score'] = result['score']
                combined_scores[doc_id]['source'] = 'both'
            else:
                combined_scores[doc_id] = {
                    'score': result['normalized_score'] * self.qdrant_weight,
                    'es_score': 0.0,
                    'qdrant_score': result['score'],
                    'source': 'qdrant',
                    'payload': result.get('payload', {})
                }
        
        # Sort by combined score
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        # Convert to SearchResult objects
        fused_results = []
        for rank, (doc_id, data) in enumerate(sorted_results, start=1):
            fused_results.append(
                SearchResult(
                    document_id=doc_id,
                    score=data['score'],
                    source=data['source'],
                    rank=rank,
                    payload=data['payload']
                )
            )
        
        logger.debug(f"Weighted fusion: {len(fused_results)} results")
        
        return fused_results
    
    def _normalize_scores(self, results: List[Dict], score_key: str) -> List[Dict]:
        """Normalize scores to [0, 1] range"""
        if not results:
            return []
        
        scores = [r[score_key] for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All scores are the same
            for r in results:
                r['normalized_score'] = 1.0
        else:
            for r in results:
                r['normalized_score'] = (r[score_key] - min_score) / (max_score - min_score)
        
        return results

class HybridSearchService:
    """
    Unified hybrid search service
    """
    
    def __init__(self):
        """Initialize hybrid search"""
        from .elasticsearch_service import ElasticsearchService
        from .qdrant_service import QdrantService
        
        self.es_service = ElasticsearchService()
        self.qdrant_service = QdrantService()
        
        # Get fusion algorithm from settings
        from django.conf import settings
        fusion_config = settings.SEARCH_CONFIG['fusion']
        
        algorithm = fusion_config.get('algorithm', 'rrf')
        
        if algorithm == 'rrf':
            k = fusion_config.get('k', 60)
            self.fusion = ReciprocalRankFusion(k=k)
        elif algorithm == 'weighted':
            weights = fusion_config.get('weights', {})
            self.fusion = WeightedFusion(
                es_weight=weights.get('elasticsearch', 0.5),
                qdrant_weight=weights.get('qdrant', 0.5)
            )
        else:
            logger.warning(f"Unknown fusion algorithm: {algorithm}, using RRF")
            self.fusion = ReciprocalRankFusion()
        
        logger.info(f"Initialized hybrid search with {algorithm} fusion")
    
    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = 'relevance'
    ) -> Dict:
        """
        Perform hybrid search
        
        Args:
            query: Search query
            filters: Optional filters
            page: Page number
            page_size: Results per page
            sort_by: Sort option
        
        Returns:
            Search results dict
        """
        import time
        start_time = time.time()
        
        # Execute parallel searches
        # In production, use async/await or threading
        es_results = self.es_service.search(
            query=query,
            filters=filters,
            page=1,  # Get more results for fusion
            page_size=page_size * 2,  # 2x for better fusion
            sort_by=sort_by
        )
        
        qdrant_results = self.qdrant_service.search(
            query=query,
            filters=filters,
            limit=page_size * 2  # 2x for better fusion
        )
        
        # Fuse results
        fused = self.fusion.fuse(
            es_results=es_results.get('results', []),
            qdrant_results=qdrant_results
        )
        
        # Paginate fused results
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = fused[start_idx:end_idx]
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        # Format response
        return {
            'results': [
                {
                    'id': r.document_id,
                    'score': r.score,
                    'rank': r.rank,
                    'source': r.source,
                    **r.payload
                }
                for r in page_results
            ],
            'total': len(fused),
            'page': page,
            'page_size': page_size,
            'total_pages': (len(fused) + page_size - 1) // page_size,
            'search_time_ms': search_time_ms,
            'fusion_algorithm': self.fusion.__class__.__name__
        }
    
    def index_document(self, document) -> Dict[str, bool]:
        """
        Index document in both services
        
        Args:
            document: Document model instance
        
        Returns:
            Status dict
        """
        es_success = self.es_service.index_document(document)
        qdrant_success = self.qdrant_service.index_document(document)
        
        return {
            'elasticsearch': es_success,
            'qdrant': qdrant_success,
            'success': es_success and qdrant_success
        }
    
    def delete_document(self, document_id: str) -> Dict[str, bool]:
        """
        Delete document from both services
        
        Args:
            document_id: Document ID
        
        Returns:
            Status dict
        """
        es_success = self.es_service.delete_document(document_id)
        qdrant_success = self.qdrant_service.delete_document(document_id)
        
        return {
            'elasticsearch': es_success,
            'qdrant': qdrant_success,
            'success': es_success and qdrant_success
        }
```

---

#### Task 3.4: Management Commands for Indexing
**Assignee:** Backend Developer
**Time:** 1 day
**Priority:** High

```python
# search/management/commands/rebuild_search_index.py

"""
Management command to rebuild search indices
"""

from django.core.management.base import BaseCommand
from search.models import Document
from search.services.hybrid_search import HybridSearchService
from search.services.elasticsearch_service import ElasticsearchService
from search.services.qdrant_service import QdrantService
import time

class Command(BaseCommand):
    help = 'Rebuild search indices (Elasticsearch and Qdrant)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--service',
            type=str,
            choices=['all', 'elasticsearch', 'qdrant'],
            default='all',
            help='Which service to rebuild'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for indexing'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate indices'
        )
    
    def handle(self, *args, **options):
        service = options['service']
        batch_size = options['batch_size']
        force = options['force']
        
        self.stdout.write("="*60)
        self.stdout.write("REBUILDING SEARCH INDICES")
        self.stdout.write("="*60)
        
        start_time = time.time()
        
        # Get all active documents
        documents = Document.objects.filter(is_active=True).order_by('created_at')
        total_docs = documents.count()
        
        self.stdout.write(f"\nFound {total_docs} documents to index")
        
        # Rebuild Elasticsearch
        if service in ['all', 'elasticsearch']:
            self.stdout.write("\n--- Elasticsearch ---")
            self.rebuild_elasticsearch(documents, batch_size, force)
        
        # Rebuild Qdrant
        if service in ['all', 'qdrant']:
            self.stdout.write("\n--- Qdrant ---")
            self.rebuild_qdrant(documents, batch_size, force)
        
        elapsed = time.time() - start_time
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"✓ Rebuild completed in {elapsed:.2f}s"))
        self.stdout.write("="*60)
    
    def rebuild_elasticsearch(self, documents, batch_size, force):
        """Rebuild Elasticsearch index"""
        es_service = ElasticsearchService()
        
        # Create/recreate index
        self.stdout.write("Creating index...")
        es_service.create_index(force=force)
        
        # Bulk index in batches
        total = documents.count()
        processed = 0
        
        for i in range(0, total, batch_size):
            batch = list(documents[i:i + batch_size])
            
            result = es_service.bulk_index_documents(batch)
            processed += result['success']
            
            progress = (processed / total) * 100
            self.stdout.write(
                f"Progress: {processed}/{total} ({progress:.1f}%)"
            )
        
        self.stdout.write(
            self.style.SUCCESS(f"✓ Indexed {processed} documents in Elasticsearch")
        )
    
    def rebuild_qdrant(self, documents, batch_size, force):
        """Rebuild Qdrant collection"""
        qdrant_service = QdrantService()
        
        # Create/recreate collection
        self.stdout.write("Creating collection...")
        qdrant_service.create_collection(force=force)
        
        # Bulk index in batches
        total = documents.count()
        processed = 0
        
        for i in range(0, total, batch_size):
            batch = list(documents[i:i + batch_size])
            
            result = qdrant_service.bulk_index_documents(batch, batch_size=batch_size)
            processed += result['success']
            
            progress = (processed / total) * 100
            self.stdout.write(
                f"Progress: {processed}/{total} ({progress:.1f}%)"
            )
        
        self.stdout.write(
            self.style.SUCCESS(f"✓ Indexed {processed} documents in Qdrant")
        )
```

```python
# search/management/commands/index_document.py

"""
Management command to index a single document
"""

from django.core.management.base import BaseCommand
from search.models import Document
from search.services.hybrid_search import HybridSearchService

class Command(BaseCommand):
    help = 'Index a single document by ID'
    
    def add_arguments(self, parser):
        parser.add_argument('document_id', type=str, help='Document UUID')
    
    def handle(self, *args, **options):
        document_id = options['document_id']
        
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Document not found: {document_id}')
            )
            return
        
        self.stdout.write(f'Indexing document: {document.title}')
        
        service = HybridSearchService()
        result = service.index_document(document)
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Document indexed successfully')
            )
            self.stdout.write(f"  Elasticsearch: {'✓' if result['elasticsearch'] else '✗'}")
            self.stdout.write(f"  Qdrant: {'✓' if result['qdrant'] else '✗'}")
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ Indexing failed')
            )
```

**Usage Examples:**

```bash
# Rebuild all indices
python manage.py rebuild_search_index --force

# Rebuild only Elasticsearch
python manage.py rebuild_search_index --service elasticsearch --batch-size 200

# Rebuild only Qdrant
python manage.py rebuild_search_index --service qdrant

# Index single document
python manage.py index_document 12345678-1234-1234-1234-123456789012
```

**Checklist:**
- [ ] Implement Qdrant service
- [ ] Implement fusion algorithms (RRF, Weighted)
- [ ] Implement hybrid search service
- [ ] Create management commands
- [ ] Test indexing pipeline
- [ ] Test search with both engines
- [ ] Test fusion quality
- [ ] Performance benchmarks

---

**Продолжить с Sprint 5-6: API Endpoints & Caching?**