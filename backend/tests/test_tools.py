import pytest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock

from ..src.tools.semantic_tools import (
    AnalyzeRelationshipsTool,
    FindRelatedNotesTool,
    GenerateKnowledgeGraphTool,
    AnalyzeNoteTool
)
from ..src.tools.text_tools import (
    ChunkTextTool,
    ExtractEntitiesTool,
    SummarizeTextTool,
    AnalyzeSentimentTool
)
from ..src.tools.email_tools import (
    ProcessEmailTool,
    ExtractEmailMetadataTool,
    ConvertEmailToNoteTool,
    AnalyzeEmailThreadTool,
    ListEmailFilesTool,
    GetEmailNoteTool,
    ImportEmailsTool,
    ExportEmailsTool
)

@pytest.fixture
def sample_text() -> str:
    return """
    This is a sample text for testing purposes. It contains multiple sentences
    and some named entities like John Smith and Microsoft. The text is long
    enough to be split into chunks and analyzed for sentiment.
    """

@pytest.fixture
def sample_email() -> str:
    return """
    From: sender@example.com
    To: recipient@example.com
    Subject: Test Email
    Date: Thu, 1 Jan 2024 12:00:00 +0000

    This is a test email message.
    It contains multiple lines of text
    and some attachments.

    Best regards,
    Sender
    """

@pytest.fixture
def sample_note_path() -> str:
    return "test/sample_note.md"

class TestSemanticTools:
    async def test_analyze_relationships(
        self,
        mock_semantic_analyzer: MagicMock,
        test_vault_path: str,
        sample_note_path: str
    ) -> None:
        tool = AnalyzeRelationshipsTool()
        tool.semantic_analyzer = mock_semantic_analyzer
        result = await tool.forward([sample_note_path])
        assert result["success"] is True
        assert "analyses" in result
        assert "relationships" in result
        mock_semantic_analyzer.analyze_note.assert_called_once()

    async def test_find_related_notes(
        self,
        mock_semantic_analyzer: MagicMock,
        test_vault_path: str,
        sample_note_path: str
    ) -> None:
        tool = FindRelatedNotesTool()
        tool.semantic_analyzer = mock_semantic_analyzer
        result = await tool.forward(sample_note_path)
        assert result["success"] is True
        assert "related_notes" in result
        mock_semantic_analyzer.find_related_notes.assert_called_once()

    async def test_generate_knowledge_graph(
        self,
        mock_semantic_analyzer: MagicMock,
        test_vault_path: str
    ) -> None:
        tool = GenerateKnowledgeGraphTool()
        tool.semantic_analyzer = mock_semantic_analyzer
        result = await tool.forward()
        assert result["success"] is True
        assert "graph" in result
        mock_semantic_analyzer.generate_knowledge_graph.assert_called_once()

    async def test_analyze_note(
        self,
        mock_semantic_analyzer: MagicMock,
        test_vault_path: str,
        sample_note_path: str
    ) -> None:
        tool = AnalyzeNoteTool()
        tool.semantic_analyzer = mock_semantic_analyzer
        result = await tool.forward(sample_note_path)
        assert result["success"] is True
        assert "analysis" in result
        mock_semantic_analyzer.analyze_note.assert_called_once()

class TestTextTools:
    async def test_chunk_text(
        self,
        mock_text_processor: MagicMock,
        sample_text: str
    ) -> None:
        tool = ChunkTextTool()
        tool.text_processor = mock_text_processor
        result = await tool.forward(sample_text)
        assert result["success"] is True
        assert "chunks" in result
        mock_text_processor.chunk_text.assert_called_once()

    async def test_extract_entities(
        self,
        mock_text_processor: MagicMock,
        sample_text: str
    ) -> None:
        tool = ExtractEntitiesTool()
        tool.text_processor = mock_text_processor
        result = await tool.forward(sample_text)
        assert result["success"] is True
        assert "entities" in result
        mock_text_processor.extract_entities.assert_called_once()

    async def test_summarize_text(
        self,
        mock_text_processor: MagicMock,
        sample_text: str
    ) -> None:
        tool = SummarizeTextTool()
        tool.text_processor = mock_text_processor
        result = await tool.forward(sample_text)
        assert result["success"] is True
        assert "summary" in result
        mock_text_processor.summarize_text.assert_called_once()

    async def test_analyze_sentiment(
        self,
        mock_text_processor: MagicMock,
        sample_text: str
    ) -> None:
        tool = AnalyzeSentimentTool()
        tool.text_processor = mock_text_processor
        result = await tool.forward(sample_text)
        assert result["success"] is True
        assert "sentiment" in result
        mock_text_processor.analyze_sentiment.assert_called_once()

class TestEmailTools:
    async def test_process_email(
        self,
        mock_email_processor: MagicMock,
        sample_email: str
    ) -> None:
        tool = ProcessEmailTool()
        tool.email_processor = mock_email_processor
        result = await tool.forward(sample_email)
        assert result["success"] is True
        assert "processed_data" in result
        mock_email_processor.process_email.assert_called_once()

    async def test_extract_email_metadata(
        self,
        mock_email_processor: MagicMock,
        sample_email: str
    ) -> None:
        tool = ExtractEmailMetadataTool()
        tool.email_processor = mock_email_processor
        result = await tool.forward(sample_email)
        assert result["success"] is True
        assert "metadata" in result
        mock_email_processor.extract_metadata.assert_called_once()

    async def test_convert_email_to_note(
        self,
        mock_email_processor: MagicMock,
        sample_email: str
    ) -> None:
        tool = ConvertEmailToNoteTool()
        tool.email_processor = mock_email_processor
        result = await tool.forward(sample_email)
        assert result["success"] is True
        assert "note_data" in result
        mock_email_processor.convert_to_note.assert_called_once()

    async def test_analyze_email_thread(
        self,
        mock_email_processor: MagicMock,
        sample_email: str
    ) -> None:
        tool = AnalyzeEmailThreadTool()
        tool.email_processor = mock_email_processor
        result = await tool.forward([sample_email])
        assert result["success"] is True
        assert "thread_analysis" in result
        mock_email_processor.analyze_thread.assert_called_once()

    async def test_list_email_files(
        self,
        mock_email_processor: MagicMock,
        test_vault_path: str
    ) -> None:
        tool = ListEmailFilesTool()
        tool.email_processor = mock_email_processor
        result = await tool.forward()
        assert result["success"] is True
        assert "email_files" in result
        mock_email_processor.list_email_files.assert_called_once()

    async def test_get_email_note(
        self,
        mock_email_processor: MagicMock,
        test_vault_path: str
    ) -> None:
        tool = GetEmailNoteTool()
        tool.email_processor = mock_email_processor
        result = await tool.forward("test/sample_email.eml")
        assert result["success"] is True
        assert "note_data" in result
        mock_email_processor.get_email_note.assert_called_once()

    async def test_import_emails(
        self,
        mock_email_processor: MagicMock,
        test_vault_path: str
    ) -> None:
        tool = ImportEmailsTool()
        tool.email_processor = mock_email_processor
        result = await tool.forward("mbox", "test/sample.mbox")
        assert result["success"] is True
        assert "imported_emails" in result
        mock_email_processor.import_emails.assert_called_once()

    async def test_export_emails(
        self,
        mock_email_processor: MagicMock,
        test_vault_path: str
    ) -> None:
        tool = ExportEmailsTool()
        tool.email_processor = mock_email_processor
        result = await tool.forward("pdf", ["test/sample_email.eml"], "test/output.pdf")
        assert result["success"] is True
        assert "exported_files" in result
        mock_email_processor.export_emails.assert_called_once() 