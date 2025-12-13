"""
Internationalization API Routes
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ios_core.i18n.language_detector import language_detector
from ios_core.i18n.translator import translator
from ios_core.i18n.multilingual_processor import multilingual_processor
from ios_core.i18n.locale_manager import locale_manager
from ios_core.security.rbac import require_permission, Permission
from ..dependencies import get_current_user

router = APIRouter()


class DetectLanguageRequest(BaseModel):
    text: str
    hint: Optional[str] = None


class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str


class ProcessDocumentRequest(BaseModel):
    document_id: str
    generate_translations: bool = False
    target_languages: Optional[List[str]] = None


class MultilingualSearchRequest(BaseModel):
    query: str
    query_language: Optional[str] = None
    search_languages: Optional[List[str]] = None
    limit: int = 10


@router.post("/detect-language")
async def detect_language(
    request: DetectLanguageRequest
):
    """
    Detect text language
    
    Uses ensemble of detection methods for accuracy.
    """
    
    try:
        result = language_detector.detect(
            text=request.text,
            hint=request.hint
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Language detection failed: {str(e)}"
        )


@router.post("/translate")
async def translate_text(
    request: TranslateRequest
):
    """
    Translate text
    
    Supports: de, ru, en
    """
    
    try:
        translated = await translator.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
        
        return {
            "original": request.text,
            "translated": translated,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/process-document")
@require_permission(Permission.DOCUMENT_UPDATE)
async def process_document_multilingual(
    request: ProcessDocumentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Process document for multilingual support
    
    - Detects language
    - Generates translations (optional)
    - Creates multilingual indexes
    
    Requires: DOCUMENT_UPDATE permission
    """
    
    try:
        # Process document
        result = await multilingual_processor.process_document(
            doc_id=request.document_id,
            generate_translations=request.generate_translations,
            target_languages=request.target_languages
        )
        
        # Create multilingual index
        if request.generate_translations:
            index_result = await multilingual_processor.create_multilingual_index(
                doc_id=request.document_id
            )
            result['indexing'] = index_result
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multilingual processing failed: {str(e)}"
        )


@router.post("/search-multilingual")
@require_permission(Permission.DOCUMENT_READ)
async def search_multilingual(
    request: MultilingualSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Search across multiple languages
    
    - Auto-detects query language
    - Translates query to target languages
    - Searches in all languages
    - Returns merged results
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        results = await multilingual_processor.search_multilingual(
            query=request.query,
            query_language=request.query_language,
            search_languages=request.search_languages,
            limit=request.limit
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multilingual search failed: {str(e)}"
        )


@router.get("/translations/{lang}")
async def get_translations(
    lang: str
):
    """
    Get UI translations for language
    
    Returns all translation strings for the specified language.
    """
    
    try:
        translations = locale_manager.get_all(lang=lang)
        
        if not translations:
            raise HTTPException(
                status_code=404,
                detail=f"Translations not found for language: {lang}"
            )
        
        return {
            "language": lang,
            "translations": translations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get translations: {str(e)}"
        )


@router.get("/supported-languages")
async def get_supported_languages():
    """
    Get list of supported languages
    """
    
    return {
        "languages": [
            {
                "code": "de",
                "name": "Deutsch",
                "native_name": "Deutsch"
            },
            {
                "code": "ru",
                "name": "Russian",
                "native_name": "Русский"
            },
            {
                "code": "en",
                "name": "English",
                "native_name": "English"
            }
        ]
    }