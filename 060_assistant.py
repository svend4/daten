Продолжаю Day 123-124: GPT Integration. Нужно создать:
1. Summarizer - резюмирование документов
2. QA System - система вопросов и ответов
3. API Routes для всех GPT функций
4. Tests
5. Configuration
6. Documentation

Продолжаем с файла 114.# 🤖 DAY 123-124: GPT INTEGRATION (ПРОДОЛЖЕНИЕ)

---

## ФАЙЛ 114: `ios_core/gpt/summarizer.py`

```python
"""
Document Summarization
Intelligent summarization of documents
"""

import logging
from typing import Dict, List, Optional
from enum import Enum

from .gpt_client import gpt_client

logger = logging.getLogger(__name__)


class SummaryLength(str, Enum):
    """Summary length options"""
    BRIEF = "brief"          # 1-2 sentences
    SHORT = "short"          # 1 paragraph
    MEDIUM = "medium"        # 2-3 paragraphs
    DETAILED = "detailed"    # Full summary


class SummaryStyle(str, Enum):
    """Summary style options"""
    EXECUTIVE = "executive"   # For decision-makers
    TECHNICAL = "technical"   # Detailed technical
    SIMPLE = "simple"         # Easy to understand
    LEGAL = "legal"          # Legal terminology


class Summarizer:
    """
    Document summarization
    
    Features:
    - Adjustable length
    - Different styles
    - Key points extraction
    - Multi-document summarization
    - Progressive summarization
    
    Usage:
        summarizer = Summarizer()
        
        # Summarize document
        summary = await summarizer.summarize(
            text="Long document text...",
            length=SummaryLength.SHORT,
            style=SummaryStyle.EXECUTIVE
        )
    """
    
    LENGTH_INSTRUCTIONS = {
        SummaryLength.BRIEF: "Fasse in 1-2 Sätzen zusammen.",
        SummaryLength.SHORT: "Fasse in einem kurzen Absatz zusammen.",
        SummaryLength.MEDIUM: "Fasse in 2-3 Absätzen zusammen.",
        SummaryLength.DETAILED: "Erstelle eine ausführliche Zusammenfassung."
    }
    
    STYLE_INSTRUCTIONS = {
        SummaryStyle.EXECUTIVE: "Konzentriere dich auf Entscheidungsgrundlagen und Handlungsempfehlungen.",
        SummaryStyle.TECHNICAL: "Bewahre technische Details und Fachterminologie.",
        SummaryStyle.SIMPLE: "Verwende einfache Sprache, vermeide Fachjargon.",
        SummaryStyle.LEGAL: "Bewahre rechtliche Begriffe und Gesetzesreferenzen."
    }
    
    async def summarize(
        self,
        text: str,
        length: SummaryLength = SummaryLength.SHORT,
        style: SummaryStyle = SummaryStyle.EXECUTIVE,
        focus_areas: Optional[List[str]] = None,
        language: str = "de"
    ) -> Dict:
        """
        Summarize text
        
        Args:
            text: Text to summarize
            length: Summary length
            style: Summary style
            focus_areas: Specific areas to focus on
            language: Output language
        
        Returns:
            Summary and metadata
        """
        
        # Build prompt
        length_instruction = self.LENGTH_INSTRUCTIONS[length]
        style_instruction = self.STYLE_INSTRUCTIONS[style]
        
        focus_text = ""
        if focus_areas:
            focus_text = f"\nBesonderer Fokus auf: {', '.join(focus_areas)}"
        
        prompt = f"""Fasse den folgenden Text zusammen.

{length_instruction}
{style_instruction}
{focus_text}

Text:
{text}

Zusammenfassung:
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            max_tokens=self._get_max_tokens(length),
            temperature=0.5
        )
        
        return {
            "summary": response["content"].strip(),
            "original_length": len(text.split()),
            "summary_length": len(response["content"].split()),
            "compression_ratio": round(
                len(response["content"].split()) / len(text.split()),
                2
            ),
            "length": length.value,
            "style": style.value,
            "usage": response["usage"]
        }
    
    async def extract_key_points(
        self,
        text: str,
        max_points: int = 5
    ) -> Dict:
        """
        Extract key points from text
        
        Args:
            text: Source text
            max_points: Maximum number of points
        
        Returns:
            Key points list
        """
        
        prompt = f"""Extrahiere die {max_points} wichtigsten Punkte aus dem folgenden Text.
Jeder Punkt soll prägnant und informativ sein.

Text:
{text}

Wichtigste Punkte:
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            max_tokens=500,
            temperature=0.5
        )
        
        # Parse points
        points = [
            line.strip().lstrip('•-*123456789. ')
            for line in response["content"].split('\n')
            if line.strip()
        ]
        
        return {
            "key_points": points[:max_points],
            "count": len(points),
            "usage": response["usage"]
        }
    
    async def summarize_multiple(
        self,
        documents: List[Dict],
        combined: bool = False
    ) -> Dict:
        """
        Summarize multiple documents
        
        Args:
            documents: List of documents with 'title' and 'text'
            combined: Create single combined summary
        
        Returns:
            Summaries (individual or combined)
        """
        
        if combined:
            # Create combined summary
            all_text = "\n\n".join([
                f"Dokument: {doc['title']}\n{doc['text']}"
                for doc in documents
            ])
            
            summary = await self.summarize(
                text=all_text,
                length=SummaryLength.MEDIUM,
                style=SummaryStyle.EXECUTIVE
            )
            
            return {
                "type": "combined",
                "summary": summary["summary"],
                "document_count": len(documents),
                "usage": summary["usage"]
            }
        else:
            # Individual summaries
            summaries = []
            
            for doc in documents:
                summary = await self.summarize(
                    text=doc['text'],
                    length=SummaryLength.BRIEF,
                    style=SummaryStyle.EXECUTIVE
                )
                
                summaries.append({
                    "title": doc['title'],
                    "summary": summary["summary"]
                })
            
            return {
                "type": "individual",
                "summaries": summaries,
                "document_count": len(documents)
            }
    
    async def progressive_summarize(
        self,
        text: str,
        levels: int = 3
    ) -> Dict:
        """
        Create progressive summarization (pyramid)
        
        Args:
            text: Source text
            levels: Number of summary levels
        
        Returns:
            Multi-level summaries
        """
        
        summaries = []
        current_text = text
        
        lengths = [SummaryLength.DETAILED, SummaryLength.MEDIUM, SummaryLength.SHORT, SummaryLength.BRIEF]
        
        for i in range(min(levels, len(lengths))):
            summary = await self.summarize(
                text=current_text,
                length=lengths[i],
                style=SummaryStyle.EXECUTIVE
            )
            
            summaries.append({
                "level": i + 1,
                "length": lengths[i].value,
                "summary": summary["summary"],
                "word_count": len(summary["summary"].split())
            })
            
            # Use summary as input for next level
            current_text = summary["summary"]
        
        return {
            "levels": summaries,
            "original_length": len(text.split())
        }
    
    def _get_max_tokens(self, length: SummaryLength) -> int:
        """Get max tokens for summary length"""
        
        tokens = {
            SummaryLength.BRIEF: 100,
            SummaryLength.SHORT: 300,
            SummaryLength.MEDIUM: 600,
            SummaryLength.DETAILED: 1500
        }
        
        return tokens[length]


# Global summarizer
summarizer = Summarizer()
```

