Отлично! Теперь переходим к Day 123-124: GPT Integration. Это будет включать:

1. GPT API Integration для генерации текста
2. Document Generation (автоматическое создание документов)
3. Template Processing (обработка шаблонов)
4. Smart Suggestions (умные подсказки)
5. Content Enhancement (улучшение контента)
6. Summarization (резюмирование)
7. Question Answering (ответы на вопросы)

Создам:
- GPT Client (интеграция с OpenAI API)
- Document Generator (генерация документов)
- Template Engine (обработка шаблонов)
- Content Enhancer (улучшение текста)
- Summarization Service (резюмирование)
- Q&A System (вопрос-ответ)
- API Routes
- Tests
- Documentation# 🤖 DAY 123-124: GPT INTEGRATION

---

## 📊 ЦЕЛЬ

Интеграция GPT для интеллектуальной генерации контента:
- **Document Generation** - автоматическое создание документов
- **Template Processing** - заполнение шаблонов
- **Content Enhancement** - улучшение текста
- **Summarization** - автоматическое резюмирование
- **Question Answering** - ответы на вопросы
- **Smart Suggestions** - интеллектуальные подсказки

---

## ФАЙЛ 109: `ios_core/gpt/__init__.py`

```python
"""
GPT Integration Module
"""

from .gpt_client import GPTClient, gpt_client
from .document_generator import DocumentGenerator, document_generator
from .template_engine import TemplateEngine, template_engine
from .content_enhancer import ContentEnhancer, content_enhancer
from .summarizer import Summarizer, summarizer
from .qa_system import QASystem, qa_system

__all__ = [
    'GPTClient',
    'gpt_client',
    'DocumentGenerator',
    'document_generator',
    'TemplateEngine',
    'template_engine',
    'ContentEnhancer',
    'content_enhancer',
    'Summarizer',
    'summarizer',
    'QASystem',
    'qa_system',
]
```

---

## ФАЙЛ 110: `ios_core/gpt/gpt_client.py`

```python
"""
GPT API Client
OpenAI GPT-4 integration
"""

import logging
from typing import List, Dict, Optional, AsyncIterator
import asyncio
from datetime import datetime

import openai
from openai import AsyncOpenAI

from ..config import settings

logger = logging.getLogger(__name__)


class GPTClient:
    """
    GPT API Client
    
    Features:
    - Text generation
    - Chat completion
    - Streaming responses
    - Function calling
    - Token management
    - Error handling & retries
    
    Usage:
        client = GPTClient()
        
        # Generate text
        response = await client.generate(
            prompt="Write an objection letter...",
            max_tokens=1000
        )
        
        # Chat
        response = await client.chat(
            messages=[
                {"role": "system", "content": "You are a legal assistant."},
                {"role": "user", "content": "How do I apply for a personal budget?"}
            ]
        )
    """
    
    # Model configurations
    MODELS = {
        "gpt-4-turbo": {
            "name": "gpt-4-turbo-preview",
            "max_tokens": 128000,
            "cost_per_1k_input": 0.01,
            "cost_per_1k_output": 0.03
        },
        "gpt-4": {
            "name": "gpt-4",
            "max_tokens": 8192,
            "cost_per_1k_input": 0.03,
            "cost_per_1k_output": 0.06
        },
        "gpt-3.5-turbo": {
            "name": "gpt-3.5-turbo",
            "max_tokens": 16385,
            "cost_per_1k_input": 0.0005,
            "cost_per_1k_output": 0.0015
        }
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo",
        temperature: float = 0.7,
        max_retries: int = 3
    ):
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        stop: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate text completion
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            system_prompt: System instruction
            stop: Stop sequences
        
        Returns:
            Response dict with text and metadata
        """
        
        # Build messages
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        return await self.chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop
        )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: Optional[float] = None,
        stop: Optional[List[str]] = None,
        functions: Optional[List[Dict]] = None,
        function_call: Optional[str] = None
    ) -> Dict:
        """
        Chat completion
        
        Args:
            messages: List of messages
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            stop: Stop sequences
            functions: Available functions
            function_call: Function call mode
        
        Returns:
            Response dict
        """
        
        if temperature is None:
            temperature = self.temperature
        
        model_config = self.MODELS[self.model]
        
        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=model_config["name"],
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                functions=functions,
                function_call=function_call
            )
            
            # Extract response
            choice = response.choices[0]
            message = choice.message
            
            # Update usage
            usage = response.usage
            self.total_input_tokens += usage.prompt_tokens
            self.total_output_tokens += usage.completion_tokens
            
            # Calculate cost
            input_cost = (usage.prompt_tokens / 1000) * model_config["cost_per_1k_input"]
            output_cost = (usage.completion_tokens / 1000) * model_config["cost_per_1k_output"]
            total_cost = input_cost + output_cost
            self.total_cost += total_cost
            
            # Build response
            result = {
                "content": message.content,
                "role": message.role,
                "finish_reason": choice.finish_reason,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                "cost": {
                    "input": input_cost,
                    "output": output_cost,
                    "total": total_cost
                },
                "model": model_config["name"]
            }
            
            # Include function call if present
            if message.function_call:
                result["function_call"] = {
                    "name": message.function_call.name,
                    "arguments": message.function_call.arguments
                }
            
            return result
            
        except Exception as e:
            logger.error(f"GPT API error: {e}", exc_info=True)
            raise
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: Optional[float] = None
    ) -> AsyncIterator[str]:
        """
        Stream chat completion
        
        Args:
            messages: List of messages
            max_tokens: Maximum tokens
            temperature: Sampling temperature
        
        Yields:
            Text chunks as they arrive
        """
        
        if temperature is None:
            temperature = self.temperature
        
        model_config = self.MODELS[self.model]
        
        try:
            stream = await self.client.chat.completions.create(
                model=model_config["name"],
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"GPT streaming error: {e}", exc_info=True)
            raise
    
    async def embed(
        self,
        text: str,
        model: str = "text-embedding-ada-002"
    ) -> List[float]:
        """
        Generate text embedding
        
        Args:
            text: Input text
            model: Embedding model
        
        Returns:
            Embedding vector
        """
        
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "model": self.model
        }
    
    def reset_usage_stats(self):
        """Reset usage counters"""
        
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0


# Global GPT client
gpt_client = GPTClient(
    model=settings.gpt_model,
    temperature=settings.gpt_temperature
)
```

