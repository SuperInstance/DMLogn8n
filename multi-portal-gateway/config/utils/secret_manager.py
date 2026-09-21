"""
Secret management integration for DMLogn8n multi-agent platform.
Supports multiple secret backends including HashiCorp Vault, AWS Secrets Manager,
environment variables, and encrypted files.
"""

import os
import json
import base64
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
import threading
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class SecretMetadata:
    """Secret metadata."""
    name: str
    version: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    description: Optional[str] = None
    tags: List[str] = None
    environment: str = "unknown"
    source: str = "unknown"


class SecretBackend(ABC):
    """Abstract base class for secret backends."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def get_secret(self, secret_name: str, version: Optional[str] = None) -> Optional[str]:
        """Get a secret value."""
        pass

    @abstractmethod
    def get_secrets(self, secret_names: List[str]) -> Dict[str, Optional[str]]:
        """Get multiple secrets."""
        pass

    @abstractmethod
    def set_secret(self, secret_name: str, secret_value: str, metadata: Optional[SecretMetadata] = None) -> bool:
        """Set a secret value."""
        pass

    @abstractmethod
    def delete_secret(self, secret_name: str) -> bool:
        """Delete a secret."""
        pass

    @abstractmethod
    def list_secrets(self, path: str = "") -> List[str]:
        """List available secrets."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check backend health."""
        pass


class EnvironmentVariableBackend(SecretBackend):
    """Environment variable secret backend."""

    def __init__(self, prefix: str = "SECRET_"):
        super().__init__("environment_variables")
        self.prefix = prefix

    def get_secret(self, secret_name: str, version: Optional[str] = None) -> Optional[str]:
        """Get secret from environment variable."""
        env_key = f"{self.prefix}{secret_name.upper()}"
        return os.getenv(env_key)

    def get_secrets(self, secret_names: List[str]) -> Dict[str, Optional[str]]:
        """Get multiple secrets from environment variables."""
        return {name: self.get_secret(name) for name in secret_names}

    def set_secret(self, secret_name: str, secret_value: str, metadata: Optional[SecretMetadata] = None) -> bool:
        """Set environment variable (not recommended for production)."""
        try:
            env_key = f"{self.prefix}{secret_name.upper()}"
            os.environ[env_key] = secret_value
            return True
        except Exception as e:
            self.logger.error(f"Failed to set environment variable {env_key}: {str(e)}")
            return False

    def delete_secret(self, secret_name: str) -> bool:
        """Delete environment variable."""
        try:
            env_key = f"{self.prefix}{secret_name.upper()}"
            if env_key in os.environ:
                del os.environ[env_key]
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete environment variable {env_key}: {str(e)}")
            return False

    def list_secrets(self, path: str = "") -> List[str]:
        """List environment variable secrets."""
        secrets = []
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                secret_name = key[len(self.prefix):].lower()
                if not path or secret_name.startswith(path.lower()):
                    secrets.append(secret_name)
        return secrets

    def health_check(self) -> bool:
        """Environment variables are always available."""
        return True


