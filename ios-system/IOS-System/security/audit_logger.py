"""
Advanced Audit Log System - Комплексное логирование действий пользователей
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import logging
from dataclasses import dataclass, asdict
import asyncio

logger = logging.getLogger(__name__)


class AuditActionType(Enum):
    """Типы аудируемых действий"""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # Authorization
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    
    # Document operations
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_VIEWED = "document_viewed"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_DOWNLOADED = "document_downloaded"
    DOCUMENT_SHARED = "document_shared"
    
    # Search operations
    SEARCH_PERFORMED = "search_performed"
    SEARCH_FAILED = "search_failed"
    
    # Data operations
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    DATA_DELETED = "data_deleted"
    
    # System operations
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    
    # Security events
    SECURITY_ALERT = "security_alert"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BRUTE_FORCE_DETECTED = "brute_force_detected"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"


class AuditSeverityLevel(Enum):
    """Уровни серьезности событий"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLogEntry:
    """Запись в audit log"""
    timestamp: datetime
    action_type: AuditActionType
    user_id: Optional[str]
    user_email: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action_result: str  # success, failure, partial
    severity: AuditSeverityLevel
    details: Dict[str, Any]
    request_id: Optional[str]
    session_id: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['action_type'] = self.action_type.value
        data['severity'] = self.severity.value
        return data
        
    def to_json(self) -> str:
        """Конвертация в JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """
    Централизованная система audit logging
    """
    
    def __init__(
        self,
        db_manager: Any = None,
        enable_database_logging: bool = True,
        enable_file_logging: bool = True,
        log_file_path: str = "logs/audit.log"
    ):
        self.db_manager = db_manager
        self.enable_database_logging = enable_database_logging
        self.enable_file_logging = enable_file_logging
        self.log_file_path = log_file_path
        
        # Setup file logger
        if enable_file_logging:
            self.file_logger = logging.getLogger('audit_logger')
            handler = logging.FileHandler(log_file_path)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.file_logger.addHandler(handler)
            self.file_logger.setLevel(logging.INFO)
            
    async def log(
        self,
        action_type: AuditActionType,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action_result: str = "success",
        severity: AuditSeverityLevel = AuditSeverityLevel.INFO,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Логирование аудируемого действия
        
        Args:
            action_type: Тип действия
            user_id: ID пользователя
            user_email: Email пользователя
            ip_address: IP адрес
            user_agent: User agent
            resource_type: Тип ресурса
            resource_id: ID ресурса
            action_result: Результат (success, failure, partial)
            severity: Уровень серьезности
            details: Дополнительные детали
            request_id: ID запроса
            session_id: ID сессии
        """
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            action_type=action_type,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action_result=action_result,
            severity=severity,
            details=details or {},
            request_id=request_id,
            session_id=session_id
        )
        
        # Log to file
        if self.enable_file_logging:
            self._log_to_file(entry)
            
        # Log to database
        if self.enable_database_logging and self.db_manager:
            await self._log_to_database(entry)
            
        # Log to system logger
        self._log_to_system(entry)
        
    def _log_to_file(self, entry: AuditLogEntry):
        """Логирование в файл"""
        try:
            log_message = (
                f"[{entry.action_type.value}] "
                f"User: {entry.user_email or entry.user_id or 'anonymous'} "
                f"IP: {entry.ip_address} "
                f"Resource: {entry.resource_type}/{entry.resource_id} "
                f"Result: {entry.action_result} "
                f"Details: {json.dumps(entry.details)}"
            )
            
            if entry.severity == AuditSeverityLevel.CRITICAL:
                self.file_logger.critical(log_message)
            elif entry.severity == AuditSeverityLevel.ERROR:
                self.file_logger.error(log_message)
            elif entry.severity == AuditSeverityLevel.WARNING:
                self.file_logger.warning(log_message)
            else:
                self.file_logger.info(log_message)
                
        except Exception as e:
            logger.error(f"Failed to log to file: {e}")
            
    async def _log_to_database(self, entry: AuditLogEntry):
        """Логирование в базу данных"""
        try:
            query = """
            INSERT INTO audit_logs (
                timestamp, action_type, user_id, user_email, ip_address, 
                user_agent, resource_type, resource_id, action_result, 
                severity, details, request_id, session_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
            )
            """
            
            await self.db_manager.execute(
                query,
                entry.timestamp,
                entry.action_type.value,
                entry.user_id,
                entry.user_email,
                entry.ip_address,
                entry.user_agent,
                entry.resource_type,
                entry.resource_id,
                entry.action_result,
                entry.severity.value,
                json.dumps(entry.details),
                entry.request_id,
                entry.session_id
            )
            
        except Exception as e:
            logger.error(f"Failed to log to database: {e}")
            
    def _log_to_system(self, entry: AuditLogEntry):
        """Логирование в системный logger"""
        log_message = (
            f"AUDIT: [{entry.action_type.value}] "
            f"User: {entry.user_email or entry.user_id or 'anonymous'} "
            f"Result: {entry.action_result}"
        )
        
        if entry.severity == AuditSeverityLevel.CRITICAL:
            logger.critical(log_message)
        elif entry.severity == AuditSeverityLevel.ERROR:
            logger.error(log_message)
        elif entry.severity == AuditSeverityLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
            
    async def search_logs(
        self,
        user_id: Optional[str] = None,
        action_type: Optional[AuditActionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        resource_type: Optional[str] = None,
        severity: Optional[AuditSeverityLevel] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Поиск в audit logs
        
        Returns:
            Список найденных записей
        """
        if not self.db_manager:
            return []
            
        try:
            conditions = []
            params = []
            param_count = 1
            
            if user_id:
                conditions.append(f"user_id = ${param_count}")
                params.append(user_id)
                param_count += 1
                
            if action_type:
                conditions.append(f"action_type = ${param_count}")
                params.append(action_type.value)
                param_count += 1
                
            if start_date:
                conditions.append(f"timestamp >= ${param_count}")
                params.append(start_date)
                param_count += 1
                
            if end_date:
                conditions.append(f"timestamp <= ${param_count}")
                params.append(end_date)
                param_count += 1
                
            if resource_type:
                conditions.append(f"resource_type = ${param_count}")
                params.append(resource_type)
                param_count += 1
                
            if severity:
                conditions.append(f"severity = ${param_count}")
                params.append(severity.value)
                param_count += 1
                
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f"""
            SELECT * FROM audit_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ${param_count}
            """
            params.append(limit)
            
            rows = await self.db_manager.fetch(query, *params)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to search audit logs: {e}")
            return []
            
    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Получение активности пользователя
        
        Returns:
            Статистика активности
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            query = """
            SELECT 
                action_type,
                COUNT(*) as count,
                MAX(timestamp) as last_action
            FROM audit_logs
            WHERE user_id = $1 AND timestamp >= $2
            GROUP BY action_type
            ORDER BY count DESC
            """
            
            rows = await self.db_manager.fetch(query, user_id, start_date)
            
            return {
                "user_id": user_id,
                "period_days": days,
                "total_actions": sum(row['count'] for row in rows),
                "actions_by_type": [dict(row) for row in rows]
            }
            
        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return {}


# Helper functions
async def log_user_login(
    audit_logger: AuditLogger,
    user_id: str,
    user_email: str,
    ip_address: str,
    success: bool = True,
    details: Optional[Dict] = None
):
    """Логирование попытки входа"""
    await audit_logger.log(
        action_type=AuditActionType.LOGIN if success else AuditActionType.LOGIN_FAILED,
        user_id=user_id if success else None,
        user_email=user_email,
        ip_address=ip_address,
        action_result="success" if success else "failure",
        severity=AuditSeverityLevel.INFO if success else AuditSeverityLevel.WARNING,
        details=details or {}
    )


async def log_document_access(
    audit_logger: AuditLogger,
    user_id: str,
    document_id: str,
    action: str,  # viewed, updated, deleted
    ip_address: Optional[str] = None
):
    """Логирование доступа к документу"""
    action_map = {
        'viewed': AuditActionType.DOCUMENT_VIEWED,
        'updated': AuditActionType.DOCUMENT_UPDATED,
        'deleted': AuditActionType.DOCUMENT_DELETED
    }
    
    await audit_logger.log(
        action_type=action_map.get(action, AuditActionType.DOCUMENT_VIEWED),
        user_id=user_id,
        ip_address=ip_address,
        resource_type="document",
        resource_id=document_id,
        severity=AuditSeverityLevel.INFO
    )


async def log_security_event(
    audit_logger: AuditLogger,
    event_type: str,
    user_id: Optional[str],
    ip_address: str,
    details: Dict[str, Any]
):
    """Логирование события безопасности"""
    action_map = {
        'brute_force': AuditActionType.BRUTE_FORCE_DETECTED,
        'sql_injection': AuditActionType.SQL_INJECTION_ATTEMPT,
        'suspicious': AuditActionType.SUSPICIOUS_ACTIVITY
    }
    
    await audit_logger.log(
        action_type=action_map.get(event_type, AuditActionType.SECURITY_ALERT),
        user_id=user_id,
        ip_address=ip_address,
        action_result="detected",
        severity=AuditSeverityLevel.CRITICAL,
        details=details
    )
