Пользователь хочет продолжить с WebSocket API и примерами клиентских запросов. Я продолжу разработку API интерфейсов, добавив:

1. WebSocket API для real-time обновлений
2. Примеры клиентских запросов (Python, JavaScript, cURL)
3. GraphQL API (опционально)
4. Deployment guide
5. Docker configuration
6. Примеры интеграции с Android приложениями

Начну с WebSocket API и клиентских примеров.# ЧАСТЬ 9: WEBSOCKET API И КЛИЕНТСКИЕ ПРИМЕРЫ

## 9.1 WebSocket API для Real-time обновлений

```python
# api/websocket.py
"""
WebSocket API для real-time обновлений
Позволяет клиентам получать обновления в реальном времени
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set, List
import json
import asyncio
from datetime import datetime

# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        # Активные соединения: {user_id: Set[WebSocket]}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Подписки на события: {event_type: Set[user_id]}
        self.subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Подключить клиента"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        # Отправить приветственное сообщение
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            },
            websocket
        )
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Отключить клиента"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Удалить пользователя если нет активных соединений
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Удалить все подписки
                for event_type in list(self.subscriptions.keys()):
                    self.subscriptions[event_type].discard(user_id)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Отправить сообщение конкретному соединению"""
        await websocket.send_json(message)
    
    async def send_to_user(self, message: dict, user_id: str):
        """Отправить сообщение всем соединениям пользователя"""
        if user_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Удалить отключенные соединения
            for connection in disconnected:
                self.disconnect(connection, user_id)
    
    async def broadcast(self, message: dict, event_type: str = None):
        """Отправить сообщение всем подписанным пользователям"""
        
        # Определить получателей
        if event_type and event_type in self.subscriptions:
            recipients = self.subscriptions[event_type]
        else:
            recipients = self.active_connections.keys()
        
        # Отправить всем
        for user_id in recipients:
            await self.send_to_user(message, user_id)
    
    def subscribe(self, user_id: str, event_type: str):
        """Подписать пользователя на событие"""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = set()
        
        self.subscriptions[event_type].add(user_id)
    
    def unsubscribe(self, user_id: str, event_type: str):
        """Отписать пользователя от события"""
        if event_type in self.subscriptions:
            self.subscriptions[event_type].discard(user_id)


# Глобальный менеджер соединений
manager = ConnectionManager()


# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str
):
    """
    WebSocket endpoint для real-time обновлений
    
    Сообщения от клиента:
    {
        "action": "subscribe|unsubscribe|ping",
        "event_type": "document.added|entity.extracted|search.completed|...",
        "data": {...}
    }
    
    Сообщения к клиенту:
    {
        "type": "event_type",
        "data": {...},
        "timestamp": "ISO8601"
    }
    """
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Получить сообщение от клиента
            data = await websocket.receive_json()
            
            action = data.get("action")
            
            if action == "subscribe":
                event_type = data.get("event_type")
                if event_type:
                    manager.subscribe(user_id, event_type)
                    await manager.send_personal_message(
                        {
                            "type": "subscription",
                            "status": "subscribed",
                            "event_type": event_type
                        },
                        websocket
                    )
            
            elif action == "unsubscribe":
                event_type = data.get("event_type")
                if event_type:
                    manager.unsubscribe(user_id, event_type)
                    await manager.send_personal_message(
                        {
                            "type": "subscription",
                            "status": "unsubscribed",
                            "event_type": event_type
                        },
                        websocket
                    )
            
            elif action == "ping":
                await manager.send_personal_message(
                    {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    },
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


# ============================================================================
# EVENT EMITTERS (Отправка событий)
# ============================================================================

async def emit_document_added(doc_id: str, domain_name: str, metadata: dict):
    """Отправить событие о добавлении документа"""
    await manager.broadcast(
        {
            "type": "document.added",
            "data": {
                "doc_id": doc_id,
                "domain": domain_name,
                "metadata": metadata
            },
            "timestamp": datetime.now().isoformat()
        },
        event_type="document.added"
    )


async def emit_entity_extracted(entity: 'Entity', domain_name: str):
    """Отправить событие об извлечении сущности"""
    await manager.broadcast(
        {
            "type": "entity.extracted",
            "data": {
                "entity": entity.to_dict(),
                "domain": domain_name
            },
            "timestamp": datetime.now().isoformat()
        },
        event_type="entity.extracted"
    )


async def emit_search_completed(query: str, results_count: int, user_id: str):
    """Отправить событие о завершении поиска"""
    await manager.send_to_user(
        {
            "type": "search.completed",
            "data": {
                "query": query,
                "results_count": results_count
            },
            "timestamp": datetime.now().isoformat()
        },
        user_id
    )


async def emit_classification_completed(doc_id: str, classification: dict, user_id: str):
    """Отправить событие о завершении классификации"""
    await manager.send_to_user(
        {
            "type": "classification.completed",
            "data": {
                "doc_id": doc_id,
                "classification": classification
            },
            "timestamp": datetime.now().isoformat()
        },
        user_id
    )


async def emit_graph_updated(domain_name: str, stats: dict):
    """Отправить событие об обновлении графа"""
    await manager.broadcast(
        {
            "type": "graph.updated",
            "data": {
                "domain": domain_name,
                "statistics": stats
            },
            "timestamp": datetime.now().isoformat()
        },
        event_type="graph.updated"
    )
```

