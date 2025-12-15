"""
Payment management for the web interface.

This module handles Stripe payment processing for the hosted version.
"""

import stripe
import os
import logging
from typing import Dict, Any, Optional
from ..models.payment import PaymentIntent
from .beta import BetaManager

logger = logging.getLogger(__name__)


class PaymentManager:
    """
    Manages payment processing via Stripe.
    
    Handles payment intent creation, verification, and webhook processing
    for the web interface.
    """
    
    def __init__(self, stripe_secret_key: Optional[str] = None, beta_manager: Optional[BetaManager] = None):
        """
        Initialize the payment manager.
        
        Args:
            stripe_secret_key: Stripe secret key (defaults to environment variable)
            beta_manager: Beta manager instance for checking beta users
        """
        self.stripe_secret_key = stripe_secret_key or os.environ.get('STRIPE_SECRET_KEY')
        if self.stripe_secret_key:
            stripe.api_key = self.stripe_secret_key
        
        # Beta manager for checking beta users
        self.beta_manager = beta_manager or BetaManager()
        
        # Default pricing (can be configured via environment variables)
        self.default_amount = int(os.environ.get('PAYMENT_AMOUNT_CENTS', '300'))  # $3.00 in cents
        self.default_currency = os.environ.get('PAYMENT_CURRENCY', 'usd')
        
        logger.info(f"PaymentManager initialized with default amount: ${self.default_amount/100:.2f} {self.default_currency.upper()}")
    
    def create_payment_intent(self, amount: int = None, currency: str = None, metadata: Dict[str, Any] = None) -> PaymentIntent:
        """
        Create a Stripe payment intent.
        
        Args:
            amount: Amount in cents (defaults to configured amount)
            currency: Currency code (defaults to USD)
            metadata: Additional metadata for the payment
            
        Returns:
            PaymentIntent object with Stripe details
            
        Raises:
            ValueError: If Stripe is not configured or payment creation fails
        """
        if not self.stripe_secret_key:
            raise ValueError("Stripe secret key not configured. Set STRIPE_SECRET_KEY environment variable.")
        
        amount = amount or self.default_amount
        currency = currency or self.default_currency
        metadata = metadata or {}
        
        # Add default metadata
        metadata.update({
            'service': 'llm-context-exporter',
            'version': '1.0.0'
        })
        
        try:
            logger.info(f"Creating payment intent for ${amount/100:.2f} {currency.upper()}")
            
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata,
                automatic_payment_methods={'enabled': True},
                description="LLM Context Export"
            )
            
            logger.info(f"Payment intent created: {intent.id}")
            
            return PaymentIntent(
                id=intent.id,
                amount=intent.amount,
                currency=intent.currency,
                status=intent.status,
                client_secret=intent.client_secret
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Payment intent creation failed: {e}")
            raise ValueError(f"Payment intent creation failed: {e}")
    
    def verify_payment(self, payment_intent_id: str) -> bool:
        """
        Verify that a payment was completed successfully.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            True if payment was successful
        """
        if not self.stripe_secret_key:
            logger.warning("Cannot verify payment: Stripe not configured")
            return False
        
        try:
            logger.info(f"Verifying payment: {payment_intent_id}")
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            is_successful = intent.status == 'succeeded'
            logger.info(f"Payment {payment_intent_id} status: {intent.status} (successful: {is_successful})")
            
            return is_successful
            
        except stripe.error.StripeError as e:
            logger.error(f"Payment verification failed for {payment_intent_id}: {e}")
            return False
    
    def is_beta_user(self, email: str) -> bool:
        """
        Check if user has beta access (bypasses payment).
        
        Args:
            email: User email address
            
        Returns:
            True if user is in beta program
        """
        if not email:
            return False
            
        is_beta = self.beta_manager.is_beta_user(email)
        logger.info(f"Beta user check for {email}: {is_beta}")
        return is_beta
    
    def requires_payment(self, user_context: Dict[str, Any]) -> bool:
        """
        Determine if payment is required for this user/request.
        
        Args:
            user_context: Context about the user and request
                - source: 'cli' or 'web'
                - email: user email (optional)
            
        Returns:
            True if payment is required
        """
        # CLI users don't pay (Requirements 16.1)
        if user_context.get('source') == 'cli':
            logger.info("Payment not required: CLI user")
            return False
        
        # Beta users don't pay (Requirements 17.1)
        email = user_context.get('email')
        if email and self.is_beta_user(email):
            logger.info(f"Payment not required: Beta user {email}")
            return False
        
        # Web interface users pay
        logger.info("Payment required: Web interface user")
        return True
    
    def handle_webhook(self, payload: str, signature: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.
        
        Args:
            payload: Webhook payload
            signature: Stripe signature header
            
        Returns:
            Dictionary with processing results
            
        Raises:
            ValueError: If webhook verification fails
        """
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        if not webhook_secret:
            raise ValueError("Webhook secret not configured. Set STRIPE_WEBHOOK_SECRET environment variable.")
        
        try:
            logger.info("Processing Stripe webhook")
            
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            
            event_type = event['type']
            logger.info(f"Webhook event type: {event_type}")
            
            # Handle different event types
            if event_type == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                payment_id = payment_intent['id']
                amount = payment_intent['amount']
                
                logger.info(f"Payment succeeded: {payment_id} for ${amount/100:.2f}")
                
                # Send email receipt via Stripe (Requirements 16.5)
                # This is handled automatically by Stripe if configured
                
                return {
                    'status': 'success', 
                    'payment_id': payment_id,
                    'amount': amount,
                    'event_type': event_type
                }
            
            elif event_type == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                payment_id = payment_intent['id']
                
                logger.warning(f"Payment failed: {payment_id}")
                
                return {
                    'status': 'failed',
                    'payment_id': payment_id,
                    'event_type': event_type
                }
            
            else:
                logger.info(f"Ignoring webhook event type: {event_type}")
                return {'status': 'ignored', 'event_type': event_type}
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise ValueError(f"Webhook signature verification failed: {e}")
        except ValueError as e:
            logger.error(f"Webhook processing failed: {e}")
            raise ValueError(f"Webhook processing failed: {e}")
    
    def get_payment_status(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Get detailed payment status information.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            Dictionary with payment status details
        """
        if not self.stripe_secret_key:
            return {'error': 'Stripe not configured'}
        
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'id': intent.id,
                'status': intent.status,
                'amount': intent.amount,
                'currency': intent.currency,
                'created': intent.created,
                'description': intent.description,
                'metadata': intent.metadata
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve payment status for {payment_intent_id}: {e}")
            return {'error': str(e)}