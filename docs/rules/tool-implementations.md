---
description: This document describes the implementation of tools in DiscoSui. These will all work with smolagents agent.
globs: 
alwaysApply: false
---
# DiscoSui Tools Implementation Guide

## Overview

This document describes the implementation of tools in DiscoSui. These will all work with smolagents agent.

## Tool Categories

1. Core Tools
   - `note_tools.py`: Basic note management (create, read, update, delete)
   - `folder_tools.py`: Folder operations and structure management
   - `tag_tools.py`: Tag management and organization
   - `search_tools.py`: Search functionality across the vault

2. Content Processing Tools
   - `audio_tools.py`: Audio transcription and integration
   - `email_tools.py`: Email processing and integration
   - `content_tools.py`: Content manipulation and enhancement
   - `markdown_tools.py`: Markdown formatting and processing

3. Intelligence Tools
   - `semantic_tools.py`: Semantic analysis and relationships
   - `indexing_tools.py`: Vault indexing and RAG implementation
   - `llm_tools.py`: LLM-based operations and processing
   - `hierarchy_tools.py`: Knowledge hierarchy management

4. Integration Tools
   - `plugin_tools.py`: Obsidian plugin integration
   - `api_tools.py`: External API integration
   - `sync_tools.py`: Synchronization with external services
   - `backup_tools.py`: Backup and version control

## Implementation Details

### Core Tools

#### note_tools.py

```python
from pydantic import BaseModel
from src.core.obsidian_utils import read_note, write_note, delete_note

class CreateNoteInput(BaseModel):
    note_name: str
    content: str
    template: str = None

def create_note(input: CreateNoteInput) -> None:
    """Creates a new note with optional template.

    Args:
        input: CreateNoteInput containing note_name, content, and optional template.

    Raises:
        FileExistsError: If note already exists
        Exception: If any error occurs during creation
    """
    try:
        if template:
            # Apply template formatting
            content = apply_template(input.template, input.content)
        else:
            content = input.content
        write_note(input.note_name, content)
    except Exception as e:
        raise Exception(f"Error creating note: {e}")

class UpdateNoteInput(BaseModel):
    note_name: str
    content: str
    append: bool = False

def update_note(input: UpdateNoteInput) -> None:
    """Updates an existing note.

    Args:
        input: UpdateNoteInput containing note_name, content, and append flag.

    Raises:
        FileNotFoundError: If note doesn't exist
        Exception: If any error occurs during update
    """
    try:
        if input.append:
            existing_content = read_note(input.note_name)
            content = existing_content + "\n" + input.content
        else:
            content = input.content
        write_note(input.note_name, content)
    except Exception as e:
        raise Exception(f"Error updating note: {e}")
```

#### folder_tools.py

```python
from pydantic import BaseModel
from src.core.obsidian_utils import create_folder, move_folder, delete_folder

class CreateFolderInput(BaseModel):
    folder_path: str

def create_folder(input: CreateFolderInput) -> None:
    """Creates a new folder in the vault.

    Args:
        input: CreateFolderInput containing folder_path.

    Raises:
        Exception: If any error occurs during creation
    """
    try:
        create_folder(input.folder_path)
    except Exception as e:
        raise Exception(f"Error creating folder: {e}")

class MoveFolderInput(BaseModel):
    source_path: str
    destination_path: str

def move_folder(input: MoveFolderInput) -> None:
    """Moves a folder to a new location.

    Args:
        input: MoveFolderInput containing source and destination paths.

    Raises:
        FileNotFoundError: If source folder doesn't exist
        Exception: If any error occurs during move
    """
    try:
        move_folder(input.source_path, input.destination_path)
    except Exception as e:
        raise Exception(f"Error moving folder: {e}")
```

### Content Processing Tools

#### markdown_tools.py

```python
from pydantic import BaseModel
from src.core.obsidian_utils import process_markdown

class FormatMarkdownInput(BaseModel):
    content: str
    style: str = "default"

def format_markdown(input: FormatMarkdownInput) -> str:
    """Formats markdown content according to specified style.

    Args:
        input: FormatMarkdownInput containing content and style.

    Returns:
        str: Formatted markdown content

    Raises:
        ValueError: If style is invalid
        Exception: If any error occurs during formatting
    """
    try:
        return process_markdown(input.content, input.style)
    except Exception as e:
        raise Exception(f"Error formatting markdown: {e}")
```

