"""
Slack Integration
Send notifications to Slack channels
"""

import logging
from typing import Optional, Dict, List
import asyncio

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class SlackIntegration:
    """
    Slack integration for notifications
    
    Features:
    - Send messages to channels
    - Rich message formatting
    - Attachment support
    - Interactive buttons
    - Thread replies
    
    Usage:
        slack = SlackIntegration(webhook_url="...")
        
        await slack.send_message(
            channel="#general",
            text="Document created",
            blocks=[...]
        )
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.slack_webhook_url
    
    async def send_message(
        self,
        text: str,
        channel: Optional[str] = None,
        username: Optional[str] = None,
        icon_emoji: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """
        Send message to Slack
        
        Args:
            text: Message text (fallback)
            channel: Channel name (e.g., "#general")
            username: Bot username
            icon_emoji: Bot emoji (e.g., ":robot_face:")
            blocks: Block Kit blocks
            attachments: Legacy attachments
        
        Returns:
            True if sent successfully
        """
        
        if not self.webhook_url:
            logger.error("Slack webhook URL not configured")
            return False
        
        payload = {
            "text": text
        }
        
        if channel:
            payload["channel"] = channel
        
        if username:
            payload["username"] = username
        
        if icon_emoji:
            payload["icon_emoji"] = icon_emoji
        
        if blocks:
            payload["blocks"] = blocks
        
        if attachments:
            payload["attachments"] = attachments
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Sent Slack message: {text[:50]}")
                    return True
                else:
                    logger.error(
                        f"Slack error {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False
    
    async def send_document_notification(
        self,
        document_title: str,
        document_id: str,
        action: str = "created",
        user: str = "Unknown"
    ):
        """
        Send document notification
        
        Args:
            document_title: Document title
            document_id: Document ID
            action: Action performed (created, updated, deleted)
            user: User who performed action
        """
        
        color = {
            "created": "#36a64f",  # Green
            "updated": "#ff9900",  # Orange
            "deleted": "#ff0000"   # Red
        }.get(action, "#808080")
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Document {action}*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Title:*\n{document_title}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*By:*\n{user}"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Document"
                        },
                        "url": f"{settings.app_url}/documents/{document_id}"
                    }
                ]
            }
        ]
        
        await self.send_message(
            text=f"Document {action}: {document_title}",
            blocks=blocks
        )
    
    async def send_search_alert(
        self,
        query: str,
        results_count: int,
        threshold: int = 0
    ):
        """
        Send search alert (e.g., zero results)
        
        Args:
            query: Search query
            results_count: Number of results
            threshold: Alert threshold (0 = zero results)
        """
        
        if results_count > threshold:
            return  # No alert needed
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⚠️ *Search Alert: Zero Results*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Query:*\n{query}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Results:*\n{results_count}"
                    }
                ]
            }
        ]
        
        await self.send_message(
            text=f"Zero results for query: {query}",
            blocks=blocks
        )
    
    async def send_error_notification(
        self,
        error_type: str,
        error_message: str,
        severity: str = "error"
    ):
        """
        Send error notification
        
        Args:
            error_type: Error type/category
            error_message: Error details
            severity: Severity level (info, warning, error, critical)
        """
        
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }.get(severity, "❌")
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *{severity.upper()}: {error_type}*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{error_message}```"
                }
            }
        ]
        
        await self.send_message(
            text=f"{severity.upper()}: {error_type}",
            blocks=blocks
        )


# Global Slack integration
slack_integration = SlackIntegration()