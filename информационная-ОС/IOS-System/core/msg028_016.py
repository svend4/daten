# ⚠️ ПРОБЛЕМА: Domain класс делает слишком много
class Domain:
    def add_document(self, doc):
        # Сохранение
        # Классификация  
        # Извлечение сущностей
        # Обновление графа
        # Индексирование
        
# ✅ РЕШЕНИЕ: Разделить на сервисы
class DocumentService:
    def __init__(self, storage, classifier, entity_extractor, indexer):
        ...
    
    def add_document(self, doc):
        # Координация, но не реализация