### Intelligence Tools

#### semantic_tools.py

```python
from pydantic import BaseModel
from src.core.obsidian_utils import analyze_semantics, find_relationships

class AnalyzeContentInput(BaseModel):
    content: str
    analysis_type: str = "basic"

def analyze_content(input: AnalyzeContentInput) -> dict:
    """Performs semantic analysis on content.

    Args:
        input: AnalyzeContentInput containing content and analysis type.

    Returns:
        dict: Analysis results

    Raises:
        ValueError: If analysis type is invalid
        Exception: If any error occurs during analysis
    """
    try:
        return analyze_semantics(input.content, input.analysis_type)
    except Exception as e:
        raise Exception(f"Error analyzing content: {e}")
```

## Usage Guidelines

1. Error Handling
   - All tools should implement proper error handling
   - Use specific exception types for different error cases
   - Provide clear error messages with context

2. Input Validation
   - Use Pydantic models for input validation
   - Implement strict type checking
   - Provide clear parameter descriptions

3. Documentation
   - Include detailed docstrings for all functions
   - Document all parameters and return values
   - Provide usage examples

4. Testing
   - Write unit tests for all tools
   - Include edge cases in tests
   - Maintain high test coverage

## Best Practices

1. Tool Design
   - Keep tools focused and single-purpose
   - Follow SOLID principles
   - Maintain consistency across tools

2. Performance
   - Implement caching where appropriate
   - Optimize for large vaults
   - Consider async operations for I/O-heavy tasks

3. Security
   - Validate all inputs
   - Sanitize file paths
   - Handle sensitive data appropriately

4. Maintainability
   - Follow consistent coding style
   - Keep functions small and focused
   - Use meaningful variable names

## Integration Guidelines

1. Plugin Integration
   - Follow Obsidian plugin guidelines
   - Maintain compatibility with Obsidian API
   - Handle plugin lifecycle events

2. External Services
   - Implement proper authentication
   - Handle rate limiting
   - Manage API keys securely

3. Data Synchronization
   - Implement conflict resolution
   - Handle offline operations
   - Maintain data integrity

## Deployment

1. Environment Setup
   - Use virtual environments
   - Manage dependencies with requirements.txt
   - Document environment variables

2. Testing
   - Run unit tests before deployment
   - Perform integration testing
   - Validate in staging environment

3. Monitoring
   - Implement logging
   - Track performance metrics
   - Monitor error rates

## Contributing

1. Code Standards
   - Follow PEP 8 guidelines
   - Use type hints
   - Write clear commit messages

2. Documentation
   - Update docs with changes
   - Include example usage
   - Document breaking changes

3. Testing
   - Add tests for new features
   - Update existing tests
   - Maintain test coverage

Custom tools:

audio_tools.py: Handles audio transcription and linking, which are core features for integrating audio content.
content_tools.py: Manages content manipulation, including summarization and proofreading, leveraging the LLM's capabilities.
email_tools.py: Facilitates email integration, importing emails and linking them to notes.
folder_tools.py: Provides tools for folder management, essential for organizing the Obsidian vault.
hierarchy_tools.py: Manages the hierarchical structure of notes, a key aspect of DiscoSui's organization.
indexing_tools.py: Handles vault indexing and RAG queries, crucial for efficient information retrieval.
note_tools.py: Offers basic note management functionalities, like creating and updating notes.
reorganization_tools.py: Manages note reorganization, including merging and splitting notes, to maintain a clean vault.
semantic_tools.py: Performs semantic analysis and finds related notes, enhancing knowledge discovery.
tag_tools.py: Manages tags, a vital part of Obsidian's organization system

1. audio_tools.py

transcribe_audio:

Python
from pydantic import BaseModel
from src.core.obsidian_utils import write_note
from src.services.audio_integration.audio_transcriber import transcribe
import os

class TranscribeAudioInput(BaseModel):
    audio_path: str
    note_name: str

