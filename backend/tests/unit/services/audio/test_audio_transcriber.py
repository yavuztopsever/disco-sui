import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.audio.transcriber import AudioTranscriber
from src.core.config import Settings
from src.core.exceptions import AudioTranscriptionError

@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.whisper_model_name = "base"
    return settings

@pytest.fixture
def mock_whisper():
    with patch("whisper.load_model") as mock_load:
        mock_model = MagicMock()
        mock_load.return_value = mock_model
        yield mock_model

@pytest.fixture
def audio_transcriber(mock_settings, mock_whisper):
    with patch("torch.cuda.is_available", return_value=False):
        return AudioTranscriber(settings=mock_settings)

def test_transcriber_initialization(audio_transcriber):
    """Test transcriber initialization."""
    assert audio_transcriber is not None
    assert audio_transcriber.settings is not None
    assert audio_transcriber.model is not None

@pytest.mark.asyncio
async def test_transcribe_audio(audio_transcriber, mock_whisper):
    """Test audio transcription."""
    audio_file = Path("test/audio.mp3")
    mock_whisper.transcribe.return_value = {
        "text": "This is a test transcription",
        "segments": [
            {"start": 0, "end": 5, "text": "This is a test"},
            {"start": 5, "end": 10, "text": "transcription"}
        ],
        "language": "en"
    }
    
    result = await audio_transcriber.transcribe_audio(audio_file)
    assert result is not None
    assert result["text"] == "This is a test transcription"
    assert len(result["segments"]) == 2
    assert result["language"] == "en"

@pytest.mark.asyncio
async def test_transcribe_segment(audio_transcriber, mock_whisper):
    """Test segment transcription."""
    audio_file = Path("test/audio.mp3")
    start_time = 0.0
    end_time = 5.0
    mock_whisper.transcribe.return_value = {
        "text": "This is a test segment",
        "segments": [{"start": 0, "end": 5, "text": "This is a test segment"}],
        "language": "en"
    }
    
    result = await audio_transcriber.transcribe_segment(audio_file, start_time, end_time)
    assert result is not None
    assert result["text"] == "This is a test segment"
    assert len(result["segments"]) == 1

@pytest.mark.asyncio
async def test_detect_language(audio_transcriber, mock_whisper):
    """Test language detection."""
    audio_file = Path("test/audio.mp3")
    mock_whisper.detect_language.return_value = "en"
    
    result = await audio_transcriber.detect_language(audio_file)
    assert result == "en"

@pytest.mark.asyncio
async def test_generate_timestamps(audio_transcriber, mock_whisper):
    """Test timestamp generation."""
    audio_file = Path("test/audio.mp3")
    mock_whisper.transcribe.return_value = {
        "segments": [
            {"start": 0, "end": 5, "text": "First segment"},
            {"start": 5, "end": 10, "text": "Second segment"}
        ]
    }
    
    result = await audio_transcriber.generate_timestamps(audio_file)
    assert len(result) == 2
    assert all("start" in segment and "end" in segment for segment in result)

@pytest.mark.asyncio
async def test_error_handling_invalid_audio(audio_transcriber, mock_whisper):
    """Test error handling for invalid audio."""
    audio_file = Path("test/invalid.mp3")
    mock_whisper.transcribe.side_effect = Exception("Invalid audio file")
    
    with pytest.raises(AudioTranscriptionError):
        await audio_transcriber.transcribe_audio(audio_file)

@pytest.mark.asyncio
async def test_error_handling_unsupported_language(audio_transcriber, mock_whisper):
    """Test error handling for unsupported language."""
    audio_file = Path("test/audio.mp3")
    mock_whisper.detect_language.side_effect = Exception("Unsupported language")
    
    with pytest.raises(AudioTranscriptionError):
        await audio_transcriber.detect_language(audio_file)

def test_get_transcription_config(audio_transcriber):
    """Test getting transcription configuration."""
    config = audio_transcriber.get_transcription_config()
    assert isinstance(config, dict)
    assert "model_name" in config
    assert "device" in config

def test_set_transcription_config(audio_transcriber):
    """Test setting transcription configuration."""
    new_config = {
        "model_name": "large",
        "device": "cpu"
    }
    audio_transcriber.set_transcription_config(new_config)
    assert audio_transcriber.settings.whisper_model_name == "large" 