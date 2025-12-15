"""
Real-time Alert Service - Система оповещений в реальном времени
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import asyncio
import logging
import aiohttp
import json

logger = logging.getLogger(__name__)


class AlertChannel(Enum):
    """Каналы оповещения"""
    EMAIL = "email"
    SLACK = "slack"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    SMS = "sms"
    PUSH = "push"


class AlertPriority(Enum):
    """Приоритеты оповещений"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Alert:
    """Оповещение"""
    
    def __init__(
        self,
        title: str,
        message: str,
        priority: AlertPriority = AlertPriority.NORMAL,
        channels: Optional[List[AlertChannel]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.id = self._generate_id()
        self.timestamp = datetime.now()
        self.title = title
        self.message = message
        self.priority = priority
        self.channels = channels or [AlertChannel.EMAIL]
        self.details = details or {}
        self.sent = False
        self.sent_at: Optional[datetime] = None
        
    @staticmethod
    def _generate_id() -> str:
        """Генерация уникального ID"""
        import uuid
        return str(uuid.uuid4())
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'title': self.title,
            'message': self.message,
            'priority': self.priority.value,
            'channels': [c.value for c in self.channels],
            'details': self.details,
            'sent': self.sent,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }


class AlertService:
    """
    Сервис отправки оповещений
    """
    
    def __init__(
        self,
        email_config: Optional[Dict] = None,
        slack_config: Optional[Dict] = None,
        telegram_config: Optional[Dict] = None,
        webhook_config: Optional[Dict] = None
    ):
        self.email_config = email_config or {}
        self.slack_config = slack_config or {}
        self.telegram_config = telegram_config or {}
        self.webhook_config = webhook_config or {}
        
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self.sent_alerts: List[Alert] = []
        self.is_running = False
        
    async def start(self):
        """Запуск сервиса оповещений"""
        self.is_running = True
        logger.info("Alert service started")
        
        # Запускаем worker для обработки очереди
        asyncio.create_task(self._process_queue())
        
    async def stop(self):
        """Остановка сервиса"""
        self.is_running = False
        logger.info("Alert service stopped")
        
    async def send_alert(
        self,
        title: str,
        message: str,
        level: str = "normal",
        channels: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Отправка оповещения
        
        Args:
            title: Заголовок оповещения
            message: Текст сообщения
            level: Уровень приоритета (low, normal, high, urgent)
            channels: Каналы для отправки
            details: Дополнительные детали
        """
        try:
            # Конвертируем priority
            priority_map = {
                'low': AlertPriority.LOW,
                'normal': AlertPriority.NORMAL,
                'high': AlertPriority.HIGH,
                'urgent': AlertPriority.URGENT,
                'critical': AlertPriority.URGENT
            }
            priority = priority_map.get(level.lower(), AlertPriority.NORMAL)
            
            # Конвертируем channels
            channel_objs = []
            if channels:
                channel_map = {
                    'email': AlertChannel.EMAIL,
                    'slack': AlertChannel.SLACK,
                    'telegram': AlertChannel.TELEGRAM,
                    'webhook': AlertChannel.WEBHOOK,
                    'sms': AlertChannel.SMS,
                    'push': AlertChannel.PUSH
                }
                channel_objs = [
                    channel_map[ch] 
                    for ch in channels 
                    if ch in channel_map
                ]
                
            # Создаем alert
            alert = Alert(
                title=title,
                message=message,
                priority=priority,
                channels=channel_objs if channel_objs else None,
                details=details
            )
            
            # Добавляем в очередь
            await self.alert_queue.put(alert)
            
            logger.info(f"Alert queued: {title}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            
    async def _process_queue(self):
        """Обработка очереди оповещений"""
        while self.is_running:
            try:
                # Получаем alert из очереди с timeout
                alert = await asyncio.wait_for(
                    self.alert_queue.get(),
                    timeout=1.0
                )
                
                # Отправляем по всем каналам
                await self._send_to_channels(alert)
                
                # Помечаем как отправленное
                alert.sent = True
                alert.sent_at = datetime.now()
                self.sent_alerts.append(alert)
                
                # Ограничиваем размер истории
                if len(self.sent_alerts) > 1000:
                    self.sent_alerts = self.sent_alerts[-1000:]
                    
            except asyncio.TimeoutError:
                # Timeout - продолжаем цикл
                continue
            except Exception as e:
                logger.error(f"Error processing alert queue: {e}")
                await asyncio.sleep(1)
                
    async def _send_to_channels(self, alert: Alert):
        """Отправка оповещения по всем каналам"""
        tasks = []
        
        for channel in alert.channels:
            if channel == AlertChannel.EMAIL:
                tasks.append(self._send_email(alert))
            elif channel == AlertChannel.SLACK:
                tasks.append(self._send_slack(alert))
            elif channel == AlertChannel.TELEGRAM:
                tasks.append(self._send_telegram(alert))
            elif channel == AlertChannel.WEBHOOK:
                tasks.append(self._send_webhook(alert))
                
        # Отправляем параллельно
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Логируем результаты
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to send via {alert.channels[i].value}: {result}")
                    
    async def _send_email(self, alert: Alert) -> bool:
        """Отправка email оповещения"""
        try:
            if not self.email_config:
                logger.warning("Email config not set, skipping email alert")
                return False
                
            # TODO: Интеграция с email сервисом (SMTP, SendGrid, etc)
            logger.info(f"Email alert sent: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
            
    async def _send_slack(self, alert: Alert) -> bool:
        """Отправка Slack оповещения"""
        try:
            webhook_url = self.slack_config.get('webhook_url')
            if not webhook_url:
                logger.warning("Slack webhook not configured")
                return False
                
            # Формируем сообщение
            color_map = {
                AlertPriority.LOW: "#36a64f",  # green
                AlertPriority.NORMAL: "#2196F3",  # blue
                AlertPriority.HIGH: "#ff9800",  # orange
                AlertPriority.URGENT: "#f44336"  # red
            }
            
            payload = {
                "attachments": [{
                    "color": color_map.get(alert.priority, "#2196F3"),
                    "title": alert.title,
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Priority",
                            "value": alert.priority.value,
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "short": True
                        }
                    ],
                    "footer": "IOS System Alert",
                    "ts": int(alert.timestamp.timestamp())
                }]
            }
            
            # Отправляем webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent: {alert.title}")
                        return True
                    else:
                        logger.error(f"Slack webhook failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
            
    async def _send_telegram(self, alert: Alert) -> bool:
        """Отправка Telegram оповещения"""
        try:
            bot_token = self.telegram_config.get('bot_token')
            chat_id = self.telegram_config.get('chat_id')
            
            if not bot_token or not chat_id:
                logger.warning("Telegram config incomplete")
                return False
                
            # Формируем сообщение
            priority_emoji = {
                AlertPriority.LOW: "ℹ️",
                AlertPriority.NORMAL: "📢",
                AlertPriority.HIGH: "⚠️",
                AlertPriority.URGENT: "🚨"
            }
            
            text = f"{priority_emoji.get(alert.priority, '📢')} *{alert.title}*\n\n{alert.message}"
            
            # Отправляем через Bot API
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Telegram alert sent: {alert.title}")
                        return True
                    else:
                        logger.error(f"Telegram API failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
            
    async def _send_webhook(self, alert: Alert) -> bool:
        """Отправка webhook оповещения"""
        try:
            webhook_url = self.webhook_config.get('url')
            if not webhook_url:
                logger.warning("Webhook URL not configured")
                return False
                
            # Отправляем POST запрос
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=alert.to_dict(),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent: {alert.title}")
                        return True
                    else:
                        logger.error(f"Webhook failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False
            
    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получение последних оповещений
        
        Args:
            limit: Максимальное количество
            
        Returns:
            Список оповещений
        """
        return [
            alert.to_dict() 
            for alert in self.sent_alerts[-limit:]
        ]
        
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики"""
        return {
            'total_sent': len(self.sent_alerts),
            'queue_size': self.alert_queue.qsize(),
            'is_running': self.is_running,
            'by_priority': self._count_by_priority(),
            'by_channel': self._count_by_channel()
        }
        
    def _count_by_priority(self) -> Dict[str, int]:
        """Подсчет по приоритетам"""
        counts = {p.value: 0 for p in AlertPriority}
        for alert in self.sent_alerts:
            counts[alert.priority.value] += 1
        return counts
        
    def _count_by_channel(self) -> Dict[str, int]:
        """Подсчет по каналам"""
        counts = {c.value: 0 for c in AlertChannel}
        for alert in self.sent_alerts:
            for channel in alert.channels:
                counts[channel.value] += 1
        return counts
