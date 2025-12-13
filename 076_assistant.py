Отлично! Продолжаем с Day 131-132: External Integrations & SDK. Это будет включать:

1. SDK для разных языков (Python, JavaScript, TypeScript)
2. Интеграции с внешними сервисами (Slack, Email, Cloud Storage)
3. OAuth провайдеры
4. API клиенты
5. Integration middleware
6. Документация

Начнем!# 🔌 DAY 131-132: EXTERNAL INTEGRATIONS & SDK

---

## 📊 ЦЕЛЬ

Создание SDK и интеграций для внешних сервисов:
- **Python SDK** - официальный SDK для Python
- **JavaScript/TypeScript SDK** - SDK для Node.js и браузера
- **External Integrations** - Slack, Email, Cloud Storage
- **OAuth Providers** - Google, Microsoft, GitHub
- **API Client Generator** - автоматическая генерация клиентов
- **Integration Templates** - готовые шаблоны интеграций

---

## ФАЙЛ 21: `sdk/python/ios_sdk/__init__.py`

```python
"""
IOS System Python SDK
Official Python client for IOS API

Installation:
    pip install ios-sdk

Usage:
    from ios_sdk import IOSClient
    
    client = IOSClient(api_key="your_key")
    
    # Create document
    doc = client.documents.create(
        title="My Document",
        content="Content here"
    )
    
    # Search
    results = client.search.query("personal budget")
"""

from .client import IOSClient
from .exceptions import (
    IOSError,
    AuthenticationError,
    RateLimitError,
    NotFoundError
)
from .models import Document, SearchResult, User

__version__ = "1.0.0"

__all__ = [
    'IOSClient',
    'IOSError',
    'AuthenticationError',
    'RateLimitError',
    'NotFoundError',
    'Document',
    'SearchResult',
    'User',
]
```

---

## ФАЙЛ 22: `sdk/python/ios_sdk/client.py`

```python
"""
IOS SDK Client
"""

import requests
from typing import Optional, Dict, List, Any
from datetime import datetime

from .resources.documents import DocumentsResource
from .resources.search import SearchResource
from .resources.webhooks import WebhooksResource
from .resources.users import UsersResource
from .exceptions import (
    IOSError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ServerError
)


class IOSClient:
    """
    IOS System API Client
    
    Args:
        api_key: API key for authentication
        base_url: API base URL (default: https://api.ios-system.com)
        timeout: Request timeout in seconds
        
    Example:
        >>> client = IOSClient(api_key="sk_test_...")
        >>> docs = client.documents.list()
        >>> for doc in docs:
        ...     print(doc.title)
    """
    
    DEFAULT_BASE_URL = "https://api.ios-system.com"
    DEFAULT_TIMEOUT = 30
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT
    ):
        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"ios-sdk-python/1.0.0"
        })
        
        # Initialize resources
        self.documents = DocumentsResource(self)
        self.search = SearchResource(self)
        self.webhooks = WebhooksResource(self)
        self.users = UsersResource(self)
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        """
        Make API request
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON body
            
        Returns:
            Response data
            
        Raises:
            IOSError: On API errors
        """
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout,
                **kwargs
            )
            
            # Check for errors
            self._handle_response_errors(response)
            
            # Return JSON data
            return response.json() if response.content else {}
            
        except requests.exceptions.Timeout:
            raise IOSError("Request timeout")
        
        except requests.exceptions.ConnectionError:
            raise IOSError("Connection error")
        
        except requests.exceptions.RequestException as e:
            raise IOSError(f"Request failed: {str(e)}")
    
    def _handle_response_errors(self, response: requests.Response):
        """Handle HTTP errors"""
        
        if response.status_code >= 200 and response.status_code < 300:
            return  # Success
        
        # Parse error
        try:
            error_data = response.json()
            error_message = error_data.get("detail", "Unknown error")
        except:
            error_message = response.text or "Unknown error"
        
        # Map status codes to exceptions
        if response.status_code == 401:
            raise AuthenticationError(error_message)
        
        elif response.status_code == 404:
            raise NotFoundError(error_message)
        
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(error_message, retry_after=retry_after)
        
        elif response.status_code >= 500:
            raise ServerError(error_message)
        
        else:
            raise IOSError(f"HTTP {response.status_code}: {error_message}")
    
    def get(self, endpoint: str, **kwargs) -> Dict:
        """GET request"""
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> Dict:
        """POST request"""
        return self.request("POST", endpoint, **kwargs)
    
    def patch(self, endpoint: str, **kwargs) -> Dict:
        """PATCH request"""
        return self.request("PATCH", endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict:
        """DELETE request"""
        return self.request("DELETE", endpoint, **kwargs)
```

