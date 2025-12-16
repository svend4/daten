"""
Metrics Collector - Сбор и хранение метрик системы
"""
import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Сборщик метрик для мониторинга системы
    """

    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = defaultdict(list)
        self._start_time = datetime.now()
        logger.info("Metrics Collector initialized")

    def increment(self, name: str, value: int = 1):
        """Увеличение счетчика"""
        self._counters[name] += value

    def decrement(self, name: str, value: int = 1):
        """Уменьшение счетчика"""
        self._counters[name] -= value

    def gauge(self, name: str, value: float):
        """Установка значения gauge"""
        self._gauges[name] = value

    def histogram(self, name: str, value: float):
        """Добавление значения в гистограмму"""
        self._histograms[name].append(value)
        # Ограничиваем размер
        if len(self._histograms[name]) > 10000:
            self._histograms[name] = self._histograms[name][-5000:]

    def get_metrics(self) -> Dict[str, Any]:
        """Получение всех метрик"""
        uptime = (datetime.now() - self._start_time).total_seconds()

        return {
            "uptime_seconds": uptime,
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: {
                    "count": len(values),
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "avg": sum(values) / len(values) if values else 0
                }
                for name, values in self._histograms.items()
            },
            "timestamp": datetime.now().isoformat()
        }

    # Event handlers for integration with EventBus
    def on_search_performed(self, data: Any):
        """Обработчик события поиска"""
        self.increment("search.total")

    def on_search_failed(self, data: Any):
        """Обработчик ошибки поиска"""
        self.increment("search.failed")

    def on_classification_completed(self, data: Any):
        """Обработчик завершения классификации"""
        self.increment("classification.total")

    def on_entity_extracted(self, data: Any):
        """Обработчик извлечения сущности"""
        self.increment("entities.extracted")

    def on_relation_extracted(self, data: Any):
        """Обработчик извлечения связи"""
        self.increment("relations.extracted")

    def reset(self):
        """Сброс всех метрик"""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._start_time = datetime.now()

    def __repr__(self) -> str:
        return f"MetricsCollector(counters={len(self._counters)}, gauges={len(self._gauges)})"
