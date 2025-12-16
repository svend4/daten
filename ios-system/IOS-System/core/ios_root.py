"""
IOS Root - Корневой компонент системы
"""
import logging
from typing import Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class IOSRoot:
    """
    Корневой компонент IOS System
    Управляет файловой структурой и координирует работу системы
    """

    def __init__(
        self,
        event_bus: Any = None,
        db_manager: Any = None,
        cache: Any = None,
        root_path: Optional[Path] = None
    ):
        self.event_bus = event_bus
        self.db_manager = db_manager
        self.cache = cache
        self.root_path = root_path or Path("/data/ios-root")
        self._initialized = False

    async def initialize(self):
        """Инициализация корневого компонента"""
        logger.info("Initializing IOS Root...")

        # Создаем базовые директории
        self.root_path.mkdir(parents=True, exist_ok=True)

        directories = [
            "documents",
            "uploads",
            "exports",
            "cache",
            "indices",
            "temp"
        ]

        for dir_name in directories:
            dir_path = self.root_path / dir_name
            dir_path.mkdir(exist_ok=True)

        self._initialized = True
        logger.info(f"✅ IOS Root initialized at {self.root_path}")

    async def shutdown(self):
        """Завершение работы"""
        logger.info("Shutting down IOS Root...")
        self._initialized = False
        logger.info("✅ IOS Root shutdown complete")

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def get_path(self, *parts) -> Path:
        """Получение пути относительно корня"""
        return self.root_path.joinpath(*parts)

    def __repr__(self) -> str:
        return f"IOSRoot(path={self.root_path}, initialized={self._initialized})"
