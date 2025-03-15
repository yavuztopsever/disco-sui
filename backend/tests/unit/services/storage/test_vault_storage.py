import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from src.services.storage.vault_storage import VaultStorage

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_fs():
    return MagicMock()

@pytest.fixture
def vault_storage(mock_context, mock_fs):
    with patch("src.services.storage.vault_storage.os", mock_fs):
        return VaultStorage(
            context=mock_context,
            vault_path="test/vault"
        )

def test_vault_storage_initialization(vault_storage):
    """Test vault storage initialization."""
    assert vault_storage is not None
    assert vault_storage.vault_path == "test/vault"

def test_create_note(vault_storage):
    """Test note creation."""
    note_path = "test/note.md"
    content = "# Test Note\nContent"
    
    with patch("builtins.open", mock_open()) as mock_file:
        result = vault_storage.create_note(note_path, content)
        mock_file.assert_called_once_with(note_path, "w", encoding="utf-8")
        mock_file().write.assert_called_once_with(content)
    
    assert result["success"] is True
    assert result["path"] == note_path

def test_read_note(vault_storage):
    """Test note reading."""
    note_path = "test/note.md"
    content = "# Test Note\nContent"
    
    with patch("builtins.open", mock_open(read_data=content)) as mock_file:
        result = vault_storage.read_note(note_path)
        mock_file.assert_called_once_with(note_path, "r", encoding="utf-8")
    
    assert result["success"] is True
    assert result["content"] == content

def test_update_note(vault_storage):
    """Test note updating."""
    note_path = "test/note.md"
    new_content = "# Updated Note\nNew content"
    
    with patch("builtins.open", mock_open()) as mock_file:
        result = vault_storage.update_note(note_path, new_content)
        mock_file.assert_called_once_with(note_path, "w", encoding="utf-8")
        mock_file().write.assert_called_once_with(new_content)
    
    assert result["success"] is True
    assert result["path"] == note_path

def test_delete_note(vault_storage, mock_fs):
    """Test note deletion."""
    note_path = "test/note.md"
    mock_fs.path.exists.return_value = True
    
    result = vault_storage.delete_note(note_path)
    mock_fs.remove.assert_called_once_with(note_path)
    assert result["success"] is True

def test_list_notes(vault_storage, mock_fs):
    """Test listing notes."""
    mock_fs.walk.return_value = [
        ("test/vault", ["folder1"], ["note1.md"]),
        ("test/vault/folder1", [], ["note2.md"])
    ]
    
    result = vault_storage.list_notes()
    assert result["success"] is True
    assert len(result["notes"]) == 2
    assert "note1.md" in [Path(note).name for note in result["notes"]]

def test_move_note(vault_storage, mock_fs):
    """Test moving note."""
    source = "old/path/note.md"
    target = "new/path/note.md"
    mock_fs.path.exists.return_value = True
    
    result = vault_storage.move_note(source, target)
    mock_fs.rename.assert_called_once_with(source, target)
    assert result["success"] is True
    assert result["new_path"] == target

def test_copy_note(vault_storage, mock_fs):
    """Test copying note."""
    source = "source/note.md"
    target = "target/note.md"
    content = "# Test Note\nContent"
    
    with patch("builtins.open", mock_open(read_data=content)) as mock_file:
        result = vault_storage.copy_note(source, target)
    
    assert result["success"] is True
    assert result["new_path"] == target

def test_create_folder(vault_storage, mock_fs):
    """Test folder creation."""
    folder_path = "test/new_folder"
    mock_fs.path.exists.return_value = False
    
    result = vault_storage.create_folder(folder_path)
    mock_fs.makedirs.assert_called_once_with(folder_path, exist_ok=True)
    assert result["success"] is True
    assert result["path"] == folder_path

def test_delete_folder(vault_storage, mock_fs):
    """Test folder deletion."""
    folder_path = "test/folder"
    mock_fs.path.exists.return_value = True
    
    result = vault_storage.delete_folder(folder_path)
    mock_fs.rmdir.assert_called_once_with(folder_path)
    assert result["success"] is True

def test_list_folders(vault_storage, mock_fs):
    """Test listing folders."""
    mock_fs.walk.return_value = [
        ("test/vault", ["folder1", "folder2"], []),
        ("test/vault/folder1", ["subfolder"], []),
        ("test/vault/folder2", [], [])
    ]
    
    result = vault_storage.list_folders()
    assert result["success"] is True
    assert len(result["folders"]) == 3

def test_error_handling_file_not_found(vault_storage):
    """Test error handling for file not found."""
    note_path = "nonexistent/note.md"
    
    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.side_effect = FileNotFoundError()
        result = vault_storage.read_note(note_path)
    
    assert result["success"] is False
    assert "error" in result

def test_search_notes(vault_storage):
    """Test note searching."""
    query = "test"
    mock_results = [
        {"path": "note1.md", "score": 0.9},
        {"path": "note2.md", "score": 0.7}
    ]
    
    with patch("src.services.storage.vault_storage.search_notes") as mock_search:
        mock_search.return_value = {"success": True, "results": mock_results}
        result = vault_storage.search_notes(query)
    
    assert result["success"] is True
    assert len(result["results"]) == 2

def test_get_note_metadata(vault_storage):
    """Test getting note metadata."""
    note_path = "test/note.md"
    mock_fs.path.getmtime.return_value = 1234567890
    mock_fs.path.getsize.return_value = 1024
    
    result = vault_storage.get_note_metadata(note_path)
    assert result["success"] is True
    assert "modified_time" in result["metadata"]
    assert "size" in result["metadata"]

def test_validate_note_path(vault_storage, mock_fs):
    """Test note path validation."""
    valid_path = "test/valid_note.md"
    invalid_path = "../invalid/path.md"
    
    # Test valid path
    result = vault_storage.validate_note_path(valid_path)
    assert result["success"] is True
    assert result["valid"] is True
    
    # Test invalid path
    result = vault_storage.validate_note_path(invalid_path)
    assert result["success"] is True
    assert result["valid"] is False 