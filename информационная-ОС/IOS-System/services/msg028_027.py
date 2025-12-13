# ⚠️ ПРОБЛЕМА: Жесткая зависимость
class SearchEngine:
    def __init__(self, domain):
        self.indexer = DocumentIndexer(domain.path)  # Hardcoded
        
# ✅ РЕШЕНИЕ: DI контейнер
class SearchEngine:
    def __init__(self, indexer: DocumentIndexer):
        self.indexer = indexer