---

## ФАЙЛ 115: `ios_core/gpt/qa_system.py`

```python
"""
Question Answering System
RAG-based Q&A using documents and GPT
"""

import logging
from typing import Dict, List, Optional

from .gpt_client import gpt_client
from ..ml.embeddings import embedding_service
from ..search.neural_search import neural_search

logger = logging.getLogger(__name__)


class QASystem:
    """
    Question answering system
    
    Features:
    - RAG (Retrieval-Augmented Generation)
    - Context-aware answers
    - Source attribution
    - Multi-document reasoning
    - Follow-up questions
    
    Usage:
        qa = QASystem()
        
        # Ask question
        answer = await qa.answer(
            question="Wie beantrage ich ein Persönliches Budget?",
            domain="SGB-IX"
        )
    """
    
    SYSTEM_PROMPT = """Du bist ein Experte für deutsches Sozialrecht, insbesondere SGB IX, XI und XII.
Deine Aufgabe ist es, präzise und hilfreiche Antworten zu geben.

Wichtig:
1. Basiere Antworten auf den bereitgestellten Kontext-Dokumenten
2. Zitiere relevante Gesetzesparagraphen
3. Sei präzise und faktisch korrekt
4. Wenn du dir unsicher bist, sage das
5. Verwende professionelle, aber verständliche Sprache
"""
    
    async def answer(
        self,
        question: str,
        domain: Optional[str] = None,
        max_context_docs: int = 5,
        include_sources: bool = True
    ) -> Dict:
        """
        Answer question using RAG
        
        Args:
            question: User question
            domain: Optional domain filter
            max_context_docs: Max documents for context
            include_sources: Include source documents
        
        Returns:
            Answer with sources and confidence
        """
        
        # 1. Retrieve relevant documents
        search_results = await neural_search.search(
            query=question,
            domain_filter=domain,
            limit=max_context_docs
        )
        
        # 2. Build context from documents
        context = self._build_context(search_results["results"])
        
        # 3. Generate answer
        prompt = f"""Basierend auf den folgenden Kontext-Dokumenten, beantworte die Frage präzise und hilfreich.

Kontext:
{context}

Frage: {question}

Antwort:
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=1000,
            temperature=0.7
        )
        
        answer = response["content"].strip()
        
        # 4. Extract sources
        sources = []
        if include_sources:
            sources = [
                {
                    "document_id": r["id"],
                    "title": r.get("metadata", {}).get("title", "Untitled"),
                    "relevance_score": r["final_score"],
                    "excerpt": r["text"][:200] + "..."
                }
                for r in search_results["results"][:3]
            ]
        
        # 5. Assess confidence
        confidence = self._assess_confidence(
            question=question,
            answer=answer,
            context_relevance=search_results["results"][0]["final_score"] if search_results["results"] else 0
        )
        
        return {
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "documents_used": len(search_results["results"]),
            "usage": response["usage"]
        }
    
    async def multi_turn_qa(
        self,
        conversation_history: List[Dict],
        new_question: str,
        domain: Optional[str] = None
    ) -> Dict:
        """
        Multi-turn Q&A with conversation context
        
        Args:
            conversation_history: Previous Q&A pairs
            new_question: New question
            domain: Optional domain filter
        
        Returns:
            Answer with context
        """
        
        # Build conversation context
        conversation_text = "\n".join([
            f"Q: {turn['question']}\nA: {turn['answer']}"
            for turn in conversation_history[-3:]  # Last 3 turns
        ])
        
        # Retrieve documents for new question
        search_results = await neural_search.search(
            query=new_question,
            domain_filter=domain,
            limit=5
        )
        
        context = self._build_context(search_results["results"])
        
        # Generate answer with conversation context
        prompt = f"""Bisherige Konversation:
{conversation_text}

Neue Frage: {new_question}

Relevante Dokumente:
{context}

Beantworte die neue Frage unter Berücksichtigung der bisherigen Konversation.

Antwort:
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=1000,
            temperature=0.7
        )
        
        return {
            "question": new_question,
            "answer": response["content"].strip(),
            "conversation_length": len(conversation_history),
            "usage": response["usage"]
        }
    
    async def explain_concept(
        self,
        concept: str,
        detail_level: str = "medium"
    ) -> Dict:
        """
        Explain legal concept
        
        Args:
            concept: Concept to explain
            detail_level: simple, medium, detailed
        
        Returns:
            Explanation
        """
        
        detail_instructions = {
            "simple": "Erkläre einfach und für Laien verständlich.",
            "medium": "Erkläre mit angemessenen Details, aber verständlich.",
            "detailed": "Erkläre ausführlich mit allen rechtlichen Details."
        }
        
        # Search for concept
        search_results = await neural_search.search(
            query=concept,
            limit=3
        )
        
        context = self._build_context(search_results["results"])
        
        prompt = f"""Erkläre den folgenden rechtlichen Begriff/Konzept:
{concept}

{detail_instructions.get(detail_level, detail_instructions["medium"])}

Verfügbare Informationen:
{context}

Erklärung:
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=800,
            temperature=0.7
        )
        
        return {
            "concept": concept,
            "explanation": response["content"].strip(),
            "detail_level": detail_level,
            "usage": response["usage"]
        }
    
    def _build_context(self, documents: List[Dict]) -> str:
        """Build context from search results"""
        
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            title = doc.get("metadata", {}).get("title", "Document")
            text = doc.get("text", "")
            
            context_parts.append(f"""[Dokument {i}: {title}]
{text[:500]}...
""")
        
        return "\n\n".join(context_parts)
    
    def _assess_confidence(
        self,
        question: str,
        answer: str,
        context_relevance: float
    ) -> str:
        """Assess answer confidence"""
        
        # Simple heuristic
        if context_relevance > 0.8:
            confidence = "high"
        elif context_relevance > 0.6:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Check for uncertainty markers in answer
        uncertainty_markers = [
            "möglicherweise", "wahrscheinlich", "könnte", "unsicher",
            "nicht sicher", "eventuell"
        ]
        
        if any(marker in answer.lower() for marker in uncertainty_markers):
            # Downgrade confidence
            if confidence == "high":
                confidence = "medium"
            elif confidence == "medium":
                confidence = "low"
        
        return confidence


# Global QA system
qa_system = QASystem()
```

