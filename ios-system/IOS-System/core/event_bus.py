"""
Event Bus - Шина событий для асинхронного взаимодействия компонентов
"""
import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventBus:
    """
    Асинхронная шина событий
    Позволяет компонентам общаться через publish/subscribe паттерн
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = asyncio.Lock()
        logger.info("Event Bus initialized")

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Подписка на событие

        Args:
            event_type: Тип события (например, 'document.created')
            callback: Функция-обработчик события
        """
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to '{event_type}': {callback.__name__}")

    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """
        Отписка от события

        Args:
            event_type: Тип события
            callback: Функция-обработчик

        Returns:
            True если callback был найден и удален
        """
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            logger.debug(f"Unsubscribed from '{event_type}': {callback.__name__}")
            return True
        return False

    async def publish(self, event_type: str, data: Any = None) -> None:
        """
        Публикация события

        Args:
            event_type: Тип события
            data: Данные события
        """
        subscribers = self._subscribers.get(event_type, [])

        if not subscribers:
            logger.debug(f"No subscribers for event '{event_type}'")
            return

        logger.debug(f"Publishing '{event_type}' to {len(subscribers)} subscribers")

        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Error in event handler for '{event_type}': {e}")

    def publish_sync(self, event_type: str, data: Any = None) -> None:
        """
        Синхронная публикация события (для non-async контекста)
        """
        subscribers = self._subscribers.get(event_type, [])

        for callback in subscribers:
            try:
                if not asyncio.iscoroutinefunction(callback):
                    callback(data)
            except Exception as e:
                logger.error(f"Error in sync event handler for '{event_type}': {e}")

    def get_subscribers_count(self, event_type: str) -> int:
        """Количество подписчиков на событие"""
        return len(self._subscribers.get(event_type, []))

    def list_events(self) -> List[str]:
        """Список всех типов событий с подписчиками"""
        return list(self._subscribers.keys())

    def clear(self) -> None:
        """Очистка всех подписок"""
        self._subscribers.clear()
        logger.info("Event Bus cleared")

    def __repr__(self) -> str:
        total = sum(len(subs) for subs in self._subscribers.values())
        return f"EventBus(events={len(self._subscribers)}, subscribers={total})"
