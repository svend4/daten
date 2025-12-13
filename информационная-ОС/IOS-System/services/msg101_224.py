"""
HashiCorp Vault Integration
Centralized secrets management with automatic rotation

Features:
- Secret storage and retrieval
- Dynamic database credentials
- API key management
- Certificate management
- Automatic secret rotation
- Audit logging
"""

import logging
import hvac
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json

from ..config import settings

logger = logging.getLogger(__name__)


class VaultClient:
    """
    HashiCorp Vault client wrapper
    
    Provides simplified interface for secret management
    """
    
    def __init__(
        self,
        vault_url: str = None,
        vault_token: str = None,
        namespace: str = None
    ):
        self.vault_url = vault_url or settings.vault_url
        self.vault_token = vault_token or settings.vault_token
        self.namespace = namespace or settings.vault_namespace
        
        # Initialize Vault client
        self.client = hvac.Client(
            url=self.vault_url,
            token=self.vault_token,
            namespace=self.namespace
        )
        
        # Verify connection
        if not self.client.is_authenticated():
            raise ValueError("Vault authentication failed")
        
        logger.info("Vault client initialized successfully")
    
    def get_secret(self, path: str, key: str = None) -> Any:
        """
        Retrieve secret from Vault
        
        Args:
            path: Secret path (e.g., 'secret/data/database')
            key: Optional specific key to retrieve
        
        Returns:
            Secret value or dict of secrets
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path
            )
            
            data = response['data']['data']
            
            if key:
                return data.get(key)
            return data
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret from {path}: {e}")
            raise
    
    def set_secret(
        self,
        path: str,
        secrets: Dict[str, Any],
        cas: int = None
    ) -> bool:
        """
        Store secret in Vault
        
        Args:
            path: Secret path
            secrets: Dict of secret key-value pairs
            cas: Check-and-set parameter for optimistic locking
        
        Returns:
            True if successful
        """
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secrets,
                cas=cas
            )
            
            logger.info(f"Secret stored successfully at {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret at {path}: {e}")
            raise
    
    def delete_secret(self, path: str, versions: list = None) -> bool:
        """
        Delete secret from Vault
        
        Args:
            path: Secret path
            versions: Optional list of versions to delete
        
        Returns:
            True if successful
        """
        try:
            if versions:
                self.client.secrets.kv.v2.delete_secret_versions(
                    path=path,
                    versions=versions
                )
            else:
                self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                    path=path
                )
            
            logger.info(f"Secret deleted from {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete secret from {path}: {e}")
            raise
    
    def list_secrets(self, path: str) -> list:
        """
        List secrets at path
        
        Args:
            path: Path to list
        
        Returns:
            List of secret names
        """
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path=path
            )
            
            return response['data']['keys']
            
        except Exception as e:
            logger.error(f"Failed to list secrets at {path}: {e}")
            raise


class DatabaseCredentialsManager:
    """
    Manages dynamic database credentials using Vault
    
    Automatically rotates credentials on schedule
    """
    
    def __init__(self, vault_client: VaultClient):
        self.vault = vault_client
        self.credentials_cache = {}
        self.cache_ttl = timedelta(minutes=5)
    
    def get_database_credentials(
        self,
        database: str = "postgres"
    ) -> Dict[str, str]:
        """
        Get database credentials from Vault
        
        Credentials are dynamically generated and time-limited
        """
        # Check cache first
        cache_key = f"db_creds_{database}"
        
        if cache_key in self.credentials_cache:
            cached_creds, cached_time = self.credentials_cache[cache_key]
            
            if datetime.now() - cached_time < self.cache_ttl:
                logger.debug(f"Returning cached credentials for {database}")
                return cached_creds
        
        try:
            # Generate dynamic credentials
            response = self.vault.client.secrets.database.generate_credentials(
                name=database
            )
            
            credentials = {
                'username': response['data']['username'],
                'password': response['data']['password'],
                'lease_id': response['lease_id'],
                'lease_duration': response['lease_duration']
            }
            
            # Cache credentials
            self.credentials_cache[cache_key] = (
                credentials,
                datetime.now()
            )
            
            logger.info(f"Generated new database credentials for {database}")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to generate database credentials: {e}")
            raise
    
    def revoke_credentials(self, lease_id: str) -> bool:
        """
        Revoke database credentials
        
        Args:
            lease_id: Lease ID from credential generation
        
        Returns:
            True if successful
        """
        try:
            self.vault.client.sys.revoke_lease(lease_id=lease_id)
            logger.info(f"Revoked credentials with lease {lease_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke credentials: {e}")
            raise
    
    def rotate_root_credentials(self, database: str = "postgres") -> bool:
        """
        Rotate root database credentials
        
        Vault will update root password and update its own configuration
        """
        try:
            self.vault.client.secrets.database.rotate_root_credentials(
                name=database
            )
            
            logger.info(f"Rotated root credentials for {database}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate root credentials: {e}")
            raise


class APIKeyManager:
    """
    Manages API keys using Vault Transit engine
    
    Provides encryption/decryption for sensitive API keys
    """
    
    def __init__(self, vault_client: VaultClient):
        self.vault = vault_client
        self.transit_key = "api-keys"
    
    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt API key using Vault Transit
        
        Args:
            api_key: Plain text API key
        
        Returns:
            Encrypted API key (ciphertext)
        """
        try:
            response = self.vault.client.secrets.transit.encrypt_data(
                name=self.transit_key,
                plaintext=api_key
            )
            
            ciphertext = response['data']['ciphertext']
            logger.debug("API key encrypted successfully")
            
            return ciphertext
            
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {e}")
            raise
    
    def decrypt_api_key(self, ciphertext: str) -> str:
        """
        Decrypt API key using Vault Transit
        
        Args:
            ciphertext: Encrypted API key
        
        Returns:
            Plain text API key
        """
        try:
            response = self.vault.client.secrets.transit.decrypt_data(
                name=self.transit_key,
                ciphertext=ciphertext
            )
            
            plaintext = response['data']['plaintext']
            logger.debug("API key decrypted successfully")
            
            return plaintext
            
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            raise
    
    def rotate_encryption_key(self) -> bool:
        """
        Rotate Transit encryption key
        
        Creates new key version for future encryptions
        """
        try:
            self.vault.client.secrets.transit.rotate_key(
                name=self.transit_key
            )
            
            logger.info(f"Rotated Transit key: {self.transit_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate Transit key: {e}")
            raise