---

## ФАЙЛ 23: `sdk/python/ios_sdk/resources/documents.py`

```python
"""
Documents Resource
"""

from typing import List, Optional, Dict, Any
from ..models import Document


class DocumentsResource:
    """
    Documents API resource
    
    Example:
        >>> docs = client.documents.list(limit=10)
        >>> doc = client.documents.create(
        ...     title="My Doc",
        ...     content="Content"
        ... )
        >>> doc = client.documents.get("doc_123")
        >>> client.documents.update("doc_123", title="Updated")
        >>> client.documents.delete("doc_123")
    """
    
    def __init__(self, client):
        self.client = client
    
    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        domain_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Document]:
        """
        List documents
        
        Args:
            limit: Max documents to return
            offset: Pagination offset
            domain_id: Filter by domain
            search: Search query
            
        Returns:
            List of documents
        """
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if domain_id:
            params["domain_id"] = domain_id
        
        if search:
            params["search"] = search
        
        response = self.client.get("/api/documents", params=params)
        
        return [
            Document.from_dict(doc)
            for doc in response.get("documents", [])
        ]
    
    def get(self, document_id: str) -> Document:
        """
        Get document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            Document
        """
        
        response = self.client.get(f"/api/documents/{document_id}")
        return Document.from_dict(response)
    
    def create(
        self,
        title: str,
        content: str,
        domain_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Document:
        """
        Create document
        
        Args:
            title: Document title
            content: Document content
            domain_id: Domain ID
            metadata: Additional metadata
            
        Returns:
            Created document
        """
        
        data = {
            "title": title,
            "content": content
        }
        
        if domain_id:
            data["domain_id"] = domain_id
        
        if metadata:
            data["metadata"] = metadata
        
        response = self.client.post("/api/documents", json=data)
        return Document.from_dict(response)
    
    def update(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Document:
        """
        Update document
        
        Args:
            document_id: Document ID
            title: New title
            content: New content
            metadata: New metadata
            
        Returns:
            Updated document
        """
        
        data = {}
        
        if title is not None:
            data["title"] = title
        
        if content is not None:
            data["content"] = content
        
        if metadata is not None:
            data["metadata"] = metadata
        
        response = self.client.patch(
            f"/api/documents/{document_id}",
            json=data
        )
        
        return Document.from_dict(response)
    
    def delete(self, document_id: str) -> bool:
        """
        Delete document
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted
        """
        
        self.client.delete(f"/api/documents/{document_id}")
        return True
```

---

## ФАЙЛ 24: `sdk/python/ios_sdk/resources/search.py`