def transcribe_audio(input: TranscribeAudioInput) -> None:
    """Transcribes an audio file and creates a new note with the transcription.

    Args:
        input: TranscribeAudioInput containing audio_path and note_name.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        Exception: If any other error occurs during transcription or note creation.
    """
    if not os.path.exists(input.audio_path):
        raise FileNotFoundError(f"Audio file not found: {input.audio_path}")

    try:
        transcription = transcribe(input.audio_path)
        write_note(input.note_name, transcription)
    except Exception as e:
        raise Exception(f"Error transcribing audio: {e}")
 link_audio_to_note:

Python
from pydantic import BaseModel
from src.core.obsidian_utils import read_note, write_note

class LinkAudioInput(BaseModel):
    audio_path: str
    note_name: str

def link_audio_to_note(input: LinkAudioInput) -> None:
    """Links an audio file to an existing note.

    Args:
        input: LinkAudioInput containing audio_path and note_name.

    Raises:
        FileNotFoundError: If the note does not exist.
        Exception: If any other error occurs during linking.
    """
    try:
        note_content = read_note(input.note_name)
        link_markdown = f"\n@Audio\n"
        updated_content = note_content + link_markdown
        write_note(input.note_name, updated_content)
    except FileNotFoundError:
        raise FileNotFoundError(f"Note not found: {input.note_name}")
    except Exception as e:
        raise Exception(f"Error linking audio: {e}")



2. content_tools.py

summarize_note:

Python
from pydantic import BaseModel
from src.core.obsidian_utils import read_note
from src.services.content_manipulation.manipulator import summarize_text

class SummarizeNoteInput(BaseModel):
    note_name: str

def summarize_note(input: SummarizeNoteInput) -> str:
    """Summarizes a note using the LLM.

    Args:
        input: SummarizeNoteInput containing note_name.

    Returns:
        str: The summary of the note.

    Raises:
        FileNotFoundError: If the note does not exist.
        Exception: If any error occurs during summarization.
    """
    try:
        note_content = read_note(input.note_name)
        summary = summarize_text(note_content)
        return summary
    except FileNotFoundError:
        raise FileNotFoundError(f"Note not found: {input.note_name}")
    except Exception as e:
        raise Exception(f"Error summarizing note: {e}")
 proofread_note:

Python
from pydantic import BaseModel
from src.core.obsidian_utils import read_note, write_note
from src.services.content_manipulation.manipulator import proofread_text

class ProofreadNoteInput(BaseModel):
    note_name: str

def proofread_note(input: ProofreadNoteInput) -> None:
    """Proofreads and corrects a note.

    Args:
        input: ProofreadNoteInput containing note_name.

    Raises:
        FileNotFoundError: If the note does not exist.
        Exception: If any error occurs during proofreading.
    """
    try:
        note_content = read_note(input.note_name)
        proofread_content = proofread_text(note_content)
        write_note(input.note_name, proofread_content)
    except FileNotFoundError:
        raise FileNotFoundError(f"Note not found: {input.note_name}")
    except Exception as e:
        raise Exception(f"Error proofreading note: {e}")




3. email_tools.py

import_email:

Python
from pydantic import BaseModel
from src.core.obsidian_utils import write_note
from src.services.email_integration.email_processor import process_email
import os

class ImportEmailInput(BaseModel):
    email_path: str
    note_name: str

def import_email(input: ImportEmailInput) -> None:
    """Imports an email and creates a new note.

    Args:
        input: ImportEmailInput containing email_path and note_name.

    Raises:
        FileNotFoundError: If the email file does not exist.
        Exception: If any error occurs during email processing or note creation.
    """
    if not os.path.exists(input.email_path):
        raise FileNotFoundError(f"Email file not found: {input.email_path}")

    try:
        email_content = process_email(input.email_path)
        write_note(input.note_name, email_content)
    except Exception as e:
        raise Exception(f"Error importing email: {e}")
 link_email_to_note:

Python
from pydantic import BaseModel
from src.core.obsidian_utils import read_note, write_note

class LinkEmailInput(BaseModel):
    email_path: str
    note_name: str

def link_email_to_note(input: LinkEmailInput) -> None:
    """Links an email to an existing note.

    Args:
        input: LinkEmailInput containing email_path and note_name.

    Raises:
        FileNotFoundError: If the note does not exist.
        Exception: If any error occurs during linking.
    """
    try:
        note_content = read_note(input.note_name)
        link_markdown = f"\n@Email\n"
        updated_content = note_content + link_markdown
        write_note(input.note_name, updated_content)
    except FileNotFoundError:
        raise FileNotFoundError(f"Note not found: {input.note_name}")
    except Exception as e:
        raise Exception(f"Error linking email: {e}")




