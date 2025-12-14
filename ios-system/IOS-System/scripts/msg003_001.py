class MetadataManager:
    """Управление всеми метаданными домена"""
    
    def __init__(self, domain_path: str):
        self.taxonomy = self.load_taxonomy(f"{domain_path}/metadata/taxonomy.json")
        self.entity_types = self.load_entity_types(f"{domain_path}/metadata/entity-types.json")
        self.relation_types = self.load_relation_types(f"{domain_path}/metadata/relation-types.json")
        
    def get_category_path(self, document: Document) -> str:
        """Определить путь в таксономии для документа"""
        # Анализ содержимого документа
        keywords = self.extract_keywords(document)
        entities = self.extract_entities(document)
        
        # Поиск наилучшего соответствия в таксономии
        best_match = self.taxonomy.find_best_match(keywords, entities)
        
        return best_match.path  # Например: "SGB-IX/Teilhabe/Persönliches Budget"
    
    def generate_metadata(self, document: Document) -> dict:
        """Генерация метаданных для документа"""
        return {
            "title": self.extract_title(document),
            "category": self.get_category_path(document),
            "entities": self.extract_entities(document),
            "keywords": self.extract_keywords(document),
            "summary": self.generate_summary(document),
            "date_created": document.creation_date,
            "date_modified": document.modification_date,
            "language": self.detect_language(document),
            "document_type": self.classify_document_type(document),
            "related_documents": self.find_related(document)
        }