"""
GPT API Routes
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ios_core.gpt.document_generator import document_generator
from ios_core.gpt.template_engine import template_engine
from ios_core.gpt.content_enhancer import content_enhancer, EnhancementType
from ios_core.gpt.summarizer import summarizer, SummaryLength, SummaryStyle
from ios_core.gpt.qa_system import qa_system
from ios_core.security.rbac import require_permission, Permission
from ..dependencies import get_current_user

router = APIRouter()


# ========================================================================
# Request/Response Models
# ========================================================================

class GenerateObjectionRequest(BaseModel):
    case_details: dict = Field(..., description="Case information")
    template: Optional[str] = None


class GenerateApplicationRequest(BaseModel):
    benefit_type: str
    applicant_info: dict
    justification: str


class FillTemplateRequest(BaseModel):
    template: str
    context: dict
    auto_complete: bool = True


class EnhanceContentRequest(BaseModel):
    text: str
    enhancement_type: str
    instructions: Optional[str] = None


class SummarizeRequest(BaseModel):
    text: str
    length: str = "short"
    style: str = "executive"
    focus_areas: Optional[List[str]] = None


class AnswerQuestionRequest(BaseModel):
    question: str
    domain: Optional[str] = None
    max_context_docs: int = Field(5, ge=1, le=10)


class MultiTurnQARequest(BaseModel):
    conversation_history: List[dict]
    new_question: str
    domain: Optional[str] = None


# ========================================================================
# Document Generation
# ========================================================================

@router.post("/generate/objection")
@require_permission(Permission.DOCUMENT_CREATE)
async def generate_objection(
    request: GenerateObjectionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate objection letter (Widerspruch)
    
    Creates a formal objection against an administrative decision.
    
    Requires: DOCUMENT_CREATE permission
    """
    
    try:
        result = await document_generator.generate_objection(
            case_details=request.case_details,
            template=request.template
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document generation failed: {str(e)}"
        )


@router.post("/generate/application")
@require_permission(Permission.DOCUMENT_CREATE)
async def generate_application(
    request: GenerateApplicationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate benefit application (Antrag)
    
    Creates a formal application for social benefits.
    
    Requires: DOCUMENT_CREATE permission
    """
    
    try:
        result = await document_generator.generate_application(
            benefit_type=request.benefit_type,
            applicant_info=request.applicant_info,
            justification=request.justification
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Application generation failed: {str(e)}"
        )


# ========================================================================
# Template Processing
# ========================================================================

@router.post("/template/fill")
@require_permission(Permission.DOCUMENT_CREATE)
async def fill_template(
    request: FillTemplateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Fill template with GPT auto-completion
    
    Fills template variables. Missing fields are auto-completed
    using GPT if auto_complete is True.
    
    Requires: DOCUMENT_CREATE permission
    """
    
    try:
        result = await template_engine.fill_template(
            template=request.template,
            context=request.context,
            auto_complete=request.auto_complete
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Template filling failed: {str(e)}"
        )


# ========================================================================
# Content Enhancement
# ========================================================================

@router.post("/enhance")
@require_permission(Permission.DOCUMENT_UPDATE)
async def enhance_content(
    request: EnhanceContentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Enhance content quality
    
    Improves text through:
    - grammar: Fix grammar and spelling
    - style: Improve writing style
    - clarity: Make clearer
    - formality: Increase formality
    - conciseness: Make more concise
    - completeness: Add missing details
    
    Requires: DOCUMENT_UPDATE permission
    """
    
    try:
        enhancement_type = EnhancementType(request.enhancement_type)
        
        result = await content_enhancer.enhance(
            text=request.text,
            enhancement_type=enhancement_type,
            instructions=request.instructions
        )
        
        return result
        
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid enhancement type: {request.enhancement_type}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Enhancement failed: {str(e)}"
        )


@router.post("/proofread")
@require_permission(Permission.DOCUMENT_UPDATE)
async def proofread_text(
    text: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Comprehensive proofreading
    
    Returns corrections and improvement suggestions.
    
    Requires: DOCUMENT_UPDATE permission
    """
    
    try:
        result = await content_enhancer.proofread(text=text)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Proofreading failed: {str(e)}"
        )


@router.post("/translate")
@require_permission(Permission.DOCUMENT_READ)
async def translate_text(
    text: str,
    target_language: str = "de",
    current_user: dict = Depends(get_current_user)
):
    """
    Translate text
    
    Supports: de, ru, en
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        result = await content_enhancer.translate(
            text=text,
            target_language=target_language
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )


# ========================================================================
# Summarization
# ========================================================================

@router.post("/summarize")
@require_permission(Permission.DOCUMENT_READ)
async def summarize_text(
    request: SummarizeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Summarize text
    
    Length options: brief, short, medium, detailed
    Style options: executive, technical, simple, legal
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        length = SummaryLength(request.length)
        style = SummaryStyle(request.style)
        
        result = await summarizer.summarize(
            text=request.text,
            length=length,
            style=style,
            focus_areas=request.focus_areas
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parameter: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )


@router.post("/extract-key-points")
@require_permission(Permission.DOCUMENT_READ)
async def extract_key_points(
    text: str,
    max_points: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """
    Extract key points from text
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        result = await summarizer.extract_key_points(
            text=text,
            max_points=max_points
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Key point extraction failed: {str(e)}"
        )


# ========================================================================
# Question Answering
# ========================================================================

@router.post("/qa/answer")
@require_permission(Permission.DOCUMENT_READ)
async def answer_question(
    request: AnswerQuestionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Answer question using RAG
    
    Retrieves relevant documents and generates answer using GPT.
    Includes source attribution and confidence assessment.
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        result = await qa_system.answer(
            question=request.question,
            domain=request.domain,
            max_context_docs=request.max_context_docs
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Q&A failed: {str(e)}"
        )


@router.post("/qa/multi-turn")
@require_permission(Permission.DOCUMENT_READ)
async def multi_turn_qa(
    request: MultiTurnQARequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Multi-turn question answering
    
    Maintains conversation context for follow-up questions.
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        result = await qa_system.multi_turn_qa(
            conversation_history=request.conversation_history,
            new_question=request.new_question,
            domain=request.domain
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multi-turn Q&A failed: {str(e)}"
        )


@router.get("/qa/explain")
@require_permission(Permission.DOCUMENT_READ)
async def explain_concept(
    concept: str,
    detail_level: str = "medium",
    current_user: dict = Depends(get_current_user)
):
    """
    Explain legal concept
    
    Detail levels: simple, medium, detailed
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        result = await qa_system.explain_concept(
            concept=concept,
            detail_level=detail_level
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Concept explanation failed: {str(e)}"
        )


# ========================================================================
# Usage Stats
# ========================================================================

@router.get("/usage")
@require_permission(Permission.ADMIN_VIEW)
async def get_gpt_usage(
    current_user: dict = Depends(get_current_user)
):
    """
    Get GPT usage statistics
    
    Returns token usage and costs.
    
    Requires: ADMIN_VIEW permission
    """
    
    from ios_core.gpt.gpt_client import gpt_client
    
    stats = gpt_client.get_usage_stats()
    
    return stats