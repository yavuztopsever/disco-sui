import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.audio.audio_service import AudioService, AudioConfig

@pytest.fixture
def mock_config():
    return {
        "watch_directory": "/tmp/audio/watch",
        "output_directory": "/tmp/audio/output",
        "supported_formats": ["mp3", "wav", "m4a", "ogg"],
        "check_interval": 300,
        "whisper_model": "base",
        "batch_size": 16,
        "device": "cpu",
        "language": "en"
    }

@pytest.fixture
def mock_processor():
    return MagicMock()

@pytest.fixture
def mock_transcriber():
    return MagicMock()

@pytest.fixture
def audio_service(mock_config, mock_processor, mock_transcriber):
    with patch("pathlib.Path.mkdir"):  # Mock directory creation
        return AudioService(
            processor=mock_processor,
            transcriber=mock_transcriber,
            config=mock_config
        )

def test_audio_service_initialization(audio_service):
    """Test audio service initialization."""
    assert audio_service is not None
    assert audio_service.processor is not None
    assert audio_service.transcriber is not None
    assert isinstance(audio_service.config_model, AudioConfig)
    assert audio_service.config_model.watch_directory == Path("/tmp/audio/watch")
    assert audio_service.config_model.output_directory == Path("/tmp/audio/output")

@pytest.mark.asyncio
async def test_process_audio(audio_service, mock_processor):
    """Test audio processing."""
    audio_path = "test/audio.mp3"
    mock_processor.process_audio.return_value = {
        "success": True,
        "duration": 120,
        "format": "mp3",
        "channels": 2,
        "sample_rate": 44100
    }
    
    result = await audio_service.process_audio(audio_path)
    assert result["success"] is True
    assert result["duration"] == 120
    assert result["format"] == "mp3"

@pytest.mark.asyncio
async def test_transcribe_audio(audio_service, mock_transcriber):
    """Test audio transcription."""
    audio_path = "test/audio.mp3"
    mock_transcriber.transcribe.return_value = {
        "success": True,
        "text": "This is a test transcription",
        "language": "en",
        "duration": 120
    }
    
    result = await audio_service.transcribe_audio(audio_path)
    assert result["success"] is True
    assert "text" in result
    assert result["language"] == "en"

@pytest.mark.asyncio
async def test_extract_metadata(audio_service, mock_processor):
    """Test metadata extraction."""
    audio_path = "test/audio.mp3"
    mock_processor.extract_metadata.return_value = {
        "success": True,
        "metadata": {
            "title": "Test Audio",
            "artist": "Test Artist",
            "duration": 120
        }
    }
    
    result = await audio_service.extract_metadata(audio_path)
    assert result["success"] is True
    assert "metadata" in result
    assert result["metadata"]["title"] == "Test Audio"

@pytest.mark.asyncio
async def test_convert_format(audio_service, mock_processor):
    """Test format conversion."""
    audio_path = "test/audio.mp3"
    target_format = "wav"
    mock_processor.convert_format.return_value = {
        "success": True,
        "format": target_format,
        "output_path": "test/audio.wav"
    }
    
    result = await audio_service.convert_format(audio_path, target_format)
    assert result["success"] is True
    assert result["format"] == target_format

@pytest.mark.asyncio
async def test_split_audio(audio_service, mock_processor):
    """Test audio splitting."""
    audio_path = "test/audio.mp3"
    segments = [{"start": 0, "end": 30}, {"start": 30, "end": 60}]
    mock_processor.split_audio.return_value = {
        "success": True,
        "segments": [
            {"path": "test/segment_1.mp3"},
            {"path": "test/segment_2.mp3"}
        ]
    }
    
    result = await audio_service.split_audio(audio_path, segments)
    assert result["success"] is True
    assert len(result["segments"]) == 2

@pytest.mark.asyncio
async def test_merge_audio(audio_service, mock_processor):
    """Test audio merging."""
    audio_paths = ["test/audio1.mp3", "test/audio2.mp3"]
    mock_processor.merge_audio.return_value = {
        "success": True,
        "output_path": "test/merged.mp3"
    }
    
    result = await audio_service.merge_audio(audio_paths)
    assert result["success"] is True
    assert "output_path" in result

@pytest.mark.asyncio
async def test_analyze_audio(audio_service, mock_processor):
    """Test audio analysis."""
    audio_path = "test/audio.mp3"
    mock_processor.analyze_audio.return_value = {
        "success": True,
        "analysis": {
            "duration": 120,
            "bit_rate": 192000,
            "sample_rate": 44100
        }
    }
    
    result = await audio_service.analyze_audio(audio_path)
    assert result["success"] is True
    assert "analysis" in result

@pytest.mark.asyncio
async def test_detect_silence(audio_service, mock_processor):
    """Test silence detection."""
    audio_path = "test/audio.mp3"
    mock_processor.detect_silence.return_value = {
        "success": True,
        "silent_regions": [
            {"start": 10, "end": 15},
            {"start": 30, "end": 35}
        ]
    }
    
    result = await audio_service.detect_silence(audio_path)
    assert result["success"] is True
    assert len(result["silent_regions"]) == 2

@pytest.mark.asyncio
async def test_normalize_audio(audio_service, mock_processor):
    """Test audio normalization."""
    audio_path = "test/audio.mp3"
    target_level = -18
    mock_processor.normalize_audio.return_value = {
        "success": True,
        "output_path": "test/normalized.mp3",
        "peak_level": target_level
    }
    
    result = await audio_service.normalize_audio(audio_path, target_level)
    assert result["success"] is True
    assert result["peak_level"] == target_level

@pytest.mark.asyncio
async def test_batch_process(audio_service, mock_processor):
    """Test batch processing."""
    audio_paths = ["test/audio1.mp3", "test/audio2.mp3"]
    mock_processor.batch_process.return_value = {
        "success": True,
        "results": [
            {"path": "test/audio1.mp3", "success": True},
            {"path": "test/audio2.mp3", "success": True}
        ]
    }
    
    result = await audio_service.batch_process(audio_paths)
    assert result["success"] is True
    assert len(result["results"]) == 2

@pytest.mark.asyncio
async def test_validate_audio(audio_service, mock_processor):
    """Test audio validation."""
    audio_path = "test/audio.mp3"
    mock_processor.validate_audio.return_value = {
        "success": True,
        "valid": True,
        "format_valid": True,
        "codec_valid": True
    }
    
    result = await audio_service.validate_audio(audio_path)
    assert result["success"] is True
    assert result["valid"] is True

@pytest.mark.asyncio
async def test_error_handling(audio_service, mock_processor):
    """Test error handling."""
    audio_path = "test/invalid.mp3"
    mock_processor.process_audio.side_effect = Exception("Test error")
    
    result = await audio_service.process_audio(audio_path)
    assert result["success"] is False
    assert "error" in result

@pytest.mark.asyncio
async def test_get_supported_formats(audio_service):
    """Test getting supported formats."""
    formats = await audio_service.get_supported_formats()
    assert isinstance(formats, list)
    assert all(isinstance(fmt, str) for fmt in formats)

@pytest.mark.asyncio
async def test_get_transcription_languages(audio_service, mock_transcriber):
    """Test getting transcription languages."""
    mock_transcriber.get_supported_languages.return_value = ["en", "es", "fr"]
    
    languages = await audio_service.get_transcription_languages()
    assert isinstance(languages, list)
    assert "en" in languages 