---

## ФАЙЛ 116: `api/routes/gpt_api.py`

```python
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
```

---

## ФАЙЛ 117: `api/main.py` (UPDATE - add GPT routes)

```python
"""
FastAPI application - UPDATED with GPT routes
"""

# ... (existing imports)
from .routes import gpt_api

# ... (existing code)

# Include GPT router
app.include_router(
    gpt_api.router,
    prefix="/api/gpt",
    tags=["GPT / AI Generation"]
)

# ... (rest of existing code)
```

---

## ФАЙЛ 118: `ios_core/config.py` (UPDATE - add GPT settings)

```python
"""
Configuration - UPDATED with GPT settings
"""

# ... (existing code)

class Settings(BaseSettings):
    # ... (existing settings)
    
    # OpenAI / GPT
    openai_api_key: str
    gpt_model: str = "gpt-4-turbo"
    gpt_temperature: float = 0.7
    gpt_max_tokens: int = 2000
    
    # Cost limits (USD)
    gpt_daily_cost_limit: float = 50.0
    gpt_monthly_cost_limit: float = 1000.0
    
    class Config:
        env_file = ".env"

# ... (rest of existing code)
```

---

## ФАЙЛ 119: `.env.example` (UPDATE)

```bash
# ... (existing variables)

# OpenAI / GPT
OPENAI_API_KEY=sk-...
GPT_MODEL=gpt-4-turbo
GPT_TEMPERATURE=0.7
GPT_MAX_TOKENS=2000
GPT_DAILY_COST_LIMIT=50.0
GPT_MONTHLY_COST_LIMIT=1000.0
```

