# Email Service

## Overview
The Email Service is responsible for processing and managing email-related functionality in DiscoSui. It combines the previous email processing and integration features into a single, cohesive service.

## Features
- Email file processing (EML format)
- Automatic email note creation
- Attachment handling
- Email metadata extraction
- HTML content processing
- Email organization and tagging

## Architecture

### Directory Structure
```
services/email/
├── models/         # Data models and schemas
├── controllers/    # Request handlers and business logic
├── utils/          # Email-specific utilities
├── service.py      # Main service implementation
└── config.py       # Service configuration
```

### Components
1. **EmailService (service.py)**
   - Main service class handling email processing
   - Coordinates between different components
   - Manages email processing lifecycle

2. **Models**
   - `EmailModel`: Core email data structure
   - `AttachmentModel`: Attachment metadata
   - `EmailNoteModel`: Obsidian note representation

3. **Controllers**
   - `EmailProcessor`: Handles email file processing
   - `NoteGenerator`: Generates Obsidian notes
   - `AttachmentHandler`: Manages email attachments

4. **Utilities**
   - Email parsing helpers
   - File system operations
   - Format conversion utilities

## Configuration
```python
EMAIL_CONFIG = {
    'RAW_EMAILS_DIR': str,           # Directory for raw email files
    'PROCESSED_EMAILS_DIR': str,     # Directory for processed files
    'CHECK_INTERVAL_MINUTES': int,   # Processing interval
    'SUPPORTED_FORMATS': List[str],  # Supported email formats
    'MAX_FILE_SIZE_MB': int,        # Maximum file size
    'ATTACHMENT_STORAGE': str       # Attachment storage location
}
```

## API Endpoints
- `POST /api/email/process`: Process new email files
- `GET /api/email/status`: Get processing status
- `GET /api/email/attachments/{id}`: Retrieve attachment
- `POST /api/email/reprocess`: Reprocess specific emails

## Integration
The Email Service integrates with:
- Content Service: For note creation and management
- Organization Service: For tagging and categorization
- Analysis Service: For content analysis and indexing

## Error Handling
- File format validation
- Size limit enforcement
- Processing error recovery
- Attachment handling errors

## Best Practices
1. Regular monitoring of processing queue
2. Periodic cleanup of processed files
3. Secure attachment handling
4. Proper error logging and monitoring

## Development Guidelines
1. Follow service-oriented architecture principles
2. Maintain separation of concerns
3. Use dependency injection
4. Write comprehensive tests
5. Document API changes
