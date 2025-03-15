# DiscoSui - Your Intelligent Obsidian Companion

<div align="center">

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue)](https://www.docker.com/get-started)
[![Obsidian](https://img.shields.io/badge/obsidian-1.0.0%2B-purple)](https://obsidian.md/)

</div>

## Overview

DiscoSui transforms your Obsidian vault into a dynamic, interactive knowledge base. Using natural language processing, intelligent automation, and advanced retrieval techniques, DiscoSui helps you effortlessly access, manage, and expand your knowledge within Obsidian.

### Key Features

- 🗣️ **Natural Language Interaction**: Chat with your vault using natural language
- 🤖 **Intelligent Automation**: Automate tasks using smolagents and Tool Manager
- 🔍 **Context-Aware Insights**: Get detailed, contextual responses through RAG
- 🔗 **Seamless Integration**: Automatically open relevant notes and nodes
- 📝 **Template Enforcement**: Maintain consistent note structure
- 🏷️ **Smart Tag Management**: Intelligent tag organization and suggestions
- 📊 **Knowledge Graph**: Visual representation of your knowledge connections
- 🎵 **Audio Processing**: Transcribe and analyze audio content
- 📧 **Email Integration**: Process and organize email content
- 🔎 **Semantic Search**: Find related content intelligently

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- Node.js 16+
- Obsidian

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yavuztopsever/DiscoSui.git
   cd DiscoSui
   ```

2. **Run Setup**
   ```bash
   ./setup.sh
   ```

3. **Configure Plugin**
   - Open Obsidian Settings
   - Go to Community Plugins
   - Enable DiscoSui
   - Configure API URL as `http://localhost:5000`

For detailed installation instructions, see our [Installation Guide](docs/getting-started/installation.md).

## Documentation

- [User Guide](docs/user-guide/README.md)
- [Developer Guide](docs/developer-guide/architecture.md)
- [API Reference](docs/api-reference/README.md)
- [Deployment Guide](docs/deployment/README.md)

## Project Structure

```
discosui/
├── backend/                 # Python FastAPI backend
│   ├── src/
│   │   ├── core/           # Core functionality
│   │   ├── services/       # Core services
│   │   ├── tools/          # SmolAgent tools
│   │   ├── agents/         # AI agents
│   │   └── main.py         # Entry point
├── frontend/               # React frontend
├── docs/                   # Documentation
├── docker/                 # Docker configuration
├── config/                # Configuration files
├── scripts/               # Utility scripts
└── setup.sh              # Setup script
```

## Development

### Setup Development Environment

```bash
./setup.sh dev
```

### Available Commands

- `./setup.sh` - Full setup (default)
- `./setup.sh dev` - Setup development environment
- `./setup.sh start` - Start services
- `./setup.sh stop` - Stop services
- `./setup.sh restart` - Restart services
- `./setup.sh logs` - View service logs
- `./setup.sh help` - Show help message

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Flow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Security

Security is important to us. Please see our [Security Policy](SECURITY.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Obsidian](https://obsidian.md/) for the amazing knowledge base platform
- [OpenAI](https://openai.com/) for the powerful language models
- [smolagents](https://github.com/example/smolagents) for the agent framework
- All our contributors and users

## Support

- [GitHub Issues](https://github.com/yourusername/DiscoSui/issues)
- [Documentation](docs/)