## 9.2 Клиентские примеры - Python

```python
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
```

## 9.3 Клиентские примеры - JavaScript/TypeScript

```javascript
// examples/javascript_client.js
/**
 * JavaScript/TypeScript клиент для IOS API
 */

class IOSClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.token = null;
        this.ws = null;
    }

    // ========================================================================
    // AUTHENTICATION
    // ========================================================================

    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            const data = await response.json();
            this.token = data.access_token;
            return true;
        }

        return false;
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    // ========================================================================
    // DOMAINS
    // ========================================================================

    async listDomains() {
        const response = await fetch(`${this.baseUrl}/api/domains`, {
            headers: this.getHeaders()
        });

        return await response.json();
    }

    async createDomain(name, language = 'de', description = '', entityTypes = []) {
        const response = await fetch(`${this.baseUrl}/api/domains`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({
                name,
                language,
                description,
                entity_types: entityTypes
            })
        });

        return await response.json();
    }

    async getDomain(domainName) {
        const response = await fetch(`${this.baseUrl}/api/domains/${domainName}`, {
            headers: this.getHeaders()
        });

        return await response.json();
    }

    // ========================================================================
    // DOCUMENTS
    // ========================================================================

    async uploadDocument(file, domainName, title = null, author = null, tags = []) {
        const formData = new FormData();
        formData.append('file', file);

        const params = new URLSearchParams({ domain_name: domainName });
        if (title) params.append('title', title);
        if (author) params.append('author', author);
        tags.forEach(tag => params.append('tags', tag));

        const response = await fetch(
            `${this.baseUrl}/api/documents/upload?${params}`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                },
                body: formData
            }
        );

        return await response.json();
    }

    // ========================================================================
    // SEARCH
    // ========================================================================

    async search(query, options = {}) {
        const {
            domainName = null,
            searchType = 'full_text',
            limit = 10,
            offset = 0,
            filters = {},
            ranking = 'hybrid'
        } = options;

        const response = await fetch(`${this.baseUrl}/api/search`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({
                query,
                domain_name: domainName,
                search_type: searchType,
                limit,
                offset,
                filters,
                ranking
            })
        });

        return await response.json();
    }

    async autocomplete(prefix, domainName = null, maxSuggestions = 10) {
        const params = new URLSearchParams({
            prefix,
            max_suggestions: maxSuggestions
        });

        if (domainName) {
            params.append('domain_name', domainName);
        }

        const response = await fetch(
            `${this.baseUrl}/api/search/suggest?${params}`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    // ========================================================================
    // KNOWLEDGE GRAPH
    // ========================================================================

    async getGraphStatistics(domainName) {
        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/statistics`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    async listEntities(domainName, entityType = null, limit = 100) {
        const params = new URLSearchParams({ limit });
        if (entityType) params.append('entity_type', entityType);

        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/entities?${params}`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    async getEntity(domainName, entityId) {
        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/entities/${entityId}`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    async getRelatedEntities(domainName, entityId, relationType = null, direction = 'both') {
        const params = new URLSearchParams({ direction });
        if (relationType) params.append('relation_type', relationType);

        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/entities/${entityId}/related?${params}`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    async createEntity(domainName, entityType, name, properties = {}, sourceDocument = 'manual', confidence = 1.0) {
        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/entities`,
            {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    type: entityType,
                    name,
                    properties,
                    source_document: sourceDocument,
                    confidence
                })
            }
        );

        return await response.json();
    }

    async queryGraph(domainName, queryType, query, parameters = {}, limit = 10) {
        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/query`,
            {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    query_type: queryType,
                    query,
                    parameters,
                    limit
                })
            }
        );

        return await response.json();
    }

    // ========================================================================
    // CONTEXTS
    // ========================================================================

    async listContexts() {
        const response = await fetch(`${this.baseUrl}/api/contexts`, {
            headers: this.getHeaders()
        });

        return await response.json();
    }

    async createContext(name, contextType, description = '', activeDomains = [], properties = {}) {
        const response = await fetch(`${this.baseUrl}/api/contexts`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({
                name,
                type: contextType,
                description,
                active_domains: activeDomains,
                properties
            })
        });

        return await response.json();
    }

    async switchContext(contextId) {
        const response = await fetch(
            `${this.baseUrl}/api/contexts/${contextId}/switch`,
            {
                method: 'POST',
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    // ========================================================================
    // ANALYTICS
    // ========================================================================

    async getGraphAnalytics(domainName, analysisType, topN = 10) {
        const params = new URLSearchParams({
            analysis_type: analysisType,
            top_n: topN
        });

        const response = await fetch(
            `${this.baseUrl}/api/analytics/${domainName}/graph?${params}`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    // ========================================================================
    // WEBSOCKET
    // ========================================================================

    connectWebSocket(userId, onMessageCallback = null) {
        const wsUrl = this.baseUrl
            .replace('http://', 'ws://')
            .replace('https://', 'wss://');

        this.ws = new WebSocket(`${wsUrl}/ws/${userId}`);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);

            if (onMessageCallback) {
                onMessageCallback(data);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed');
        };
    }

    subscribeToEvent(eventType) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'subscribe',
                event_type: eventType
            }));
        }
    }

    unsubscribeFromEvent(eventType) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'unsubscribe',
                event_type: eventType
            }));
        }
    }
}


// ============================================================================
// ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
// ============================================================================

async function exampleUsage() {
    // Создать клиента
    const client = new IOSClient('http://localhost:8000');

    // Войти
    const loggedIn = await client.login('admin', 'admin');
    if (loggedIn) {
        console.log('✓ Logged in successfully');
    }

    // Создать домен
    const domain = await client.createDomain(
        'SGB-IX',
        'de',
        'Deutsches Sozialrecht',
        ['Gesetz', 'Paragraph', 'Behörde']
    );
    console.log(`✓ Created domain: ${domain.name}`);

    // Поиск
    const results = await client.search('Persönliches Budget', {
        domainName: 'SGB-IX',
        searchType: 'hybrid',
        limit: 5
    });
    console.log(`✓ Found ${results.total_count} documents`);
    results.results.forEach(result => {
        console.log(`  - ${result.title} (score: ${result.score.toFixed(3)})`);
    });

    // Автодополнение
    const suggestions = await client.autocomplete('Pers', 'SGB-IX', 5);
    console.log('✓ Autocomplete suggestions:', suggestions);

    // Статистика графа
    const stats = await client.getGraphStatistics('SGB-IX');
    console.log('✓ Graph statistics:');
    console.log(`  Entities: ${stats.total_entities}`);
    console.log(`  Relations: ${stats.total_relations}`);

    // Сущности
    const entities = await client.listEntities('SGB-IX', 'Paragraph', 10);
    console.log(`✓ Found ${entities.length} paragraphs`);

    // Аналитика
    const analytics = await client.getGraphAnalytics('SGB-IX', 'most_connected', 5);
    console.log('✓ Top 5 most connected entities:');
    analytics.results.forEach(item => {
        const entity = item.entity;
        console.log(`  - ${entity.name} (${entity.type}): ${item.degree} connections`);
    });

    // WebSocket
    client.connectWebSocket('user123', (data) => {
        console.log(`Received: ${data.type}`);
    });

    client.subscribeToEvent('document.added');
    client.subscribeToEvent('entity.extracted');
}

// Запустить примеры (в браузере или Node.js)
// exampleUsage();
```

## 9.4 Клиентские примеры - cURL

```bash
#!/bin/bash
# examples/curl_examples.sh
# Примеры использования API через cURL

BASE_URL="http://localhost:8000"
TOKEN=""

# ============================================================================
# AUTHENTICATION
# ============================================================================

# Вход
echo "=== Login ==="
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Token: ${TOKEN:0:20}..."

# ============================================================================
# DOMAINS
# ============================================================================

# Список доменов
echo -e "\n=== List Domains ==="
curl -s -X GET "$BASE_URL/api/domains" \
  -H "Authorization: Bearer $TOKEN" | jq

# Создать домен
echo -e "\n=== Create Domain ==="
curl -s -X POST "$BASE_URL/api/domains" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SGB-IX",
    "language": "de",
    "description": "Deutsches Sozialrecht",
    "entity_types": ["Gesetz", "Paragraph", "Behörde", "Leistung"]
  }' | jq

# Получить домен
echo -e "\n=== Get Domain ==="
curl -s -X GET "$BASE_URL/api/domains/SGB-IX" \
  -H "Authorization: Bearer $TOKEN" | jq

# ============================================================================
# DOCUMENTS
# ============================================================================

# Загрузить документ
echo -e "\n=== Upload Document ==="
curl -s -X POST "$BASE_URL/api/documents/upload?domain_name=SGB-IX&title=Test+Document" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/document.pdf" | jq

# ============================================================================
# SEARCH
# ============================================================================

# Полнотекстовый поиск
echo -e "\n=== Full-Text Search ==="
curl -s -X POST "$BASE_URL/api/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Persönliches Budget",
    "domain_name": "SGB-IX",
    "search_type": "full_text",
    "limit": 5
  }' | jq

# Семантический поиск
echo -e "\n=== Semantic Search ==="
curl -s -X POST "$BASE_URL/api/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Wie bekomme ich Unterstützung?",
    "domain_name": "SGB-IX",
    "search_type": "semantic",
    "limit": 5
  }' | jq

# Гибридный поиск
echo -e "\n=== Hybrid Search ==="
curl -s -X POST "$BASE_URL/api/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SGB IX Teilhabe",
    "domain_name": "SGB-IX",
    "search_type": "hybrid",
    "ranking": "hybrid",
    "limit": 5
  }' | jq

# Автодополнение
echo -e "\n=== Autocomplete ==="
curl -s -X GET "$BASE_URL/api/search/suggest?prefix=Pers&domain_name=SGB-IX&max_suggestions=5" \
  -H "Authorization: Bearer $TOKEN" | jq

# ============================================================================
# KNOWLEDGE GRAPH
# ============================================================================

# Статистика графа
echo -e "\n=== Graph Statistics ==="
curl -s -X GET "$BASE_URL/api/graph/SGB-IX/statistics" \
  -H "Authorization: Bearer $TOKEN" | jq

# Список сущностей
echo -e "\n=== List Entities ==="
curl -s -X GET "$BASE_URL/api/graph/SGB-IX/entities?entity_type=Paragraph&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq

# Создать сущность
echo -e "\n=== Create Entity ==="
curl -s -X POST "$BASE_URL/api/graph/SGB-IX/entities" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Paragraph",
    "name": "§29",
    "properties": {
      "title": "Persönliches Budget",
      "law": "SGB-IX"
    },
    "source_document": "manual",
    "confidence": 1.0
  }' | jq

# Получить сущность
echo -e "\n=== Get Entity ==="
ENTITY_ID="entity_Paragraph_§29"
curl -s -X GET "$BASE_URL/api/graph/SGB-IX/entities/$ENTITY_ID" \
  -H "Authorization: Bearer $TOKEN" | jq

# Получить связанные сущности
echo -e "\n=== Get Related Entities ==="
curl -s -X GET "$BASE_URL/api/graph/SGB-IX/entities/$ENTITY_ID/related?direction=both" \
  -H "Authorization: Bearer $TOKEN" | jq

# Создать отношение
echo -e "\n=== Create Relation ==="
curl -s -X POST "$BASE_URL/api/graph/SGB-IX/relations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "verweist_auf",
    "source_id": "entity_para_29",
    "target_id": "entity_para_8",
    "properties": {},
    "confidence": 0.95
  }' | jq

# Запрос к графу (Cypher-like)
echo -e "\n=== Graph Query ==="
curl -s -X POST "$BASE_URL/api/graph/SGB-IX/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "cypher",
    "query": "MATCH (p:Paragraph)-[:belongs_to]->(g:Gesetz) RETURN p, g",
    "limit": 10
  }' | jq

# ============================================================================
# CONTEXTS
# ============================================================================

# Список контекстов
echo -e "\n=== List Contexts ==="
curl -s -X GET "$BASE_URL/api/contexts" \
  -H "Authorization: Bearer $TOKEN" | jq

# Создать контекст
echo -e "\n=== Create Context ==="
curl -s -X POST "$BASE_URL/api/contexts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Court Case S 12/2024",
    "type": "legal_case",
    "description": "Personal budget dispute",
    "active_domains": ["SGB-IX"],
    "properties": {
      "case_number": "S 12/2024",
      "court": "Sozialgericht München"
    }
  }' | jq

# Переключить контекст
echo -e "\n=== Switch Context ==="
CONTEXT_ID="ctx_court_case_s_12_2024"
curl -s -X POST "$BASE_URL/api/contexts/$CONTEXT_ID/switch" \
  -H "Authorization: Bearer $TOKEN" | jq

# ============================================================================
# ANALYTICS
# ============================================================================

# Наиболее связанные сущности
echo -e "\n=== Most Connected Entities ==="
curl -s -X GET "$BASE_URL/api/analytics/SGB-IX/graph?analysis_type=most_connected&top_n=5" \
  -H "Authorization: Bearer $TOKEN" | jq

# Центральные сущности
echo -e "\n=== Central Entities ==="
curl -s -X GET "$BASE_URL/api/analytics/SGB-IX/graph?analysis_type=central&top_n=5" \
  -H "Authorization: Bearer $TOKEN" | jq

# Обнаружение сообществ
echo -e "\n=== Communities ==="
curl -s -X GET "$BASE_URL/api/analytics/SGB-IX/graph?analysis_type=communities" \
  -H "Authorization: Bearer $TOKEN" | jq

# Рекомендации
echo -e "\n=== Recommendations ==="
curl -s -X GET "$BASE_URL/api/analytics/SGB-IX/graph?analysis_type=recommendations" \
  -H "Authorization: Bearer $TOKEN" | jq

# ============================================================================
# EXPORT
# ============================================================================

# Экспорт графа в GEXF (Gephi)
echo -e "\n=== Export Graph (GEXF) ==="
curl -X GET "$BASE_URL/api/export/SGB-IX/graph?format=gexf" \
  -H "Authorization: Bearer $TOKEN" \
  -o "graph_export.gexf"

# Экспорт графа в JSON
echo -e "\n=== Export Graph (JSON) ==="
curl -s -X GET "$BASE_URL/api/export/SGB-IX/graph?format=json" \
  -H "Authorization: Bearer $TOKEN" | jq

# ============================================================================
# SYSTEM
# ============================================================================

# Статус системы
echo -e "\n=== System Status ==="
curl -s -X GET "$BASE_URL/api/system/status" \
  -H "Authorization: Bearer $TOKEN" | jq

# Health check
echo -e "\n=== Health Check ==="
curl -s -X GET "$BASE_URL/api/system/health" | jq
```

Продолжить с Android интеграцией и Docker deployment?