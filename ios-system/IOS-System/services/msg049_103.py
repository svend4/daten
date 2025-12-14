"""
Machine Learning module
"""

from .bert_client import BERTClient
from .embeddings import EmbeddingService
from .similarity import SimilarityService

__all__ = [
    'BERTClient',
    'EmbeddingService',
    'SimilarityService',
]