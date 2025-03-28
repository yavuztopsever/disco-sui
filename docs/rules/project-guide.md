---
description: project guide to follow
globs: 
alwaysApply: false
---
# DiscoSui - Your Intelligent Obsidian Companion

## 1. Project Overview

DiscoSui aims to transform your Obsidian vault into a dynamic, interactive knowledge base. By leveraging natural language processing, intelligent automation, and advanced retrieval techniques, DiscoSui empowers you to effortlessly access, manage, and expand your knowledge within Obsidian.

## 2. Project Details

### 2.1. Project Name: DiscoSui

### 2.2. Core Vision

Transform your Obsidian vault into a dynamic, interactive knowledge base.

### 2.3. Project Goals

* **Empower Natural Language Interaction:** Enable users to interact with their Obsidian vaults through intuitive, conversational language.
* **Automate Obsidian Workflows:** Utilize smolagents and a robust Tool Manager to automate tasks, enhance productivity, and streamline note management.
* **Provide Context-Aware Insights:** Deliver detailed, contextually relevant responses to user queries through Retrieval Augmented Generation (RAG).
* **Seamless Obsidian Integration:** Automatically open relevant notes and nodes within Obsidian for immediate exploration and action.
* **Maintain Vault Integrity:** Enforce note templates, manage tags, and ensure a coherent knowledge hierarchy.
* **Create a 2nd brain:** That has full personal context through logs, documents and notes and interface between user and vault with llm.

### 2.4. Target Audience

Obsidian users who seek:

* Advanced automation and intelligent assistance.
* Enhanced information retrieval and knowledge discovery.
* A more interactive and intuitive experience with their notes.
* Users who want to keep a clean and well organized vault.

## 3. Project Structure

discosui/
├── backend/                 # Python FastAPI backend
│   ├── src/
│   │   ├── core/           # Core functionality and shared components
│   │   ├── services/       # Core services
│   │   ├── tools/          # Tools for SmolAgents to call
│   │   ├── agents/         # AI agents implementation
│   │   └── main.py         # Main application entry point
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   └── index.js       # React entry point
├── src/                    # Obsidian plugin source
├── docs/                   # Project documentation
│   ├── api/               # API documentation
│   ├── architecture/      # Architecture docs
│   └── services/          # Service-specific documentation
├── docker/                # Docker configuration
├── config/                # Configuration files
├── rules/                 # Project rules and documentation
├── obsidian-disco-sui-plugin/ # Obsidian plugin directory
├── manifest.json          # Plugin manifest
├── package.json           # Node.js dependencies
├── tsconfig.json         # TypeScript configuration
├── requirements.txt      # Python dependencies
├── setup.sh             # Setup script
├── run.sh              # Run script
└── version-bump.mjs    # Version management script

### 2.5. Core Workflow

1.  **Natural Language Input:** Users interact with DiscoSui via a chat-like interface within Obsidian.
2.  **Intelligent Request Routing:** The Tool Manager analyzes the user's request.
3.  **Automated Task Execution:** Tools are executed to perform actions.
4.  **Contextual Question Answering (RAG):** For questions, RAG is employed.
5.  **Seamless Obsidian Integration:** Relevant notes and nodes are automatically opened.
6.  **Response Delivery:** The response is presented to the user.

### 2.6. Key Features

* **Natural Language Interaction:** Conversational interface.
* **Intelligent Tool Manager:** Automatic routing of requests.
* **Retrieval Augmented Generation (RAG):** Context-aware question answering.
* **Automatic Note Opening:** Direct access to relevant notes.
* **Template Enforcement and Note Audit:**
    * Real-time Template Enforcement.
    * Comprehensive Note Audit.
    * Automated Correction.
    * Manual Correction Guidance.
    * Scheduled Audits and Notifications.
    * User Interface.
* **Intelligent Tag Management:**
    * Create and maintain a tag database.
    * Semantic tag searching and automatic tag addition.
    * New tag creation with naming conventions and database integration.
