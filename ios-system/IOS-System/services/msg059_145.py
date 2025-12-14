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