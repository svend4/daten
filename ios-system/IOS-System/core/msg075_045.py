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