```python
"""
Search Resource
"""

from typing import List, Optional, Dict
from ..models import SearchResult


class SearchResource:
    """
    Search API resource
    
    Example:
        >>> # Basic search
        >>> results = client.search.query("personal budget")
        >>> for result in results:
        ...     print(result.title, result.score)
        
        >>> # Neural search
        >>> results = client.search.neural(
        ...     query="Persönliches Budget",
        ...     limit=10
        ... )
        
        >>> # Semantic search
        >>> results = client.search.semantic(
        ...     query="budget for disabled people",
        ...     threshold=0.8
        ... )
    """
    
    def __init__(self, client):
        self.client = client
    
    def query(
        self,
        query: str,
        limit: int = 10,
        domain_id: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Basic search
        
        Args:
            query: Search query
            limit: Max results
            domain_id: Filter by domain
            
        Returns:
            Search results
        """
        
        params = {
            "query": query,
            "limit": limit
        }
        
        if domain_id:
            params["domain_id"] = domain_id
        
        response = self.client.get("/api/search", params=params)
        
        return [
            SearchResult.from_dict(result)
            for result in response.get("results", [])
        ]
    
    def neural(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[SearchResult]:
        """
        Neural search (semantic + keyword hybrid)
        
        Args:
            query: Search query
            limit: Max results
            score_threshold: Minimum score
            
        Returns:
            Search results
        """
        
        params = {
            "query": query,
            "limit": limit,
            "score_threshold": score_threshold
        }
        
        response = self.client.get("/api/search/neural", params=params)
        
        return [
            SearchResult.from_dict(result)
            for result in response.get("results", [])
        ]
    
    def semantic(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.8
    ) -> List[SearchResult]:
        """
        Semantic search (embeddings only)
        
        Args:
            query: Search query
            limit: Max results
            threshold: Similarity threshold
            
        Returns:
            Search results
        """
        
        params = {
            "query": query,
            "limit": limit,
            "threshold": threshold
        }
        
        response = self.client.get("/api/semantic/search", params=params)
        
        return [
            SearchResult.from_dict(result)
            for result in response.get("results", [])
        ]
```

---

## ФАЙЛ 25: `sdk/python/ios_sdk/models.py`

```python
"""
SDK Models
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Document:
    """Document model"""
    
    id: str
    title: str
    content: str
    domain_id: Optional[str] = None
    metadata: Optional[Dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Document":
        """Create from API response"""
        
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            domain_id=data.get("domain_id"),
            metadata=data.get("metadata"),
            created_at=cls._parse_datetime(data.get("created_at")),
            updated_at=cls._parse_datetime(data.get("updated_at"))
        )
    
    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string"""
        
        if not dt_str:
            return None
        
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except:
            return None


@dataclass
class SearchResult:
    """Search result model"""
    
    document_id: str
    title: str
    content: str
    score: float
    highlight: Optional[str] = None
    metadata: Optional[Dict] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SearchResult":
        """Create from API response"""
        
        return cls(
            document_id=data["document_id"],
            title=data["title"],
            content=data.get("content", ""),
            score=data["score"],
            highlight=data.get("highlight"),
            metadata=data.get("metadata")
        )


@dataclass
class User:
    """User model"""
    
    id: str
    email: str
    username: str
    is_active: bool
    roles: List[str]
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "User":
        """Create from API response"""
        
        return cls(
            id=data["id"],
            email=data["email"],
            username=data["username"],
            is_active=data.get("is_active", True),
            roles=data.get("roles", []),
            created_at=Document._parse_datetime(data.get("created_at"))
        )


@dataclass
class Webhook:
    """Webhook model"""
    
    id: str
    name: str
    url: str
    event_types: List[str]
    is_active: bool
    secret: Optional[str] = None
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Webhook":
        """Create from API response"""
        
        return cls(
            id=data["id"],
            name=data["name"],
            url=data["url"],
            event_types=data.get("event_types", []),
            is_active=data.get("is_active", True),
            secret=data.get("secret"),
            created_at=Document._parse_datetime(data.get("created_at"))
        )
```

---

## ФАЙЛ 26: `sdk/python/ios_sdk/exceptions.py`

```python
"""
SDK Exceptions
"""

from typing import Optional


class IOSError(Exception):
    """Base exception for IOS SDK"""
    pass


class AuthenticationError(IOSError):
    """Authentication failed"""
    pass


class RateLimitError(IOSError):
    """Rate limit exceeded"""
    
    def __init__(self, message: str, retry_after: Optional[str] = None):
        super().__init__(message)
        self.retry_after = retry_after


class NotFoundError(IOSError):
    """Resource not found"""
    pass


class ValidationError(IOSError):
    """Validation error"""
    pass


class ServerError(IOSError):
    """Server error"""
    pass
```

