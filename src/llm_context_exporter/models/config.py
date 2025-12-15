"""
Configuration models for LLM Context Exporter.

These models represent user configuration and filtering preferences.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator


class FilterConfig(BaseModel):
    """User filtering preferences."""
    
    excluded_conversation_ids: List[str] = Field(default_factory=list, description="Conversation IDs to exclude")
    excluded_topics: List[str] = Field(default_factory=list, description="Topics to exclude")
    date_range: Optional[Tuple[datetime, datetime]] = Field(None, description="Date range filter (start, end)")
    min_relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum relevance score")
    
    @field_validator('excluded_conversation_ids')
    @classmethod
    def validate_excluded_conversation_ids(cls, v):
        # Remove empty strings and duplicates
        return list(set(id.strip() for id in v if id.strip()))
    
    @field_validator('excluded_topics')
    @classmethod
    def validate_excluded_topics(cls, v):
        # Remove empty strings and duplicates, preserve case for display
        return list(set(topic.strip() for topic in v if topic.strip()))
    
    @field_validator('date_range')
    @classmethod
    def validate_date_range(cls, v):
        if v is not None:
            start, end = v
            if start >= end:
                raise ValueError("Start date must be before end date")
        return v


class ExportConfig(BaseModel):
    """Configuration for export operation."""
    
    input_path: str = Field(..., description="Path to input export file")
    target_platform: str = Field(..., description="Target platform: 'gemini' or 'ollama'")
    output_path: str = Field(..., description="Path for output files")
    base_model: Optional[str] = Field(None, description="Base model for Ollama (e.g., 'qwen')")
    filters: Optional[FilterConfig] = Field(None, description="Filtering configuration")
    interactive: bool = Field(default=False, description="Enable interactive filtering mode")
    incremental: bool = Field(default=False, description="Enable incremental update mode")
    previous_context_path: Optional[str] = Field(None, description="Path to previous context for incremental updates")
    
    @field_validator('input_path')
    @classmethod
    def validate_input_path(cls, v):
        if not v.strip():
            raise ValueError("Input path cannot be empty")
        return v.strip()
    
    @field_validator('target_platform')
    @classmethod
    def validate_target_platform(cls, v):
        valid_platforms = ['gemini', 'ollama']
        if v not in valid_platforms:
            raise ValueError(f"Target platform must be one of: {', '.join(valid_platforms)}")
        return v
    
    @field_validator('output_path')
    @classmethod
    def validate_output_path(cls, v):
        if not v.strip():
            raise ValueError("Output path cannot be empty")
        return v.strip()
    
    @field_validator('base_model')
    @classmethod
    def validate_base_model(cls, v, info):
        if info.data.get('target_platform') == 'ollama' and not v:
            raise ValueError("Base model is required for Ollama target")
        return v
    
    @field_validator('previous_context_path')
    @classmethod
    def validate_previous_context_path(cls, v, info):
        if info.data.get('incremental') and not v:
            raise ValueError("Previous context path is required for incremental updates")
        return v