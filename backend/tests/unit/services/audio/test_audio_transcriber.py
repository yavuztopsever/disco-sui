import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.audio.audio_transcriber import AudioTranscriber

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_processor():
    return MagicMock()

@pytest.fixture
def mock_model():
    return MagicMock()

@pytest.fixture
def audio_transcriber(mock_context, mock_processor, mock_model):
    return AudioTranscriber(
        context=mock_context,
        processor=mock_processor,
        model=mock_model
    )

def test_transcriber_initialization(audio_transcriber):
    """Test transcriber initialization."""
    assert audio_transcriber is not None
    assert audio_transcriber.processor is not None
    assert audio_transcriber.model is not None

def test_transcribe_audio(audio_transcriber, mock_model):
    """Test audio transcription."""
    audio_path = "test/audio.mp3"
    mock_model.transcribe.return_value = {
        "success": True,
        "text": "This is a test transcription",
        "segments": [
            {"start": 0, "end": 2, "text": "This is"},
            {"start": 2, "end": 4, "text": "a test transcription"}
        ],
        "language": "en"
    }
    
    result = audio_transcriber.transcribe(audio_path)
    assert result["success"] is True
    assert "text" in result
    assert len(result["segments"]) == 2
    assert result["language"] == "en"

def test_transcribe_with_timestamps(audio_transcriber, mock_model):
    """Test transcription with timestamps."""
    audio_path = "test/audio.mp3"
    mock_model.transcribe_detailed.return_value = {
        "success": True,
        "segments": [
            {
                "start": 0.0,
                "end": 2.0,
                "text": "This is",
                "confidence": 0.95
            },
            {
                "start": 2.0,
                "end": 4.0,
                "text": "a test transcription",
                "confidence": 0.92
            }
        ]
    }
    
    result = audio_transcriber.transcribe_with_timestamps(audio_path)
    assert result["success"] is True
    assert len(result["segments"]) == 2
    assert all("confidence" in segment for segment in result["segments"])

def test_detect_language(audio_transcriber, mock_model):
    """Test language detection."""
    audio_path = "test/audio.mp3"
    mock_model.detect_language.return_value = {
        "success": True,
        "language": "en",
        "confidence": 0.98
    }
    
    result = audio_transcriber.detect_language(audio_path)
    assert result["success"] is True
    assert result["language"] == "en"
    assert result["confidence"] > 0.9

def test_diarize_speakers(audio_transcriber, mock_model):
    """Test speaker diarization."""
    audio_path = "test/audio.mp3"
    mock_model.diarize.return_value = {
        "success": True,
        "speakers": [
            {"id": "speaker_1", "segments": [(0, 2), (4, 6)]},
            {"id": "speaker_2", "segments": [(2, 4), (6, 8)]}
        ]
    }
    
    result = audio_transcriber.diarize_speakers(audio_path)
    assert result["success"] is True
    assert len(result["speakers"]) == 2
    assert all("segments" in speaker for speaker in result["speakers"])

def test_batch_transcribe(audio_transcriber, mock_model):
    """Test batch transcription."""
    audio_paths = ["test/audio1.mp3", "test/audio2.mp3"]
    mock_model.batch_transcribe.return_value = {
        "success": True,
        "results": [
            {
                "path": "test/audio1.mp3",
                "text": "First transcription",
                "success": True
            },
            {
                "path": "test/audio2.mp3",
                "text": "Second transcription",
                "success": True
            }
        ]
    }
    
    result = audio_transcriber.batch_transcribe(audio_paths)
    assert result["success"] is True
    assert len(result["results"]) == 2
    assert all(r["success"] for r in result["results"])

def test_transcribe_segment(audio_transcriber, mock_model):
    """Test segment transcription."""
    audio_path = "test/audio.mp3"
    segment = {"start": 10, "end": 20}
    mock_model.transcribe_segment.return_value = {
        "success": True,
        "text": "Segment transcription",
        "start": 10,
        "end": 20,
        "confidence": 0.94
    }
    
    result = audio_transcriber.transcribe_segment(audio_path, segment)
    assert result["success"] is True
    assert "text" in result
    assert result["start"] == segment["start"]
    assert result["end"] == segment["end"]

def test_get_supported_languages(audio_transcriber, mock_model):
    """Test getting supported languages."""
    mock_model.get_supported_languages.return_value = {
        "success": True,
        "languages": ["en", "es", "fr", "de", "it"]
    }
    
    result = audio_transcriber.get_supported_languages()
    assert result["success"] is True
    assert isinstance(result["languages"], list)
    assert len(result["languages"]) > 0

def test_validate_audio_format(audio_transcriber, mock_processor):
    """Test audio format validation."""
    audio_path = "test/audio.mp3"
    mock_processor.validate_format.return_value = {
        "success": True,
        "valid": True,
        "format": "mp3",
        "supported": True
    }
    
    result = audio_transcriber.validate_audio_format(audio_path)
    assert result["success"] is True
    assert result["valid"] is True
    assert result["supported"] is True

def test_get_model_info(audio_transcriber, mock_model):
    """Test getting model information."""
    mock_model.get_info.return_value = {
        "success": True,
        "name": "whisper-large-v3",
        "languages": ["en", "es", "fr"],
        "features": ["transcription", "translation"]
    }
    
    result = audio_transcriber.get_model_info()
    assert result["success"] is True
    assert "name" in result
    assert "languages" in result
    assert "features" in result

def test_translate_transcription(audio_transcriber, mock_model):
    """Test transcription translation."""
    text = "This is a test"
    target_language = "es"
    mock_model.translate.return_value = {
        "success": True,
        "text": "Esto es una prueba",
        "source_language": "en",
        "target_language": "es"
    }
    
    result = audio_transcriber.translate_transcription(text, target_language)
    assert result["success"] is True
    assert "text" in result
    assert result["target_language"] == target_language

def test_error_handling_invalid_audio(audio_transcriber, mock_model):
    """Test error handling for invalid audio."""
    audio_path = "test/invalid.mp3"
    mock_model.transcribe.side_effect = Exception("Invalid audio file")
    
    result = audio_transcriber.transcribe(audio_path)
    assert result["success"] is False
    assert "error" in result

def test_error_handling_unsupported_language(audio_transcriber, mock_model):
    """Test error handling for unsupported language."""
    text = "Test text"
    target_language = "unsupported"
    mock_model.translate.side_effect = Exception("Unsupported language")
    
    result = audio_transcriber.translate_transcription(text, target_language)
    assert result["success"] is False
    assert "error" in result

def test_get_transcription_config(audio_transcriber):
    """Test getting transcription configuration."""
    result = audio_transcriber.get_transcription_config()
    assert result["success"] is True
    assert "model_type" in result
    assert "supported_formats" in result
    assert "max_duration" in result

def test_set_transcription_config(audio_transcriber):
    """Test setting transcription configuration."""
    config = {
        "model_type": "whisper-large-v3",
        "language": "en",
        "timestamp_method": "word"
    }
    
    result = audio_transcriber.set_transcription_config(config)
    assert result["success"] is True
    assert result["config"]["model_type"] == config["model_type"]
    assert result["config"]["language"] == config["language"] 