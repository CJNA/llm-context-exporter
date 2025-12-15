"""
Tests for model validation logic.

Tests that our Pydantic models properly validate input data
and raise appropriate errors for invalid data.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from llm_context_exporter.models import (
    Message,
    Conversation,
    ParsedExport,
    UniversalContextPack,
    ProjectBrief,
    FilterConfig,
    GeminiOutput,
    OllamaOutput,
    ValidationSuite,
    ValidationQuestion,
    PaymentIntent,
    BetaUser,
    Feedback,
)


class TestMessageValidation:
    """Test Message model validation."""
    
    def test_invalid_role(self):
        """Test that invalid roles are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Message(
                role="invalid_role",
                content="Test content",
                timestamp=datetime.now()
            )
        assert "Role must be 'user' or 'assistant'" in str(exc_info.value)
    
    def test_empty_content(self):
        """Test that empty content is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Message(
                role="user",
                content="   ",  # Only whitespace
                timestamp=datetime.now()
            )
        assert "Message content cannot be empty" in str(exc_info.value)


class TestConversationValidation:
    """Test Conversation model validation."""
    
    def test_empty_id(self):
        """Test that empty conversation ID is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Conversation(
                id="   ",  # Only whitespace
                title="Test",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[]
            )
        assert "Conversation ID cannot be empty" in str(exc_info.value)
    
    def test_empty_messages(self):
        """Test that conversations must have at least one message."""
        with pytest.raises(ValidationError) as exc_info:
            Conversation(
                id="test_123",
                title="Test",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[]
            )
        assert "Conversation must have at least one message" in str(exc_info.value)


class TestProjectBriefValidation:
    """Test ProjectBrief model validation."""
    
    def test_empty_name(self):
        """Test that empty project name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectBrief(
                name="   ",  # Only whitespace
                description="Test project",
                last_discussed=datetime.now()
            )
        assert "Project name cannot be empty" in str(exc_info.value)
    
    def test_relevance_score_bounds(self):
        """Test that relevance score is bounded between 0 and 1."""
        # Test negative score
        with pytest.raises(ValidationError):
            ProjectBrief(
                name="Test",
                description="Test project",
                last_discussed=datetime.now(),
                relevance_score=-0.1
            )
        
        # Test score > 1
        with pytest.raises(ValidationError):
            ProjectBrief(
                name="Test",
                description="Test project",
                last_discussed=datetime.now(),
                relevance_score=1.1
            )
        
        # Test valid scores
        project = ProjectBrief(
            name="Test",
            description="Test project",
            last_discussed=datetime.now(),
            relevance_score=0.5
        )
        assert project.relevance_score == 0.5


class TestFilterConfigValidation:
    """Test FilterConfig model validation."""
    
    def test_date_range_validation(self):
        """Test that date range validation works correctly."""
        start = datetime.now()
        end = datetime.now()
        
        # Test invalid range (start >= end)
        with pytest.raises(ValidationError) as exc_info:
            FilterConfig(date_range=(end, start))
        assert "Start date must be before end date" in str(exc_info.value)


class TestValidationQuestionValidation:
    """Test ValidationQuestion model validation."""
    
    def test_invalid_category(self):
        """Test that invalid categories are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationQuestion(
                question="Test question?",
                expected_answer_summary="Test answer",
                category="invalid_category"
            )
        assert "Category must be one of: project, preference, technical" in str(exc_info.value)
    
    def test_empty_fields(self):
        """Test that empty required fields are rejected."""
        # Empty question
        with pytest.raises(ValidationError) as exc_info:
            ValidationQuestion(
                question="   ",
                expected_answer_summary="Test answer",
                category="project"
            )
        assert "Question cannot be empty" in str(exc_info.value)
        
        # Empty expected answer
        with pytest.raises(ValidationError) as exc_info:
            ValidationQuestion(
                question="Test question?",
                expected_answer_summary="   ",
                category="project"
            )
        assert "Expected answer summary cannot be empty" in str(exc_info.value)