4. folder_tools.py

create_folder:

Python
from pydantic import BaseModel
from src.core.obsidian_utils import create_folder

class CreateFolderInput(BaseModel):
    folder_path: str

def create_folder(input: CreateFolderInput) -> None:
    """Creates a new folder.

    Args:
        input: CreateFolderInput containing folder_path.

    Raises:
        Exception: If any error occurs during folder creation.
    """
    try:
        create_folder(input.folder_path)
    except Exception as e:
        raise Exception(f"Error creating folder: {e}")
 move_folder:

Python
from pydantic import BaseModel
from src.core.obsidian_utils import move_file
import os

class MoveFolderInput(BaseModel):
    source_path: str
    destination_path: str

def move_folder(input: MoveFolderInput) -> None:
    """Moves a folder.

    Args:
        input: MoveFolderInput containing source_path and destination_path.

    Raises:
        FileNotFoundError: If the source folder does not exist.
        Exception: If any error occurs during folder movement.
    """
    if not os.path.exists(input.source_path):
        raise FileNotFoundError(f"Source folder not found: {input.source_path}")

    try:
        move_file(input.source_path, input.destination_path)
    except Exception as e:
        raise Exception(f"Error moving folder: {e}")



5. hierarchy_tools.py

create_hierarchy:

Python
from pydantic import BaseModel
from src.core.obsidian_utils import create_note, write_note
import os

class CreateHierarchyInput(BaseModel):
    hierarchy_data: dict

def create_hierarchy(input: CreateHierarchyInput) -> None:
    """Creates a hierarchical structure of notes.

    Args:
        input: CreateHierarchyInput containing hierarchy_data (e.g., {"parent": {"child1": "content1", "child2": "content2"}}).

    Raises:
        Exception: If any error occurs during note creation.
    """
    def create_notes_recursive(data, parent_path=""):
        for note_name, content in data.items():
            note_path = os.path.join(parent_path, f"{note_name}.md")
            try:
                create_note(note_path)
                write_note(note_path, content)
                if isinstance(content, dict):
                    create_notes_recursive(content, os.path.dirname(note_path))
            except Exception as e:
                raise Exception(f"Error creating note {note_path}: {e}")

    create_notes_recursive(input.hierarchy_data)
 reorganize_hierarchy:

Python
from pydantic import BaseModel
from src.services.reorganization.reorganizer import reorganize_hierarchy as reorganize_vault_hierarchy

class ReorganizeHierarchyInput(BaseModel):
    root_note: str

def reorganize_hierarchy(input: ReorganizeHierarchyInput) -> None:
    """Reorganizes the hierarchical structure based on semantic analysis.

    Args:
        input: ReorganizeHierarchyInput containing root_note.

    Raises:
        Exception: If any error occurs during reorganization.
    """
    try:
        reorganize_vault_hierarchy(input.root_note)
    except Exception as e:
        raise Exception(f"Error reorganizing hierarchy: {e}")



6. indexing_tools.py

index_vault:

Python
from src.services.indexing.indexer import index_vault as index_all_notes

def index_vault() -> None:
    """Indexes the Obsidian vault.

    Raises:
        Exception: If any error occurs during indexing.
    """
    try:
        index_all_notes()
    except Exception as e:
        raise Exception(f"Error indexing vault: {e}")
 rag_query:

Python
from pydantic import BaseModel
from src.services.indexing.rag import rag_query as perform_rag_query

class RAGQueryInput(BaseModel):
    query: str

def rag_query(input: RAGQueryInput) -> str:
    """Performs a RAG query.

    Args:
        input: RAGQueryInput containing query.

    Returns:
        str: The response from the RAG query.

    Raises:
        Exception: If any error occurs during the RAG query.
    """
    try:
        return perform_rag_query(input.query)
    except Exception as e:
        raise Exception(f"Error performing RAG query: {e}")



7. note_tools.py

create_note:

Python
from pydantic import BaseModel
from src.core.obsidian_utils import create_note, write_note

class CreateNoteInput(BaseModel):
    note_name: str
    content: str