---

## ФАЙЛ 111: `ios_core/gpt/document_generator.py`

```python
"""
Document Generator
Automated document creation using GPT
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

from .gpt_client import gpt_client
from ..database import async_session
from ..models import DocumentModel
import uuid

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """
    Automated document generation
    
    Features:
    - Generate from templates
    - Legal document creation
    - Form filling
    - Multi-section documents
    - Quality validation
    
    Usage:
        generator = DocumentGenerator()
        
        # Generate objection letter
        doc = await generator.generate_objection(
            case_details={
                "applicant_name": "Max Mustermann",
                "decision_date": "2024-01-15",
                "reason": "Insufficient justification"
            }
        )
    """
    
    # System prompts for different document types
    SYSTEM_PROMPTS = {
        "objection": """You are a German legal assistant specializing in social law (Sozialrecht).
Generate professional objection letters (Widersprüche) against administrative decisions.
Follow German legal standards and formal language.
Structure: Betreff, Anrede, Sachverhalt, Begründung, Antrag, Grußformel.""",
        
        "application": """You are a German administrative assistant.
Generate professional applications (Anträge) for social benefits.
Use clear, formal German language.
Structure: Betreff, Anrede, Antrag, Begründung, Anlagen, Grußformel.""",
        
        "report": """You are a professional report writer for social services.
Generate comprehensive reports in German.
Use structured format with clear sections.
Include: Zusammenfassung, Hauptteil, Schlussfolgerungen."""
    }
    
    async def generate_objection(
        self,
        case_details: Dict,
        template: Optional[str] = None
    ) -> Dict:
        """
        Generate objection letter (Widerspruch)
        
        Args:
            case_details: Case information
            template: Optional custom template
        
        Returns:
            Generated document
        """
        
        # Build prompt
        prompt = self._build_objection_prompt(case_details, template)
        
        # Generate
        response = await gpt_client.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPTS["objection"],
            max_tokens=2000,
            temperature=0.7
        )
        
        # Extract content
        content = response["content"]
        
        # Create document
        doc = await self._save_document(
            title=f"Widerspruch - {case_details.get('applicant_name', 'N/A')}",
            content=content,
            doc_type="objection",
            metadata={
                "case_details": case_details,
                "generated_at": datetime.utcnow().isoformat(),
                "model": response["model"],
                "tokens": response["usage"]["total_tokens"],
                "cost": response["cost"]["total"]
            }
        )
        
        return {
            "document_id": doc.id,
            "title": doc.title,
            "content": content,
            "metadata": doc.metadata,
            "usage": response["usage"],
            "cost": response["cost"]
        }
    
    def _build_objection_prompt(
        self,
        case_details: Dict,
        template: Optional[str]
    ) -> str:
        """Build prompt for objection letter"""
        
        if template:
            return template.format(**case_details)
        
        # Default prompt
        prompt = f"""Erstelle einen formellen Widerspruch gegen einen Bescheid mit folgenden Informationen:

Antragsteller: {case_details.get('applicant_name', 'N/A')}
Bescheiddatum: {case_details.get('decision_date', 'N/A')}
Aktenzeichen: {case_details.get('case_number', 'N/A')}
Begründung: {case_details.get('reason', 'N/A')}

Zusätzliche Details:
{json.dumps(case_details.get('additional_info', {}), indent=2, ensure_ascii=False)}

Der Widerspruch soll:
1. Formal korrekt sein
2. Rechtlich fundiert argumentieren
3. Relevante Gesetzesgrundlagen (SGB IX, XII) zitieren
4. Höflich aber bestimmt formuliert sein
5. Einen klaren Antrag enthalten
"""
        
        return prompt
    
    async def generate_application(
        self,
        benefit_type: str,
        applicant_info: Dict,
        justification: str
    ) -> Dict:
        """
        Generate benefit application (Antrag)
        
        Args:
            benefit_type: Type of benefit (e.g., "Persönliches Budget")
            applicant_info: Applicant information
            justification: Reason for application
        
        Returns:
            Generated document
        """
        
        prompt = f"""Erstelle einen formellen Antrag auf {benefit_type} mit folgenden Informationen:

Antragsteller:
{json.dumps(applicant_info, indent=2, ensure_ascii=False)}

Begründung:
{justification}

Der Antrag soll:
1. Alle erforderlichen Angaben enthalten
2. Die Rechtsgrundlage nennen
3. Eine überzeugende Begründung liefern
4. Notwendige Anlagen auflisten
5. Formal korrekt sein
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPTS["application"],
            max_tokens=2000,
            temperature=0.7
        )
        
        content = response["content"]
        
        doc = await self._save_document(
            title=f"Antrag auf {benefit_type} - {applicant_info.get('name', 'N/A')}",
            content=content,
            doc_type="application",
            metadata={
                "benefit_type": benefit_type,
                "applicant": applicant_info,
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "document_id": doc.id,
            "title": doc.title,
            "content": content,
            "usage": response["usage"]
        }
    
    async def generate_report(
        self,
        title: str,
        sections: List[Dict],
        summary: Optional[str] = None
    ) -> Dict:
        """
        Generate structured report
        
        Args:
            title: Report title
            sections: List of sections with titles and content
            summary: Optional executive summary
        
        Returns:
            Generated document
        """
        
        # Build sections prompt
        sections_text = "\n\n".join([
            f"## {section['title']}\n{section.get('content', section.get('prompt', ''))}"
            for section in sections
        ])
        
        prompt = f"""Erstelle einen professionellen Bericht mit folgendem Titel:
{title}

{"Zusammenfassung: " + summary if summary else ""}

Abschnitte:
{sections_text}

Der Bericht soll:
1. Klar strukturiert sein
2. Professionelle Sprache verwenden
3. Fakten präzise darstellen
4. Schlussfolgerungen ziehen
5. Handlungsempfehlungen geben (falls relevant)
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPTS["report"],
            max_tokens=3000,
            temperature=0.7
        )
        
        content = response["content"]
        
        doc = await self._save_document(
            title=title,
            content=content,
            doc_type="report",
            metadata={
                "sections": [s["title"] for s in sections],
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "document_id": doc.id,
            "title": doc.title,
            "content": content,
            "usage": response["usage"]
        }
    
    async def _save_document(
        self,
        title: str,
        content: str,
        doc_type: str,
        metadata: Dict
    ) -> DocumentModel:
        """Save generated document to database"""
        
        async with async_session() as session:
            doc = DocumentModel(
                id=str(uuid.uuid4()),
                title=title,
                content=content,
                domain_id="generated",
                domain_name="Generated Documents",
                metadata={
                    **metadata,
                    "document_type": doc_type,
                    "auto_generated": True
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            
            logger.info(f"Saved generated document: {doc.id}")
            return doc


# Global document generator
document_generator = DocumentGenerator()
```

