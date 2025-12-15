class Domain:
    """Представляет тематический домен знаний"""
    
    def __init__(self, name: str, path: str, config: dict):
        self.name = name
        self.path = path
        self.config = config
        
        # Загрузка компонентов
        self.taxonomy = Taxonomy(f"{path}/metadata/taxonomy.json")
        self.entity_types = EntityTypes(f"{path}/metadata/entity-types.json")
        self.knowledge_graph = KnowledgeGraph(f"{path}/knowledge-graph")
        self.search_engine = DomainSearchEngine(f"{path}/indexes")
        self.cache = DomainCache(f"{path}/cache")
        
    def add_document(self, document: Document) -> None:
        """Добавить документ в домен"""
        # 1. Классифицировать документ
        classification = self.classify(document)
        
        # 2. Извлечь сущности и отношения
        entities = self.extract_entities(document)
        relations = self.extract_relations(document, entities)
        
        # 3. Обновить граф знаний
        self.knowledge_graph.add_entities(entities)
        self.knowledge_graph.add_relations(relations)
        
        # 4. Проиндексировать
        self.search_engine.index_document(document, classification)
        
        # 5. Сохранить документ
        storage_path = self.get_storage_path(classification)
        document.save(storage_path)
        
    def classify(self, document: Document) -> Classification:
        """Классифицировать документ"""
        classifier = DomainClassifier(self)
        return classifier.classify(document)
    
    def extract_entities(self, document: Document) -> List[Entity]:
        """Извлечь сущности из документа"""
        extractor = EntityExtractor(self.entity_types)
        return extractor.extract(document)
    
    def extract_relations(self, document: Document, entities: List[Entity]) -> List[Relation]:
        """Извлечь отношения между сущностями"""
        extractor = RelationExtractor(self.relation_types)
        return extractor.extract(document, entities)