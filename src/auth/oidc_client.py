"""
OIDC client for handling OAuth2 authentication flows.
"""
import secrets
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oidc.core import CodeIDToken
import httpx

from .oidc_config import oidc_config, OIDCProviderConfig


class OIDCClient:
    """Client for handling OIDC authentication flows."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.config = oidc_config.get_provider(provider_name)
        if not self.config:
            raise ValueError(f"Provider '{provider_name}' not configured")
        
        self._client: Optional[AsyncOAuth2Client] = None
        self._discovery_cache: Optional[Dict[str, Any]] = None
    
    async def _get_client(self) -> AsyncOAuth2Client:
        """Get or create the OAuth2 client."""
        if not self._client:
            self._client = AsyncOAuth2Client(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                redirect_uri=self.config.redirect_uri
            )
        return self._client
    
    async def _get_discovery_document(self) -> Dict[str, Any]:
        """Fetch and cache the OIDC discovery document."""
        if not self._discovery_cache:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.config.discovery_url)
                response.raise_for_status()
                self._discovery_cache = response.json()
        return self._discovery_cache
    
    def generate_state(self) -> str:
        """Generate a secure random state parameter."""
        return secrets.token_urlsafe(32)
    
    async def get_authorization_url(self, state: str) -> str:
        """Generate the authorization URL for the OIDC provider."""
        discovery = await self._get_discovery_document()
        authorization_endpoint = discovery["authorization_endpoint"]
        
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(self.config.scopes),
            "response_type": "code",
            "state": state,
            "access_type": "offline",  # For Google to get refresh token
            "prompt": "consent"  # Force consent screen to get refresh token
        }
        
        return f"{authorization_endpoint}?{urlencode(params)}"
    
    async def exchange_code_for_tokens(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        discovery = await self._get_discovery_document()
        token_endpoint = discovery["token_endpoint"]
        
        client = await self._get_client()
        
        token_data = await client.fetch_token(
            token_endpoint,
            code=code,
            redirect_uri=self.config.redirect_uri
        )
        
        return token_data
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from the OIDC provider."""
        discovery = await self._get_discovery_document()
        userinfo_endpoint = discovery["userinfo_endpoint"]
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(userinfo_endpoint, headers=headers)
            response.raise_for_status()
            return response.json()
    
    def verify_id_token(self, id_token: str, nonce: Optional[str] = None) -> Dict[str, Any]:
        """Verify and decode the ID token."""
        # For production, you should verify the token signature
        # For now, we'll decode without verification (not recommended for production)
        import jwt
        
        # Decode without verification for development
        # In production, fetch and use the provider's public keys
        decoded = jwt.decode(id_token, options={"verify_signature": False})
        
        # Basic validation
        if decoded.get("iss") != "https://accounts.google.com":
            raise ValueError("Invalid issuer")
        
        if decoded.get("aud") != self.config.client_id:
            raise ValueError("Invalid audience")
        
        return decoded
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an access token using a refresh token."""
        discovery = await self._get_discovery_document()
        token_endpoint = discovery["token_endpoint"]
        
        client = await self._get_client()
        
        token_data = await client.refresh_token(
            token_endpoint,
            refresh_token=refresh_token
        )
        
        return token_data


def get_oidc_client(provider_name: str) -> OIDCClient:
    """Factory function to get an OIDC client for a provider."""
    return OIDCClient(provider_name)
