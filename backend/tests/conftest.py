"""Pytest configuration and fixtures."""

import os
import pytest
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

@pytest.fixture
def test_vault_path(tmp_path) -> Path:
    """Create a temporary vault path."""
    vault_path = tmp_path / "test_vault"
    vault_path.mkdir()
    return vault_path

@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings."""
    settings = MagicMock()
    settings.VAULT_PATH = "/test/vault"
    settings.AUDIO_FILES_DIR = "/test/audio"
    settings.RAW_EMAILS_DIR = "/test/emails/raw"
    settings.PROCESSED_EMAILS_DIR = "/test/emails/processed"
    settings.RAG_VECTOR_DB_PATH = "/test/vector_db"
    settings.RAG_CHUNK_SIZE = 512
    settings.RAG_CHUNK_OVERLAP = 128
    return settings

@pytest.fixture
def mock_obsidian_utils() -> MagicMock:
    """Create mock ObsidianUtils."""
    return MagicMock()

@pytest.fixture
def mock_llm() -> MagicMock:
    """Create mock LLM."""
    return MagicMock()

@pytest.fixture
def mock_vector_db() -> MagicMock:
    """Create mock vector database."""
    return MagicMock() 