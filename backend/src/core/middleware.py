"""
Middleware components for the DiscoSui application.
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from collections import defaultdict
import time
from typing import Dict, List, Tuple
from src.core.config import settings
from src.core.exceptions import RateLimitError

class RateLimiter:
    """Rate limiter implementation using a sliding window."""
    
    def __init__(self, requests_per_minute: int, window_seconds: int):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_rate_limited(self, client_id: str) -> bool:
        """Check if the client is rate limited."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Remove old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        # Check if rate limit is exceeded
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return True
        
        # Add current request
        self.requests[client_id].append(now)
        return False

# Initialize rate limiter
rate_limiter = RateLimiter(
    requests_per_minute=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW
)

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    # Get client identifier (IP address or API key)
    client_id = request.headers.get("X-API-Key") or request.client.host
    
    if rate_limiter.is_rate_limited(client_id):
        raise RateLimitError("Rate limit exceeded")
    
    response = await call_next(request)
    return response

class SecurityHeadersMiddleware:
    """Middleware to add security headers to responses."""
    
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

class RequestValidationMiddleware:
    """Middleware to validate request headers and content."""
    
    async def __call__(self, request: Request, call_next):
        # Validate content type
        content_type = request.headers.get("content-type", "")
        if request.method in ["POST", "PUT", "PATCH"]:
            if not content_type.startswith("application/json"):
                return JSONResponse(
                    status_code=415,
                    content={"error": "Unsupported media type"}
                )
        
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            return JSONResponse(
                status_code=413,
                content={"error": "Request too large"}
            )
        
        response = await call_next(request)
        return response

class LoggingMiddleware:
    """Middleware to log request and response information."""
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        print(f"Request: {request.method} {request.url}")
        print(f"Headers: {request.headers}")
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        print(f"Response: {response.status_code}")
        print(f"Process time: {process_time:.2f}s")
        
        return response

class ErrorHandlingMiddleware:
    """Middleware to handle and format errors consistently."""
    
    async def __call__(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the error
            print(f"Error: {str(e)}")
            
            # Format error response
            if isinstance(e, RateLimitError):
                return JSONResponse(
                    status_code=429,
                    content={"error": str(e)}
                )
            elif isinstance(e, HTTPException):
                return JSONResponse(
                    status_code=e.status_code,
                    content={"error": str(e.detail)}
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Internal server error"}
                ) 