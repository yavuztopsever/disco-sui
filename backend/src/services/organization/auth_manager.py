"""Authentication manager implementation."""

from typing import Dict, Optional
from datetime import datetime, timedelta
import jwt
from pydantic import BaseModel, ConfigDict

from ...core.exceptions import AuthenticationError
from ..base_service import BaseService


class AuthConfig(BaseModel):
    """Configuration for authentication."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    secret_key: str
    token_expiry: int = 3600  # 1 hour
    refresh_expiry: int = 86400  # 24 hours


class AuthToken(BaseModel):
    """Authentication token."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthManager(BaseService):
    """Service for managing authentication."""
    
    def __init__(self, config: AuthConfig):
        """Initialize the auth manager.
        
        Args:
            config: Authentication configuration
        """
        super().__init__()
        self.config = config
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the auth manager."""
        if self._initialized:
            return
        
        self._initialized = True
    
    async def create_tokens(self, user_id: str, claims: Optional[Dict] = None) -> AuthToken:
        """Create access and refresh tokens.
        
        Args:
            user_id: User ID
            claims: Optional additional claims
            
        Returns:
            Authentication tokens
            
        Raises:
            AuthenticationError: If token creation fails
        """
        try:
            now = datetime.utcnow()
            
            access_claims = {
                "sub": user_id,
                "iat": now,
                "exp": now + timedelta(seconds=self.config.token_expiry),
                "type": "access"
            }
            if claims:
                access_claims.update(claims)
            
            refresh_claims = {
                "sub": user_id,
                "iat": now,
                "exp": now + timedelta(seconds=self.config.refresh_expiry),
                "type": "refresh"
            }
            
            access_token = jwt.encode(
                access_claims,
                self.config.secret_key,
                algorithm="HS256"
            )
            
            refresh_token = jwt.encode(
                refresh_claims,
                self.config.secret_key,
                algorithm="HS256"
            )
            
            return AuthToken(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.config.token_expiry
            )
        except Exception as e:
            raise AuthenticationError(f"Failed to create tokens: {str(e)}")
    
    async def verify_token(self, token: str, token_type: str = "access") -> Dict:
        """Verify and decode a token.
        
        Args:
            token: Token to verify
            token_type: Expected token type
            
        Returns:
            Decoded token claims
            
        Raises:
            AuthenticationError: If token verification fails
        """
        try:
            claims = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=["HS256"]
            )
            
            if claims.get("type") != token_type:
                raise AuthenticationError("Invalid token type")
            
            return claims
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    async def refresh_tokens(self, refresh_token: str) -> AuthToken:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New authentication tokens
            
        Raises:
            AuthenticationError: If token refresh fails
        """
        try:
            claims = await self.verify_token(refresh_token, "refresh")
            return await self.create_tokens(claims["sub"])
        except Exception as e:
            raise AuthenticationError(f"Failed to refresh tokens: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False 