def create_note(input: CreateNoteInput) -> None:
    """Creates a new note.

    Args:
        input: CreateNoteInput containing note_name and content.

    Raises:
        Exception: If any error occurs during note creation.
    """
    try:
        create_note(input.note_name)
        write_note(input.note_name, input.content)
    except Exception as e:
        raise Exception(f"Error creating note: {e}")
 update_note:

Python
from pydantic import BaseModel
from src.core.obsidian_utils import write_note

class UpdateNoteInput(BaseModel):
    note_name: str
    content: str

def update_note(input: UpdateNoteInput) -> None:
    """Updates an existing note.

    Args:
        input: UpdateNoteInput containing note_name and content.

    Raises:
        FileNotFoundError: If the note does not exist.
        Exception: If any error occurs during note update.
    """
    try:
        write_note(input.note_name, input.content)
    except FileNotFoundError:
        raise FileNotFoundError(f"Note not found: {input.note_name}")
    except Exception as e:
        raise Exception(f"Error updating note: {e}")



8. reorganization_tools.py

merge_notes:

Python
from pydantic import BaseModel
from src.services.reorganization.reorganizer import merge_notes as merge_vault_notes

class MergeNotesInput(BaseModel):
    note1_name: str
    note2_name: str

def merge_notes(input: MergeNotesInput) -> None:
    """Merges two notes.

    Args:
        input: MergeNotesInput containing note1_name and note2_name.

    Raises:
        FileNotFoundError: If either note does not exist.
        Exception: If any error occurs during merging.
    """
    try:
        merge_vault_notes(input.note1_name, input.note2_name)
    except FileNotFoundError:
        raise FileNotFoundError("One or both notes not found.")
    except Exception as e:
        raise Exception(f"Error merging notes: {e}")
 split_note:

Python
from pydantic import BaseModel
from src.services.reorganization.reorganizer import split_note as split_vault_note

class SplitNoteInput(BaseModel):
    note_name: str
    split_criteria: str

def split_note(input: SplitNoteInput) -> None:
    """Splits a note into multiple notes.

    Args:
        input: SplitNoteInput containing note_name and split_criteria.

    Raises:
        FileNotFoundError: If the note does not exist.
        Exception: If any error occurs during splitting.
    """
    try:
        split_vault_note(input.note_name, input.split_criteria)
    except FileNotFoundError:
        raise FileNotFoundError(f"Note not found: {input.note_name}")
    except Exception as e:
        raise Exception(f"Error splitting note: {e}")




9. semantic_tools.py

analyze_note:

Python
from pydantic import BaseModel
from src.services.semantic_analysis.semantic_analyzer import analyze_note as analyze_vault_note

class AnalyzeNoteInput(BaseModel):
    note_name: str

def analyze_note(input: AnalyzeNoteInput) -> dict:
    """Analyzes a note semantically.

    Args:
        input: AnalyzeNoteInput containing note_name.

    Returns:
        dict: The semantic analysis results.

    Raises:
        FileNotFoundError: If the note does not exist.
        Exception: If any error occurs during analysis.
    """
    try:
        return analyze_vault_note(input.note_name)
    except FileNotFoundError:
        raise FileNotFoundError(f"Note not found: {input.note_name}")
    except Exception as e:
        raise Exception(f"Error analyzing note: {e}")
 find_related_notes:

Python
from pydantic import BaseModel
from src.services.semantic_analysis.semantic_analyzer import find_related_notes as find_vault_related_notes

class FindRelatedNotesInput(BaseModel):
    note_name: str

def find_related_notes(input: FindRelatedNotesInput) -> list:
    """Finds related notes based on semantic analysis.

    Args:
        input: FindRelatedNotesInput containing note_name.

    Returns:
        list: A list of related note names.

    Raises:
        FileNotFoundError: If the note does not exist.
        Exception: If any error occurs during finding related notes.
    """
    try:
        return find_vault_related_notes(input.note_name)
    except Exception as e:
        raise Exception(f"Error finding related notes: {e}")




10. tag_tools.py

Purpose: Tools for managing tags within the Obsidian vault.

Tools:

add_tag_to_note: Adds a tag to an existing note.

Python
from pydantic import BaseModel
from src.core.obsidian_utils import read_note, write_note, update_frontmatter
import yaml

class AddTagToNoteInput(BaseModel):
    note_name: str
    tag: str

