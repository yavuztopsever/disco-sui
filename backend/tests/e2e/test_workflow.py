"""End-to-end tests for DiscoSui workflow."""

import pytest
import asyncio
from pathlib import Path
import shutil
import wave
import numpy as np
from datetime import datetime

from src.services.audio.audio_transcriber import AudioTranscriber
from src.services.email.email_processor import EmailProcessor
from src.services.analysis.analysis_service import AnalysisService
from src.services.organization.organization_service import OrganizationService
from src.core.config import Settings
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_environment(tmp_path):
    """Set up complete test environment."""
    # Create main directories
    vault_path = tmp_path / "vault"
    audio_dir = tmp_path / "audio"
    email_raw_dir = tmp_path / "emails" / "raw"
    email_processed_dir = tmp_path / "emails" / "processed"
    vector_db_path = tmp_path / "vector_db"
    
    # Create directory structure
    for directory in [vault_path, audio_dir, email_raw_dir, email_processed_dir, vector_db_path]:
        directory.mkdir(parents=True)
    
    # Create test audio file
    audio_path = audio_dir / "test.wav"
    with wave.open(str(audio_path), 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(44100)
        samples = np.zeros(44100, dtype=np.int16)
        wav_file.writeframes(samples.tobytes())
    
    # Create test email file
    email_path = email_raw_dir / "test.eml"
    email_content = """From: test@example.com
Subject: Test Email
Date: Thu, 14 Mar 2024 12:00:00 +0000

This is a test email."""
    email_path.write_text(email_content)
    
    return {
        "vault_path": vault_path,
        "audio_dir": audio_dir,
        "email_raw_dir": email_raw_dir,
        "email_processed_dir": email_processed_dir,
        "vector_db_path": vector_db_path
    }

@pytest.mark.asyncio
async def test_complete_workflow(test_environment):
    """Test the complete DiscoSui workflow."""
    # Initialize settings
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        AUDIO_FILES_DIR=str(test_environment["audio_dir"]),
        RAW_EMAILS_DIR=str(test_environment["email_raw_dir"]),
        PROCESSED_EMAILS_DIR=str(test_environment["email_processed_dir"]),
        RAG_VECTOR_DB_PATH=str(test_environment["vector_db_path"])
    )
    
    # Initialize services
    obsidian_utils = ObsidianUtils()
    audio_service = AudioTranscriber()
    email_service = EmailProcessor()
    analysis_service = AnalysisService()
    organization_service = OrganizationService()
    
    # Configure services
    for service in [audio_service, email_service, analysis_service, organization_service]:
        service.settings = settings
        service.obsidian_utils = obsidian_utils
    
    # Start services
    await asyncio.gather(
        audio_service.start(),
        email_service.start(),
        analysis_service.start(),
        organization_service.start()
    )
    
    # Verify audio processing
    audio_transcripts = list(test_environment["vault_path"].glob("**/test.wav.md"))
    assert len(audio_transcripts) == 1
    transcript_content = audio_transcripts[0].read_text()
    assert "Audio Transcript" in transcript_content
    
    # Verify email processing
    email_notes = list(test_environment["vault_path"].glob("**/test.eml.md"))
    assert len(email_notes) == 1
    email_note_content = email_notes[0].read_text()
    assert "test@example.com" in email_note_content
    
    # Verify analysis results
    analysis_files = list(test_environment["vector_db_path"].glob("*"))
    assert len(analysis_files) > 0
    
    # Verify organization
    assert (test_environment["vault_path"] / "audio_transcripts").exists()
    assert (test_environment["vault_path"] / "emails").exists()
    
    # Stop services
    await asyncio.gather(
        audio_service.stop(),
        email_service.stop(),
        analysis_service.stop(),
        organization_service.stop()
    ) 