class CertificateManager:
    """
    Manages SSL/TLS certificates using Vault PKI
    
    Issues and renews certificates automatically
    """
    
    def __init__(self, vault_client: VaultClient):
        self.vault = vault_client
        self.pki_role = "ios-system"
    
    def issue_certificate(
        self,
        common_name: str,
        alt_names: list = None,
        ttl: str = "87600h"  # 10 years
    ) -> Dict:
        """
        Issue new certificate
        
        Args:
            common_name: Certificate CN (e.g., api.ios-system.com)
            alt_names: List of SANs
            ttl: Certificate validity period
        
        Returns:
            Dict with certificate, private key, CA chain
        """
        try:
            response = self.vault.client.secrets.pki.generate_certificate(
                name=self.pki_role,
                common_name=common_name,
                alt_names=alt_names or [],
                ttl=ttl
            )
            
            certificate_data = {
                'certificate': response['data']['certificate'],
                'private_key': response['data']['private_key'],
                'ca_chain': response['data']['ca_chain'],
                'serial_number': response['data']['serial_number'],
                'expiration': response['data']['expiration']
            }
            
            logger.info(f"Issued certificate for {common_name}")
            return certificate_data
            
        except Exception as e:
            logger.error(f"Failed to issue certificate: {e}")
            raise
    
    def revoke_certificate(self, serial_number: str) -> bool:
        """
        Revoke certificate
        
        Args:
            serial_number: Certificate serial number
        
        Returns:
            True if successful
        """
        try:
            self.vault.client.secrets.pki.revoke_certificate(
                serial_number=serial_number
            )
            
            logger.info(f"Revoked certificate: {serial_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke certificate: {e}")
            raise


