# api/websocket.py - Enhanced

from fastapi import WebSocket
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_tasks: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
    
    async def send_task_progress(self, user_id: str, task_id: str, progress: dict):
        """Send task progress to user"""
        if user_id in self.active_connections:
            message = {
                'type': 'task.progress',
                'task_id': task_id,
                'data': progress
            }
            
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)
    
    async def send_task_complete(self, user_id: str, task_id: str, result: dict):
        """Send task completion"""
        if user_id in self.active_connections:
            message = {
                'type': 'task.complete',
                'task_id': task_id,
                'result': result
            }
            
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)


manager = ConnectionManager()