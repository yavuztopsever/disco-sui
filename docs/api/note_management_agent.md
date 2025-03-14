# NoteManagementAgent API Documentation

## Overview

The `NoteManagementAgent` class is a powerful tool for managing Obsidian vaults through natural language interaction. It provides comprehensive note management capabilities, including note creation, deletion, modification, semantic search, and organization.

## Class: NoteManagementAgent

### Constructor

```python
def __init__(self, vault_path: str)
```

Creates a new NoteManagementAgent instance.

**Parameters:**
- `vault_path` (str): Path to the Obsidian vault

**Raises:**
- `NoteManagementError`: If initialization fails

### Core Methods

#### process_message

```python
async def process_message(self, message: str) -> Dict[str, Any]
```

Processes a natural language message and returns an appropriate response.

**Parameters:**
- `message` (str): The user's message to process

**Returns:**
- `Dict[str, Any]`: Response containing:
  - `success` (bool): Whether the operation was successful
  - `response` (str): The formatted response message
  - `context` (str): The context of the request
  - `data` (Dict): Additional data from tool execution

**Raises:**
- `NoteManagementError`: If message processing fails

#### run

```python
async def run(self, task: str) -> Union[Dict[str, Any], str]
```

Runs the agent on a given task.

**Parameters:**
- `task` (str): The task to run

**Returns:**
- `Union[Dict[str, Any], str]`: The result of running the task

### Tool Management

#### get_tool_usage_stats

```python
def get_tool_usage_stats(self) -> Dict[str, Any]
```

Gets statistics about tool usage.

**Returns:**
- `Dict[str, Any]`: Tool usage statistics containing:
  - `total_calls` (int): Total number of calls to the tool
  - `successful_calls` (int): Number of successful calls
  - `failed_calls` (int): Number of failed calls
  - `last_used` (str): ISO format timestamp of last usage
  - `common_errors` (Dict[str, int]): Count of common error messages

### Internal Methods

#### _initialize_knowledge_base

```python
def _initialize_knowledge_base(self)
```

Initializes the knowledge base by indexing all notes.

**Raises:**
- `NoteManagementError`: If knowledge base initialization fails

#### _ensure_plugin_setup

```python
def _ensure_plugin_setup(self)
```

Ensures the Obsidian plugin directory structure exists.

**Raises:**
- `NoteManagementError`: If plugin setup fails

#### _track_tool_usage

```python
def _track_tool_usage(self, tool_name: str, success: bool, error: Optional[str] = None)
```

Tracks tool usage statistics.

**Parameters:**
- `tool_name` (str): Name of the tool
- `success` (bool): Whether the tool execution was successful
- `error` (Optional[str]): Error message if the tool execution failed

## Available Tools

The NoteManagementAgent comes with a comprehensive set of tools:

### Note Management Tools
- `CreateNoteTool`: Create new notes
- `DeleteNoteTool`: Delete existing notes
- `ListNotesTool`: List all notes in the vault
- `SearchNotesTool`: Search for notes
- `UpdateNoteTool`: Update existing notes

### Folder Management Tools
- `CreateFolderTool`: Create new folders
- `DeleteFolderTool`: Delete folders
- `MoveFolderTool`: Move folders
- `ListFoldersTool`: List all folders
- `GetFolderContentsTool`: Get folder contents

### Tag Management Tools
- `TagManagerTool`: Manage note tags

### Template Management Tools
- `CreateTemplateTool`: Create note templates
- `DeleteTemplateTool`: Delete templates
- `ListTemplatesTool`: List available templates
- `ApplyTemplateTool`: Apply templates to notes
- `GetTemplateContentTool`: Get template content

### Audio Processing Tools
- `TranscribeAudioTool`: Transcribe audio files
- `ListAudioFilesTool`: List audio files
- `GetTranscriptionNoteTool`: Get transcription notes

### Email Processing Tools
- `ProcessEmailTool`: Process email files
- `ListEmailFilesTool`: List email files
- `GetEmailNoteTool`: Get email notes

### Indexing and Search Tools
- `IndexNoteTool`: Index notes for search
- `ClusterNotesTool`: Cluster related notes

### Semantic Analysis Tools
- `AnalyzeRelationshipsTool`: Analyze note relationships
- `FindRelatedNotesTool`: Find related notes
- `GenerateKnowledgeGraphTool`: Generate knowledge graphs

### Vault Organization Tools
- `AnalyzeVaultStructureTool`: Analyze vault structure
- `ReorganizeVaultTool`: Reorganize vault
- `SuggestOrganizationTool`: Suggest organization improvements

### Hierarchy Management Tools
- `HierarchyManagerTool`: Manage note hierarchies

### Additional Tools
- `OpenNoteTool`: Open notes in Obsidian

## Error Handling

The NoteManagementAgent uses custom exceptions for error handling:

- `NoteManagementError`: Base error for note management operations
- `NoteNotFoundError`: When a note cannot be found
- `NoteAlreadyExistsError`: When trying to create a note that already exists
- `TemplateNotFoundError`: When a template cannot be found
- `FrontmatterError`: When there's an error with note frontmatter

## Logging

The agent uses Python's built-in logging module with the following levels:

- `INFO`: General operation information
- `WARNING`: Non-critical issues
- `ERROR`: Critical issues that affect functionality
- `DEBUG`: Detailed debugging information

## Example Usage

```python
# Initialize the agent
agent = NoteManagementAgent("/path/to/vault")

# Process a natural language request
response = await agent.process_message("Create a new note titled 'Meeting Notes' with today's date")

# Check the response
if response["success"]:
    print(response["response"])
else:
    print(f"Error: {response['error']}")

# Get tool usage statistics
stats = agent.get_tool_usage_stats()
print(f"Tool usage stats: {stats}")
```

## Best Practices

1. **Error Handling**
   - Always wrap agent calls in try-except blocks
   - Handle specific exceptions before general ones
   - Log errors appropriately

2. **Performance**
   - Initialize the agent once and reuse the instance
   - Use the knowledge base indexing feature
   - Monitor tool usage statistics

3. **Security**
   - Validate user input before processing
   - Use appropriate file permissions
   - Handle sensitive data securely

4. **Maintenance**
   - Monitor log files regularly
   - Check tool usage statistics for issues
   - Keep the knowledge base up to date 