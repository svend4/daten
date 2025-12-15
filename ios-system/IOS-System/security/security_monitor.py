"""
Security Monitoring System - Мониторинг безопасности в реальном времени
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import asyncio
import logging
from dataclasses import dataclass
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Уровни угроз"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Типы угроз"""
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    DDOS = "ddos"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfiltration"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    PRIVILEGE_ESCALATION = "privilege_escalation"


@dataclass
class SecurityEvent:
    """События безопасности"""
    timestamp: datetime
    threat_type: ThreatType
    threat_level: ThreatLevel
    source_ip: str
    user_id: Optional[str]
    description: str
    details: Dict[str, Any]
    blocked: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'threat_type': self.threat_type.value,
            'threat_level': self.threat_level.value,
            'source_ip': self.source_ip,
            'user_id': self.user_id,
            'description': self.description,
            'details': self.details,
            'blocked': self.blocked
        }


class SecurityMetrics:
    """Метрики безопасности"""
    
    def __init__(self):
        self.total_events = 0
        self.events_by_type: Dict[ThreatType, int] = defaultdict(int)
        self.events_by_level: Dict[ThreatLevel, int] = defaultdict(int)
        self.blocked_attacks = 0
        self.unique_ips = set()
        self.recent_events: deque = deque(maxlen=100)
        
    def record_event(self, event: SecurityEvent):
        """Запись события"""
        self.total_events += 1
        self.events_by_type[event.threat_type] += 1
        self.events_by_level[event.threat_level] += 1
        if event.blocked:
            self.blocked_attacks += 1
        self.unique_ips.add(event.source_ip)
        self.recent_events.append(event)
        
    def get_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик"""
        return {
            'total_events': self.total_events,
            'events_by_type': {k.value: v for k, v in self.events_by_type.items()},
            'events_by_level': {k.value: v for k, v in self.events_by_level.items()},
            'blocked_attacks': self.blocked_attacks,
            'unique_ips_count': len(self.unique_ips),
            'recent_events_count': len(self.recent_events)
        }


class ThreatDetector:
    """
    Система обнаружения угроз
    """
    
    def __init__(
        self,
        redis_cache: Any = None,
        db_manager: Any = None
    ):
        self.redis_cache = redis_cache
        self.db_manager = db_manager
        
        # Счетчики для обнаружения
        self.login_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Пороги обнаружения
        self.brute_force_threshold = 5  # попыток за период
        self.brute_force_window = 300  # 5 минут
        self.ddos_threshold = 100  # запросов за период
        self.ddos_window = 60  # 1 минута
        
    async def check_brute_force(
        self,
        ip_address: str,
        user_identifier: Optional[str] = None
    ) -> Optional[SecurityEvent]:
        """
        Проверка на brute force атаку
        
        Returns:
            SecurityEvent если обнаружена атака
        """
        key = f"{ip_address}:{user_identifier}" if user_identifier else ip_address
        now = datetime.now()
        
        # Добавляем попытку
        self.login_attempts[key].append(now)
        
        # Удаляем старые попытки
        cutoff = now - timedelta(seconds=self.brute_force_window)
        self.login_attempts[key] = [
            t for t in self.login_attempts[key] if t > cutoff
        ]
        
        # Проверяем порог
        if len(self.login_attempts[key]) >= self.brute_force_threshold:
            logger.warning(f"Brute force detected from {ip_address}")
            
            event = SecurityEvent(
                timestamp=now,
                threat_type=ThreatType.BRUTE_FORCE,
                threat_level=ThreatLevel.HIGH,
                source_ip=ip_address,
                user_id=user_identifier,
                description=f"Brute force attack detected: {len(self.login_attempts[key])} attempts",
                details={
                    'attempts': len(self.login_attempts[key]),
                    'window_seconds': self.brute_force_window
                },
                blocked=True
            )
            
            # Блокируем IP
            await self._block_ip(ip_address, duration=3600)  # 1 час
            
            return event
            
        return None
        
    async def check_ddos(
        self,
        ip_address: str,
        endpoint: str
    ) -> Optional[SecurityEvent]:
        """
        Проверка на DDoS атаку
        
        Returns:
            SecurityEvent если обнаружена атака
        """
        key = f"{ip_address}:{endpoint}"
        now = datetime.now()
        
        # Добавляем запрос
        self.request_counts[key].append(now)
        
        # Считаем запросы в окне
        cutoff = now - timedelta(seconds=self.ddos_window)
        recent_requests = [t for t in self.request_counts[key] if t > cutoff]
        
        # Проверяем порог
        if len(recent_requests) >= self.ddos_threshold:
            logger.warning(f"Possible DDoS from {ip_address}")
            
            event = SecurityEvent(
                timestamp=now,
                threat_type=ThreatType.DDOS,
                threat_level=ThreatLevel.CRITICAL,
                source_ip=ip_address,
                user_id=None,
                description=f"Possible DDoS attack: {len(recent_requests)} requests",
                details={
                    'requests': len(recent_requests),
                    'window_seconds': self.ddos_window,
                    'endpoint': endpoint
                },
                blocked=True
            )
            
            # Блокируем IP
            await self._block_ip(ip_address, duration=7200)  # 2 часа
            
            return event
            
        return None
        
    async def check_sql_injection(self, query: str, ip_address: str) -> Optional[SecurityEvent]:
        """Проверка на SQL injection"""
        sql_patterns = [
            "' OR '1'='1",
            "' OR 1=1--",
            "UNION SELECT",
            "DROP TABLE",
            "'; DROP",
            "' AND '",
            "OR 1=1",
            "-- ",
            "/*",
            "xp_"
        ]
        
        query_upper = query.upper()
        
        for pattern in sql_patterns:
            if pattern.upper() in query_upper:
                logger.critical(f"SQL injection attempt from {ip_address}")
                
                event = SecurityEvent(
                    timestamp=datetime.now(),
                    threat_type=ThreatType.SQL_INJECTION,
                    threat_level=ThreatLevel.CRITICAL,
                    source_ip=ip_address,
                    user_id=None,
                    description="SQL injection attempt detected",
                    details={
                        'pattern': pattern,
                        'query_snippet': query[:100]
                    },
                    blocked=True
                )
                
                # Немедленно блокируем IP
                await self._block_ip(ip_address, duration=86400)  # 24 часа
                
                return event
                
        return None
        
    async def check_xss(self, content: str, ip_address: str) -> Optional[SecurityEvent]:
        """Проверка на XSS атаку"""
        xss_patterns = [
            "<script",
            "javascript:",
            "onerror=",
            "onload=",
            "onclick=",
            "eval(",
            "alert(",
            "<iframe"
        ]
        
        content_lower = content.lower()
        
        for pattern in xss_patterns:
            if pattern in content_lower:
                logger.warning(f"XSS attempt from {ip_address}")
                
                event = SecurityEvent(
                    timestamp=datetime.now(),
                    threat_type=ThreatType.XSS_ATTACK,
                    threat_level=ThreatLevel.HIGH,
                    source_ip=ip_address,
                    user_id=None,
                    description="XSS attack attempt detected",
                    details={
                        'pattern': pattern,
                        'content_snippet': content[:100]
                    },
                    blocked=True
                )
                
                return event
                
        return None
        
    async def check_unauthorized_access(
        self,
        user_id: str,
        resource_id: str,
        ip_address: str
    ) -> Optional[SecurityEvent]:
        """Проверка на несанкционированный доступ"""
        # Здесь должна быть логика проверки прав доступа
        # Для примера - упрощенная версия
        
        # TODO: Интеграция с RBAC системой
        
        return None
        
    async def _block_ip(self, ip_address: str, duration: int):
        """
        Блокировка IP адреса
        
        Args:
            ip_address: IP для блокировки
            duration: Длительность в секундах
        """
        if self.redis_cache:
            try:
                key = f"blocked_ip:{ip_address}"
                await self.redis_cache.set(key, "1", ex=duration)
                logger.info(f"IP {ip_address} blocked for {duration} seconds")
            except Exception as e:
                logger.error(f"Failed to block IP: {e}")
                
    async def is_ip_blocked(self, ip_address: str) -> bool:
        """
        Проверка блокировки IP
        
        Returns:
            True если IP заблокирован
        """
        if self.redis_cache:
            try:
                key = f"blocked_ip:{ip_address}"
                result = await self.redis_cache.get(key)
                return result is not None
            except Exception as e:
                logger.error(f"Failed to check IP block: {e}")
                
        return False


class SecurityMonitor:
    """
    Централизованная система мониторинга безопасности
    """
    
    def __init__(
        self,
        threat_detector: ThreatDetector,
        audit_logger: Any = None,
        alert_service: Any = None
    ):
        self.threat_detector = threat_detector
        self.audit_logger = audit_logger
        self.alert_service = alert_service
        
        self.metrics = SecurityMetrics()
        self.is_monitoring = False
        
    async def start_monitoring(self):
        """Запуск мониторинга"""
        self.is_monitoring = True
        logger.info("Security monitoring started")
        
        # Запускаем фоновую задачу для периодического анализа
        asyncio.create_task(self._periodic_analysis())
        
    async def stop_monitoring(self):
        """Остановка мониторинга"""
        self.is_monitoring = False
        logger.info("Security monitoring stopped")
        
    async def record_event(self, event: SecurityEvent):
        """
        Запись события безопасности
        
        Args:
            event: Событие для записи
        """
        # Обновляем метрики
        self.metrics.record_event(event)
        
        # Логируем в audit log
        if self.audit_logger:
            await self.audit_logger.log_security_event(
                event_type=event.threat_type.value,
                user_id=event.user_id,
                ip_address=event.source_ip,
                details=event.details
            )
            
        # Отправляем алерт если критично
        if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            await self._send_alert(event)
            
        logger.info(f"Security event recorded: {event.threat_type.value} from {event.source_ip}")
        
    async def _send_alert(self, event: SecurityEvent):
        """Отправка алерта о критическом событии"""
        if self.alert_service:
            try:
                await self.alert_service.send_alert(
                    title=f"Security Alert: {event.threat_type.value}",
                    message=event.description,
                    level=event.threat_level.value,
                    details=event.to_dict()
                )
            except Exception as e:
                logger.error(f"Failed to send security alert: {e}")
                
    async def _periodic_analysis(self):
        """Периодический анализ безопасности"""
        while self.is_monitoring:
            try:
                # Анализ каждые 5 минут
                await asyncio.sleep(300)
                
                # Получаем метрики
                summary = self.metrics.get_summary()
                
                # Проверяем аномалии
                if summary['total_events'] > 1000:
                    logger.warning("High number of security events detected")
                    
                if summary['blocked_attacks'] > 50:
                    logger.critical("High number of blocked attacks")
                    
            except Exception as e:
                logger.error(f"Error in periodic analysis: {e}")
                
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Получение данных для dashboard
        
        Returns:
            Данные для отображения
        """
        summary = self.metrics.get_summary()
        
        # Последние события
        recent_events = [
            event.to_dict() 
            for event in list(self.metrics.recent_events)[-10:]
        ]
        
        return {
            'summary': summary,
            'recent_events': recent_events,
            'monitoring_status': 'active' if self.is_monitoring else 'inactive',
            'timestamp': datetime.now().isoformat()
        }
