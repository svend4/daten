"""
Multilingual Document Processor
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .language_detector import language_detector
from .translator import translator
from ..ml.embeddings import embedding_service
from ..database import async_session
from ..models import DocumentModel

logger = logging.getLogger(__name__)


class MultilingualProcessor:
    """
    Process documents in multiple languages
    
    Features:
    - Language detection
    - Auto-translation
    - Multi-language indexing
    - Cross-lingual search support
    
    Usage:
        processor = MultilingualProcessor()
        
        # Process document
        result = await processor.process_document(
            doc_id="doc123",
            generate_translations=True
        )
    """
    
    SUPPORTED_LANGUAGES = ['de', 'ru', 'en']
    
    async def process_document(
        self,
        doc_id: str,
        generate_translations: bool = False,
        target_languages: Optional[List[str]] = None
    ) -> Dict:
        """
        Process document for multilingual support
        
        Args:
            doc_id: Document ID
            generate_translations: Auto-translate to other languages
            target_languages: Languages to translate to
        
        Returns:
            Processing result
        """
        
        async with async_session() as session:
            # Get document
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == doc_id)
            )
            doc = result.scalar_one_or_none()
            
            if not doc:
                raise ValueError(f"Document not found: {doc_id}")
            
            # Detect language
            text = f"{doc.title}\n\n{doc.content}"
            detection = language_detector.detect(text, hint='legal')
            
            # Update document metadata
            if not doc.metadata:
                doc.metadata = {}
            
            doc.metadata['detected_language'] = detection['language']
            doc.metadata['language_confidence'] = detection['confidence']
            
            # Generate translations if requested
            translations = {}
            if generate_translations:
                if target_languages is None:
                    target_languages = [
                        lang for lang in self.SUPPORTED_LANGUAGES
                        if lang != detection['language']
                    ]
                
                for target_lang in target_languages:
                    logger.info(
                        f"Translating {doc_id} to {target_lang}"
                    )
                    
                    translated = await translator.translate_document(
                        document={
                            'title': doc.title,
                            'content': doc.content
                        },
                        target_lang=target_lang,
                        fields=['title', 'content']
                    )
                    
                    translations[target_lang] = translated
                
                # Store translations
                doc.metadata['translations'] = translations
            
            # Update multilingual processing timestamp
            doc.metadata['multilingual_processed_at'] = datetime.utcnow().isoformat()
            
            await session.commit()
            
            return {
                'document_id': doc_id,
                'detected_language': detection['language'],
                'confidence': detection['confidence'],
                'translations_generated': list(translations.keys()),
                'translation_count': len(translations)
            }
    
    async def create_multilingual_index(
        self,
        doc_id: str
    ) -> Dict:
        """
        Create embeddings in multiple languages
        
        Args:
            doc_id: Document ID
        
        Returns:
            Indexing result
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == doc_id)
            )
            doc = result.scalar_one_or_none()
            
            if not doc:
                raise ValueError(f"Document not found: {doc_id}")
            
            # Index original
            original_text = f"{doc.title}\n\n{doc.content}"
            
            await embedding_service.index_document(
                doc_id=doc_id,
                text=original_text,
                metadata={
                    **doc.metadata,
                    'language': doc.metadata.get('detected_language', 'de')
                }
            )
            
            indexed_languages = [doc.metadata.get('detected_language', 'de')]
            
            # Index translations if available
            translations = doc.metadata.get('translations', {})
            
            for lang, translation in translations.items():
                translated_text = f"{translation['title']}\n\n{translation['content']}"
                
                # Create separate index entry
                translated_doc_id = f"{doc_id}_{lang}"
                
                await embedding_service.index_document(
                    doc_id=translated_doc_id,
                    text=translated_text,
                    metadata={
                        **doc.metadata,
                        'language': lang,
                        'is_translation': True,
                        'original_doc_id': doc_id
                    }
                )
                
                indexed_languages.append(lang)
            
            return {
                'document_id': doc_id,
                'indexed_languages': indexed_languages,
                'total_indexes': len(indexed_languages)
            }
    
    async def search_multilingual(
        self,
        query: str,
        query_language: Optional[str] = None,
        search_languages: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict:
        """
        Search across multiple languages
        
        Args:
            query: Search query
            query_language: Query language (auto-detect if None)
            search_languages: Languages to search in
            limit: Max results per language
        
        Returns:
            Multilingual search results
        """
        
        # Detect query language if not specified
        if query_language is None:
            detection = language_detector.detect(query, hint='legal')
            query_language = detection['language']
        
        # Default to all languages if not specified
        if search_languages is None:
            search_languages = self.SUPPORTED_LANGUAGES
        
        # Search in each language
        all_results = {}
        
        for target_lang in search_languages:
            # Translate query if needed
            if target_lang != query_language:
                translated_query = await translator.translate(
                    text=query,
                    source_lang=query_language,
                    target_lang=target_lang
                )
            else:
                translated_query = query
            
            # Search
            results = await embedding_service.search_similar(
                query=translated_query,
                limit=limit,
                score_threshold=0.6
            )
            
            # Filter by language
            lang_results = [
                r for r in results
                if r.get('metadata', {}).get('language') == target_lang
            ]
            
            all_results[target_lang] = {
                'query': translated_query,
                'results': lang_results,
                'count': len(lang_results)
            }
        
        return {
            'original_query': query,
            'query_language': query_language,
            'results_by_language': all_results,
            'total_results': sum(
                r['count'] for r in all_results.values()
            )
        }


# Global multilingual processor
multilingual_processor = MultilingualProcessor()