---

## ФАЙЛ 27: `sdk/python/setup.py`

```python
"""
IOS SDK Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ios-sdk",
    version="1.0.0",
    author="IOS System",
    author_email="support@ios-system.com",
    description="Official Python SDK for IOS System API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ios-system/ios-sdk-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ]
    },
)
```

---

## ФАЙЛ 28: `sdk/python/README.md`

```markdown
# IOS System Python SDK

Official Python client for IOS System API.

## Installation

```bash
pip install ios-sdk
```

## Quick Start

```python
from ios_sdk import IOSClient

# Initialize client
client = IOSClient(api_key="sk_test_...")

# Create document
doc = client.documents.create(
    title="My Document",
    content="Document content here"
)

print(f"Created document: {doc.id}")

# Search documents
results = client.search.query("personal budget")

for result in results:
    print(f"{result.title} (score: {result.score})")

# Neural search
results = client.search.neural(
    query="Persönliches Budget für Menschen mit Behinderung",
    limit=10
)
```

## Features

- **Documents** - Create, read, update, delete
- **Search** - Basic, neural, semantic search
- **Webhooks** - Manage webhook subscriptions
- **Users** - User management
- **Type hints** - Full typing support
- **Error handling** - Comprehensive exceptions

## Usage

### Documents

```python
# List documents
docs = client.documents.list(limit=50)

# Get document
doc = client.documents.get("doc_123")

# Update document
doc = client.documents.update(
    "doc_123",
    title="Updated Title"
)

# Delete document
client.documents.delete("doc_123")
```

### Search

```python
# Basic search
results = client.search.query("budget")

# Neural search (hybrid semantic + keyword)
results = client.search.neural(
    query="Persönliches Budget",
    score_threshold=0.7
)

# Semantic search (embeddings only)
results = client.search.semantic(
    query="support for disabled people",
    threshold=0.8
)
```

### Webhooks

```python
# Create webhook
webhook = client.webhooks.create(
    name="My Webhook",
    url="https://example.com/webhook",
    event_types=["document.created", "document.updated"]
)

# List webhooks
webhooks = client.webhooks.list()

# Delete webhook
client.webhooks.delete("wh_123")
```

## Error Handling

```python
from ios_sdk import (
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    IOSError
)

try:
    doc = client.documents.get("doc_123")
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Document not found")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except IOSError as e:
    print(f"API error: {e}")
```

## Configuration

```python
# Custom base URL
client = IOSClient(
    api_key="sk_test_...",
    base_url="https://custom.api.com"
)

# Custom timeout
client = IOSClient(
    api_key="sk_test_...",
    timeout=60  # seconds
)
```

## Advanced

### Async Support (Coming Soon)

```python
from ios_sdk import AsyncIOSClient

async def main():
    client = AsyncIOSClient(api_key="...")
    doc = await client.documents.create(...)
```

### Pagination

```python
# Manual pagination
offset = 0
limit = 50

while True:
    docs = client.documents.list(offset=offset, limit=limit)
    
    if not docs:
        break
    
    for doc in docs:
        print(doc.title)
    
    offset += limit
```

## Requirements

- Python 3.8+
- requests

## License

MIT

## Support

- Documentation: https://docs.ios-system.com
- GitHub: https://github.com/ios-system/ios-sdk-python
- Email: support@ios-system.com
```

---

**Продолжение следует...**

Создано:
- ✅ Python SDK (client, resources, models)
- ✅ Documents Resource
- ✅ Search Resource
- ✅ Exception handling
- ✅ Setup.py and README

**Следующие файлы:**
- JavaScript/TypeScript SDK
- External Integrations (Slack, Email)
- OAuth Providers
- Integration documentation
- Week summary

**Готовы продолжить?**