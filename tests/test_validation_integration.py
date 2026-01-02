"""
Integration tests for validation generator with formatters.
"""

import pytest
from datetime import datetime
from src.llm_context_exporter.models.core import (
    UniversalContextPack, UserProfile, ProjectBrief, UserPreferences, TechnicalContext
)
from src.llm_context_exporter.formatters.gemini import GeminiFormatter
from src.llm_context_exporter.formatters.ollama import OllamaFormatter


class TestValidationIntegration:
    """Test validation generator integration with formatters."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = UniversalContextPack(
            version="1.0.0",
            created_at=datetime.now(),
            source_platform="chatgpt",
            user_profile=UserProfile(
                role="Software Engineer",
                expertise_areas=["Python", "Machine Learning"],
                background_summary="Experienced developer"
            ),
            projects=[
                ProjectBrief(
                    name="Web App",
                    description="A web application",
                    tech_stack=["Python", "Flask", "React"],
                    key_challenges=["Performance", "Scalability"],
                    current_status="In development",
                    last_discussed=datetime.now(),
                    relevance_score=0.9
                )
            ],
            preferences=UserPreferences(
                coding_style={"language": "Python", "style": "functional"},
                communication_style="Direct and concise",
                preferred_tools=["VS Code", "Git", "Docker"],
                work_patterns={"hours": "9-5", "methodology": "Agile"}
            ),
            technical_context=TechnicalContext(
                languages=["Python", "JavaScript", "SQL"],
                frameworks=["Flask", "React", "TensorFlow"],
                tools=["Docker", "Git", "VS Code"],
                domains=["Web Development", "Machine Learning"]
            ),
            metadata={}
        )
    
    def test_gemini_formatter_validation_integration(self):
        """Test that Gemini formatter includes proper validation tests."""
        formatter = GeminiFormatter()
        output = formatter.format_context(self.context)
        
        # Check that validation tests are included
        assert output.validation_tests is not None
        assert output.validation_tests.target_platform == "gemini"
        assert len(output.validation_tests.questions) > 0
        
        # Check that platform-specific artifacts are included
        assert hasattr(output.validation_tests, 'platform_artifacts')
        artifacts = output.validation_tests.platform_artifacts
        assert artifacts["type"] == "manual_checklist"
        assert "checklist" in artifacts
        assert "instructions" in artifacts
        
        # Verify checklist format
        checklist = artifacts["checklist"]
        assert len(checklist) == len(output.validation_tests.questions)
        for item in checklist:
            assert "step" in item
            assert "action" in item
            assert "expected" in item
            assert "check" in item
            assert item["check"] == "□"
    
    def test_ollama_formatter_validation_integration(self):
        """Test that Ollama formatter includes proper validation tests."""
        formatter = OllamaFormatter()
        output = formatter.format_context(self.context)
        
        # Check that validation tests are included
        assert output.validation_tests is not None
        assert output.validation_tests.target_platform == "ollama"
        assert len(output.validation_tests.questions) > 0
        
        # Check that platform-specific artifacts are included
        artifacts = output.validation_tests.platform_artifacts
        assert artifacts["type"] == "cli_commands"
        assert "commands" in artifacts
        assert "instructions" in artifacts
        
        # Verify commands format
        commands = artifacts["commands"]
        assert len(commands) == len(output.validation_tests.questions)
        for cmd in commands:
            assert "step" in cmd
            assert "command" in cmd
            assert "expected" in cmd
            assert "ollama run" in cmd["command"]
    
    def test_validation_questions_cover_all_categories(self):
        """Test that validation questions cover all expected categories."""
        formatter = GeminiFormatter()
        output = formatter.format_context(self.context)
        
        categories = {q.category for q in output.validation_tests.questions}
        
        # Should have questions from different categories based on our context
        assert "project" in categories  # We have projects
        assert "preference" in categories  # We have preferences
        assert "technical" in categories  # We have technical context
    
    def test_validation_questions_reference_context_data(self):
        """Test that validation questions reference actual context data."""
        formatter = GeminiFormatter()
        output = formatter.format_context(self.context)
        
        # Collect all expected answers
        all_expected = " ".join([q.expected_answer_summary for q in output.validation_tests.questions])
        
        # Should mention our project
        assert "Web App" in all_expected
        
        # Should mention our role
        assert "Software Engineer" in all_expected
        
        # Should mention our languages
        assert "Python" in all_expected
        
        # Should mention our tools
        assert "VS Code" in all_expected
    
    def test_empty_context_validation(self):
        """Test validation generation with minimal context."""
        minimal_context = UniversalContextPack(
            version="1.0.0",
            created_at=datetime.now(),
            source_platform="chatgpt",
            user_profile=UserProfile(),
            projects=[],
            preferences=UserPreferences(),
            technical_context=TechnicalContext(),
            metadata={}
        )
        
        formatter = GeminiFormatter()
        output = formatter.format_context(minimal_context)
        
        # Should still have validation tests, even if minimal
        assert output.validation_tests is not None
        assert len(output.validation_tests.questions) > 0
        
        # Should have platform artifacts
        assert hasattr(output.validation_tests, 'platform_artifacts')
        artifacts = output.validation_tests.platform_artifacts
        assert artifacts["type"] == "manual_checklist"