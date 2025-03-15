import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.audio.processor import AudioProcessor
from src.core.config import Settings

@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.template_path = Path("templates")
    return settings

@pytest.fixture
def mock_template():
    template = MagicMock()
    template.render.return_value = "Rendered template"
    return template

@pytest.fixture
def audio_processor(mock_settings, mock_template):
    with patch("jinja2.Environment") as mock_env:
        mock_env.return_value.get_template.return_value = mock_template
        return AudioProcessor(settings=mock_settings)

def test_processor_initialization(audio_processor):
    """Test processor initialization."""
    assert audio_processor is not None
    assert audio_processor.settings is not None
    assert audio_processor.template_env is not None
    assert audio_processor.audio_template is not None

@pytest.mark.asyncio
async def test_process_transcription(audio_processor):
    """Test transcription processing."""
    transcription = {
        "text": "This is a test transcription with a task: TODO review meeting notes",
        "duration": 120.0,
        "language": "en",
        "segments": [
            {"start": 0, "end": 5, "text": "This is a test"},
            {"start": 5, "end": 10, "text": "transcription with a task:"},
            {"start": 10, "end": 15, "text": "TODO review meeting notes"}
        ]
    }
    
    result = await audio_processor.process_transcription(transcription)
    assert result is not None
    assert "tasks" in result
    assert "summary" in result
    assert "suggestions" in result

def test_extract_tasks(audio_processor):
    """Test task extraction from text."""
    text = """
    Here are some tasks:
    TODO: Review the document
    TASK: Update the presentation
    ACTION ITEM: Send follow-up email
    """
    
    tasks = audio_processor._extract_tasks(text)
    assert len(tasks) == 3
    assert "Review the document" in tasks
    assert "Update the presentation" in tasks
    assert "Send follow-up email" in tasks

@pytest.mark.asyncio
async def test_generate_summary(audio_processor):
    """Test summary generation."""
    text = "This is a test transcription that should be summarized."
    summary = await audio_processor._generate_summary(text)
    assert summary is not None
    assert isinstance(summary, str)

@pytest.mark.asyncio
async def test_generate_suggestions(audio_processor):
    """Test suggestion generation."""
    text = "This is a test transcription that should generate suggestions."
    suggestions = await audio_processor._generate_suggestions(text)
    assert suggestions is not None
    assert isinstance(suggestions, list)

def test_generate_note_content(audio_processor, mock_template):
    """Test note content generation."""
    audio_file = Path("test/audio.mp3")
    transcription_data = {
        "text": "Test transcription",
        "duration": 120.0,
        "language": "en",
        "segments": []
    }
    metadata = {
        "title": "Test Audio",
        "created_at": "2024-03-15"
    }
    
    content = audio_processor.generate_note_content(
        audio_file,
        transcription_data,
        metadata
    )
    assert content == "Rendered template"
    mock_template.render.assert_called_once()

@pytest.mark.asyncio
async def test_search_audio_notes(audio_processor):
    """Test audio note searching."""
    query = "test query"
    results = await audio_processor.search_audio_notes(query)
    assert isinstance(results, list)

@pytest.mark.asyncio
async def test_get_audio_metadata(audio_processor):
    """Test getting audio metadata."""
    note_path = "test/note.md"
    metadata = await audio_processor.get_audio_metadata(note_path)
    assert isinstance(metadata, dict)

@pytest.mark.asyncio
async def test_update_categories(audio_processor):
    """Test updating categories."""
    note_path = "test/note.md"
    categories = ["meeting", "important"]
    await audio_processor.update_categories(note_path, categories)

@pytest.mark.asyncio
async def test_cleanup_old_audio(audio_processor):
    """Test cleaning up old audio files."""
    await audio_processor.cleanup_old_audio(days=30) 