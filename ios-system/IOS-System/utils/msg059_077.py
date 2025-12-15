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