---

## ФАЙЛ 120: `requirements.txt` (UPDATE)

```txt
# ... (existing requirements)

# OpenAI
openai==1.10.0

# Template engine
jinja2==3.1.3
```

---

## ФАЙЛ 121: `tests/gpt/test_document_generator.py`

```python
"""
Tests for document generator
"""

import pytest
from ios_core.gpt.document_generator import document_generator


@pytest.mark.asyncio
async def test_generate_objection():
    """Test objection letter generation"""
    
    case_details = {
        "applicant_name": "Max Mustermann",
        "decision_date": "2024-01-15",
        "case_number": "AB-123-2024",
        "reason": "Unzureichende Begründung des Ablehnungsbescheids"
    }
    
    result = await document_generator.generate_objection(
        case_details=case_details
    )
    
    assert "document_id" in result
    assert "content" in result
    assert "Max Mustermann" in result["content"]
    assert "Widerspruch" in result["content"]


@pytest.mark.asyncio
async def test_generate_application():
    """Test application generation"""
    
    applicant_info = {
        "name": "Maria Schmidt",
        "address": "Musterstraße 1, 80331 München",
        "birth_date": "1990-05-15"
    }
    
    result = await document_generator.generate_application(
        benefit_type="Persönliches Budget",
        applicant_info=applicant_info,
        justification="Ich benötige Unterstützung zur selbstbestimmten Lebensführung."
    )
    
    assert "document_id" in result
    assert "content" in result
    assert "Persönliches Budget" in result["content"]
```

