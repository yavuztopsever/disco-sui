import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import uvicorn
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from src.agents.NoteManagementAgent import NoteManagementAgent
from src.services.audio.transcription.scheduler import AudioTranscriptionScheduler
from src.services.email.processing.scheduler import EmailProcessingScheduler
from src.core.config import settings
from src.core.exceptions import (
    NoteManagementError,
    AudioProcessingError,
    EmailProcessingError,
    AuthenticationError,
    ValidationError
)
from src.core.middleware import (
    rate_limit_middleware,
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    LoggingMiddleware,
    ErrorHandlingMiddleware
)
from src.core.logging import get_logger
from src.core.cache import cached, invalidate_cache

# Initialize logger
logger = get_logger(__name__)

# Load environment variables
load_dotenv('.env.local')

# Initialize FastAPI app
app = FastAPI(
    title="DiscoSui API",
    description="An intelligent Obsidian companion that transforms your vault into a dynamic knowledge base",
    version="1.0.0"
)

# Add middleware
app.middleware("http")(rate_limit_middleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Security
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.API_KEY:
        logger.warning(f"Invalid API key attempt from {api_key[:8]}...")
        raise AuthenticationError("Invalid API key")
    return api_key

# Add CORS middleware with proper security settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent
agent = NoteManagementAgent(os.getenv('VAULT_PATH', './notes'))

# Initialize schedulers
audio_scheduler = AudioTranscriptionScheduler()
email_scheduler = EmailProcessingScheduler()

class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    message: str = Field(..., description="The natural language message to process")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the message")

class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    success: bool = Field(..., description="Whether the operation was successful")
    response: str = Field(..., description="The response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class ToolInfo(BaseModel):
    """Model for tool information."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of the tool")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")

@app.exception_handler(NoteManagementError)
async def note_management_error_handler(request, exc):
    logger.error(f"Note management error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": str(exc)}
    )

@app.exception_handler(AudioProcessingError)
async def audio_processing_error_handler(request, exc):
    logger.error(f"Audio processing error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": str(exc)}
    )

@app.exception_handler(EmailProcessingError)
async def email_processing_error_handler(request, exc):
    logger.error(f"Email processing error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": str(exc)}
    )

@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request, exc):
    logger.error(f"Authentication error: {str(exc)}")
    return JSONResponse(
        status_code=401,
        content={"success": False, "error": str(exc)}
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": str(exc)}
    )

@app.on_event("startup")
async def startup_event():
    """Start background tasks when the application starts."""
    try:
        logger.info("Starting background tasks...")
        # Start the audio transcription scheduler
        asyncio.create_task(audio_scheduler.start())
        
        # Start the email processing scheduler if enabled
        if settings.EMAIL_PROCESSING_ENABLED:
            asyncio.create_task(email_scheduler.start())
        logger.info("Background tasks started successfully")
    except Exception as e:
        logger.error(f"Failed to start background tasks: {str(e)}")
        raise RuntimeError(f"Failed to start background tasks: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up when the application shuts down."""
    try:
        logger.info("Stopping background tasks...")
        # Stop the schedulers
        audio_scheduler.stop()
        email_scheduler.stop()
        logger.info("Background tasks stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop background tasks: {str(e)}")
        raise RuntimeError(f"Failed to stop background tasks: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
@invalidate_cache("list_tools")  # Invalidate tools cache when chat is used
async def chat(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Process a natural language message and return a response.
    
    This endpoint handles all natural language interactions with the DiscoSui agent.
    
    Features:
    - Note creation, updates, and deletion
    - Note searching and analysis
    - Vault organization and management
    - Content generation and manipulation
    
    Parameters:
    - message: The natural language message to process
    - context: Optional additional context for the message
    
    Returns:
    - success: Whether the operation was successful
    - response: The response message
    - data: Additional response data (if any)
    - error: Error message (if operation failed)
    """
    try:
        logger.info(f"Processing chat message: {request.message[:100]}...")
        # Process the message and get the response
        result = await agent.process_message(request.message)
        
        # Ensure we have a valid response
        if not result:
            logger.error("No response received from the agent")
            raise NoteManagementError("No response received from the agent")
            
        # If the response is already in our expected format, return it directly
        if isinstance(result, dict) and "success" in result:
            logger.info("Successfully processed chat message")
            return ChatResponse(
                success=result["success"],
                response=result.get("response", "No response provided"),
                data=result.get("data"),
                error=result.get("error")
            )
            
        # Otherwise, wrap it in our standard format
        logger.info("Successfully processed chat message")
        return ChatResponse(
            success=True,
            response=str(result),
            data={"raw_result": result}
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise NoteManagementError(f"Error processing message: {str(e)}")

@app.get("/tools", response_model=Dict[str, List[ToolInfo]])
@cached(ttl=3600)  # Cache tools list for 1 hour
async def list_tools(api_key: str = Depends(verify_api_key)):
    """
    Get a list of available tools and their documentation.
    
    Returns:
    - A dictionary containing lists of available tools and their documentation
    """
    try:
        logger.info("Retrieving available tools")
        tools = [
            ToolInfo(
                name=tool_name,
                description=agent.get_tool_documentation(tool_name),
                parameters=agent.get_tool_parameters(tool_name)
            )
            for tool_name in agent.get_available_tools()
        ]
        logger.info(f"Successfully retrieved {len(tools)} tools")
        return {
            "success": True,
            "tools": tools
        }
    except Exception as e:
        logger.error(f"Error retrieving tools: {str(e)}")
        raise NoteManagementError(f"Error retrieving tools: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring service health.
    
    Returns:
    - status: The current status of the service
    - version: The current version of the API
    """
    try:
        # Check Redis connection
        await app.state.redis.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        redis_status = "unhealthy"

    return {
        "status": "healthy",
        "version": app.version,
        "components": {
            "api": "healthy",
            "redis": redis_status
        }
    }

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="DiscoSui API",
        version="1.0.0",
        description="An intelligent Obsidian companion that transforms your vault into a dynamic knowledge base",
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    # Add security requirement to all endpoints
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"ApiKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    logger.info(f"Starting DiscoSui API server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        debug=settings.DEBUG
    ) 