class FileBackend(SecretBackend):
    """File-based secret backend with encryption."""

    def __init__(self, secrets_file: Union[str, Path], encryption_key: Optional[str] = None):
        super().__init__("file_backend")
        self.secrets_file = Path(secrets_file)
        self.secrets_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize encryption
        if encryption_key:
            self.cipher = self._create_cipher(encryption_key.encode())
        else:
            key = os.getenv("SECRETS_FILE_KEY")
            if key:
                self.cipher = self._create_cipher(key.encode())
            else:
                self.cipher = None
                self.logger.warning("No encryption key provided, secrets will be stored in plain text")

        self._lock = threading.Lock()
        self._secrets_cache = {}
        self._load_secrets()

    def _create_cipher(self, key: bytes) -> Fernet:
        """Create Fernet cipher from key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'dmlogn8n_salt',
            iterations=100000,
        )
        key_bytes = kdf.derive(key)
        return Fernet(base64.urlsafe_b64encode(key_bytes))

    def _load_secrets(self) -> None:
        """Load secrets from file."""
        try:
            if self.secrets_file.exists():
                with open(self.secrets_file, 'rb') as f:
                    data = f.read()

                if self.cipher and data:
                    decrypted_data = self.cipher.decrypt(data)
                    self._secrets_cache = json.loads(decrypted_data.decode())
                else:
                    self._secrets_cache = json.loads(data.decode()) if data else {}
            else:
                self._secrets_cache = {}
        except Exception as e:
            self.logger.error(f"Failed to load secrets from {self.secrets_file}: {str(e)}")
            self._secrets_cache = {}

    def _save_secrets(self) -> None:
        """Save secrets to file."""
        try:
            data = json.dumps(self._secrets_cache, indent=2).encode()

            if self.cipher:
                encrypted_data = self.cipher.encrypt(data)
                data = encrypted_data

            # Write to temporary file first, then rename
            temp_file = self.secrets_file.with_suffix('.tmp')
            with open(temp_file, 'wb') as f:
                f.write(data)

            temp_file.rename(self.secrets_file)

        except Exception as e:
            self.logger.error(f"Failed to save secrets to {self.secrets_file}: {str(e)}")
            raise

    def get_secret(self, secret_name: str, version: Optional[str] = None) -> Optional[str]:
        """Get secret from file."""
        with self._lock:
            return self._secrets_cache.get(secret_name)

    def get_secrets(self, secret_names: List[str]) -> Dict[str, Optional[str]]:
        """Get multiple secrets from file."""
        with self._lock:
            return {name: self._secrets_cache.get(name) for name in secret_names}

    def set_secret(self, secret_name: str, secret_value: str, metadata: Optional[SecretMetadata] = None) -> bool:
        """Set secret in file."""
        try:
            with self._lock:
                self._secrets_cache[secret_name] = secret_value
                self._save_secrets()
            return True
        except Exception as e:
            self.logger.error(f"Failed to set secret {secret_name}: {str(e)}")
            return False

    def delete_secret(self, secret_name: str) -> bool:
        """Delete secret from file."""
        try:
            with self._lock:
                if secret_name in self._secrets_cache:
                    del self._secrets_cache[secret_name]
                    self._save_secrets()
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete secret {secret_name}: {str(e)}")
            return False

    def list_secrets(self, path: str = "") -> List[str]:
        """List secrets in file."""
        with self._lock:
            secrets = list(self._secrets_cache.keys())
            if path:
                secrets = [s for s in secrets if s.startswith(path)]
            return secrets

    def health_check(self) -> bool:
        """Check if secrets file is accessible."""
        try:
            return self.secrets_file.exists() or self.secrets_file.parent.exists()
        except Exception:
            return False


class HashiCorpVaultBackend(SecretBackend):
    """HashiCorp Vault backend."""

    def __init__(self, url: str, token: str, mount_point: str = "secret"):
        super().__init__("hashicorp_vault")
        self.url = url
        self.token = token
        self.mount_point = mount_point

        try:
            import hvac
            self.client = hvac.Client(url=url, token=token)
        except ImportError:
            self.logger.error("hvac library not installed. Install with: pip install hvac")
            raise ImportError("hvac library required for HashiCorp Vault backend")

    def get_secret(self, secret_name: str, version: Optional[str] = None) -> Optional[str]:
        """Get secret from Vault."""
        try:
            path = f"{self.mount_point}/data/{secret_name}"
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                version=version
            )

            if response and 'data' in response and 'data' in response['data']:
                return response['data']['data'].get('value')
            return None

        except Exception as e:
            self.logger.error(f"Failed to get secret {secret_name} from Vault: {str(e)}")
            return None

    def get_secrets(self, secret_names: List[str]) -> Dict[str, Optional[str]]:
        """Get multiple secrets from Vault."""
        return {name: self.get_secret(name) for name in secret_names}

    def set_secret(self, secret_name: str, secret_value: str, metadata: Optional[SecretMetadata] = None) -> bool:
        """Set secret in Vault."""
        try:
            path = f"{self.mount_point}/data/{secret_name}"
            secret_data = {'value': secret_value}

            if metadata:
                secret_data.update({
                    'description': metadata.description,
                    'environment': metadata.environment,
                    'tags': metadata.tags or []
                })

            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to set secret {secret_name} in Vault: {str(e)}")
            return False

    def delete_secret(self, secret_name: str) -> bool:
        """Delete secret from Vault."""
        try:
            path = f"{self.mount_point}/data/{secret_name}"
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=path)
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete secret {secret_name} from Vault: {str(e)}")
            return False

    def list_secrets(self, path: str = "") -> List[str]:
        """List secrets in Vault."""
        try:
            list_path = f"{self.mount_point}/metadata"
            if path:
                list_path += f"/{path}"

            response = self.client.secrets.kv.v2.list_secrets(path=list_path)
            if response and 'data' in response and 'keys' in response['data']:
                return response['data']['keys']
            return []

        except Exception as e:
            self.logger.error(f"Failed to list secrets from Vault: {str(e)}")
            return []

    def health_check(self) -> bool:
        """Check Vault health."""
        try:
            return self.client.sys.read_health_status()['initialized']
        except Exception:
            return False


class AWSSecretsManagerBackend(SecretBackend):
    """AWS Secrets Manager backend."""

    def __init__(self, region_name: str, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        super().__init__("aws_secrets_manager")
        self.region_name = region_name

        try:
            import boto3
            if access_key and secret_key:
                self.client = boto3.client(
                    'secretsmanager',
                    region_name=region_name,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key
                )
            else:
                self.client = boto3.client('secretsmanager', region_name=region_name)
        except ImportError:
            self.logger.error("boto3 library not installed. Install with: pip install boto3")
            raise ImportError("boto3 library required for AWS Secrets Manager backend")

    def get_secret(self, secret_name: str, version: Optional[str] = None) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        try:
            kwargs = {'SecretId': secret_name}
            if version:
                kwargs['VersionId'] = version

            response = self.client.get_secret_value(**kwargs)

            if 'SecretString' in response:
                return response['SecretString']
            elif 'SecretBinary' in response:
                return base64.b64decode(response['SecretBinary']).decode()
            return None

        except Exception as e:
            self.logger.error(f"Failed to get secret {secret_name} from AWS Secrets Manager: {str(e)}")
            return None

    def get_secrets(self, secret_names: List[str]) -> Dict[str, Optional[str]]:
        """Get multiple secrets from AWS Secrets Manager."""
        return {name: self.get_secret(name) for name in secret_names}

    def set_secret(self, secret_name: str, secret_value: str, metadata: Optional[SecretMetadata] = None) -> bool:
        """Set secret in AWS Secrets Manager."""
        try:
            kwargs = {
                'SecretId': secret_name,
                'SecretString': secret_value
            }

            if metadata and metadata.description:
                kwargs['Description'] = metadata.description

            # Try to update first, then create if it doesn't exist
            try:
                self.client.update_secret(**kwargs)
            except self.client.exceptions.ResourceNotFoundException:
                self.client.create_secret(**kwargs)

            return True

        except Exception as e:
            self.logger.error(f"Failed to set secret {secret_name} in AWS Secrets Manager: {str(e)}")
            return False

    def delete_secret(self, secret_name: str) -> bool:
        """Delete secret from AWS Secrets Manager."""
        try:
            self.client.delete_secret(SecretId=secret_name, ForceDeleteWithoutRecovery=True)
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete secret {secret_name} from AWS Secrets Manager: {str(e)}")
            return False

    def list_secrets(self, path: str = "") -> List[str]:
        """List secrets in AWS Secrets Manager."""
        try:
            secrets = []
            paginator = self.client.get_paginator('list_secrets')

            for page in paginator.paginate():
                for secret in page['SecretList']:
                    if not path or secret['Name'].startswith(path):
                        secrets.append(secret['Name'])

            return secrets

        except Exception as e:
            self.logger.error(f"Failed to list secrets from AWS Secrets Manager: {str(e)}")
            return []

    def health_check(self) -> bool:
        """Check AWS Secrets Manager health."""
        try:
            self.client.list_secrets(MaxResults=1)
            return True
        except Exception:
            return False


class SecretManager:
    """Main secret manager that coordinates multiple backends."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.backends: List[SecretBackend] = []
        self.primary_backend: Optional[SecretBackend] = None
        self._lock = threading.Lock()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = int(os.getenv("SECRETS_CACHE_TTL", "300"))  # 5 minutes

        # Initialize backends based on configuration
        self._initialize_backends()

    def _initialize_backends(self) -> None:
        """Initialize secret backends based on environment configuration."""
        # Environment variables backend (always available)
        env_backend = EnvironmentVariableBackend()
        self.backends.append(env_backend)

        # File backend
        secrets_file = os.getenv("SECRETS_FILE_PATH")
        if secrets_file:
            try:
                file_backend = FileBackend(secrets_file)
                self.backends.append(file_backend)
                self.logger.info(f"Initialized file backend: {secrets_file}")
            except Exception as e:
                self.logger.error(f"Failed to initialize file backend: {str(e)}")

        # HashiCorp Vault backend
        vault_url = os.getenv("VAULT_URL")
        vault_token = os.getenv("VAULT_TOKEN")
        if vault_url and vault_token:
            try:
                vault_backend = HashiCorpVaultBackend(vault_url, vault_token)
                self.backends.append(vault_backend)
                self.primary_backend = vault_backend
                self.logger.info(f"Initialized HashiCorp Vault backend: {vault_url}")
            except Exception as e:
                self.logger.error(f"Failed to initialize HashiCorp Vault backend: {str(e)}")

        # AWS Secrets Manager backend
        aws_region = os.getenv("AWS_REGION")
        if aws_region:
            try:
                aws_backend = AWSSecretsManagerBackend(aws_region)
                self.backends.append(aws_backend)
                if not self.primary_backend:
                    self.primary_backend = aws_backend
                self.logger.info(f"Initialized AWS Secrets Manager backend: {aws_region}")
            except Exception as e:
                self.logger.error(f"Failed to initialize AWS Secrets Manager backend: {str(e)}")

        if not self.primary_backend:
            # Use file backend as primary if available, otherwise environment variables
            for backend in self.backends:
                if isinstance(backend, FileBackend):
                    self.primary_backend = backend
                    break
            else:
                self.primary_backend = env_backend

        self.logger.info(f"Secret manager initialized with {len(self.backends)} backends")
        self.logger.info(f"Primary backend: {self.primary_backend.name}")

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        return (datetime.now(timezone.utc) - cache_entry['timestamp']).total_seconds() < self._cache_ttl

    def _get_from_cache(self, secret_name: str) -> Optional[str]:
        """Get secret from cache."""
        with self._lock:
            if secret_name in self._cache and self._is_cache_valid(self._cache[secret_name]):
                return self._cache[secret_name]['value']
        return None

    def _set_cache(self, secret_name: str, secret_value: str) -> None:
        """Set secret in cache."""
        with self._lock:
            self._cache[secret_name] = {
                'value': secret_value,
                'timestamp': datetime.now(timezone.utc)
            }

    def get_secret(self, secret_name: str, version: Optional[str] = None, use_cache: bool = True) -> Optional[str]:
        """Get a secret from available backends."""
        # Check cache first
        if use_cache:
            cached_value = self._get_from_cache(secret_name)
            if cached_value is not None:
                return cached_value

        # Try primary backend first
        if self.primary_backend:
            value = self.primary_backend.get_secret(secret_name, version)
            if value is not None:
                if use_cache:
                    self._set_cache(secret_name, value)
                return value

        # Try other backends in order
        for backend in self.backends:
            if backend == self.primary_backend:
                continue

            value = backend.get_secret(secret_name, version)
            if value is not None:
                if use_cache:
                    self._set_cache(secret_name, value)
                return value

        self.logger.warning(f"Secret not found: {secret_name}")
        return None

    def get_secrets(self, secret_names: List[str], use_cache: bool = True) -> Dict[str, Optional[str]]:
        """Get multiple secrets."""
        return {name: self.get_secret(name, use_cache=use_cache) for name in secret_names}

    def set_secret(self, secret_name: str, secret_value: str, metadata: Optional[SecretMetadata] = None, backend_name: Optional[str] = None) -> bool:
        """Set a secret in specified backend or primary backend."""
        if backend_name:
            # Use specific backend
            for backend in self.backends:
                if backend.name == backend_name:
                    success = backend.set_secret(secret_name, secret_value, metadata)
                    if success:
                        # Clear cache
                        with self._lock:
                            self._cache.pop(secret_name, None)
                    return success
            self.logger.error(f"Backend not found: {backend_name}")
            return False
        else:
            # Use primary backend
            if self.primary_backend:
                success = self.primary_backend.set_secret(secret_name, secret_value, metadata)
                if success:
                    # Clear cache
                    with self._lock:
                        self._cache.pop(secret_name, None)
                return success
            else:
                self.logger.error("No primary backend configured for writing secrets")
                return False

    def delete_secret(self, secret_name: str, backend_name: Optional[str] = None) -> bool:
        """Delete a secret."""
        if backend_name:
            # Delete from specific backend
            for backend in self.backends:
                if backend.name == backend_name:
                    success = backend.delete_secret(secret_name)
                    if success:
                        # Clear cache
                        with self._lock:
                            self._cache.pop(secret_name, None)
                    return success
            self.logger.error(f"Backend not found: {backend_name}")
            return False
        else:
            # Delete from primary backend
            if self.primary_backend:
                success = self.primary_backend.delete_secret(secret_name)
                if success:
                    # Clear cache
                    with self._lock:
                        self._cache.pop(secret_name, None)
                return success
            else:
                self.logger.error("No primary backend configured for deleting secrets")
                return False

    def list_secrets(self, path: str = "", backend_name: Optional[str] = None) -> List[str]:
        """List secrets."""
        if backend_name:
            for backend in self.backends:
                if backend.name == backend_name:
                    return backend.list_secrets(path)
            self.logger.error(f"Backend not found: {backend_name}")
            return []
        else:
            # List from primary backend
            if self.primary_backend:
                return self.primary_backend.list_secrets(path)
            else:
                self.logger.error("No primary backend configured for listing secrets")
                return []

    def health_check(self) -> Dict[str, bool]:
        """Check health of all backends."""
        health_status = {}
        for backend in self.backends:
            try:
                health_status[backend.name] = backend.health_check()
            except Exception as e:
                self.logger.error(f"Health check failed for backend {backend.name}: {str(e)}")
                health_status[backend.name] = False
        return health_status

    def clear_cache(self) -> None:
        """Clear secret cache."""
        with self._lock:
            self._cache.clear()
        self.logger.info("Secret cache cleared")

    def get_backend_names(self) -> List[str]:
        """Get list of available backend names."""
        return [backend.name for backend in self.backends]

    def get_primary_backend_name(self) -> str:
        """Get primary backend name."""
        return self.primary_backend.name if self.primary_backend else "none"


# Global secret manager instance
secret_manager = SecretManager()


# Convenience functions
def get_secret(secret_name: str, version: Optional[str] = None, use_cache: bool = True) -> Optional[str]:
    """Get a secret value."""
    return secret_manager.get_secret(secret_name, version, use_cache)


def get_secrets(secret_names: List[str], use_cache: bool = True) -> Dict[str, Optional[str]]:
    """Get multiple secrets."""
    return secret_manager.get_secrets(secret_names, use_cache)


def set_secret(secret_name: str, secret_value: str, metadata: Optional[SecretMetadata] = None, backend_name: Optional[str] = None) -> bool:
    """Set a secret value."""
    return secret_manager.set_secret(secret_name, secret_value, metadata, backend_name)