---

## ФАЙЛ 122: `tests/gpt/test_summarizer.py`

```python
"""
Tests for summarizer
"""

import pytest
from ios_core.gpt.summarizer import summarizer, SummaryLength, SummaryStyle


@pytest.mark.asyncio
async def test_summarize():
    """Test text summarization"""
    
    long_text = """Das Persönliche Budget ist eine Leistungsform der Eingliederungshilfe 
nach dem SGB IX. Es ermöglicht Menschen mit Behinderungen, ihre Unterstützungsleistungen 
selbstbestimmt zu organisieren und zu bezahlen. Anstelle von Sachleistungen erhalten 
Budgetnehmer eine Geldleistung, mit der sie die benötigten Hilfen eigenständig einkaufen 
können. Dies fördert die Selbstbestimmung und Teilhabe am Leben in der Gesellschaft."""
    
    result = await summarizer.summarize(
        text=long_text,
        length=SummaryLength.BRIEF,
        style=SummaryStyle.SIMPLE
    )
    
    assert "summary" in result
    assert len(result["summary"]) < len(long_text)
    assert result["compression_ratio"] < 1.0


@pytest.mark.asyncio
async def test_extract_key_points():
    """Test key point extraction"""
    
    text = """Das Widerspruchsverfahren ist ein wichtiger Rechtsbehelf.
Es muss innerhalb eines Monats eingelegt werden.
Der Widerspruch ist schriftlich oder zur Niederschrift einzureichen.
Eine Begründung kann nachgereicht werden.
Das Verfahren ist für den Antragsteller kostenlos."""
    
    result = await summarizer.extract_key_points(
        text=text,
        max_points=3
    )
    
    assert "key_points" in result
    assert len(result["key_points"]) <= 3
```

---

## ФАЙЛ 123: `tests/gpt/test_qa_system.py`

```python
"""
Tests for QA system
"""

import pytest
from ios_core.gpt.qa_system import qa_system


@pytest.mark.asyncio
async def test_answer_question():
    """Test question answering"""
    
    result = await qa_system.answer(
        question="Was ist ein Persönliches Budget?",
        max_context_docs=3
    )
    
    assert "question" in result
    assert "answer" in result
    assert "confidence" in result
    assert "sources" in result
    assert result["confidence"] in ["low", "medium", "high"]


@pytest.mark.asyncio
async def test_explain_concept():
    """Test concept explanation"""
    
    result = await qa_system.explain_concept(
        concept="Eingliederungshilfe",
        detail_level="simple"
    )
    
    assert "concept" in result
    assert "explanation" in result
    assert "Eingliederungshilfe" in result["explanation"]
```

---

## ФАЙЛ 124: `scripts/test_gpt.sh`