class SecretRotationScheduler:
    """
    Schedules automatic secret rotation
    
    Rotates secrets based on configurable policies
    """
    
    def __init__(self, vault_client: VaultClient):
        self.vault = vault_client
        self.rotation_policies = {}
    
    def register_rotation_policy(
        self,
        secret_path: str,
        rotation_interval: timedelta,
        rotation_callback: callable
    ):
        """
        Register secret for automatic rotation
        
        Args:
            secret_path: Path to secret in Vault
            rotation_interval: How often to rotate
            rotation_callback: Function to call for rotation
        """
        self.rotation_policies[secret_path] = {
            'interval': rotation_interval,
            'callback': rotation_callback,
            'last_rotation': datetime.now()
        }
        
        logger.info(f"Registered rotation policy for {secret_path}")
    
    async def check_and_rotate(self):
        """
        Check all policies and rotate expired secrets
        
        Should be called periodically (e.g., from scheduled task)
        """
        for secret_path, policy in self.rotation_policies.items():
            time_since_rotation = datetime.now() - policy['last_rotation']
            
            if time_since_rotation >= policy['interval']:
                logger.info(f"Rotating secret: {secret_path}")
                
                try:
                    # Call rotation callback
                    await policy['callback'](secret_path)
                    
                    # Update last rotation time
                    policy['last_rotation'] = datetime.now()
                    
                    logger.info(f"Successfully rotated {secret_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to rotate {secret_path}: {e}")


class AuditLogger:
    """
    Audit logging for Vault operations
    
    Tracks all secret access and modifications
    """
    
    def __init__(self, vault_client: VaultClient):
        self.vault = vault_client
    
    def get_audit_logs(
        self,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> list:
        """
        Retrieve audit logs from Vault
        
        Args:
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            List of audit log entries
        """
        # Note: This requires Vault Enterprise or external log aggregation
        # For open-source Vault, logs are written to file/syslog
        
        logger.info("Retrieving Vault audit logs")
        
        # Placeholder - actual implementation depends on log backend
        return []
    
    def log_secret_access(
        self,
        user: str,
        action: str,
        secret_path: str,
        result: str
    ):
        """
        Log secret access event
        
        Args:
            user: User who accessed secret
            action: Action performed (read, write, delete)
            secret_path: Path to secret
            result: success or failure
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user': user,
            'action': action,
            'secret_path': secret_path,
            'result': result
        }
        
        logger.info(f"Vault audit: {json.dumps(log_entry)}")


# ============================================
# Integration with Application
# ============================================

def init_vault() -> VaultClient:
    """Initialize Vault client"""
    return VaultClient()


def get_database_password() -> str:
    """Get database password from Vault"""
    vault = init_vault()
    db_manager = DatabaseCredentialsManager(vault)
    
    creds = db_manager.get_database_credentials()
    return creds['password']


def get_api_key(service: str) -> str:
    """Get API key for external service from Vault"""
    vault = init_vault()
    
    secret = vault.get_secret(
        path=f"secret/data/api-keys/{service}",
        key="api_key"
    )
    
    return secret


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data using Vault Transit"""
    vault = init_vault()
    api_key_manager = APIKeyManager(vault)
    
    return api_key_manager.encrypt_api_key(data)


def decrypt_sensitive_data(ciphertext: str) -> str:
    """Decrypt sensitive data using Vault Transit"""
    vault = init_vault()
    api_key_manager = APIKeyManager(vault)
    
    return api_key_manager.decrypt_api_key(ciphertext)