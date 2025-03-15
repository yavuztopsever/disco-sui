from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import asyncio
from datetime import datetime
from .base_tools import BaseTool
from ..services.service_manager import ServiceManager
from ..core.exceptions import ServiceError

logger = logging.getLogger(__name__)

class ServiceExecutionTool(BaseTool):
    """Tool for executing services like audio transcription and email parsing.
    
    This implements the ServiceExecutionTool functionality from Flow 5.
    It follows the exact sequence from Flow 5:
    1. LLMAgent identifies ServiceExecutionTool
    2. LLMAgent gets ServiceExecutionTool manifest
    3. LLMAgent generates API call
    4. ServiceAPI executes service
    5. ContentProcessor formats result
    6. NotesTool creates/updates note with processed content
    """
    
    def __init__(self, service_manager: ServiceManager, content_processor=None):
        """Initialize the service execution tool.
        
        Args:
            service_manager: Service manager instance
            content_processor: Optional content processor for formatting results
        """
        super().__init__()
        self.service_manager = service_manager
        self.content_processor = content_processor
        self.processing_queue = asyncio.Queue()
        
        # Start background processing task
        self.processing_task = asyncio.create_task(self._process_queue())
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "ServiceExecutionTool"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Execute services like audio transcription, email parsing and other content processing services"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "service": {
                "type": "string",
                "description": "The service to execute",
                "enum": ["transcription", "email_parsing", "content_processing", "backup", "indexing"],
                "required": True
            },
            "data": {
                "type": "object",
                "description": "Service-specific data to process",
                "required": True
            },
            "options": {
                "type": "object",
                "description": "Additional service options",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    def get_manifest(self) -> Dict[str, Any]:
        """Get the tool manifest for LLM agent.
        
        Returns:
            Dict[str, Any]: Tool manifest with schema and examples
        """
        return {
            "name": self.name,
            "description": self.description,
            "params": self.inputs,
            "examples": [
                {
                    "service": "transcription",
                    "data": {"audio_path": "/path/to/audio.mp3", "language": "en"}
                },
                {
                    "service": "email_parsing",
                    "data": {"email_content": "From: user@example.com\nSubject: Meeting notes", "extract_tasks": True}
                },
                {
                    "service": "content_processing",
                    "data": {"content": "This is a draft document...", "operation": "proofread"}
                }
            ]
        }
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute a service operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        service_name = parameters["service"]
        data = parameters["data"]
        options = parameters.get("options", {})
        
        try:
            # Following Flow 5: LLMAgent -> ServiceAPI -> ContentProcessor
            # Step 1: Submit the service request to the processing queue
            task_id = f"{service_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            await self.processing_queue.put({
                "task_id": task_id,
                "service": service_name,
                "data": data,
                "options": options
            })
            
            # Step 2: For synchronous operations, wait for processing and return result
            # In a real implementation, this might return a task ID for asynchronous operations
            result = await self._execute_service(service_name, data, options)
            
            # Step 3: Format the result with ContentProcessor if available
            if self.content_processor and result:
                formatted_result = await self.content_processor.format_content(
                    result, 
                    format_type=options.get("format_type", "default")
                )
                
                return {
                    "result": formatted_result
                }
            
            return {
                "result": result
            }
                
        except Exception as e:
            logger.error(f"Service execution failed: {str(e)}")
            raise
            
    async def _process_queue(self):
        """Background task to process the service queue."""
        while True:
            try:
                task = await self.processing_queue.get()
                
                # Process the task
                try:
                    await self._execute_service(
                        task["service"],
                        task["data"],
                        task["options"]
                    )
                except Exception as e:
                    logger.error(f"Failed to process task {task['task_id']}: {str(e)}")
                    
                self.processing_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("Processing queue task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in processing queue: {str(e)}")
                await asyncio.sleep(1)  # Avoid tight loops on error
            
    async def _execute_service(self, service_name: str, data: Dict[str, Any], options: Dict[str, Any]) -> Any:
        """Execute a specific service.
        
        Args:
            service_name: The service to execute
            data: Service-specific data
            options: Additional options
            
        Returns:
            The service result
            
        Raises:
            ServiceError: If the service execution fails
        """
        try:
            # Map service names to their corresponding service handlers
            if service_name == "transcription":
                return await self._execute_transcription_service(data, options)
            elif service_name == "email_parsing":
                return await self._execute_email_parsing_service(data, options)
            elif service_name == "content_processing":
                return await self._execute_content_processing_service(data, options)
            elif service_name == "backup":
                return await self._execute_backup_service(data, options)
            elif service_name == "indexing":
                return await self._execute_indexing_service(data, options)
            else:
                raise ValueError(f"Unsupported service: {service_name}")
        except Exception as e:
            logger.error(f"Service execution failed: {str(e)}")
            raise ServiceError(f"Service {service_name} execution failed: {str(e)}")
            
    async def _execute_transcription_service(self, data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute audio transcription service.
        
        This corresponds to the transcription service in Flow 5.
        """
        audio_path = data.get("audio_path")
        language = data.get("language", "en")
        
        if not audio_path:
            raise ValueError("Audio path is required for transcription")
            
        try:
            # Use the service manager to execute the service
            result = await self.service_manager.handle_request(
                service_name="audio", 
                action="transcribe",
                data={
                    "audio_path": audio_path,
                    "language": language,
                    "options": options
                }
            )
            
            return result
            
        except Exception as e:
            raise ServiceError(f"Transcription service failed: {str(e)}")
            
    async def _execute_email_parsing_service(self, data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email parsing service.
        
        This corresponds to the email parsing service in Flow 5.
        """
        email_content = data.get("email_content")
        extract_tasks = data.get("extract_tasks", False)
        
        if not email_content:
            raise ValueError("Email content is required for parsing")
            
        try:
            # Use the service manager to execute the service
            result = await self.service_manager.handle_request(
                service_name="email", 
                action="parse",
                data={
                    "content": email_content,
                    "extract_tasks": extract_tasks,
                    "options": options
                }
            )
            
            return result
            
        except Exception as e:
            raise ServiceError(f"Email parsing service failed: {str(e)}")
            
    async def _execute_content_processing_service(self, data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content processing service.
        
        This corresponds to the content processing service in Flow 5.
        """
        content = data.get("content")
        operation = data.get("operation")
        
        if not content or not operation:
            raise ValueError("Content and operation are required for content processing")
            
        try:
            # Use the service manager to execute the service
            result = await self.service_manager.handle_request(
                service_name="content", 
                action=operation,
                data={
                    "content": content,
                    "options": options
                }
            )
            
            return result
            
        except Exception as e:
            raise ServiceError(f"Content processing service failed: {str(e)}")
            
    async def _execute_backup_service(self, data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute backup service."""
        backup_type = data.get("type", "full")
        target_path = data.get("target_path")
        
        try:
            result = await self.service_manager.handle_request(
                service_name="storage", 
                action="backup",
                data={
                    "type": backup_type,
                    "target_path": target_path,
                    "options": options
                }
            )
            
            return result
            
        except Exception as e:
            raise ServiceError(f"Backup service failed: {str(e)}")
            
    async def _execute_indexing_service(self, data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute indexing service."""
        index_type = data.get("type", "content")
        target_paths = data.get("target_paths", [])
        
        try:
            result = await self.service_manager.handle_request(
                service_name="analysis", 
                action="index",
                data={
                    "type": index_type,
                    "target_paths": target_paths,
                    "options": options
                }
            )
            
            return result
            
        except Exception as e:
            raise ServiceError(f"Indexing service failed: {str(e)}")
            
    async def cleanup(self):
        """Clean up resources."""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass