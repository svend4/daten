"""
Content Enhancement
Improve and refine existing content
"""

import logging
from typing import Dict, List, Optional
from enum import Enum

from .gpt_client import gpt_client

logger = logging.getLogger(__name__)


class EnhancementType(str, Enum):
    """Types of content enhancement"""
    GRAMMAR = "grammar"
    STYLE = "style"
    CLARITY = "clarity"
    FORMALITY = "formality"
    CONCISENESS = "conciseness"
    COMPLETENESS = "completeness"


class ContentEnhancer:
    """
    Content improvement and enhancement
    
    Features:
    - Grammar correction
    - Style improvement
    - Clarity enhancement
    - Formality adjustment
    - Content expansion
    - Proofreading
    
    Usage:
        enhancer = ContentEnhancer()
        
        # Improve text
        result = await enhancer.enhance(
            text="Ich beantrage hiermit...",
            enhancement_type=EnhancementType.FORMALITY
        )
    """
    
    ENHANCEMENT_PROMPTS = {
        EnhancementType.GRAMMAR: """Korrigiere alle Grammatik-, Rechtschreib- und Zeichensetzungsfehler.
Behalte den ursprünglichen Stil und Ton bei.""",
        
        EnhancementType.STYLE: """Verbessere den Schreibstil.
Mache den Text flüssiger, professioneller und angenehmer zu lesen.
Behalte alle Fakten und Informationen bei.""",
        
        EnhancementType.CLARITY: """Mache den Text klarer und verständlicher.
Vereinfache komplizierte Sätze.
Strukturiere besser.
Behalte alle wichtigen Informationen bei.""",
        
        EnhancementType.FORMALITY: """Erhöhe die Formalität des Textes.
Verwende offizielle, professionelle Sprache.
Geeignet für Behördenkorrespondenz.""",
        
        EnhancementType.CONCISENESS: """Mache den Text prägnanter und kürzer.
Entferne Redundanzen.
Behalte alle wichtigen Informationen bei.""",
        
        EnhancementType.COMPLETENESS: """Erweitere den Text um fehlende wichtige Details.
Mache ihn vollständiger und umfassender.
Füge relevante Informationen hinzu."""
    }
    
    async def enhance(
        self,
        text: str,
        enhancement_type: EnhancementType,
        instructions: Optional[str] = None
    ) -> Dict:
        """
        Enhance content
        
        Args:
            text: Original text
            enhancement_type: Type of enhancement
            instructions: Additional instructions
        
        Returns:
            Enhanced text and changes
        """
        
        # Build prompt
        base_instruction = self.ENHANCEMENT_PROMPTS[enhancement_type]
        
        prompt = f"""{base_instruction}

{instructions if instructions else ""}

Originaltext:
{text}

Verbesserte Version:
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            max_tokens=len(text.split()) * 2,  # Allow expansion
            temperature=0.7
        )
        
        enhanced_text = response["content"].strip()
        
        return {
            "original": text,
            "enhanced": enhanced_text,
            "enhancement_type": enhancement_type.value,
            "changes": self._detect_changes(text, enhanced_text),
            "usage": response["usage"]
        }
    
    async def proofread(
        self,
        text: str,
        language: str = "de"
    ) -> Dict:
        """
        Comprehensive proofreading
        
        Args:
            text: Text to proofread
            language: Language code
        
        Returns:
            Corrections and suggestions
        """
        
        prompt = f"""Proofread this German text and provide:
1. Corrected version
2. List of errors found
3. Suggestions for improvement

Text:
{text}

Format your response as JSON:
{{
  "corrected_text": "...",
  "errors": [
    {{"type": "grammar/spelling/punctuation", "original": "...", "correction": "...", "explanation": "..."}}
  ],
  "suggestions": [
    {{"category": "style/clarity/structure", "suggestion": "..."}}
  ]
}}
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            max_tokens=len(text.split()) * 3,
            temperature=0.3
        )
        
        # Parse JSON response
        import json
        try:
            result = json.loads(response["content"])
            result["usage"] = response["usage"]
            return result
        except json.JSONDecodeError:
            return {
                "corrected_text": response["content"],
                "errors": [],
                "suggestions": [],
                "usage": response["usage"]
            }
    
    async def translate(
        self,
        text: str,
        target_language: str,
        preserve_formatting: bool = True
    ) -> Dict:
        """
        Translate text
        
        Args:
            text: Source text
            target_language: Target language (de, ru, en)
            preserve_formatting: Keep original formatting
        
        Returns:
            Translated text
        """
        
        lang_names = {
            "de": "German",
            "ru": "Russian",
            "en": "English"
        }
        
        prompt = f"""Translate this text to {lang_names.get(target_language, target_language)}.
{'Preserve all formatting, structure, and line breaks.' if preserve_formatting else ''}

Text:
{text}

Translation:
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            max_tokens=len(text.split()) * 2,
            temperature=0.3
        )
        
        return {
            "original": text,
            "translated": response["content"].strip(),
            "target_language": target_language,
            "usage": response["usage"]
        }
    
    def _detect_changes(
        self,
        original: str,
        enhanced: str
    ) -> Dict:
        """Detect changes between original and enhanced text"""
        
        import difflib
        
        # Calculate similarity
        similarity = difflib.SequenceMatcher(
            None,
            original,
            enhanced
        ).ratio()
        
        # Get diff
        differ = difflib.Differ()
        diff = list(differ.compare(
            original.split(),
            enhanced.split()
        ))
        
        # Count changes
        additions = sum(1 for d in diff if d.startswith('+ '))
        deletions = sum(1 for d in diff if d.startswith('- '))
        
        return {
            "similarity": round(similarity, 3),
            "additions": additions,
            "deletions": deletions,
            "total_changes": additions + deletions
        }


# Global content enhancer
content_enhancer = ContentEnhancer()