# DiscoSui - Your Intelligent Obsidian Companion

Transform your Obsidian vault into a dynamic, interactive knowledge base with DiscoSui.

## Project Structure

```
discosui/
├── backend/                 # Python FastAPI backend
│   ├── src/
│   │   ├── services/       # Core services
│   │   │   ├── email/      # Email processing service
│   │   │   ├── audio/      # Audio processing service
│   │   │   ├── content/    # Content management service
│   │   │   ├── analysis/   # Semantic analysis service
│   │   │   └── organization/ # Tag and structure management
│   │   ├── core/           # Core functionality
│   │   ├── tools/          # Tools for SmolAgents
│   │   └── agents/         # AI agents implementation
│   └── tests/              # Backend tests
├── docs/                   # Project documentation
│   ├── api/               # API documentation
│   ├── architecture/      # Architecture docs
│   └── services/          # Service-specific documentation
├── docker/                # Docker configuration
├── config/               # Configuration files
└── .cursor/              # Cursor IDE configuration and rules
```

## Features

- **Natural Language Interaction**: Conversational interface for your Obsidian vault
- **Intelligent Tool Manager**: Automatic routing of requests
- **Retrieval Augmented Generation (RAG)**: Context-aware question answering
- **Template Enforcement**: Ensures consistency across your vault
- **Audio & Email Integration**: Process and integrate various content types
- **Semantic Analysis**: Discover relationships and maintain knowledge structure

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/discosui.git
   cd discosui
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure the environment:
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env with your settings
   ```

4. Start the development server:
   ```bash
   # Terminal 1 - Backend
   cd backend
   python src/main.py
   ```

## Development

- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Testing

```bash
# Backend tests
cd backend
pytest
```

## Docker Deployment

```bash
docker-compose up -d
```

## Documentation

- [API Documentation](docs/api/README.md)
- [Architecture Overview](docs/architecture/overview.md)
- [Services Documentation](docs/services/README.md)

## Contributing

Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## Security

For security concerns, please review our [Security Policy](SECURITY.md).

## License

[MIT License](LICENSE)