def add_tag_to_note(input: AddTagToNoteInput) -> None:
    """Adds a tag to an existing note.

    Args:
        input: AddTagToNoteInput containing note_name and tag.

    Raises:
        FileNotFoundError: If the note does not exist.
        Exception: If any error occurs during tag addition.
    """
    try:
        note_content = read_note(input.note_name)
        frontmatter = yaml.safe_load(note_content.split('---')[1]) if '---' in note_content else {}
        tags = frontmatter.get('tags', [])
        if input.tag not in tags:
            tags.append(input.tag)
            frontmatter['tags'] = tags
            updated_content = update_frontmatter(note_content, frontmatter)
            write_note(input.note_name, updated_content)
    except FileNotFoundError:
        raise FileNotFoundError(f"Note not found: {input.note_name}")
    except Exception as e:
        raise Exception(f"Error adding tag: {e}")
 remove_tag_from_note: Removes a tag from an existing note.

Python
from pydantic import BaseModel
from src.core.obsidian_utils import read_note, write_note, update_frontmatter
import yaml

class RemoveTagFromNoteInput(BaseModel):
    note_name: str
    tag: str

def remove_tag_from_note(input: RemoveTagFromNoteInput) -> None:
    """Removes a tag from an existing note.

    Args:
        input: RemoveTagFromNoteInput containing note_name and tag.

    Raises:
        FileNotFoundError: If the note does not exist.
        Exception: If any error occurs during tag removal.
    """
    try:
        note_content = read_note(input.note_name)
        frontmatter = yaml.safe_load(note_content.split('---')[1]) if '---' in note_content else {}
        tags = frontmatter.get('tags', [])
        if input.tag in tags:
            tags.remove(input.tag)
            frontmatter['tags'] = tags
            updated_content = update_frontmatter(note_content, frontmatter)
            write_note(input.note_name, updated_content)
    except FileNotFoundError:
        raise FileNotFoundError(f"Note not found: {input.note_name}")
    except Exception as e:
        raise Exception(f"Error removing tag: {e}")




11. template_tools.py

Purpose: Tools for managing and applying note templates.

Tools:

apply_template_to_note: Applies a template to a note, either creating a new note or updating an existing one.

Python
from pydantic import BaseModel
from src.core.obsidian_utils import write_note, render_template
import os

class ApplyTemplateToNoteInput(BaseModel):
    note_name: str
    template_name: str
    template_data: dict

def apply_template_to_note(input: ApplyTemplateToNoteInput) -> None:
    """Applies a template to a note.

    Args:
        input: ApplyTemplateToNoteInput containing note_name, template_name, and template_data.

    Raises:
        FileNotFoundError: If the template does not exist.
        Exception: If any error occurs during template application.
    """
    try:
        template_path = os.path.join("src", "services", "note_management", "templates", f"{input.template_name}.j2")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {input.template_name}")

        rendered_content = render_template(input.template_name, input.template_data)
        write_note(input.note_name, rendered_content)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file not found: {input.template_name}")
    except Exception as e:
        raise Exception(f"Error applying template: {e}")
 validate_note_template: Validates if a note adheres to a specific template.

Python
from pydantic import BaseModel
from src.core.obsidian_utils import read_note, render_template
import os

class ValidateNoteTemplateInput(BaseModel):
    note_name: str
    template_name: str
    template_data: dict

def validate_note_template(input: ValidateNoteTemplateInput) -> bool:
    """Validates if a note adheres to a specific template.

    Args:
        input: ValidateNoteTemplateInput containing note_name, template_name, and template_data.

    Returns:
        bool: True if the note adheres to the template, False otherwise.

    Raises:
        FileNotFoundError: If the note or template does not exist.
        Exception: If any error occurs during validation.
    """
    try:
        note_content = read_note(input.note_name)
        template_path = os.path.join("src", "services", "note_management", "templates", f"{input.template_name}.j2")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {input.template_name}")

        rendered_template = render_template(input.template_name, input.template_data)
        return note_content == rendered_template
    except FileNotFoundError as e:
        raise FileNotFoundError(f"{e}")
    except Exception as e:
        raise Exception(f"Error validating template: {e}")

        Service Triggering Tool:

        A tool implementation for agent to manually trigger services to update the vault contents
