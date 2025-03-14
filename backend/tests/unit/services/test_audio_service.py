"""Unit tests for the audio service."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.services.audio.audio_transcriber import AudioTranscriber, AudioMetadata
from src.core.exceptions import AudioProcessingError

@pytest.fixture
def audio_transcriber(mock_settings, mock_obsidian_utils):
    """Create an AudioTranscriber instance with mocked dependencies."""
    transcriber = AudioTranscriber()
    transcriber.settings = mock_settings
    transcriber.obsidian_utils = mock_obsidian_utils
    transcriber.model = MagicMock()
    return transcriber

def test_initialize(audio_transcriber, mock_settings):
    """Test AudioTranscriber initialization."""
    audio_transcriber._initialize()
    
    assert audio_transcriber.audio_dir == Path(mock_settings.AUDIO_FILES_DIR)
    assert audio_transcriber.vault_path == Path(mock_settings.VAULT_PATH)
    assert audio_transcriber.model is not None

@pytest.mark.asyncio
async def test_start_success(audio_transcriber):
    """Test successful start of audio processing."""
    audio_transcriber.process_pending_audio = MagicMock()
    await audio_transcriber.start()
    audio_transcriber.process_pending_audio.assert_called_once()

@pytest.mark.asyncio
async def test_start_failure(audio_transcriber):
    """Test failed start of audio processing."""
    audio_transcriber.process_pending_audio = MagicMock(side_effect=Exception("Test error"))
    
    with pytest.raises(AudioProcessingError) as exc_info:
        await audio_transcriber.start()
    
    assert "Failed to start audio processing" in str(exc_info.value)

@pytest.mark.asyncio
async def test_health_check(audio_transcriber, tmp_path):
    """Test health check functionality."""
    audio_transcriber.audio_dir = tmp_path / "audio"
    audio_transcriber.vault_path = tmp_path / "vault"
    
    # Create test directories
    audio_transcriber.audio_dir.mkdir()
    audio_transcriber.vault_path.mkdir()
    
    assert await audio_transcriber.health_check() is True
    
    # Test with missing directory
    audio_transcriber.audio_dir.rmdir()
    assert await audio_transcriber.health_check() is False 