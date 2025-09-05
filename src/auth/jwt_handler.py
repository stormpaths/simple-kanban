"""
JWT token handling for authentication.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import os
from jose import JWTError, jwt
from pydantic import BaseModel


class TokenData(BaseModel):
    """Token data model for JWT payload."""
    username: Optional[str] = None
    user_id: Optional[int] = None


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class JWTHandler:
    """JWT token generation and validation handler."""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a new JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            
            if username is None or user_id is None:
                return None
                
            return TokenData(username=username, user_id=user_id)
        except JWTError:
            return None
    
    def create_token_response(self, user_id: int, username: str) -> Token:
        """Create a complete token response."""
        access_token = self.create_access_token(
            data={"sub": username, "user_id": user_id}
        )
        return Token(
            access_token=access_token,
            expires_in=self.access_token_expire_minutes * 60
        )


# Global JWT handler instance
jwt_handler = JWTHandler()
