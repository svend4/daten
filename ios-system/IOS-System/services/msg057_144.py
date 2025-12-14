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