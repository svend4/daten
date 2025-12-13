# ios_core/services/knowledge_graph.py

class KnowledgeGraphService:
    
    async def extract_entities(self, document):
        """Extract entities with proper cleanup"""
        
        entities = []
        
        try:
            # Extract entities
            raw_entities = self.entity_extractor.extract(document)
            
            # Deduplicate
            seen = set()
            for entity in raw_entities:
                entity_key = (entity.type, entity.name.lower())
                if entity_key not in seen:
                    entities.append(entity)
                    seen.add(entity_key)
            
        finally:
            # Clean up temporary resources
            del raw_entities
            seen.clear()
        
        return entities