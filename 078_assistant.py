Продолжаем Day 131-132 с созданием JavaScript/TypeScript SDK, внешних интеграций и OAuth провайдеров.

Следующие файлы:
- JavaScript/TypeScript SDK
- Slack Integration
- Email Integration
- OAuth Providers
- Integration Templates
- Documentation
- Week Summary# 🔌 DAY 131-132: EXTERNAL INTEGRATIONS & SDK (ПРОДОЛЖЕНИЕ)

---

## ФАЙЛ 29: `sdk/javascript/src/index.ts`

```typescript
/**
 * IOS System JavaScript/TypeScript SDK
 * Official client for IOS API
 * 
 * Installation:
 *   npm install @ios-system/sdk
 * 
 * Usage:
 *   import { IOSClient } from '@ios-system/sdk';
 *   
 *   const client = new IOSClient({ apiKey: 'sk_test_...' });
 *   
 *   const doc = await client.documents.create({
 *     title: 'My Document',
 *     content: 'Content here'
 *   });
 */

export { IOSClient } from './client';
export { IOSError, AuthenticationError, RateLimitError, NotFoundError } from './errors';
export type {
  Document,
  SearchResult,
  User,
  Webhook,
  CreateDocumentRequest,
  UpdateDocumentRequest,
  SearchOptions,
  WebhookOptions
} from './types';
```

---

## ФАЙЛ 30: `sdk/javascript/src/client.ts`

```typescript
/**
 * IOS Client
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { DocumentsResource } from './resources/documents';
import { SearchResource } from './resources/search';
import { WebhooksResource } from './resources/webhooks';
import { UsersResource } from './resources/users';
import {
  IOSError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ServerError
} from './errors';

export interface IOSClientOptions {
  apiKey: string;
  baseURL?: string;
  timeout?: number;
}

export class IOSClient {
  private axios: AxiosInstance;
  
  public documents: DocumentsResource;
  public search: SearchResource;
  public webhooks: WebhooksResource;
  public users: UsersResource;
  
  constructor(options: IOSClientOptions) {
    const {
      apiKey,
      baseURL = 'https://api.ios-system.com',
      timeout = 30000
    } = options;
    
    // Initialize axios
    this.axios = axios.create({
      baseURL,
      timeout,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': 'ios-sdk-js/1.0.0'
      }
    });
    
    // Add error interceptor
    this.axios.interceptors.response.use(
      response => response,
      error => this.handleError(error)
    );
    
    // Initialize resources
    this.documents = new DocumentsResource(this.axios);
    this.search = new SearchResource(this.axios);
    this.webhooks = new WebhooksResource(this.axios);
    this.users = new UsersResource(this.axios);
  }
  
  private handleError(error: AxiosError): never {
    if (!error.response) {
      throw new IOSError('Network error');
    }
    
    const { status, data } = error.response;
    const message = (data as any)?.detail || 'Unknown error';
    
    switch (status) {
      case 401:
        throw new AuthenticationError(message);
      
      case 404:
        throw new NotFoundError(message);
      
      case 429:
        const retryAfter = error.response.headers['retry-after'];
        throw new RateLimitError(message, retryAfter);
      
      case 500:
      case 502:
      case 503:
        throw new ServerError(message);
      
      default:
        throw new IOSError(`HTTP ${status}: ${message}`);
    }
  }
}
```

---

## ФАЙЛ 31: `sdk/javascript/src/resources/documents.ts`

```typescript
/**
 * Documents Resource
 */

import { AxiosInstance } from 'axios';
import {
  Document,
  CreateDocumentRequest,
  UpdateDocumentRequest,
  ListDocumentsOptions
} from '../types';

export class DocumentsResource {
  constructor(private axios: AxiosInstance) {}
  
  /**
   * List documents
   */
  async list(options?: ListDocumentsOptions): Promise<Document[]> {
    const { data } = await this.axios.get('/api/documents', {
      params: options
    });
    
    return data.documents;
  }
  
  /**
   * Get document by ID
   */
  async get(documentId: string): Promise<Document> {
    const { data } = await this.axios.get(`/api/documents/${documentId}`);
    return data;
  }
  
  /**
   * Create document
   */
  async create(request: CreateDocumentRequest): Promise<Document> {
    const { data } = await this.axios.post('/api/documents', request);
    return data;
  }
  
  /**
   * Update document
   */
  async update(
    documentId: string,
    request: UpdateDocumentRequest
  ): Promise<Document> {
    const { data } = await this.axios.patch(
      `/api/documents/${documentId}`,
      request
    );
    return data;
  }
  
  /**
   * Delete document
   */
  async delete(documentId: string): Promise<void> {
    await this.axios.delete(`/api/documents/${documentId}`);
  }
}
```

---

