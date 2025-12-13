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