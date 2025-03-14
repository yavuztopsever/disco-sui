"""Integration tests for the audio service."""

import pytest
from pathlib import Path
import shutil
import wave
import numpy as np
from datetime import datetime

from src.services.audio.audio_transcriber import AudioTranscriber
from src.core.config import Settings
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_audio_file(tmp_path) -> Path:
    """Create a test audio file."""
    audio_path = tmp_path / "test.wav"
    
    # Create a simple WAV file
    with wave.open(str(audio_path), 'w') as wav_file:
        # Set parameters
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(44100)  # 44.1kHz
        
        # Generate 1 second of silence
        samples = np.zeros(44100, dtype=np.int16)
        wav_file.writeframes(samples.tobytes())
    
    return audio_path

@pytest.fixture
def test_environment(tmp_path, test_audio_file):
    """Set up test environment."""
    # Create test directories
    vault_path = tmp_path / "vault"
    audio_dir = tmp_path / "audio"
    transcripts_dir = vault_path / "audio_transcripts"
    
    vault_path.mkdir()
    audio_dir.mkdir()
    transcripts_dir.mkdir()
    
    # Copy test audio file to audio directory
    shutil.copy(test_audio_file, audio_dir / "test.wav")
    
    return {
        "vault_path": vault_path,
        "audio_dir": audio_dir,
        "transcripts_dir": transcripts_dir
    }

@pytest.mark.asyncio
async def test_audio_processing_flow(test_environment):
    """Test the complete audio processing flow."""
    # Initialize services with test environment
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        AUDIO_FILES_DIR=str(test_environment["audio_dir"])
    )
    
    obsidian_utils = ObsidianUtils()
    
    transcriber = AudioTranscriber()
    transcriber.settings = settings
    transcriber.obsidian_utils = obsidian_utils
    
    # Start the service
    await transcriber.start()
    
    # Verify transcript file was created
    transcript_files = list(test_environment["transcripts_dir"].glob("*.md"))
    assert len(transcript_files) == 1
    
    # Verify transcript content
    transcript_content = transcript_files[0].read_text()
    assert "Audio Transcript" in transcript_content
    assert "test.wav" in transcript_content
    
    # Verify metadata
    assert "date_processed:" in transcript_content
    assert "duration:" in transcript_content 