class TestOllamaOutputValidation:
    """Test OllamaOutput model validation."""
    
    def test_modelfile_validation(self):
        """Test that Modelfile content is validated."""
        # Missing FROM directive
        with pytest.raises(ValidationError) as exc_info:
            OllamaOutput(
                modelfile_content="SYSTEM You are a helpful assistant",
                setup_commands=["ollama create test"],
                test_commands=["ollama run test"],
                validation_tests=ValidationSuite(
                    questions=[ValidationQuestion(
                        question="Test?",
                        expected_answer_summary="Test",
                        category="project"
                    )],
                    target_platform="ollama"
                )
            )
        assert "Modelfile must contain a FROM directive" in str(exc_info.value)
        
        # Valid Modelfile
        output = OllamaOutput(
            modelfile_content="FROM qwen\nSYSTEM You are a helpful assistant",
            setup_commands=["ollama create test"],
            test_commands=["ollama run test"],
            validation_tests=ValidationSuite(
                questions=[ValidationQuestion(
                    question="Test?",
                    expected_answer_summary="Test",
                    category="project"
                )],
                target_platform="ollama"
            )
        )
        assert "FROM qwen" in output.modelfile_content


class TestPaymentIntentValidation:
    """Test PaymentIntent model validation."""
    
    def test_amount_validation(self):
        """Test that payment amount must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            PaymentIntent(
                id="pi_test",
                amount=0,  # Invalid: must be positive
                status="requires_payment_method",
                client_secret="pi_test_secret"
            )
        assert "Payment amount must be positive" in str(exc_info.value)
    
    def test_currency_validation(self):
        """Test that currency code is validated."""
        with pytest.raises(ValidationError) as exc_info:
            PaymentIntent(
                id="pi_test",
                amount=500,
                currency="invalid",  # Invalid: not 3 letters
                status="requires_payment_method",
                client_secret="pi_test_secret"
            )
        assert "Currency must be a 3-letter code" in str(exc_info.value)
    
    def test_status_validation(self):
        """Test that payment status is validated."""
        with pytest.raises(ValidationError) as exc_info:
            PaymentIntent(
                id="pi_test",
                amount=500,
                status="invalid_status",
                client_secret="pi_test_secret"
            )
        assert "Invalid payment status" in str(exc_info.value)


class TestBetaUserValidation:
    """Test BetaUser model validation."""
    
    def test_email_validation(self):
        """Test that email format is validated."""
        # Invalid email format
        with pytest.raises(ValidationError) as exc_info:
            BetaUser(email="invalid_email")
        assert "Invalid email format" in str(exc_info.value)
        
        # Valid email
        user = BetaUser(email="test@example.com")
        assert user.email == "test@example.com"
    
    def test_negative_counts(self):
        """Test that negative counts are rejected."""
        with pytest.raises(ValidationError):
            BetaUser(
                email="test@example.com",
                total_exports=-1
            )
        
        with pytest.raises(ValidationError):
            BetaUser(
                email="test@example.com",
                feedback_count=-1
            )


class TestFeedbackValidation:
    """Test Feedback model validation."""
    
    def test_rating_bounds(self):
        """Test that rating is bounded between 1 and 5."""
        # Rating too low
        with pytest.raises(ValidationError):
            Feedback(
                email="test@example.com",
                rating=0,
                feedback_text="Test feedback",
                export_id="export_123",
                target_platform="gemini"
            )
        
        # Rating too high
        with pytest.raises(ValidationError):
            Feedback(
                email="test@example.com",
                rating=6,
                feedback_text="Test feedback",
                export_id="export_123",
                target_platform="gemini"
            )
        
        # Valid rating
        feedback = Feedback(
            email="test@example.com",
            rating=4,
            feedback_text="Test feedback",
            export_id="export_123",
            target_platform="gemini"
        )
        assert feedback.rating == 4
    
    def test_target_platform_validation(self):
        """Test that target platform is validated."""
        with pytest.raises(ValidationError) as exc_info:
            Feedback(
                email="test@example.com",
                rating=5,
                feedback_text="Test feedback",
                export_id="export_123",
                target_platform="invalid_platform"
            )
        assert "Target platform must be one of: gemini, ollama" in str(exc_info.value)