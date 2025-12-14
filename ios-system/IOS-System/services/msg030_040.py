"""
Classification service - wraps the classification engine
"""

import logging
from typing import Dict, List
from dataclasses import dataclass

from ..models import Document

logger = logging.getLogger(__name__)


@dataclass
class Classification:
    """Classification result"""
    document_type: str
    category: str
    subcategory: str = ""
    confidence: float = 0.0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class ClassificationService:
    """Service for document classification"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.rule_classifier = RuleBasedClassifier()
        # ML classifier будет добавлен позже
    
    async def classify(self, document: Document) -> Classification:
        """
        Classify document
        
        Args:
            document: Document to classify
            
        Returns:
            Classification result
        """
        logger.info(f"Classifying document: {document.title}")
        
        # Extract features
        features = self.feature_extractor.extract(document)
        
        # Apply rule-based classifier
        classification = self.rule_classifier.classify(features)
        
        logger.info(
            f"Classified as {classification.document_type} "
            f"with confidence {classification.confidence:.2f}"
        )
        
        return classification


class FeatureExtractor:
    """Extract features from documents"""
    
    def extract(self, document: Document) -> Dict:
        """Extract all features"""
        content = document.content.lower()
        
        features = {
            'keywords': self._extract_keywords(content),
            'entities': self._extract_entities(content),
            'structure': self._analyze_structure(content),
        }
        
        return features
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords"""
        keywords = []
        
        # Common German legal keywords
        keyword_patterns = {
            'widerspruch': ['widerspruch', 'widerspreche'],
            'antrag': ['antrag', 'beantrage'],
            'bescheid': ['bescheid', 'bewilligungsbescheid'],
            'urteil': ['urteil', 'im namen des volkes'],
        }
        
        for category, patterns in keyword_patterns.items():
            if any(pattern in content for pattern in patterns):
                keywords.append(category)
        
        return keywords
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract entities (simplified)"""
        import re
        entities = []
        
        # Paragraphs
        paragraphs = re.findall(r'§\s*(\d+[a-z]?)', content)
        entities.extend([f"§{p}" for p in paragraphs])
        
        # Laws
        laws = re.findall(r'(SGB[\s-]?[IVX]+)', content, re.IGNORECASE)
        entities.extend(laws)
        
        return entities
    
    def _analyze_structure(self, content: str) -> Dict:
        """Analyze document structure"""
        lines = content.split('\n')
        
        return {
            'line_count': len(lines),
            'has_signature': any('mit freundlichen grüßen' in line.lower() for line in lines),
            'has_date': any(self._contains_date(line) for line in lines),
        }
    
    def _contains_date(self, text: str) -> bool:
        """Check if text contains a date"""
        import re
        date_pattern = r'\d{1,2}\.\d{1,2}\.\d{4}'
        return bool(re.search(date_pattern, text))


class RuleBasedClassifier:
    """Rule-based document classifier"""
    
    def classify(self, features: Dict) -> Classification:
        """Classify based on rules"""
        keywords = features.get('keywords', [])
        entities = features.get('entities', [])
        structure = features.get('structure', {})
        
        # Rule 1: Widerspruch
        if 'widerspruch' in keywords and structure.get('has_signature'):
            return Classification(
                document_type='Widerspruch',
                category='Legal',
                subcategory='Objection',
                confidence=0.9,
                tags=['legal', 'objection']
            )
        
        # Rule 2: Antrag
        if 'antrag' in keywords and '§29' in entities:
            return Classification(
                document_type='Antrag',
                category='Application',
                subcategory='Personal Budget',
                confidence=0.85,
                tags=['application', 'personal-budget']
            )
        
        # Rule 3: Bescheid
        if 'bescheid' in keywords and structure.get('has_signature'):
            return Classification(
                document_type='Bescheid',
                category='Decision',
                confidence=0.9,
                tags=['decision', 'official']
            )
        
        # Rule 4: Urteil
        if 'urteil' in keywords:
            return Classification(
                document_type='Urteil',
                category='Legal',
                subcategory='Court Decision',
                confidence=0.95,
                tags=['court', 'decision']
            )
        
        # Default: Unknown
        return Classification(
            document_type='Unknown',
            category='Uncategorized',
            confidence=0.5,
            tags=['uncategorized']
        )