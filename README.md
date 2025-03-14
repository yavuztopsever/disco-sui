# DiscoSui Project

## Overview
DiscoSui is a powerful tool for managing and analyzing notes, emails, and other text content. The project provides a set of tools for semantic analysis, text processing, and email management.

## Features
- **Semantic Analysis**
  - Analyze relationships between notes
  - Find related notes based on content similarity
  - Generate knowledge graphs
  - Analyze individual notes for topics and entities

- **Text Processing**
  - Split text into semantic chunks
  - Extract named entities
  - Generate text summaries
  - Analyze sentiment

- **Email Management**
  - Process email content
  - Extract email metadata
  - Convert emails to notes
  - Analyze email threads
  - Import/export emails in various formats

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yavuztopsever/disco-sui.git
   cd DiscoSui
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install spaCy language model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Project Structure
```
DiscoSui/
├── backend/
│   ├── src/
│   │   ├── core/
│   │   │   ├── tool_interfaces.py
│   │   │   └── exceptions.py
│   │   ├── services/
│   │   │   ├── semantic_analysis.py
│   │   │   ├── text_processing.py
│   │   │   └── email_processing.py
│   │   └── tools/
│   │       ├── semantic_tools.py
│   │       ├── text_tools.py
│   │       └── email_tools.py
│   └── tests/
│       ├── conftest.py
│       └── test_tools.py
├── requirements.txt
└── README.md
```

## Tool Interfaces
The project uses a set of standardized interfaces for different types of tools:

### SemanticToolInterface
- Base interface for semantic analysis tools
- Provides methods for analyzing relationships, finding related notes, and generating knowledge graphs

### TextToolInterface
- Base interface for text processing tools
- Provides methods for chunking text, extracting entities, summarizing text, and analyzing sentiment

### EmailToolInterface
- Base interface for email management tools
- Provides methods for processing emails, extracting metadata, and converting emails to notes

## Development
1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run tests:
   ```bash
   pytest backend/tests/
   ```

3. Run linting and type checking:
   ```bash
   flake8 backend/
   mypy backend/
   black backend/
   isort backend/
   ```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License
This project is licensed under the MIT License - see the LICENSE file for details.
