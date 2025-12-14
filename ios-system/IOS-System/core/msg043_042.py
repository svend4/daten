# Обновить ios_core/system.py

from .search.elasticsearch_service import ElasticsearchService

class IOSSystem:
    def __init__(self):
        # Replace Whoosh with Elasticsearch
        self.search_service = ElasticsearchService()
    
    async def initialize(self):
        await self.search_service.initialize()