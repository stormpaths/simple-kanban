"""
OIDC provider configuration and utilities.
"""
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class OIDCProviderConfig:
    """Configuration for an OIDC provider."""
    client_id: str
    client_secret: str
    discovery_url: str
    redirect_uri: str
    scopes: list[str]
    name: str
    display_name: str


class OIDCConfigManager:
    """Manages OIDC provider configurations."""
    
    def __init__(self):
        self._providers: Dict[str, OIDCProviderConfig] = {}
        self._load_configurations()
    
    def _load_configurations(self):
        """Load OIDC configurations from Kubernetes secrets."""
        # Try to load from stormpath secret first (fallback)
        stormpath_config = self._load_from_secret("/var/secrets/stormpath/google-auth.json")
        if stormpath_config:
            self._providers["google"] = self._create_google_config(stormpath_config)
        
        # Try to load from kanban-specific secret (preferred)
        kanban_config = self._load_from_secret("/var/secrets/kanban/google_oauth.json")
        if kanban_config:
            self._providers["google"] = self._create_google_config(kanban_config, is_kanban_specific=True)
    
    def _load_from_secret(self, secret_path: str) -> Optional[Dict[str, Any]]:
        """Load JSON configuration from a Kubernetes secret file."""
        try:
            if os.path.exists(secret_path):
                with open(secret_path, 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
            print(f"Could not load OIDC config from {secret_path}: {e}")
        return None
    
    def _create_google_config(self, config_data: Dict[str, Any], is_kanban_specific: bool = False) -> OIDCProviderConfig:
        """Create Google OIDC configuration from loaded data."""
        web_config = config_data.get("web", {})
        
        # Determine redirect URI based on configuration source
        if is_kanban_specific:
            # Use kanban-specific callback URL
            redirect_uri = "https://kanban.stormpath.dev/api/oidc/callback/google"
        else:
            # Use stormpath callback URL as fallback
            redirect_uris = web_config.get("redirect_uris", [])
            redirect_uri = redirect_uris[0] if redirect_uris else "https://kanban.stormpath.dev/api/oidc/callback/google"
        
        return OIDCProviderConfig(
            client_id=web_config.get("client_id", ""),
            client_secret=web_config.get("client_secret", ""),
            discovery_url="https://accounts.google.com/.well-known/openid-configuration",
            redirect_uri=redirect_uri,
            scopes=["openid", "email", "profile"],
            name="google",
            display_name="Google"
        )
    
    def get_provider(self, provider_name: str) -> Optional[OIDCProviderConfig]:
        """Get configuration for a specific provider."""
        return self._providers.get(provider_name)
    
    def get_available_providers(self) -> Dict[str, str]:
        """Get list of available providers with their display names."""
        return {name: config.display_name for name, config in self._providers.items()}
    
    def is_provider_configured(self, provider_name: str) -> bool:
        """Check if a provider is properly configured."""
        config = self._providers.get(provider_name)
        if not config:
            return False
        return bool(config.client_id and config.client_secret)


# Global instance
oidc_config = OIDCConfigManager()
