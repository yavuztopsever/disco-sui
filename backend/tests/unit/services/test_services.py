"""Unit tests for service implementations."""
import pytest
from pathlib import Path
from typing import Dict, Any

@pytest.mark.unit
class TestContentService:
    """Test suite for content service."""
    
    def test_content_processing(self, mock_context, mock_processor, assertion_helper):
        """Test content processing functionality."""
        from src.services.content.content_service import ContentService
        
        content_service = ContentService(
            context=mock_context,
            processor=mock_processor
        )
        
        # Test markdown processing
        content = "# Test\nThis is **bold**"
        result = content_service.process_content(content)
        assertion_helper["assert_success"](result)
        assert "<h1>" in result["html"]
        
        # Test metadata extraction
        result = content_service.extract_metadata(content)
        assertion_helper["assert_success"](result)
        assert "title" in result["metadata"]
    
    def test_content_manipulation(self, mock_context, mock_processor, assertion_helper):
        """Test content manipulation operations."""
        from src.services.content.content_service import ContentService
        
        content_service = ContentService(
            context=mock_context,
            processor=mock_processor
        )
        
        # Test content update
        result = content_service.update_content(
            "test.md",
            "# Updated\nNew content"
        )
        assertion_helper["assert_success"](result)
        
        # Test content merge
        result = content_service.merge_content(
            "source.md",
            "target.md"
        )
        assertion_helper["assert_success"](result)

@pytest.mark.unit
class TestEmailService:
    """Test suite for email service."""
    
    def test_email_processing(self, mock_context, mock_processor, test_data_generator,
                            assertion_helper):
        """Test email processing functionality."""
        from src.services.email.email_service import EmailService
        
        email_service = EmailService(
            context=mock_context,
            processor=mock_processor
        )
        
        # Test email parsing
        test_email = test_data_generator("email")
        result = email_service.process_email(test_email)
        assertion_helper["assert_success"](result)
        assert result["content"] is not None
        
        # Test attachment handling
        result = email_service.process_attachments(test_email)
        assertion_helper["assert_success"](result)
        assert isinstance(result["attachments"], list)
    
    def test_email_conversion(self, mock_context, mock_processor, test_data_generator,
                            assertion_helper):
        """Test email to note conversion."""
        from src.services.email.email_service import EmailService
        
        email_service = EmailService(
            context=mock_context,
            processor=mock_processor
        )
        
        # Convert email to note
        test_email = test_data_generator("email")
        result = email_service.convert_to_note(test_email)
        assertion_helper["assert_success"](result)
        assert result["note"]["title"] is not None
        assert result["note"]["content"] is not None

@pytest.mark.unit
class TestAudioService:
    """Test suite for audio service."""
    
    def test_audio_processing(self, mock_context, mock_processor, test_data_generator,
                            assertion_helper):
        """Test audio processing functionality."""
        from src.services.audio.audio_service import AudioService
        
        audio_service = AudioService(
            context=mock_context,
            processor=mock_processor
        )
        
        # Test audio transcription
        test_audio = test_data_generator("audio")
        result = audio_service.transcribe_audio(test_audio["filename"])
        assertion_helper["assert_success"](result)
        assert result["transcription"] is not None
        
        # Test audio metadata extraction
        result = audio_service.extract_metadata(test_audio["filename"])
        assertion_helper["assert_success"](result)
        assert result["metadata"]["duration"] == test_audio["duration"]
    
    def test_audio_conversion(self, mock_context, mock_processor, test_data_generator,
                            assertion_helper):
        """Test audio format conversion."""
        from src.services.audio.audio_service import AudioService
        
        audio_service = AudioService(
            context=mock_context,
            processor=mock_processor
        )
        
        # Convert audio format
        test_audio = test_data_generator("audio")
        result = audio_service.convert_format(
            test_audio["filename"],
            target_format="wav"
        )
        assertion_helper["assert_success"](result)
        assert result["output_file"].endswith(".wav")

@pytest.mark.unit
class TestAnalysisService:
    """Test suite for analysis service."""
    
    def test_content_analysis(self, mock_context, mock_processor, assertion_helper):
        """Test content analysis functionality."""
        from src.services.analysis.analysis_service import AnalysisService
        
        analysis_service = AnalysisService(
            context=mock_context,
            processor=mock_processor
        )
        
        # Test text analysis
        result = analysis_service.analyze_text("Test content for analysis")
        assertion_helper["assert_success"](result)
        assert "topics" in result
        assert "sentiment" in result
        
        # Test similarity analysis
        result = analysis_service.analyze_similarity(
            "First text",
            "Second text"
        )
        assertion_helper["assert_success"](result)
        assert "similarity_score" in result
    
    def test_metadata_analysis(self, mock_context, mock_processor, assertion_helper):
        """Test metadata analysis functionality."""
        from src.services.analysis.analysis_service import AnalysisService
        
        analysis_service = AnalysisService(
            context=mock_context,
            processor=mock_processor
        )
        
        # Test metadata extraction
        result = analysis_service.analyze_metadata({
            "tags": ["test", "analysis"],
            "created": "2024-01-01"
        })
        assertion_helper["assert_success"](result)
        assert "tag_categories" in result
        assert "temporal_analysis" in result 