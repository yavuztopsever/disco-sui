# DiscoSui Architecture

## Overview

DiscoSui is a modern web application built with a microservices architecture, consisting of a Python FastAPI backend and a React/TypeScript frontend. The application uses AI agents to process natural language requests and manage Obsidian vaults.

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │    Backend      │     │    Redis        │
│  (React/TS)     │◄───►│  (FastAPI)      │◄───►│   (Cache)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Components

### Frontend

- **Framework**: React with TypeScript
- **State Management**: React Context + Hooks
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **Testing**: Jest + React Testing Library

### Backend

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **AI Integration**: OpenAI GPT-4
- **Caching**: Redis
- **Testing**: Pytest

## Data Flow

1. User sends a message through the frontend interface
2. Frontend makes an API request to the backend
3. Backend processes the request using AI agents
4. AI agents interact with the Obsidian vault
5. Results are cached in Redis
6. Response is sent back to the frontend

## AI Agents

### NoteManagementAgent

- Handles note creation, updates, and deletion
- Manages note organization and structure
- Processes natural language requests

### VaultAnalysisAgent

- Analyzes vault structure and content
- Provides insights and recommendations
- Helps with organization

### ContentGenerationAgent

- Generates content based on user requests
- Helps with note creation and updates
- Maintains consistency in content style

## Security

- API authentication using OpenAI API key
- Rate limiting per API key
- Input validation and sanitization
- Secure WebSocket connections
- Environment variable management

## Deployment

### Docker

- Separate containers for frontend, backend, and Redis
- Docker Compose for local development
- Production-ready Dockerfiles

### Environment Variables

Required environment variables:
- `OPENAI_API_KEY`: OpenAI API key
- `VAULT_PATH`: Path to Obsidian vault
- `NODE_ENV`: Environment (development/production)
- `REDIS_URL`: Redis connection URL

## Monitoring and Logging

- Application metrics collection
- Error tracking and reporting
- Performance monitoring
- Log aggregation

## Development Workflow

1. Local development using Docker Compose
2. Code review process
3. Automated testing
4. CI/CD pipeline
5. Staging deployment
6. Production deployment

## Future Improvements

1. Add support for multiple AI providers
2. Implement offline mode
3. Add collaborative features
4. Enhance security features
5. Improve performance optimization
6. Add more AI agent capabilities 