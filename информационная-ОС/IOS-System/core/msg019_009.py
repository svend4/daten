# examples/python_client.py
"""
Python клиент для IOS API
"""

import requests
import json
from typing import Dict, List, Optional
import websocket
import threading

class IOSClient:
    """Python клиент для Information Operating System"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.token = None
        self.ws = None
        
    # ========================================================================
    # AUTHENTICATION
    # ========================================================================
    
    def login(self, username: str, password: str) -> bool:
        """Вход в систему"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            return True
        
        return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки с токеном"""
        headers = {"Content-Type": "application/json"}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        return headers
    
    # ========================================================================
    # DOMAINS
    # ========================================================================
    
    def list_domains(self) -> List[str]:
        """Получить список доменов"""
        response = requests.get(
            f"{self.base_url}/api/domains",
            headers=self._get_headers()
        )
        
        return response.json()
    
    def create_domain(self, name: str, language: str = "de", 
                     description: str = "", entity_types: List[str] = None) -> Dict:
        """Создать новый домен"""
        data = {
            "name": name,
            "language": language,
            "description": description,
            "entity_types": entity_types or []
        }
        
        response = requests.post(
            f"{self.base_url}/api/domains",
            json=data,
            headers=self._get_headers()
        )
        
        return response.json()
    
    def get_domain(self, domain_name: str) -> Dict:
        """Получить информацию о домене"""
        response = requests.get(
            f"{self.base_url}/api/domains/{domain_name}",
            headers=self._get_headers()
        )
        
        return response.json()
    
    # ========================================================================
    # DOCUMENTS
    # ========================================================================
    
    def upload_document(self, file_path: str, domain_name: str, 
                       title: Optional[str] = None, 
                       author: Optional[str] = None,
                       tags: List[str] = None) -> Dict:
        """Загрузить документ"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            
            params = {'domain_name': domain_name}
            
            if title:
                params['title'] = title
            if author:
                params['author'] = author
            if tags:
                params['tags'] = tags
            
            response = requests.post(
                f"{self.base_url}/api/documents/upload",
                files=files,
                params=params,
                headers={"Authorization": f"Bearer {self.token}"}
            )
        
        return response.json()
    
    # ========================================================================
    # SEARCH
    # ========================================================================
    
    def search(self, query: str, domain_name: Optional[str] = None,
               search_type: str = "full_text", limit: int = 10,
               filters: Dict = None) -> Dict:
        """Поиск документов"""
        data = {
            "query": query,
            "search_type": search_type,
            "domain_name": domain_name,
            "limit": limit,
            "filters": filters or {}
        }
        
        response = requests.post(
            f"{self.base_url}/api/search",
            json=data,
            headers=self._get_headers()
        )
        
        return response.json()
    
    def autocomplete(self, prefix: str, domain_name: Optional[str] = None,
                    max_suggestions: int = 10) -> List[str]:
        """Автодополнение"""
        params = {
            "prefix": prefix,
            "max_suggestions": max_suggestions
        }
        
        if domain_name:
            params["domain_name"] = domain_name
        
        response = requests.get(
            f"{self.base_url}/api/search/suggest",
            params=params,
            headers=self._get_headers()
        )
        
        return response.json()
    
    # ========================================================================
    # KNOWLEDGE GRAPH
    # ========================================================================
    
    def get_graph_statistics(self, domain_name: str) -> Dict:
        """Получить статистику графа"""
        response = requests.get(
            f"{self.base_url}/api/graph/{domain_name}/statistics",
            headers=self._get_headers()
        )
        
        return response.json()
    
    def list_entities(self, domain_name: str, entity_type: Optional[str] = None,
                     limit: int = 100) -> List[Dict]:
        """Получить список сущностей"""
        params = {"limit": limit}
        
        if entity_type:
            params["entity_type"] = entity_type
        
        response = requests.get(
            f"{self.base_url}/api/graph/{domain_name}/entities",
            params=params,
            headers=self._get_headers()
        )
        
        return response.json()
    
    def get_entity(self, domain_name: str, entity_id: str) -> Dict:
        """Получить сущность"""
        response = requests.get(
            f"{self.base_url}/api/graph/{domain_name}/entities/{entity_id}",
            headers=self._get_headers()
        )
        
        return response.json()
    
    def get_related_entities(self, domain_name: str, entity_id: str,
                           relation_type: Optional[str] = None,
                           direction: str = "both") -> List[Dict]:
        """Получить связанные сущности"""
        params = {"direction": direction}
        
        if relation_type:
            params["relation_type"] = relation_type
        
        response = requests.get(
            f"{self.base_url}/api/graph/{domain_name}/entities/{entity_id}/related",
            params=params,
            headers=self._get_headers()
        )
        
        return response.json()
    
    def create_entity(self, domain_name: str, entity_type: str, name: str,
                     properties: Dict = None, source_document: str = "manual",
                     confidence: float = 1.0) -> Dict:
        """Создать сущность"""
        data = {
            "type": entity_type,
            "name": name,
            "properties": properties or {},
            "source_document": source_document,
            "confidence": confidence
        }
        
        response = requests.post(
            f"{self.base_url}/api/graph/{domain_name}/entities",
            json=data,
            headers=self._get_headers()
        )
        
        return response.json()
    
    def create_relation(self, domain_name: str, relation_type: str,
                       source_id: str, target_id: str,
                       properties: Dict = None, confidence: float = 1.0) -> Dict:
        """Создать отношение"""
        data = {
            "type": relation_type,
            "source_id": source_id,
            "target_id": target_id,
            "properties": properties or {},
            "confidence": confidence
        }
        
        response = requests.post(
            f"{self.base_url}/api/graph/{domain_name}/relations",
            json=data,
            headers=self._get_headers()
        )
        
        return response.json()
    
    def query_graph(self, domain_name: str, query_type: str, query: str,
                   parameters: Dict = None, limit: int = 10) -> Dict:
        """Запрос к графу"""
        data = {
            "query_type": query_type,
            "query": query,
            "parameters": parameters or {},
            "limit": limit
        }
        
        response = requests.post(
            f"{self.base_url}/api/graph/{domain_name}/query",
            json=data,
            headers=self._get_headers()
        )
        
        return response.json()
    
    # ========================================================================
    # CONTEXTS
    # ========================================================================
    
    def list_contexts(self) -> List[Dict]:
        """Получить список контекстов"""
        response = requests.get(
            f"{self.base_url}/api/contexts",
            headers=self._get_headers()
        )
        
        return response.json()
    
    def create_context(self, name: str, context_type: str,
                      description: str = "", active_domains: List[str] = None,
                      properties: Dict = None) -> Dict:
        """Создать контекст"""
        data = {
            "name": name,
            "type": context_type,
            "description": description,
            "active_domains": active_domains or [],
            "properties": properties or {}
        }
        
        response = requests.post(
            f"{self.base_url}/api/contexts",
            json=data,
            headers=self._get_headers()
        )
        
        return response.json()
    
    def switch_context(self, context_id: str) -> Dict:
        """Переключить контекст"""
        response = requests.post(
            f"{self.base_url}/api/contexts/{context_id}/switch",
            headers=self._get_headers()
        )
        
        return response.json()
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def get_graph_analytics(self, domain_name: str, analysis_type: str,
                           top_n: int = 10) -> Dict:
        """Получить аналитику графа"""
        params = {
            "analysis_type": analysis_type,
            "top_n": top_n
        }
        
        response = requests.get(
            f"{self.base_url}/api/analytics/{domain_name}/graph",
            params=params,
            headers=self._get_headers()
        )
        
        return response.json()
    
    # ========================================================================
    # WEBSOCKET
    # ========================================================================
    
    def connect_websocket(self, user_id: str, on_message_callback=None):
        """Подключиться к WebSocket"""
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        
        def on_message(ws, message):
            data = json.loads(message)
            print(f"WebSocket message: {data}")
            
            if on_message_callback:
                on_message_callback(data)
        
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print("WebSocket closed")
        
        def on_open(ws):
            print("WebSocket connected")
        
        self.ws = websocket.WebSocketApp(
            f"{ws_url}/ws/{user_id}",
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        self.ws.on_open = on_open
        
        # Запустить в отдельном потоке
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
    
    def subscribe_to_event(self, event_type: str):
        """Подписаться на событие"""
        if self.ws:
            self.ws.send(json.dumps({
                "action": "subscribe",
                "event_type": event_type
            }))
    
    def unsubscribe_from_event(self, event_type: str):
        """Отписаться от события"""
        if self.ws:
            self.ws.send(json.dumps({
                "action": "unsubscribe",
                "event_type": event_type
            }))


# ============================================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# ============================================================================

def example_usage():
    """Примеры использования Python клиента"""
    
    # Создать клиента
    client = IOSClient(base_url="http://localhost:8000")
    
    # Войти
    if client.login("admin", "admin"):
        print("✓ Logged in successfully")
    
    # Создать домен
    domain = client.create_domain(
        name="SGB-IX",
        language="de",
        description="Deutsches Sozialrecht",
        entity_types=["Gesetz", "Paragraph", "Behörde"]
    )
    print(f"✓ Created domain: {domain['name']}")
    
    # Загрузить документ
    doc = client.upload_document(
        file_path="/path/to/document.pdf",
        domain_name="SGB-IX",
        title="Widerspruch gegen Bescheid",
        tags=["widerspruch", "sgb-ix"]
    )
    print(f"✓ Uploaded document: {doc['doc_id']}")
    
    # Поиск
    results = client.search(
        query="Persönliches Budget",
        domain_name="SGB-IX",
        search_type="hybrid",
        limit=5
    )
    print(f"✓ Found {results['total_count']} documents")
    for result in results['results']:
        print(f"  - {result['title']} (score: {result['score']:.3f})")
    
    # Получить статистику графа
    stats = client.get_graph_statistics("SGB-IX")
    print(f"✓ Graph statistics:")
    print(f"  Entities: {stats['total_entities']}")
    print(f"  Relations: {stats['total_relations']}")
    
    # Получить сущности
    entities = client.list_entities("SGB-IX", entity_type="Paragraph", limit=10)
    print(f"✓ Found {len(entities)} paragraphs")
    
    # Получить связанные сущности
    if entities:
        entity_id = entities[0]['id']
        related = client.get_related_entities("SGB-IX", entity_id)
        print(f"✓ Found {len(related)} related entities")
    
    # Аналитика
    analytics = client.get_graph_analytics(
        domain_name="SGB-IX",
        analysis_type="most_connected",
        top_n=5
    )
    print(f"✓ Top 5 most connected entities:")
    for item in analytics['results']:
        entity = item['entity']
        print(f"  - {entity['name']} ({entity['type']}): {item['degree']} connections")
    
    # WebSocket
    def on_message(data):
        print(f"Received: {data['type']}")
    
    client.connect_websocket("user123", on_message_callback=on_message)
    client.subscribe_to_event("document.added")
    client.subscribe_to_event("entity.extracted")
    
    # Ждать события
    import time
    time.sleep(60)


if __name__ == "__main__":
    example_usage()