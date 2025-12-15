"""
Payment and beta testing models for LLM Context Exporter.

These models support the web interface payment system and beta user management.
"""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator


class PaymentIntent(BaseModel):
    """Stripe payment intent information."""
    
    id: str = Field(..., description="Stripe payment intent ID")
    amount: int = Field(..., description="Payment amount in cents")
    currency: str = Field(default="usd", description="Payment currency")
    status: str = Field(..., description="Payment status")
    client_secret: str = Field(..., description="Client secret for frontend")
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        if not v.strip():
            raise ValueError("Payment intent ID cannot be empty")
        return v.strip()
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Payment amount must be positive")
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        # Basic currency code validation
        if len(v) != 3 or not v.isalpha():
            raise ValueError("Currency must be a 3-letter code")
        return v.lower()
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = [
            'requires_payment_method',
            'requires_confirmation',
            'requires_action',
            'processing',
            'requires_capture',
            'canceled',
            'succeeded'
        ]
        if v not in valid_statuses:
            raise ValueError(f"Invalid payment status: {v}")
        return v
    
    @field_validator('client_secret')
    @classmethod
    def validate_client_secret(cls, v):
        if not v.strip():
            raise ValueError("Client secret cannot be empty")
        return v.strip()


class BetaUser(BaseModel):
    """Beta program participant."""
    
    email: str = Field(..., description="User email address")
    added_date: datetime = Field(default_factory=datetime.now, description="When user was added to beta")
    notes: str = Field(default="", description="Admin notes about the user")
    total_exports: int = Field(default=0, ge=0, description="Total number of exports performed")
    last_export_date: Optional[datetime] = Field(None, description="Date of last export")
    feedback_count: int = Field(default=0, ge=0, description="Number of feedback submissions")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Basic email validation
        if not v.strip():
            raise ValueError("Email cannot be empty")
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError("Invalid email format")
        return v.strip().lower()


class UsageStats(BaseModel):
    """Usage statistics for a user."""
    
    total_exports: int = Field(default=0, ge=0, description="Total number of exports")
    exports_by_target: Dict[str, int] = Field(default_factory=dict, description="Exports by target platform")
    total_conversations_processed: int = Field(default=0, ge=0, description="Total conversations processed")
    average_export_size_mb: float = Field(default=0.0, ge=0.0, description="Average export size in MB")
    last_export_date: Optional[datetime] = Field(None, description="Date of last export")
    
    @field_validator('exports_by_target')
    @classmethod
    def validate_exports_by_target(cls, v):
        # Ensure all values are non-negative integers
        for platform, count in v.items():
            if not isinstance(count, int) or count < 0:
                raise ValueError(f"Export count for {platform} must be a non-negative integer")
        return v


class Feedback(BaseModel):
    """User feedback submission."""
    
    email: str = Field(..., description="User email address")
    timestamp: datetime = Field(default_factory=datetime.now, description="When feedback was submitted")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5 stars")
    feedback_text: str = Field(..., description="Feedback text")
    export_id: str = Field(..., description="ID of the export this feedback relates to")
    target_platform: str = Field(..., description="Target platform used")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Basic email validation
        if not v.strip():
            raise ValueError("Email cannot be empty")
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError("Invalid email format")
        return v.strip().lower()
    
    @field_validator('feedback_text')
    @classmethod
    def validate_feedback_text(cls, v):
        if not v.strip():
            raise ValueError("Feedback text cannot be empty")
        return v.strip()
    
    @field_validator('export_id')
    @classmethod
    def validate_export_id(cls, v):
        if not v.strip():
            raise ValueError("Export ID cannot be empty")
        return v.strip()
    
    @field_validator('target_platform')
    @classmethod
    def validate_target_platform(cls, v):
        valid_platforms = ['gemini', 'ollama']
        if v not in valid_platforms:
            raise ValueError(f"Target platform must be one of: {', '.join(valid_platforms)}")
        return v