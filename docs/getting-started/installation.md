# Installation Guide

## Prerequisites

Before installing DiscoSui, ensure you have the following prerequisites installed:

- Docker
- Docker Compose
- Python 3.9+
- Node.js 16+
- Obsidian

## Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/DiscoSui.git
   cd DiscoSui
   ```

2. **Run Setup Script**
   ```bash
   ./setup.sh
   ```
   This will:
   - Check dependencies
   - Set up the environment
   - Install the Obsidian plugin
   - Start required services

3. **Configure Environment**
   - Edit `.env` file with your settings:
     ```env
     OPENAI_API_KEY=your_api_key
     VAULT_PATH=/path/to/your/vault
     ```

4. **Configure Obsidian Plugin**
   1. Open Obsidian Settings
   2. Go to Community Plugins
   3. Enable DiscoSui
   4. Configure API URL as `http://localhost:5000`

## Development Setup

For development, use:
```bash
./setup.sh dev
```

This will:
- Set up Python virtual environment
- Install development dependencies
- Install frontend dependencies

## Available Commands

- `./setup.sh` - Full setup (default)
- `./setup.sh dev` - Setup development environment
- `./setup.sh start` - Start services
- `./setup.sh stop` - Stop services
- `./setup.sh restart` - Restart services
- `./setup.sh logs` - View service logs
- `./setup.sh help` - Show help message

## Troubleshooting

### Common Issues

1. **Services Not Starting**
   - Check Docker logs: `./setup.sh logs`
   - Ensure ports are not in use
   - Verify environment variables

2. **Plugin Not Working**
   - Verify API is running
   - Check Obsidian plugin settings
   - Review plugin logs in Obsidian

3. **API Key Issues**
   - Ensure OpenAI API key is valid
   - Check `.env` file configuration
   - Verify environment variables are loaded

For more issues, check our [GitHub Issues](https://github.com/yourusername/DiscoSui/issues). 