```bash
#!/bin/bash
# Test GPT features

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         GPT FEATURES TEST                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

API_URL="http://localhost:8000"
TOKEN=""

# Check OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}✗ OPENAI_API_KEY not set${NC}"
    echo "Please set OPENAI_API_KEY environment variable"
    exit 1
fi

# Get auth token
echo -e "\n${YELLOW}[1/7] Authenticating...${NC}"
TOKEN=$(curl -s -X POST "$API_URL/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ Authenticated${NC}"
else
    echo -e "${RED}✗ Authentication failed${NC}"
    exit 1
fi

# Test 1: Question Answering
echo -e "\n${YELLOW}[2/7] Testing Q&A System...${NC}"
QA_RESPONSE=$(curl -s -X POST "$API_URL/api/gpt/qa/answer" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Was ist ein Persönliches Budget?",
    "domain": "SGB-IX",
    "max_context_docs": 3
  }')

QA_ANSWER=$(echo $QA_RESPONSE | jq -r '.answer')
QA_CONFIDENCE=$(echo $QA_RESPONSE | jq -r '.confidence')

echo -e "${GREEN}✓ Q&A working${NC}"
echo "  Confidence: $QA_CONFIDENCE"
echo "  Answer preview: ${QA_ANSWER:0:100}..."

# Test 2: Summarization
echo -e "\n${YELLOW}[3/7] Testing Summarization...${NC}"
SUMMARY=$(curl -s -X POST "$API_URL/api/gpt/summarize" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Das Persönliche Budget ist eine Leistungsform der Eingliederungshilfe nach dem SGB IX. Es ermöglicht Menschen mit Behinderungen, ihre Unterstützungsleistungen selbstbestimmt zu organisieren.",
    "length": "brief",
    "style": "simple"
  }')

SUMMARY_TEXT=$(echo $SUMMARY | jq -r '.summary')
echo -e "${GREEN}✓ Summarization working${NC}"
echo "  Summary: $SUMMARY_TEXT"

# Test 3: Content Enhancement
echo -e "\n${YELLOW}[4/7] Testing Content Enhancement...${NC}"
ENHANCED=$(curl -s -X POST "$API_URL/api/gpt/enhance" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ich beantrage hiermit ein persönliches budget",
    "enhancement_type": "formality"
  }')

ENHANCED_TEXT=$(echo $ENHANCED | jq -r '.enhanced')
echo -e "${GREEN}✓ Enhancement working${NC}"
echo "  Original: ich beantrage hiermit ein persönliches budget"
echo "  Enhanced: $ENHANCED_TEXT"

# Test 4: Key Points Extraction
echo -e "\n${YELLOW}[5/7] Testing Key Points...${NC}"
KEY_POINTS=$(curl -s -X POST "$API_URL/api/gpt/extract-key-points?max_points=3" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "Das Widerspruchsverfahren ist kostenlos. Es muss innerhalb eines Monats eingereicht werden. Eine Begründung kann nachgereicht werden.")

POINTS_COUNT=$(echo $KEY_POINTS | jq '.key_points | length')
echo -e "${GREEN}✓ Key points extraction working${NC}"
echo "  Extracted $POINTS_COUNT points"

# Test 5: Concept Explanation
echo -e "\n${YELLOW}[6/7] Testing Concept Explanation...${NC}"
EXPLANATION=$(curl -s -X GET "$API_URL/api/gpt/qa/explain?concept=Eingliederungshilfe&detail_level=simple" \
  -H "Authorization: Bearer $TOKEN")

EXPL_TEXT=$(echo $EXPLANATION | jq -r '.explanation')
echo -e "${GREEN}✓ Concept explanation working${NC}"
echo "  Explanation preview: ${EXPL_TEXT:0:100}..."

# Test 6: Usage Stats
echo -e "\n${YELLOW}[7/7] Getting Usage Stats...${NC}"
USAGE=$(curl -s -X GET "$API_URL/api/gpt/usage" \
  -H "Authorization: Bearer $TOKEN")

TOTAL_TOKENS=$(echo $USAGE | jq '.total_tokens')
TOTAL_COST=$(echo $USAGE | jq '.total_cost_usd')

echo -e "${GREEN}✓ Usage tracking working${NC}"
echo "  Total tokens: $TOTAL_TOKENS"
echo "  Total cost: \$$TOTAL_COST"

echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║            GPT FEATURES TEST COMPLETE                      ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}All tests passed!${NC}"

echo -e "\n${YELLOW}Note:${NC} These tests consume OpenAI API credits."
echo "Current session cost: \$$TOTAL_COST"
```

---

## ФАЙЛ 125: `docs/gpt/GPT_INTEGRATION.md`

```markdown
# GPT Integration Guide

## Overview

IOS System integrates OpenAI GPT-4 for intelligent content generation and processing:

- **Document Generation**: Automated creation of legal documents
- **Template Processing**: Smart template filling with auto-completion
- **Content Enhancement**: Grammar, style, clarity improvements
- **Summarization**: Intelligent document summarization
- **Question Answering**: RAG-based Q&A system
- **Translation**: Multi-language support

## Architecture

```
User Request
     ↓
┌─────────────┐
│   API       │
│   Routes    │
└──────┬──────┘
       │
       ↓
