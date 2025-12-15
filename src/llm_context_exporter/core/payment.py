"""
Core payment management functionality.

This module provides the main PaymentManager class that integrates
Stripe payment processing with beta user management.
"""

import logging
from typing import Dict, Any, Optional
from ..models.payment import PaymentIntent
from ..web.payment import PaymentManager as WebPaymentManager
from ..web.beta import BetaManager

logger = logging.getLogger(__name__)


class PaymentManager:
    """
    Main payment manager that integrates payment processing with beta user management.
    
    This class provides a unified interface for payment operations, combining
    Stripe payment processing with beta user management and usage tracking.
    """
    
    def __init__(self, stripe_secret_key: Optional[str] = None, beta_manager: Optional[BetaManager] = None):
        """
        Initialize the payment manager.
        
        Args:
            stripe_secret_key: Stripe secret key (defaults to environment variable)
            beta_manager: Beta manager instance for checking beta users
        """
        self.beta_manager = beta_manager or BetaManager()
        self.web_payment_manager = WebPaymentManager(
            stripe_secret_key=stripe_secret_key,
            beta_manager=self.beta_manager
        )
        
        logger.info("PaymentManager initialized")
    
    def create_payment_intent(self, amount: int, currency: str = "usd") -> PaymentIntent:
        """
        Create a Stripe payment intent.
        
        Args:
            amount: Payment amount in cents
            currency: Payment currency (default: USD)
            
        Returns:
            PaymentIntent object with Stripe details
            
        Raises:
            ValueError: If payment creation fails
        """
        return self.web_payment_manager.create_payment_intent(amount, currency)
    
    def verify_payment(self, payment_intent_id: str) -> bool:
        """
        Verify that a payment was completed successfully.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            True if payment was successful
        """
        return self.web_payment_manager.verify_payment(payment_intent_id)
    
    def is_beta_user(self, email: str) -> bool:
        """
        Check if user has beta access.
        
        Args:
            email: User email address
            
        Returns:
            True if user is in beta program
        """
        return self.beta_manager.is_beta_user(email)
    
    def requires_payment(self, user_context: Dict[str, Any]) -> bool:
        """
        Determine if payment is required (bypass for CLI and beta users).
        
        Args:
            user_context: Context about the user and request
                - source: 'cli' or 'web'
                - email: user email (optional)
            
        Returns:
            True if payment is required
        """
        return self.web_payment_manager.requires_payment(user_context)
    
    def handle_webhook(self, payload: str, signature: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.
        
        Args:
            payload: Webhook payload
            signature: Stripe signature header
            
        Returns:
            Dictionary with processing results
        """
        return self.web_payment_manager.handle_webhook(payload, signature)
    
    def record_export(self, email: str, target_platform: str, conversations_processed: int = 0, export_size_mb: float = 0.0) -> None:
        """
        Record an export by a user (for beta users).
        
        Args:
            email: User email address
            target_platform: Target platform (gemini/ollama)
            conversations_processed: Number of conversations processed
            export_size_mb: Size of export in MB
        """
        if self.is_beta_user(email):
            self.beta_manager.record_export(email, target_platform, conversations_processed, export_size_mb)
            logger.info(f"Recorded export for beta user {email}: {target_platform}")
    
    def add_beta_user(self, email: str, notes: str = "") -> None:
        """
        Add user to beta whitelist.
        
        Args:
            email: User email address
            notes: Optional notes about the user
        """
        self.beta_manager.add_beta_user(email, notes)
        logger.info(f"Added beta user: {email}")
    
    def remove_beta_user(self, email: str) -> None:
        """
        Remove user from beta whitelist.
        
        Args:
            email: User email address
        """
        self.beta_manager.remove_beta_user(email)
        logger.info(f"Removed beta user: {email}")
    
    def get_payment_status(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Get detailed payment status information.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            Dictionary with payment status details
        """
        return self.web_payment_manager.get_payment_status(payment_intent_id)