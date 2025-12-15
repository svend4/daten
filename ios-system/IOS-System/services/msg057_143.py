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