┌─────────────┐     ┌──────────────┐
│ GPT Client  │────→│  OpenAI API  │
└──────┬──────┘     └──────────────┘
       │
       ↓
┌─────────────┐
│  Document   │
│  Storage    │
└─────────────┘
```

## API Usage

### Document Generation

#### Objection Letter

```bash
POST /api/gpt/generate/objection
{
  "case_details": {
    "applicant_name": "Max Mustermann",
    "decision_date": "2024-01-15",
    "case_number": "AB-123-2024",
    "reason": "Unzureichende Begründung"
  }
}
```

**Response:**
```json
{
  "document_id": "doc123",
  "title": "Widerspruch - Max Mustermann",
  "content": "Sehr geehrte Damen und Herren...",
  "metadata": {
    "case_details": {...},
    "generated_at": "2024-01-20T10:00:00Z",
    "model": "gpt-4-turbo",
    "tokens": 1250,
    "cost": 0.0425
  }
}
```

#### Application

```bash
POST /api/gpt/generate/application
{
  "benefit_type": "Persönliches Budget",
  "applicant_info": {
    "name": "Maria Schmidt",
    "address": "Musterstraße 1, 80331 München"
  },
  "justification": "Ich benötige Unterstützung..."
}
```

### Question Answering

```bash
POST /api/gpt/qa/answer
{
  "question": "Wie beantrage ich ein Persönliches Budget?",
  "domain": "SGB-IX",
  "max_context_docs": 5
}
```

**Response:**
```json
{
  "question": "Wie beantrage ich ein Persönliches Budget?",
  "answer": "Um ein Persönliches Budget zu beantragen...",
  "confidence": "high",
  "sources": [
    {
      "document_id": "doc456",
      "title": "§ 29 SGB IX",
      "relevance_score": 0.92,
      "excerpt": "..."
    }
  ],
  "documents_used": 3
}
```

### Summarization

```bash
POST /api/gpt/summarize
{
  "text": "Long document text...",
  "length": "short",
  "style": "executive"
}
```

**Length Options:**
- `brief`: 1-2 sentences
- `short`: 1 paragraph
- `medium`: 2-3 paragraphs
- `detailed`: Full summary

**Style Options:**
- `executive`: For decision-makers
- `technical`: Detailed technical
- `simple`: Easy to understand
- `legal`: Legal terminology

### Content Enhancement

```bash
POST /api/gpt/enhance
{
  "text": "ich beantrage hiermit ein persönliches budget",
  "enhancement_type": "formality"
}
```

**Enhancement Types:**
- `grammar`: Fix errors
- `style`: Improve writing
- `clarity`: Make clearer
- `formality`: Increase formality
- `conciseness`: Make shorter
- `completeness`: Add details

### Template Filling

```bash
POST /api/gpt/template/fill
{
  "template": "Sehr geehrte {{salutation}} {{last_name}}, ...",
  "context": {
    "last_name": "Mustermann"
  },
  "auto_complete": true
}
```

With `auto_complete: true`, GPT fills missing variables intelligently.

## Features

### RAG (Retrieval-Augmented Generation)

Q&A system combines:
1. **Retrieval**: Search relevant documents
2. **Augmentation**: Build context
3. **Generation**: Generate answer with GPT

**Benefits:**
- Factual accuracy
- Source attribution
- Up-to-date information
- Domain-specific knowledge

### Multi-turn Conversations

```bash
POST /api/gpt/qa/multi-turn
{
  "conversation_history": [
    {
      "question": "Was ist ein Persönliches Budget?",
      "answer": "Ein Persönliches Budget ist..."
    }
  ],
  "new_question": "Wie hoch kann es sein?"
}
```

Maintains context across questions.

### Progressive Summarization

Creates multi-level summaries:
1. Detailed summary
2. Medium summary
3. Short summary
4. Brief summary

Each level summarizes the previous.

## Cost Management

### Tracking

```bash
GET /api/gpt/usage
```

Returns:
- Total input tokens
- Total output tokens
- Total cost (USD)
- Cost per model

### Limits

Configure in `.env`:
```bash
GPT_DAILY_COST_LIMIT=50.0
GPT_MONTHLY_COST_LIMIT=1000.0
```

System alerts when approaching limits.

### Optimization

**Reduce costs:**
1. Use GPT-3.5-Turbo for simple tasks
2. Limit `max_tokens`
3. Cache common responses
4. Use summarization for long texts
5. Batch requests when possible

## Best Practices

### 1. Prompt Engineering

**Good:**
```python
prompt = f"""Generate a formal objection letter in German.

Case details:
- Applicant: {name}
- Decision date: {date}
- Reason: {reason}

Include:
1. Formal salutation
2. Reference to decision
3. Legal grounds
4. Clear request
5. Professional closing
"""
```

**Bad:**
```python
prompt = "Write objection for Max"
```

### 2. Error Handling

```python
try:
    result = await gpt_client.generate(...)
