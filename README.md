# DiscoSui - AI-Powered Note Management System

[![CI](https://github.com/yavuztopsever/disco-sui/actions/workflows/ci.yml/badge.svg)](https://github.com/yavuztopsever/disco-sui/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Obsidian Downloads](https://img.shields.io/badge/dynamic/json?logo=obsidian&color=%23483699&label=downloads&query=%24%5B%22obsidian-disco-sui%22%5D.downloads&url=https%3A%2F%2Fraw.githubusercontent.com%2Fobsidianmd%2Fobsidian-releases%2Fmaster%2Fcommunity-plugin-stats.json)](https://obsidian.md/plugins?id=obsidian-disco-sui)

## Overview

DiscoSui is an advanced note management system that combines the power of artificial intelligence with the flexibility of Obsidian. It helps you organize, process, and enhance your notes using state-of-the-art AI capabilities.

### Key Features

- 🤖 **AI-Powered Processing**: Automatically analyze and enhance your notes using advanced AI models
- 🔄 **Real-time Integration**: Seamless integration with Obsidian for immediate note processing
- 📝 **Smart Templates**: Intelligent template suggestions based on note content
- 🔍 **Context-Aware Processing**: Understanding of note relationships and context
- 🌐 **API Integration**: Robust API for extending functionality

## Quick Start

### Prerequisites

- Node.js (v16.x or later)
- npm or yarn
- Obsidian (v0.15.0 or later)
- Python 3.11 or later (for backend services)

### Installation

1. **Obsidian Plugin Installation**
   ```bash
   # Clone the repository
   git clone https://github.com/yavuztopsever/disco-sui.git
   cd disco-sui

   # Install dependencies
   npm install

   # Build the plugin
   npm run build
   ```

2. **Backend Setup**
   ```bash
   # Create and activate virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Start the backend server
   python app.py
   ```

### Configuration

1. Open Obsidian Settings
2. Navigate to Community Plugins
3. Enable DiscoSui
4. Configure the plugin settings:
   - API Endpoint
   - Vault Path
   - HuggingFace Token (optional)

## Architecture

DiscoSui follows a modern, modular architecture:

- **Frontend**: Obsidian plugin built with TypeScript
- **Backend**: Python-based API server with AI capabilities
- **AI Engine**: Leverages HuggingFace's models for note processing
- **Database**: SQLite for local storage, extensible to other databases

## Development

### Project Structure

```
disco-sui/
├── src/                 # Plugin source code
│   ├── components/     # UI components
│   ├── lib/           # Core functionality
│   └── types/         # TypeScript type definitions
├── api/                # Backend API
├── tests/              # Test suites
└── docs/               # Documentation
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and development process.

### Testing

```bash
# Run frontend tests
npm test

# Run backend tests
pytest
```

## API Documentation

The DiscoSui API provides endpoints for:

- Note Processing
- Template Management
- AI Analysis
- Vault Operations

For detailed API documentation, see [API.md](docs/API.md).

## Roadmap

- [ ] Enhanced AI Models Integration
- [ ] Collaborative Note Processing
- [ ] Advanced Template System
- [ ] Mobile Support
- [ ] Real-time Collaboration Features

## Support

- [Issue Tracker](https://github.com/yavuztopsever/disco-sui/issues)
- [Documentation](https://github.com/yavuztopsever/disco-sui/wiki)
- [Community Forum](https://github.com/yavuztopsever/disco-sui/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Obsidian Community
- HuggingFace Team
- All Contributors

---

Made with ❤️ by [Yavuz Topsever](https://github.com/yavuztopsever)
