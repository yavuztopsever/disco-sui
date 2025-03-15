import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.audio.processor import AudioProcessor

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_ffmpeg():
    return MagicMock()

@pytest.fixture
def audio_processor(mock_context, mock_ffmpeg):
    with patch("src.services.audio.processor.ffmpeg", mock_ffmpeg):
        return AudioProcessor(context=mock_context)

def test_processor_initialization(audio_processor):
    """Test processor initialization."""
    assert audio_processor is not None
    assert audio_processor.context is not None

def test_process_audio(audio_processor, mock_ffmpeg):
    """Test audio processing."""
    audio_path = "test/audio.mp3"
    mock_ffmpeg.probe.return_value = {
        "streams": [{
            "codec_type": "audio",
            "duration": "120.0",
            "sample_rate": "44100",
            "channels": 2
        }]
    }
    
    result = audio_processor.process_audio(audio_path)
    assert result["success"] is True
    assert result["duration"] == 120.0
    assert result["sample_rate"] == 44100
    assert result["channels"] == 2

def test_extract_metadata(audio_processor, mock_ffmpeg):
    """Test metadata extraction."""
    audio_path = "test/audio.mp3"
    mock_ffmpeg.probe.return_value = {
        "format": {
            "tags": {
                "title": "Test Audio",
                "artist": "Test Artist",
                "album": "Test Album",
                "date": "2024"
            }
        }
    }
    
    result = audio_processor.extract_metadata(audio_path)
    assert result["success"] is True
    assert result["metadata"]["title"] == "Test Audio"
    assert result["metadata"]["artist"] == "Test Artist"

def test_convert_format(audio_processor, mock_ffmpeg):
    """Test format conversion."""
    audio_path = "test/audio.mp3"
    target_format = "wav"
    mock_ffmpeg.input.return_value.output.return_value.run.return_value = (b"", b"")
    
    result = audio_processor.convert_format(audio_path, target_format)
    assert result["success"] is True
    assert result["format"] == target_format
    assert result["output_path"].endswith(f".{target_format}")

def test_split_audio(audio_processor, mock_ffmpeg):
    """Test audio splitting."""
    audio_path = "test/audio.mp3"
    segments = [
        {"start": 0, "end": 30},
        {"start": 30, "end": 60}
    ]
    mock_ffmpeg.input.return_value.output.return_value.run.return_value = (b"", b"")
    
    result = audio_processor.split_audio(audio_path, segments)
    assert result["success"] is True
    assert len(result["segments"]) == len(segments)
    assert all("path" in segment for segment in result["segments"])

def test_merge_audio(audio_processor, mock_ffmpeg):
    """Test audio merging."""
    audio_paths = ["test/audio1.mp3", "test/audio2.mp3"]
    mock_ffmpeg.input.return_value.output.return_value.run.return_value = (b"", b"")
    
    result = audio_processor.merge_audio(audio_paths)
    assert result["success"] is True
    assert "output_path" in result
    assert result["output_path"].endswith(".mp3")

def test_analyze_audio(audio_processor, mock_ffmpeg):
    """Test audio analysis."""
    audio_path = "test/audio.mp3"
    mock_ffmpeg.probe.return_value = {
        "streams": [{
            "codec_type": "audio",
            "duration": "120.0",
            "bit_rate": "192000",
            "sample_rate": "44100",
            "channels": 2
        }]
    }
    
    result = audio_processor.analyze_audio(audio_path)
    assert result["success"] is True
    assert "analysis" in result
    assert "duration" in result["analysis"]
    assert "bit_rate" in result["analysis"]

def test_detect_silence(audio_processor, mock_ffmpeg):
    """Test silence detection."""
    audio_path = "test/audio.mp3"
    mock_ffmpeg.probe.return_value = {
        "frames": [
            {"pts": 10.0, "silence_start": 0.5},
            {"pts": 15.0, "silence_end": 0.5},
            {"pts": 30.0, "silence_start": 0.5},
            {"pts": 35.0, "silence_end": 0.5}
        ]
    }
    
    result = audio_processor.detect_silence(audio_path)
    assert result["success"] is True
    assert len(result["silent_regions"]) == 2
    assert all("start" in region and "end" in region for region in result["silent_regions"])

def test_normalize_audio(audio_processor, mock_ffmpeg):
    """Test audio normalization."""
    audio_path = "test/audio.mp3"
    target_level = -18
    mock_ffmpeg.input.return_value.output.return_value.run.return_value = (b"", b"")
    
    result = audio_processor.normalize_audio(audio_path, target_level)
    assert result["success"] is True
    assert "output_path" in result
    assert result["peak_level"] == target_level

def test_validate_audio(audio_processor, mock_ffmpeg):
    """Test audio validation."""
    audio_path = "test/audio.mp3"
    mock_ffmpeg.probe.return_value = {
        "streams": [{
            "codec_type": "audio",
            "codec_name": "mp3",
            "duration": "120.0",
            "bit_rate": "192000"
        }]
    }
    
    result = audio_processor.validate_audio(audio_path)
    assert result["success"] is True
    assert result["valid"] is True
    assert result["format_valid"] is True
    assert result["codec_valid"] is True

def test_get_audio_duration(audio_processor, mock_ffmpeg):
    """Test getting audio duration."""
    audio_path = "test/audio.mp3"
    mock_ffmpeg.probe.return_value = {
        "format": {
            "duration": "120.5"
        }
    }
    
    result = audio_processor.get_duration(audio_path)
    assert result["success"] is True
    assert result["duration"] == 120.5

def test_get_audio_format(audio_processor, mock_ffmpeg):
    """Test getting audio format."""
    audio_path = "test/audio.mp3"
    mock_ffmpeg.probe.return_value = {
        "format": {
            "format_name": "mp3",
            "format_long_name": "MP3 (MPEG audio layer 3)"
        }
    }
    
    result = audio_processor.get_format(audio_path)
    assert result["success"] is True
    assert result["format"] == "mp3"
    assert "format_long_name" in result

def test_error_handling_invalid_file(audio_processor, mock_ffmpeg):
    """Test error handling for invalid file."""
    audio_path = "test/invalid.mp3"
    mock_ffmpeg.probe.side_effect = Exception("Invalid file")
    
    result = audio_processor.process_audio(audio_path)
    assert result["success"] is False
    assert "error" in result

def test_error_handling_conversion_failure(audio_processor, mock_ffmpeg):
    """Test error handling for conversion failure."""
    audio_path = "test/audio.mp3"
    mock_ffmpeg.input.return_value.output.return_value.run.side_effect = Exception("Conversion failed")
    
    result = audio_processor.convert_format(audio_path, "wav")
    assert result["success"] is False
    assert "error" in result

def test_batch_process(audio_processor, mock_ffmpeg):
    """Test batch processing."""
    audio_paths = ["test/audio1.mp3", "test/audio2.mp3"]
    mock_ffmpeg.probe.return_value = {
        "streams": [{
            "codec_type": "audio",
            "duration": "60.0",
            "sample_rate": "44100"
        }]
    }
    
    result = audio_processor.batch_process(audio_paths)
    assert result["success"] is True
    assert len(result["results"]) == len(audio_paths)
    assert all(r["success"] for r in result["results"])

def test_get_supported_formats(audio_processor):
    """Test getting supported formats."""
    result = audio_processor.get_supported_formats()
    assert result["success"] is True
    assert isinstance(result["formats"], list)
    assert "mp3" in result["formats"]
    assert "wav" in result["formats"] 