"""Integration tests for audio processing flow."""

import pytest
from pathlib import Path
import shutil
import wave
import numpy as np
from datetime import datetime

from src.core.config import Settings
from src.services.audio.audio_transcriber import AudioTranscriber
from src.services.audio.audio_processor import AudioProcessor
from src.core.obsidian_utils import ObsidianUtils
from src.services.note_management.note_manager import NoteManager

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
    preview_dir = vault_path / "audio_previews"
    
    vault_path.mkdir()
    audio_dir.mkdir()
    transcripts_dir.mkdir()
    preview_dir.mkdir()
    
    # Copy test audio file to audio directory
    shutil.copy(test_audio_file, audio_dir / "test.wav")
    
    return {
        "vault_path": vault_path,
        "audio_dir": audio_dir,
        "transcripts_dir": transcripts_dir,
        "preview_dir": preview_dir
    }

@pytest.mark.asyncio
async def test_audio_transcription_flow(test_environment):
    """Test the audio transcription flow."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        AUDIO_FILES_DIR=str(test_environment["audio_dir"])
    )
    
    transcriber = AudioTranscriber()
    await transcriber.initialize(settings)
    
    # Process audio file
    audio_path = test_environment["audio_dir"] / "test.wav"
    result = await transcriber.transcribe_audio(audio_path)
    
    # Verify transcription
    assert result.success is True
    assert result.transcript is not None
    assert len(result.transcript) > 0
    
    # Verify transcript note creation
    transcript_path = test_environment["transcripts_dir"] / "test_transcript.md"
    assert transcript_path.exists()
    
    # Verify transcript content
    content = transcript_path.read_text()
    assert "Audio Transcript" in content
    assert "test.wav" in content
    assert "Transcription" in content

@pytest.mark.asyncio
async def test_audio_analysis_flow(test_environment):
    """Test the audio analysis flow."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        AUDIO_FILES_DIR=str(test_environment["audio_dir"])
    )
    
    processor = AudioProcessor()
    await processor.initialize(settings)
    
    # Process audio file
    audio_path = test_environment["audio_dir"] / "test.wav"
    result = await processor.analyze_audio(audio_path)
    
    # Verify analysis
    assert result.success is True
    assert result.duration is not None
    assert result.sample_rate == 44100
    assert result.channels == 1
    
    # Verify waveform generation
    waveform_path = test_environment["preview_dir"] / "test_waveform.png"
    assert waveform_path.exists()

@pytest.mark.asyncio
async def test_audio_note_integration_flow(test_environment):
    """Test the integration of audio processing with note management."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        AUDIO_FILES_DIR=str(test_environment["audio_dir"])
    )
    
    transcriber = AudioTranscriber()
    note_manager = NoteManager()
    
    await transcriber.initialize(settings)
    await note_manager.initialize(settings)
    
    # Process audio and create note
    audio_path = test_environment["audio_dir"] / "test.wav"
    transcript_result = await transcriber.transcribe_audio(audio_path)
    
    note_data = {
        "title": "Audio Note Test",
        "content": f"""# Audio Note Test

## Audio Information
- File: test.wav
- Duration: {transcript_result.duration}s
- Recorded: {datetime.now().strftime("%Y-%m-%d")}

## Transcription
{transcript_result.transcript}

## Summary
{transcript_result.summary}
"""
    }
    
    note_result = await note_manager.create_note(note_data)
    
    # Verify note creation
    assert note_result.success is True
    note_path = test_environment["vault_path"] / "Audio Note Test.md"
    assert note_path.exists()
    
    # Verify note content
    content = note_path.read_text()
    assert "Audio Note Test" in content
    assert "test.wav" in content
    assert transcript_result.transcript in content

@pytest.mark.asyncio
async def test_audio_task_extraction_flow(test_environment):
    """Test the extraction of tasks from audio transcripts."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        AUDIO_FILES_DIR=str(test_environment["audio_dir"])
    )
    
    transcriber = AudioTranscriber()
    processor = AudioProcessor()
    
    await transcriber.initialize(settings)
    await processor.initialize(settings)
    
    # Process audio and extract tasks
    audio_path = test_environment["audio_dir"] / "test.wav"
    transcript_result = await transcriber.transcribe_audio(audio_path)
    task_result = await processor.extract_tasks(transcript_result.transcript)
    
    # Verify task extraction
    assert task_result.success is True
    assert task_result.tasks is not None
    
    # Create task note
    task_note_path = test_environment["vault_path"] / "Audio Tasks.md"
    task_content = "# Tasks from Audio Recording\n\n"
    for task in task_result.tasks:
        task_content += f"- [ ] {task}\n"
    
    task_note_path.write_text(task_content)
    
    # Verify task note
    assert task_note_path.exists()
    content = task_note_path.read_text()
    assert "Tasks from Audio Recording" in content
    assert all(task in content for task in task_result.tasks) 