class DataBus:
    """Системная шина для передачи данных между компонентами"""
    
    def __init__(self):
        self.subscribers = {}  # Подписчики на события
        self.message_queue = queue.Queue()  # Очередь сообщений
        self.running = False
        
    def publish(self, event_type: str, data: dict):
        """Публикация события в шину"""
        event = {
            'type': event_type,
            'timestamp': datetime.now(),
            'data': data
        }
        self.message_queue.put(event)
        
    def subscribe(self, event_type: str, callback: Callable):
        """Подписка на события определенного типа"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
    def start(self):
        """Запустить обработку событий"""
        self.running = True
        while self.running:
            try:
                event = self.message_queue.get(timeout=1)
                self._dispatch_event(event)
            except queue.Empty:
                continue
                
    def _dispatch_event(self, event: dict):
        """Отправить событие всем подписчикам"""
        event_type = event['type']
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logging.error(f"Error in event handler: {e}")

# Примеры событий
EVENTS = {
    'DOCUMENT_ADDED': 'document.added',
    'DOCUMENT_UPDATED': 'document.updated',
    'DOCUMENT_DELETED': 'document.deleted',
    'ENTITY_EXTRACTED': 'entity.extracted',
    'RELATION_CREATED': 'relation.created',
    'SEARCH_PERFORMED': 'search.performed',
    'INDEX_UPDATED': 'index.updated'
}