## ФАЙЛ 32: `sdk/javascript/src/resources/search.ts`

```typescript
/**
 * Search Resource
 */

import { AxiosInstance } from 'axios';
import { SearchResult, SearchOptions } from '../types';

export class SearchResource {
  constructor(private axios: AxiosInstance) {}
  
  /**
   * Basic search
   */
  async query(
    query: string,
    options?: SearchOptions
  ): Promise<SearchResult[]> {
    const { data } = await this.axios.get('/api/search', {
      params: { query, ...options }
    });
    
    return data.results;
  }
  
  /**
   * Neural search (hybrid)
   */
  async neural(
    query: string,
    options?: SearchOptions
  ): Promise<SearchResult[]> {
    const { data } = await this.axios.get('/api/search/neural', {
      params: { query, ...options }
    });
    
    return data.results;
  }
  
  /**
   * Semantic search (embeddings)
   */
  async semantic(
    query: string,
    options?: SearchOptions
  ): Promise<SearchResult[]> {
    const { data } = await this.axios.get('/api/semantic/search', {
      params: { query, ...options }
    });
    
    return data.results;
  }
}
```

---

## ФАЙЛ 33: `sdk/javascript/src/types.ts`

```typescript
/**
 * SDK Types
 */

export interface Document {
  id: string;
  title: string;
  content: string;
  domain_id?: string;
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface CreateDocumentRequest {
  title: string;
  content: string;
  domain_id?: string;
  metadata?: Record<string, any>;
}

export interface UpdateDocumentRequest {
  title?: string;
  content?: string;
  metadata?: Record<string, any>;
}

export interface ListDocumentsOptions {
  limit?: number;
  offset?: number;
  domain_id?: string;
  search?: string;
}

export interface SearchResult {
  document_id: string;
  title: string;
  content: string;
  score: number;
  highlight?: string;
  metadata?: Record<string, any>;
}

export interface SearchOptions {
  limit?: number;
  domain_id?: string;
  score_threshold?: number;
  threshold?: number;
}

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  roles: string[];
  created_at?: string;
}

export interface Webhook {
  id: string;
  name: string;
  url: string;
  event_types: string[];
  is_active: boolean;
  secret?: string;
  created_at?: string;
}

export interface WebhookOptions {
  name: string;
  url: string;
  event_types: string[];
  secret?: string;
}
```

---

## ФАЙЛ 34: `sdk/javascript/src/errors.ts`

```typescript
/**
 * SDK Errors
 */

export class IOSError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'IOSError';
  }
}

export class AuthenticationError extends IOSError {
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

export class RateLimitError extends IOSError {
  retryAfter?: string;
  
  constructor(message: string, retryAfter?: string) {
    super(message);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

export class NotFoundError extends IOSError {
  constructor(message: string) {
    super(message);
    this.name = 'NotFoundError';
  }
}

export class ServerError extends IOSError {
  constructor(message: string) {
    super(message);
    this.name = 'ServerError';
  }
}
```

---

## ФАЙЛ 35: `sdk/javascript/package.json`

```json
{
  "name": "@ios-system/sdk",
  "version": "1.0.0",
  "description": "Official JavaScript/TypeScript SDK for IOS System API",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "lint": "eslint src/**/*.ts",
    "prepublishOnly": "npm run build"
  },
  "keywords": [
    "ios-system",
    "api",
    "sdk",
    "client"
  ],
  "author": "IOS System",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/ios-system/ios-sdk-js"
  },
  "dependencies": {
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "jest": "^29.0.0",
    "@types/jest": "^29.0.0",
    "eslint": "^8.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0"
  }
}
```

---

## ФАЙЛ 36: `ios_core/integrations/__init__.py`

```python
"""
External Integrations Module
"""

from .slack import SlackIntegration, slack_integration
from .email import EmailIntegration, email_integration
from .oauth import OAuthProvider, GoogleOAuth, MicrosoftOAuth, GitHubOAuth

__all__ = [
    'SlackIntegration',
    'slack_integration',
    'EmailIntegration',
    'email_integration',
    'OAuthProvider',
    'GoogleOAuth',
    'MicrosoftOAuth',
    'GitHubOAuth',
]
```

---

## ФАЙЛ 37: `ios_core/integrations/slack.py`

```python
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
```

---

## ФАЙЛ 38: `ios_core/integrations/email.py`

```python
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
```

---

**Продолжение следует...**

Создано:
- ✅ JavaScript/TypeScript SDK (complete)
- ✅ Slack Integration
- ✅ Email Integration
- ✅ Package.json configs

**Следующие файлы:**
- OAuth Providers (Google, Microsoft, GitHub)
- Integration examples
- Tests
- Documentation
- Week 21-22 Summary

**Готовы продолжить?**