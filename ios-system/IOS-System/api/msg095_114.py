"""
CDN Integration for Static Assets
Supports CloudFlare, AWS CloudFront, and generic CDN providers
"""

import logging
import hashlib
from typing import Optional, Dict
from urllib.parse import urljoin

import boto3
from botocore.exceptions import ClientError

from ..config import settings

logger = logging.getLogger(__name__)


class CDNProvider:
    """Base CDN provider interface"""
    
    def purge_cache(self, urls: list[str]) -> bool:
        """Purge CDN cache for specific URLs"""
        raise NotImplementedError
    
    def get_url(self, path: str) -> str:
        """Get CDN URL for an asset"""
        raise NotImplementedError


class CloudFlareCDN(CDNProvider):
    """
    CloudFlare CDN integration
    
    Features:
    - Cache purging
    - URL generation
    - Zone management
    """
    
    def __init__(
        self,
        zone_id: str,
        api_token: str,
        cdn_domain: str
    ):
        self.zone_id = zone_id
        self.api_token = api_token
        self.cdn_domain = cdn_domain
        self.api_base = "https://api.cloudflare.com/client/v4"
    
    def purge_cache(self, urls: list[str]) -> bool:
        """Purge CloudFlare cache for URLs"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # CloudFlare allows up to 30 URLs per request
        for i in range(0, len(urls), 30):
            batch = urls[i:i+30]
            
            payload = {"files": batch}
            
            try:
                response = requests.post(
                    f"{self.api_base}/zones/{self.zone_id}/purge_cache",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"CloudFlare purge failed: {response.text}")
                    return False
                
                logger.info(f"Purged {len(batch)} URLs from CloudFlare")
                
            except Exception as e:
                logger.error(f"CloudFlare API error: {e}")
                return False
        
        return True
    
    def purge_all(self) -> bool:
        """Purge entire CloudFlare cache"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"purge_everything": True}
        
        try:
            response = requests.post(
                f"{self.api_base}/zones/{self.zone_id}/purge_cache",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                logger.info("Purged all CloudFlare cache")
                return True
            else:
                logger.error(f"CloudFlare purge all failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"CloudFlare API error: {e}")
            return False
    
    def get_url(self, path: str) -> str:
        """Get CloudFlare CDN URL"""
        return urljoin(f"https://{self.cdn_domain}", path)


class CloudFrontCDN(CDNProvider):
    """
    AWS CloudFront CDN integration
    """
    
    def __init__(
        self,
        distribution_id: str,
        cdn_domain: str,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None
    ):
        self.distribution_id = distribution_id
        self.cdn_domain = cdn_domain
        
        # Initialize CloudFront client
        self.client = boto3.client(
            'cloudfront',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
    
    def purge_cache(self, paths: list[str]) -> bool:
        """Create CloudFront invalidation"""
        import time
        
        # CloudFront expects paths starting with /
        paths = [p if p.startswith('/') else f'/{p}' for p in paths]
        
        try:
            # Create invalidation
            response = self.client.create_invalidation(
                DistributionId=self.distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': str(time.time())
                }
            )
            
            invalidation_id = response['Invalidation']['Id']
            logger.info(f"CloudFront invalidation created: {invalidation_id}")
            
            return True
            
        except ClientError as e:
            logger.error(f"CloudFront invalidation failed: {e}")
            return False
    
    def purge_all(self) -> bool:
        """Invalidate all CloudFront cache"""
        return self.purge_cache(['/*'])
    
    def get_url(self, path: str) -> str:
        """Get CloudFront CDN URL"""
        return urljoin(f"https://{self.cdn_domain}", path)


class CDNManager:
    """
    Manages CDN operations across multiple providers
    
    Features:
    - Automatic asset URL generation
    - Cache purging
    - Asset versioning
    - Multiple CDN support
    """
    
    def __init__(self, provider: CDNProvider):
        self.provider = provider
        self.enabled = settings.cdn_enabled
    
    def get_asset_url(
        self,
        path: str,
        version: Optional[str] = None
    ) -> str:
        """
        Get CDN URL for an asset
        
        Args:
            path: Asset path (e.g., 'css/style.css')
            version: Optional version/hash for cache busting
        
        Returns:
            Full CDN URL
        """
        if not self.enabled:
            # Return local URL if CDN disabled
            return urljoin(settings.app_url, path)
        
        # Add version query parameter for cache busting
        if version:
            path = f"{path}?v={version}"
        
        return self.provider.get_url(path)
    
    def get_versioned_url(self, path: str, content: bytes) -> str:
        """
        Get CDN URL with content-based versioning
        
        Uses MD5 hash of content as version
        """
        version = hashlib.md5(content).hexdigest()[:8]
        return self.get_asset_url(path, version=version)
    
    def purge_assets(self, paths: list[str]) -> bool:
        """Purge specific assets from CDN cache"""
        if not self.enabled:
            logger.warning("CDN disabled, skipping purge")
            return True
        
        full_urls = [self.get_asset_url(path) for path in paths]
        return self.provider.purge_cache(full_urls)
    
    def purge_all(self) -> bool:
        """Purge entire CDN cache"""
        if not self.enabled:
            logger.warning("CDN disabled, skipping purge")
            return True
        
        return self.provider.purge_all()
    
    def warm_cache(self, paths: list[str]) -> bool:
        """
        Warm CDN cache by prefetching assets
        
        Makes HTTP requests to assets to populate CDN cache
        """
        import requests
        
        if not self.enabled:
            logger.warning("CDN disabled, skipping warm")
            return True
        
        logger.info(f"Warming CDN cache for {len(paths)} assets")
        
        for path in paths:
            url = self.get_asset_url(path)
            
            try:
                response = requests.head(url, timeout=5)
                if response.status_code == 200:
                    logger.debug(f"Warmed: {url}")
                else:
                    logger.warning(f"Failed to warm {url}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error warming {url}: {e}")
        
        logger.info("CDN cache warming completed")
        return True


def get_cdn_manager() -> CDNManager:
    """
    Initialize and return CDN manager
    
    Automatically selects provider based on configuration
    """
    if settings.cdn_provider == "cloudflare":
        provider = CloudFlareCDN(
            zone_id=settings.cloudflare_zone_id,
            api_token=settings.cloudflare_api_token,
            cdn_domain=settings.cdn_domain
        )
    elif settings.cdn_provider == "cloudfront":
        provider = CloudFrontCDN(
            distribution_id=settings.cloudfront_distribution_id,
            cdn_domain=settings.cdn_domain,
            aws_access_key=settings.aws_access_key_id,
            aws_secret_key=settings.aws_secret_access_key
        )
    else:
        # Generic CDN provider
        provider = CDNProvider()
    
    return CDNManager(provider)