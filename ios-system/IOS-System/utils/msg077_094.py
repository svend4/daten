"""
Email Integration
Send emails via SMTP
"""

import logging
from typing import Optional, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from ..config import settings

logger = logging.getLogger(__name__)


class EmailIntegration:
    """
    Email integration via SMTP
    
    Features:
    - HTML and plain text emails
    - Attachments
    - Templates
    - Batch sending
    
    Usage:
        email = EmailIntegration()
        
        await email.send(
            to="user@example.com",
            subject="Welcome",
            html="<h1>Welcome!</h1>"
        )
    """
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ):
        self.smtp_host = smtp_host or settings.smtp_host
        self.smtp_port = smtp_port or settings.smtp_port
        self.smtp_user = smtp_user or settings.smtp_user
        self.smtp_password = smtp_password or settings.smtp_password
        self.from_email = from_email or settings.email_from
        self.from_name = from_name or "IOS System"
    
    async def send(
        self,
        to: str,
        subject: str,
        text: Optional[str] = None,
        html: Optional[str] = None,
        attachments: Optional[List[tuple]] = None
    ) -> bool:
        """
        Send email
        
        Args:
            to: Recipient email
            subject: Email subject
            text: Plain text content
            html: HTML content
            attachments: List of (filename, content) tuples
        
        Returns:
            True if sent successfully
        """
        
        if not self.smtp_host:
            logger.error("SMTP not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to
            msg['Subject'] = subject
            
            # Add text/html parts
            if text:
                msg.attach(MIMEText(text, 'plain'))
            
            if html:
                msg.attach(MIMEText(html, 'html'))
            
            # Add attachments
            if attachments:
                for filename, content in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={filename}'
                    )
                    msg.attach(part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                
                server.send_message(msg)
            
            logger.info(f"Sent email to {to}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_welcome_email(self, user_email: str, username: str):
        """Send welcome email to new user"""
        
        html = f"""
        <html>
          <body>
            <h1>Welcome to IOS System!</h1>
            <p>Hi {username},</p>
            <p>Thank you for joining IOS System. We're excited to have you on board!</p>
            <p>
              <a href="{settings.app_url}/login">Login to your account</a>
            </p>
            <p>Best regards,<br>The IOS Team</p>
          </body>
        </html>
        """
        
        await self.send(
            to=user_email,
            subject="Welcome to IOS System",
            html=html
        )
    
    async def send_document_notification(
        self,
        user_email: str,
        document_title: str,
        document_id: str,
        action: str = "created"
    ):
        """Send document notification email"""
        
        html = f"""
        <html>
          <body>
            <h2>Document {action.title()}</h2>
            <p>The document "{document_title}" has been {action}.</p>
            <p>
              <a href="{settings.app_url}/documents/{document_id}">
                View Document
              </a>
            </p>
          </body>
        </html>
        """
        
        await self.send(
            to=user_email,
            subject=f"Document {action.title()}: {document_title}",
            html=html
        )
    
    async def send_password_reset(
        self,
        user_email: str,
        reset_token: str
    ):
        """Send password reset email"""
        
        reset_url = f"{settings.app_url}/reset-password?token={reset_token}"
        
        html = f"""
        <html>
          <body>
            <h2>Password Reset Request</h2>
            <p>Click the link below to reset your password:</p>
            <p>
              <a href="{reset_url}">Reset Password</a>
            </p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
          </body>
        </html>
        """
        
        await self.send(
            to=user_email,
            subject="Password Reset Request",
            html=html
        )


# Global email integration
email_integration = EmailIntegration()