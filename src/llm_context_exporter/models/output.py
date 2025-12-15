"""
Output models for LLM Context Exporter.

These models represent the formatted output for different target platforms
and validation testing.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field, field_validator


class ValidationQuestion(BaseModel):
    """Single validation question for testing context transfer."""
    
    question: str = Field(..., description="The validation question")
    expected_answer_summary: str = Field(..., description="Summary of expected answer")
    category: str = Field(..., description="Question category: 'project', 'preference', or 'technical'")
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()
    
    @field_validator('expected_answer_summary')
    @classmethod
    def validate_expected_answer_summary(cls, v):
        if not v.strip():
            raise ValueError("Expected answer summary cannot be empty")
        return v.strip()
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        valid_categories = ['project', 'preference', 'technical']
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
        return v


class ValidationSuite(BaseModel):
    """Test questions for validation."""
    
    questions: List[ValidationQuestion] = Field(default_factory=list, description="Validation questions")
    target_platform: str = Field(..., description="Target platform for validation")
    platform_artifacts: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific validation artifacts")
    
    @field_validator('questions')
    @classmethod
    def validate_questions(cls, v):
        if not v:
            raise ValueError("Validation suite must contain at least one question")
        return v
    
    @field_validator('target_platform')
    @classmethod
    def validate_target_platform(cls, v):
        valid_platforms = ['gemini', 'ollama']
        if v not in valid_platforms:
            raise ValueError(f"Target platform must be one of: {', '.join(valid_platforms)}")
        return v


class GeminiOutput(BaseModel):
    """Formatted output for Gemini Saved Info."""
    
    formatted_text: str = Field(..., description="Ready-to-paste text for Gemini Saved Info")
    instructions: str = Field(..., description="Step-by-step setup instructions")
    validation_tests: ValidationSuite = Field(..., description="Validation test suite")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('formatted_text')
    @classmethod
    def validate_formatted_text(cls, v):
        if not v.strip():
            raise ValueError("Formatted text cannot be empty")
        return v
    
    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v):
        if not v.strip():
            raise ValueError("Instructions cannot be empty")
        return v


class OllamaOutput(BaseModel):
    """Formatted output for Ollama."""
    
    modelfile_content: str = Field(..., description="Complete Modelfile content")
    supplementary_files: Dict[str, str] = Field(default_factory=dict, description="Additional context files if needed")
    setup_commands: List[str] = Field(default_factory=list, description="Shell commands to create model")
    test_commands: List[str] = Field(default_factory=list, description="Commands to test the model")
    validation_tests: ValidationSuite = Field(..., description="Validation test suite")
    
    @field_validator('modelfile_content')
    @classmethod
    def validate_modelfile_content(cls, v):
        if not v.strip():
            raise ValueError("Modelfile content cannot be empty")
        # Basic validation that it looks like a Modelfile
        if not any(line.strip().startswith('FROM ') for line in v.split('\n')):
            raise ValueError("Modelfile must contain a FROM directive")
        return v
    
    @field_validator('setup_commands')
    @classmethod
    def validate_setup_commands(cls, v):
        if not v:
            raise ValueError("Setup commands cannot be empty")
        return [cmd.strip() for cmd in v if cmd.strip()]
    
    @field_validator('test_commands')
    @classmethod
    def validate_test_commands(cls, v):
        if not v:
            raise ValueError("Test commands cannot be empty")
        return [cmd.strip() for cmd in v if cmd.strip()]