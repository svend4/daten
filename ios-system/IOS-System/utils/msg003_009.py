class DataStorage:
    """Управление физическим хранилищем данных"""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.file_index = FileIndex(f"{storage_path}/.index.db")
        
    def store_document(self, document: Document, metadata: dict) -> str:
        """Сохранить документ и вернуть путь"""
        # Определить путь на основе метаданных
        storage_path = self.calculate_path(metadata)
        
        # Создать директории если нужно
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # Сохранить документ
        document.save(storage_path)
        
        # Обновить индекс
        self.file_index.add_entry(storage_path, metadata)
        
        # Создать резервную копию
        self.create_backup(storage_path)
        
        return storage_path
    
    def calculate_path(self, metadata: dict) -> str:
        """Вычислить путь для хранения на основе метаданных"""
        category = metadata.get('category', 'uncategorized')
        doc_type = metadata.get('document_type', 'document')
        date = metadata.get('date_created', datetime.now())
        
        # Пример: /data/documents/anträge/2025/antrag-pb-2025-01-15.pdf
        return os.path.join(
            self.storage_path,
            'documents',
            category,
            str(date.year),
            f"{doc_type}-{date.strftime('%Y-%m-%d')}.{metadata.get('format', 'pdf')}"
        )