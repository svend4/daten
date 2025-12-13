# Создать главный файл системы
# ios_system/core.py

class IOSSystem:
    """Main IOS System orchestrator"""
    
    def __init__(self, config: Config):
        self.config = config
        self.root = IOSRoot(config.root_path)
        self.event_bus = EventBus()
        
        # Initialize components
        self.classifier = ClassificationEngine()
        self.graph_engine = KnowledgeGraphEngine()
        self.search_engine = SearchEngine()
        self.context_manager = ContextManager()
        
    async def initialize(self):
        """Initialize all components"""
        await self.root.initialize()
        await self.event_bus.start()
        
    async def add_document(self, file_path: str, domain_name: str):
        """Complete document processing pipeline"""
        # 1. Create document
        doc = Document.from_file(file_path)
        
        # 2. Classify
        classification = await self.classifier.classify(doc)
        
        # 3. Extract entities
        entities = await self.graph_engine.extract_entities(doc)
        
        # 4. Extract relations
        relations = await self.graph_engine.extract_relations(doc, entities)
        
        # 5. Index for search
        await self.search_engine.index_document(doc, classification, entities)
        
        # 6. Emit events
        await self.event_bus.publish('document.added', {
            'doc_id': doc.id,
            'domain': domain_name
        })
        
        return doc, classification, entities