* **Hierarchical Knowledge Structure:**
    * Create and manage a hierarchical knowledge structure.
    * Utilize backlinks for seamless navigation.
    * Implement complexity reduction and orphan note prevention.
    * Example Hierarchy:
        * Alice Smith (#Person)
            * Career Development (#Category)
                * Job Applications (#Main)
                    * Job Application - Senior Software Engineer at InnovateTech (#Document)
                    * Technical Interview Log - InnovateTech Round 1 (#Log)
                    * Learning Python Notes - Advanced Decorators and Generators (#Note)
                    * Email - Follow-up with InnovateTech Recruiter (#Mail)
* **Audio Transcription and Integration:** Periodic audio transcription.
* **Email Processing and Integration:** Periodic email processing.
* **Vault Indexing and Semantic Analysis:** Efficient vault indexing.
* **Hierarchy navigation** through the knowledge graph.

### 2.7. Technology Stack (Conceptual)

* Obsidian API
* Vector database (for RAG)
* Programming Language: Python 3.9+
* Agent Framework: smolagents
* Templating: jinja2
* Markdown Parsing: markdown-it-py
* YAML Parsing: PyYAML
* File System Interaction: os, pathlib
* LLM: openai gpt 4 o mini
* Audio library: whisper
* Email library: email
* Vector Database/Indexing: (configurable, e.g., ChromaDB, FAISS) for RAG
* Dependency management: Pydantic

## 4. Detailed Implementation

* **4.1. `src/core/config.py`:** Configuration settings using Pydantic.
    * **Goal:** Centralized, validated configuration management.
    * **Implementation:**
        * Use Pydantic's `BaseSettings` to define configuration variables.
        * Include:
            * `VAULT_PATH`: Path to the Obsidian vault.
            * `AUDIO_FILES_DIR`: Path to the folder containing raw audio files.
            * `RAW_EMAILS_DIR`: Path to the folder containing raw email files.
            * `PROCESSED_EMAILS_DIR`: Path to the folder where processed emails will be placed.
            * `RAG_VECTOR_DB_PATH`: Path to the vector database.
            * `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP`: Parameters for RAG chunking.
            * LLM API keys and model settings.
            * Vector database connection details.
            * Feature toggles (e.g., enable audio transcription, email processing).
        * Implement environment variable overrides and default values.
        * Ensure that all paths are validated.
* **4.2. `src/core/obsidian_utils.py`:** Obsidian vault interaction functions.
    * **Goal:** Provide a consistent and robust interface for interacting with the Obsidian vault.
    * **Implementation:**
        * Functions for:
            * `get_note_path(note_name: str) -> str`: Resolve note names to file paths.
            * `read_note(note_path: str) -> str`: Read note content.
            * `write_note(note_path: str, content: str) -> None`: Write note content.
            * `get_frontmatter(note_content: str) -> dict`: Extract YAML frontmatter.
            * `update_frontmatter(note_content: str, new_frontmatter: dict) -> str`: Update frontmatter.
            * `render_template(template_name: str, context: dict) -> str`: Render Jinja2 templates.
            * `create_folder(folder_path: str) -> None`: Create folders.
            * `move_file(source: str, destination: str) -> None`: Move files.
            * `open_note(note_path: str) -> None`: Open notes in Obsidian.
            * `open_node(note_path: str, node_id: str) -> None`: Open specific nodes within notes.
        * Use `pathlib` for file system operations.
        * Handle file not found and other exceptions.
* **4.3. `src/tools/`:** Tools for SmolAgents, separated by function, Pydantic validation.
    * **Goal:** Create modular and reusable tools for the agent.
    * **Implementation:**
        * Separate tools into individual files based on their functionality (e.g., `create_note.py`, `search_notes.py`).
        * Use Pydantic models for input and output validation.
        * Include docstrings that describe each tools function.
        * Ensure there are tools to trigger each service manually for smolagents
        * Example tool structure:
            * `class CreateNoteInput(BaseModel): ...`
            * `class CreateNoteOutput(BaseModel): ...`
            * `def create_note(input: CreateNoteInput) -> CreateNoteOutput: ...`
        * Each tool should perform a specific, well-defined task.
* **4.4. `src/core/agent.py`:** SmolAgent, Tool Manager, RAG, and workflow management.
    * **Goal:** Orchestrate user interactions, tool execution, and RAG.
    * **Implementation:**
        * Initialize SmolAgent and the Tool Manager.
        * Implement a chat loop to handle user input.
        * Use the Tool Manager to route requests to the appropriate tools.
        * Implement RAG for question answering:
            * Embed user queries.
            * Retrieve relevant chunks from the vector database.
            * Pass retrieved chunks to the LLM for response generation.
            * Include links to the original notes within the response.
        * Implement the logic to open notes and nodes in Obsidian.
        * Handle tool execution errors and provide informative messages.
* **4.5. `src/services/note_management/templates/`:** Jinja2 templates for note generation.
    * **Goal:** Provide reusable templates for creating notes.
    * **Implementation:**
        * Create Jinja2 templates for different note types (e.g., meeting notes, project notes, daily logs).
        * Use template variables for dynamic content generation.
        * Ensure templates adhere to the vault's note structure and frontmatter requirements.
* **4.6. `src/services/audio_integration/audio_transcriber.py`:** Audio transcription.
    * **Goal:** Transcribe audio files and integrate them into the vault.
    * **Implementation:**
        * Use the `whisper` library for audio transcription.
        * Implement a function that scans the audio input folder.
        * Create new notes for each audio file.
        * Add the transcription to the note content.
        * Use the LLM to summarize the transcription and extract key information.
        * Add metadata to the notes (e.g., recording date, file name).
* **4.7. `src/services/email_integration/email_processor.py`:** Email processing.
    * **Goal:** Process email files and integrate them into the vault.
    * **Implementation:**
        * Use the `email` library to parse email files.
        * Implement a function that scans the email input folder.
        * Create new notes for each email.
        * Add email content, sender, subject, and date to the note.
        * Use the LLM to summarize email content and extract relevant information.
        * Save attachments to the vault and link them to the email note.
* **4.8. `src/services/indexing/indexer.py & rag.py`:** Vector database indexing and RAG.
    * **Goal:** Index the vault for efficient retrieval and implement RAG.
    * **Implementation:**
        * Use a configurable vector database (e.g., ChromaDB, FAISS).
        * Implement functions for:
            * Chunking notes into semantic units.
            * Generating embeddings for chunks.
            * Storing embeddings and metadata in the vector database.
            * Performing similarity searches.
        * Implement RAG functions to retrieve relevant chunks and augment LLM responses.
* **4.9. `src/services/semantic_analysis/semantic_analyzer.py`:** Semantic analysis of notes.
    * **Goal:** Analyze note content to discover relationships and create a knowledge graph.
    * **Implementation:**
        * Use the LLM to extract entities, relationships, and concepts from notes.
        * Create a knowledge graph representation of the vault.
        * Implement functions for semantic search and relationship discovery.
* **4.10. `src/services/reorganization/reorganizer.py`:** Note reorganization, merging, splitting, and link updates.
    * **Goal:** Maintain a clean and organized vault.
    * **Implementation:**
        * Implement functions for:
            * Merging overlapping notes.
            * Splitting overly complex notes.
            * Updating backlinks and internal links.
            * Rebuilding hierarchical structures.
        * Use semantic analysis to identify related notes.
        * Create "related documents" sections with backlinks.
* **4.11. `src/services/content_manipulation/manipulator.py`:** Content manipulation using LLM.
    * **Goal:** Improve note content using the LLM.
    * **Implementation:**
        * Functions for:
            * Proofreading and correcting grammar.
            * Improving content clarity and flow.
            * Adding contextual information.
            * Deleting redundant parts.
            * Creating summaries.
        * Ensure content is easy to navigate and read.
* **4.12. `src/services/database_integration/database_handler.py`:** Vault as database, external document integration.
    * **Goal:** Use the vault as a central database and integrate external documents.
    * **Implementation:**
        * Create separate folders for PDFs, CSVs, images, and audio recordings.
        * Implement functions to import and link external documents to relevant notes.
        * Use the vault's file system as a database.
* **4.13. `src/core/exceptions.py`:** Custom exception classes.
    * **Goal:** Provide specific exception types for error handling.
    * **Implementation:**
        * Create custom exception classes for common errors (e.g., `NoteNotFoundError`, `TemplateNotFoundError`, `
`FrontmatterError`).
        * Use these exceptions throughout the codebase for robust error handling.
* **4.14. `src/core/tool_manager.py`:** Tool selection, RAG decision, web search integration, error handling.
    * **Goal:** Intelligently route user requests and manage tool execution.
    * **Implementation:**
        * Implement logic to analyze user requests and determine the appropriate tool(s) to use.
        * Use semantic analysis to understand the intent of the request.
        * Implement logic to decide when to use RAG:
            * If the request is a question, use RAG.
            * If the request requires information retrieval, use RAG.
        * Implement logic to decide when to perform a web search or crawl:
            * If the request requires up-to-date information.
            * If the vault lacks the necessary context.
        * Implement error handling for tool execution:
            * Catch tool-specific exceptions.
            * Provide informative error messages to the user.
            * Implement retry mechanisms for transient errors.
        * Maintain a registry of available tools.
        * Use a configuration file or database to store tool metadata.
        * Implement a mechanism for users to add or remove tools.
        * Implement a system to handle tool dependencies.
        * Create a system that can handle very large Obsidian vaults and optimize for speed.
        * Make sure to follow the given templates and structures for the vault.
        * Make sure to modify any notes that do not follow the template structure to match.

## 5. Testing

* Comprehensive unit tests using pytest.
* Test core functions, tools, and agent behavior.
* Error handling and edge case coverage.

## 6. LLM Integration

* Use `openai gpt-4-o-mini`.
* LLM-powered content generation and enhancement.
* Semantic analysis, note reorganization, and other tasks.
* LLM integration with RAG.
* Error handling and rate limiting.

## 7. Documentation

* Detailed `README.md` file.
* Up-to-date docstrings.

## 8. Dependency Management

* `requirements.txt`/`pyproject.toml`.
* Regular dependency updates.

## 9. Coding Instructions

* Follow project structure and implementation details.
* Prioritize functionality and maintainability.
* Write comprehensive unit tests.
* Adhere to Python best practices, PEP 8.
* Use Pydantic, Smolagents, and Obsidian plugin documentation.


## 10. Error Handling and Robustness

* Custom Exceptions: Use `src/core/exceptions.py`.
* Input Validation: Pydantic validation.
* File System Robustness: `pathlib`.
* LLM Error Handling: Retry mechanisms and rate limiting.
* Logging: Comprehensive logging system.
* Data Integrity: Validation and integrity checks.

## 11. Performance Optimization

* Indexing: Efficient indexing and vector database.
* Caching: Caching mechanisms.
* Asynchronous Operations: `asyncio`.
* Efficient Algorithms: Algorithms and data structures.
* Database Optimization: Queries and indexing.
* Large Vault Handling: Batch loading and memory optimization.

## 12. Plugin System

* Obsidian Plugin chat window for user interface.
* Plugin system for extensibility.
* Web Integration: API integration for tools.

## 13. Server System

* Scheduled Task Execution:
    * Docker server for backend.
    * Audio log creation: Transcription, summarization, task list, suggestions.
    * Email processing: Extraction, import, preprocessing, and document creation.
* Multi-Vault Support: Support multiple vaults.

## 14. Code Style and Maintainability

* PEP 8 Compliance.
* Type Hinting: Pydantic.
* Docstrings: Comprehensive docstrings.
* Code Modularity: Modular architecture.
* Code Reusability: Reusable components.
* Code Comments: Clear comments.
* Version Control: Git.
* Code Reviews: Regular reviews.

## 15. Dependency Management

* `requirements.txt`/`pyproject.toml`: Accurate dependency lists.
* Dependency Updates: Regular updates.
* Dependency Conflicts: Careful resolution.

## 16. RAG (Retrieval Augmented Generation) Implementation

* **Vector Database Choice:**
    * Configurable vector databases (ChromaDB, FAISS, Pinecone).
    * Abstraction layer for vector database operations.
* **Indexing Strategy:**
    * Chunk notes based on Markdown structure (headings, paragraphs, code blocks).
    * Configurable chunk size and overlap.
    * Generate embeddings using LLM's embedding model.
    * Store embeddings and metadata in the vector database.
* **Retrieval Process:**
    * Embed the user's query.
    * Similarity search in the vector database.
    * Rank retrieved chunks based on similarity score.
* **Augmentation:**
    * Pass retrieved chunks as context to the LLM.
    * Generate a detailed response.
    * Add links to original notes and sections.
* **Metadata Handling:**
    * Store metadata (tags, frontmatter, file paths).
    * Use metadata to filter and refine results.
* **Index Updates:**
    * Automatic updates when notes are created, modified, or deleted.
    * Background process or scheduled task for updates.

## 17. User Interaction and Feedback

* **Chat Interface Enhancements:**
    * Visual cues for processing.
    * Progress indicators.
    * User feedback on responses.
    * Allow the user to ask the agent to refine its previous response.
* **Error Reporting:**
    * Informative error messages.
    * Detailed error logging.
    * Mechanism for user error reporting.
* **Configuration and Customization:**
    * Clear configuration options.
    * Customizable agent behavior.
    * Allow the user to set how many notes are opened at a time, and how much context is given to the LLM during RAG operations.

## 18. Plugin Architecture

* Plugin architecture for extensibility.
* Well-documented API for plugin development.
* **Distributed Processing:**
    * Distributed processing for large vaults and complex tasks.
    * Message queues or distributed systems for task management.