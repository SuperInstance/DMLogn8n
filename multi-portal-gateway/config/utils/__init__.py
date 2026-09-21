"""
Configuration utilities for DMLogn8n multi-agent platform.
"""

from .secret_manager import (
    SecretManager,
    SecretBackend,
    EnvironmentVariableBackend,
    FileBackend,
    HashiCorpVaultBackend,
    AWSSecretsManagerBackend,
    SecretMetadata,
    secret_manager,
    get_secret,
    get_secrets,
    set_secret
)

__all__ = [
    'SecretManager',
    'SecretBackend',
    'EnvironmentVariableBackend',
    'FileBackend',
    'HashiCorpVaultBackend',
    'AWSSecretsManagerBackend',
    'SecretMetadata',
    'secret_manager',
    'get_secret',
    'get_secrets',
    'set_secret'
]