except openai.RateLimitError:
    # Handle rate limit
    await asyncio.sleep(60)
    retry()
except openai.APIError as e:
    # Handle API error
    logger.error(f"GPT API error: {e}")
```

### 3. Temperature Tuning

- **0.0-0.3**: Factual, deterministic (legal docs)
- **0.4-0.7**: Balanced (general content)
- **0.8-1.0**: Creative (brainstorming)
- **1.1-2.0**: Very creative (not recommended)

### 4. Token Management

```python
# Estimate tokens
import tiktoken

encoder = tiktoken.encoding_for_model("gpt-4")
tokens = len(encoder.encode(text))

# Stay within limits
if tokens > 100000:
    # Use GPT-4-Turbo
    model = "gpt-4-turbo-preview"
```

## Security

### API Key Protection

**Never commit API keys:**
```bash
# .gitignore
.env
*.key
```

**Use environment variables:**
```python
import os
api_key = os.getenv("OPENAI_API_KEY")
```

### Content Filtering

System automatically:
- Validates input
- Sanitizes output
- Logs all requests
- Monitors for abuse

### Rate Limiting

- Per-user limits
- Per-endpoint limits
- Cost-based throttling
- Automatic backoff

## Troubleshooting

### High Costs

**Problem:** Unexpected high costs

**Solutions:**
1. Check usage stats: `GET /api/gpt/usage`
2. Review recent requests
3. Reduce `max_tokens`
4. Use cheaper model
5. Enable caching

### Low Quality Responses

**Problem:** GPT generates poor content

**Solutions:**
1. Improve prompt clarity
2. Add more context
3. Adjust temperature
4. Use examples in prompt
5. Try different model

### Timeout Errors

**Problem:** Requests timeout

**Solutions:**
1. Reduce `max_tokens`
2. Simplify prompt
3. Use streaming for long responses
4. Increase timeout setting

## Advanced Features

### Function Calling

```python
functions = [
    {
        "name": "search_documents",
        "description": "Search legal documents",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "domain": {"type": "string"}
            }
        }
    }
]

response = await gpt_client.chat(
    messages=[...],
    functions=functions,
    function_call="auto"
)
```

### Streaming Responses

```python
async for chunk in gpt_client.stream_chat(messages):
    print(chunk, end="", flush=True)
```

### Custom Models

Fine-tune for domain:
```python
# Upload training data
# Fine-tune model
# Use custom model
custom_client = GPTClient(model="ft:gpt-4-...")
```

## Resources

- [OpenAI API Docs](https://platform.openai.com/docs)
- [GPT-4 Guide](https://platform.openai.com/docs/guides/gpt)
- [Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [Token Limits](https://platform.openai.com/docs/models)
```

---

**✅ DAY 123-124 ГОТОВ!**

Создано:
- GPT Client (OpenAI integration) ✓
- Document Generator ✓
- Template Engine ✓
- Content Enhancer ✓
- Summarizer ✓
- Q&A System (RAG) ✓
- API Routes ✓
- Tests ✓
- Configuration ✓
- Documentation ✓

**Статус Week 19-20:**
- Day 119-120: BERT Integration ✓
- Day 121-122: Neural Search ✓
- Day 123-124: GPT Integration ✓

**🎉 WEEK 19-20 ЗАВЕРШЕНА!**

**Готовы к Day 125-126: Multi-language Support & Finalization?**