---

## ФАЙЛ 112: `ios_core/gpt/template_engine.py`

```python
"""
Template Processing Engine
Fill templates with GPT-generated content
"""

import logging
from typing import Dict, List, Optional
import re
from jinja2 import Template, Environment, meta

from .gpt_client import gpt_client

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    Intelligent template processing
    
    Features:
    - Template variable detection
    - Smart field completion
    - Context-aware generation
    - Multi-language templates
    
    Usage:
        engine = TemplateEngine()
        
        # Fill template
        result = await engine.fill_template(
            template="Sehr geehrte Damen und Herren...",
            context={"applicant_name": "Max Mustermann"}
        )
    """
    
    def __init__(self):
        self.jinja_env = Environment()
    
    async def fill_template(
        self,
        template: str,
        context: Dict,
        auto_complete: bool = True
    ) -> Dict:
        """
        Fill template with context
        
        Args:
            template: Template string with {{variables}}
            context: Known context values
            auto_complete: Use GPT to complete missing fields
        
        Returns:
            Filled template and metadata
        """
        
        # Parse template to find variables
        variables = self._extract_variables(template)
        
        # Find missing variables
        missing = [v for v in variables if v not in context]
        
        # Auto-complete missing fields if enabled
        if auto_complete and missing:
            logger.info(f"Auto-completing {len(missing)} missing fields")
            
            completed = await self._auto_complete_fields(
                template=template,
                context=context,
                missing_fields=missing
            )
            
            # Merge completed values
            context = {**context, **completed}
        
        # Render template
        jinja_template = Template(template)
        filled = jinja_template.render(context)
        
        return {
            "content": filled,
            "template": template,
            "context": context,
            "variables": variables,
            "auto_completed": missing if auto_complete else []
        }
    
    def _extract_variables(self, template: str) -> List[str]:
        """Extract template variables"""
        
        # Parse with Jinja2
        ast = self.jinja_env.parse(template)
        variables = meta.find_undeclared_variables(ast)
        
        return list(variables)
    
    async def _auto_complete_fields(
        self,
        template: str,
        context: Dict,
        missing_fields: List[str]
    ) -> Dict:
        """
        Auto-complete missing template fields
        
        Uses GPT to intelligently fill missing values
        based on template context
        """
        
        prompt = f"""You are filling a German legal document template.
Given the template and known values, provide reasonable values for missing fields.

Template excerpt:
{template[:500]}...

Known values:
{context}

Missing fields to complete:
{missing_fields}

Generate appropriate values for the missing fields.
Return ONLY a JSON object with field names as keys.
Use realistic German names, addresses, dates, and legal terminology.

Example format:
{{
  "field_name": "value",
  "another_field": "another value"
}}
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        
        # Parse JSON response
        import json
        try:
            completed = json.loads(response["content"])
            return completed
        except json.JSONDecodeError:
            logger.error("Failed to parse GPT response as JSON")
            return {}
    
    async def generate_from_schema(
        self,
        schema: Dict,
        user_inputs: Dict
    ) -> Dict:
        """
        Generate document from schema definition
        
        Args:
            schema: Document schema with fields and rules
            user_inputs: User-provided values
        
        Returns:
            Generated document
        """
        
        # Extract required fields
        required_fields = schema.get("required_fields", [])
        optional_fields = schema.get("optional_fields", [])
        
        # Validate inputs
        missing_required = [
            f for f in required_fields
            if f not in user_inputs
        ]
        
        if missing_required:
            raise ValueError(f"Missing required fields: {missing_required}")
        
        # Build generation prompt
        prompt = f"""Generate a {schema.get('document_type', 'document')} in German.

Document structure:
{schema.get('structure', 'Standard format')}

Required information:
{user_inputs}

Additional instructions:
{schema.get('instructions', 'Use formal German legal language.')}
"""
        
        response = await gpt_client.generate(
            prompt=prompt,
            max_tokens=schema.get("max_length", 2000),
            temperature=0.7
        )
        
        return {
            "content": response["content"],
            "schema": schema,
            "inputs": user_inputs,
            "usage": response["usage"]
        }


# Global template engine
template_engine = TemplateEngine()
```

---

## ФАЙЛ 113: `ios_core/gpt/content_enhancer.py`

```python
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
```

---

**Продолжение следует...**

Создано:
- ✅ GPT Client (OpenAI integration)
- ✅ Document Generator (automated documents)
- ✅ Template Engine (smart templates)
- ✅ Content Enhancer (text improvement)

**Следующие файлы:**
- Summarizer (резюмирование)
- Q&A System (вопрос-ответ)
- API Routes
- Tests
- Configuration

**Готовы продолжить?**