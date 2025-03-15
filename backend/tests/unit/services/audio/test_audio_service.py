import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.audio.audio_service import AudioService

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_processor():
    return MagicMock()

@pytest.fixture
def mock_transcriber():
    return MagicMock()

@pytest.fixture
def audio_service(mock_context, mock_processor, mock_transcriber):
    return AudioService(
        context=mock_context,
        processor=mock_processor,
        transcriber=mock_transcriber
    )

def test_audio_service_initialization(audio_service):
    """Test audio service initialization."""
    assert audio_service is not None
    assert audio_service.processor is not None
    assert audio_service.transcriber is not None

def test_process_audio(audio_service, mock_processor):
    """Test audio processing."""
    audio_path = "test/audio.mp3"
    mock_processor.process_audio.return_value = {
        "success": True,
        "duration": 120,
        "format": "mp3",
        "channels": 2,
        "sample_rate": 44100
    }
    
    result = audio_service.process_audio(audio_path)
    assert result["success"] is True
    assert result["duration"] == 120
    assert result["format"] == "mp3"

def test_transcribe_audio(audio_service, mock_transcriber):
    """Test audio transcription."""
    audio_path = "test/audio.mp3"
    mock_transcriber.transcribe.return_value = {
        "success": True,
        "text": "This is a test transcription",
        "segments": [
            {"start": 0, "end": 2, "text": "This is"},
            {"start": 2, "end": 4, "text": "a test transcription"}
        ]
    }
    
    result = audio_service.transcribe_audio(audio_path)
    assert result["success"] is True
    assert "text" in result
    assert len(result["segments"]) == 2

def test_extract_metadata(audio_service, mock_processor):
    """Test metadata extraction."""
    audio_path = "test/audio.mp3"
    mock_processor.extract_metadata.return_value = {
        "success": True,
        "metadata": {
            "title": "Test Audio",
            "artist": "Test Artist",
            "album": "Test Album",
            "year": "2024"
        }
    }
    
    result = audio_service.extract_metadata(audio_path)
    assert result["success"] is True
    assert result["metadata"]["title"] == "Test Audio"
    assert result["metadata"]["artist"] == "Test Artist"

def test_convert_format(audio_service, mock_processor):
    """Test audio format conversion."""
    audio_path = "test/audio.mp3"
    target_format = "wav"
    mock_processor.convert_format.return_value = {
        "success": True,
        "output_path": "test/audio.wav",
        "format": "wav"
    }
    
    result = audio_service.convert_format(audio_path, target_format)
    assert result["success"] is True
    assert result["format"] == target_format
    assert result["output_path"].endswith(".wav")

def test_split_audio(audio_service, mock_processor):
    """Test audio splitting."""
    audio_path = "test/audio.mp3"
    segments = [
        {"start": 0, "end": 30},
        {"start": 30, "end": 60}
    ]
    mock_processor.split_audio.return_value = {
        "success": True,
        "segments": [
            {"path": "test/audio_1.mp3", "start": 0, "end": 30},
            {"path": "test/audio_2.mp3", "start": 30, "end": 60}
        ]
    }
    
    result = audio_service.split_audio(audio_path, segments)
    assert result["success"] is True
    assert len(result["segments"]) == 2

def test_merge_audio(audio_service, mock_processor):
    """Test audio merging."""
    audio_paths = ["test/audio1.mp3", "test/audio2.mp3"]
    mock_processor.merge_audio.return_value = {
        "success": True,
        "output_path": "test/merged.mp3",
        "duration": 240
    }
    
    result = audio_service.merge_audio(audio_paths)
    assert result["success"] is True
    assert "output_path" in result
    assert result["duration"] == 240

def test_analyze_audio(audio_service, mock_processor):
    """Test audio analysis."""
    audio_path = "test/audio.mp3"
    mock_processor.analyze_audio.return_value = {
        "success": True,
        "analysis": {
            "peak_amplitude": 0.8,
            "rms_level": -18,
            "noise_floor": -60,
            "dynamic_range": 42
        }
    }
    
    result = audio_service.analyze_audio(audio_path)
    assert result["success"] is True
    assert "analysis" in result
    assert "peak_amplitude" in result["analysis"]

def test_detect_silence(audio_service, mock_processor):
    """Test silence detection."""
    audio_path = "test/audio.mp3"
    mock_processor.detect_silence.return_value = {
        "success": True,
        "silent_regions": [
            {"start": 10, "end": 15},
            {"start": 30, "end": 35}
        ]
    }
    
    result = audio_service.detect_silence(audio_path)
    assert result["success"] is True
    assert len(result["silent_regions"]) == 2

def test_normalize_audio(audio_service, mock_processor):
    """Test audio normalization."""
    audio_path = "test/audio.mp3"
    target_level = -18
    mock_processor.normalize_audio.return_value = {
        "success": True,
        "output_path": "test/normalized.mp3",
        "peak_level": -18
    }
    
    result = audio_service.normalize_audio(audio_path, target_level)
    assert result["success"] is True
    assert result["peak_level"] == target_level

def test_batch_process(audio_service, mock_processor):
    """Test batch audio processing."""
    audio_paths = ["test/audio1.mp3", "test/audio2.mp3"]
    mock_processor.batch_process.return_value = {
        "success": True,
        "results": [
            {"path": "test/audio1.mp3", "success": True},
            {"path": "test/audio2.mp3", "success": True}
        ]
    }
    
    result = audio_service.batch_process(audio_paths)
    assert result["success"] is True
    assert len(result["results"]) == 2

def test_validate_audio(audio_service, mock_processor):
    """Test audio validation."""
    audio_path = "test/audio.mp3"
    mock_processor.validate_audio.return_value = {
        "success": True,
        "valid": True,
        "format_valid": True,
        "codec_valid": True,
        "duration_valid": True
    }
    
    result = audio_service.validate_audio(audio_path)
    assert result["success"] is True
    assert result["valid"] is True

def test_error_handling(audio_service, mock_processor):
    """Test error handling."""
    audio_path = "test/nonexistent.mp3"
    mock_processor.process_audio.side_effect = Exception("File not found")
    
    result = audio_service.process_audio(audio_path)
    assert result["success"] is False
    assert "error" in result

def test_get_supported_formats(audio_service):
    """Test getting supported formats."""
    result = audio_service.get_supported_formats()
    assert result["success"] is True
    assert isinstance(result["formats"], list)
    assert "mp3" in result["formats"]
    assert "wav" in result["formats"]

def test_get_transcription_languages(audio_service, mock_transcriber):
    """Test getting supported transcription languages."""
    mock_transcriber.get_supported_languages.return_value = {
        "success": True,
        "languages": ["en", "es", "fr", "de"]
    }
    
    result = audio_service.get_transcription_languages()
    assert result["success"] is True
    assert isinstance(result["languages"], list)
    assert "en" in result["languages"] 