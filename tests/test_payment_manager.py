"""
Tests for the PaymentManager class.

This module tests the payment processing functionality including
Stripe integration, beta user management, and payment requirements.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from llm_context_exporter.core.payment import PaymentManager
from llm_context_exporter.models.payment import PaymentIntent


class TestPaymentManager:
    """Test PaymentManager functionality."""
    
    def test_init_without_stripe_key(self):
        """Test PaymentManager initialization without Stripe key."""
        # Clear environment variable if it exists
        if 'STRIPE_SECRET_KEY' in os.environ:
            del os.environ['STRIPE_SECRET_KEY']
        
        manager = PaymentManager()
        assert manager is not None
        assert manager.beta_manager is not None
        assert manager.web_payment_manager is not None
    
    def test_init_with_stripe_key(self):
        """Test PaymentManager initialization with Stripe key."""
        test_key = "sk_test_123456789"
        manager = PaymentManager(stripe_secret_key=test_key)
        assert manager is not None
        assert manager.web_payment_manager.stripe_secret_key == test_key
    
    def test_requires_payment_cli_user(self):
        """Test that CLI users don't require payment."""
        manager = PaymentManager()
        
        user_context = {'source': 'cli'}
        assert not manager.requires_payment(user_context)
    
    def test_requires_payment_web_user(self):
        """Test that web users require payment."""
        manager = PaymentManager()
        
        user_context = {'source': 'web'}
        assert manager.requires_payment(user_context)
    
    @patch('llm_context_exporter.web.beta.BetaManager.is_beta_user')
    def test_requires_payment_beta_user(self, mock_is_beta):
        """Test that beta users don't require payment."""
        mock_is_beta.return_value = True
        manager = PaymentManager()
        
        user_context = {'source': 'web', 'email': 'beta@example.com'}
        assert not manager.requires_payment(user_context)
        mock_is_beta.assert_called_once_with('beta@example.com')
    
    @patch('llm_context_exporter.web.beta.BetaManager.is_beta_user')
    def test_requires_payment_regular_web_user(self, mock_is_beta):
        """Test that regular web users require payment."""
        mock_is_beta.return_value = False
        manager = PaymentManager()
        
        user_context = {'source': 'web', 'email': 'user@example.com'}
        assert manager.requires_payment(user_context)
        mock_is_beta.assert_called_once_with('user@example.com')
    
    def test_is_beta_user(self):
        """Test beta user checking."""
        with patch('llm_context_exporter.web.beta.BetaManager.is_beta_user') as mock_is_beta:
            mock_is_beta.return_value = True
            manager = PaymentManager()
            
            assert manager.is_beta_user('beta@example.com')
            mock_is_beta.assert_called_once_with('beta@example.com')
    
    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_success(self, mock_stripe_create):
        """Test successful payment intent creation."""
        # Mock Stripe response
        mock_intent = Mock()
        mock_intent.id = 'pi_test123'
        mock_intent.amount = 300
        mock_intent.currency = 'usd'
        mock_intent.status = 'requires_payment_method'
        mock_intent.client_secret = 'pi_test123_secret'
        mock_stripe_create.return_value = mock_intent
        
        manager = PaymentManager(stripe_secret_key='sk_test_123')
        
        result = manager.create_payment_intent(300, 'usd')
        
        assert isinstance(result, PaymentIntent)
        assert result.id == 'pi_test123'
        assert result.amount == 300
        assert result.currency == 'usd'
        assert result.status == 'requires_payment_method'
        assert result.client_secret == 'pi_test123_secret'
        
        mock_stripe_create.assert_called_once()
    
    def test_create_payment_intent_no_stripe_key(self):
        """Test payment intent creation without Stripe key."""
        manager = PaymentManager()  # No Stripe key
        
        with pytest.raises(ValueError, match="Stripe secret key not configured"):
            manager.create_payment_intent(300, 'usd')
    
    @patch('stripe.PaymentIntent.retrieve')
    def test_verify_payment_success(self, mock_stripe_retrieve):
        """Test successful payment verification."""
        mock_intent = Mock()
        mock_intent.status = 'succeeded'
        mock_stripe_retrieve.return_value = mock_intent
        
        manager = PaymentManager(stripe_secret_key='sk_test_123')
        
        result = manager.verify_payment('pi_test123')
        
        assert result is True
        mock_stripe_retrieve.assert_called_once_with('pi_test123')
    
    @patch('stripe.PaymentIntent.retrieve')
    def test_verify_payment_failed(self, mock_stripe_retrieve):
        """Test failed payment verification."""
        mock_intent = Mock()
        mock_intent.status = 'requires_payment_method'
        mock_stripe_retrieve.return_value = mock_intent
        
        manager = PaymentManager(stripe_secret_key='sk_test_123')
        
        result = manager.verify_payment('pi_test123')
        
        assert result is False
        mock_stripe_retrieve.assert_called_once_with('pi_test123')
    
    def test_verify_payment_no_stripe_key(self):
        """Test payment verification without Stripe key."""
        manager = PaymentManager()  # No Stripe key
        
        result = manager.verify_payment('pi_test123')
        
        assert result is False
    
    @patch('llm_context_exporter.web.beta.BetaManager.record_export')
    @patch('llm_context_exporter.web.beta.BetaManager.is_beta_user')
    def test_record_export_beta_user(self, mock_is_beta, mock_record_export):
        """Test recording export for beta user."""
        mock_is_beta.return_value = True
        manager = PaymentManager()
        
        manager.record_export('beta@example.com', 'gemini', 10, 1.5)
        
        mock_is_beta.assert_called_once_with('beta@example.com')
        mock_record_export.assert_called_once_with('beta@example.com', 'gemini', 10, 1.5)
    
    @patch('llm_context_exporter.web.beta.BetaManager.record_export')
    @patch('llm_context_exporter.web.beta.BetaManager.is_beta_user')
    def test_record_export_regular_user(self, mock_is_beta, mock_record_export):
        """Test recording export for regular user (should not record)."""
        mock_is_beta.return_value = False
        manager = PaymentManager()
        
        manager.record_export('user@example.com', 'gemini', 10, 1.5)
        
        mock_is_beta.assert_called_once_with('user@example.com')
        mock_record_export.assert_not_called()
    
    @patch('llm_context_exporter.web.beta.BetaManager.add_beta_user')
    def test_add_beta_user(self, mock_add_beta):
        """Test adding beta user."""
        manager = PaymentManager()
        
        manager.add_beta_user('beta@example.com', 'Test user')
        
        mock_add_beta.assert_called_once_with('beta@example.com', 'Test user')
    
    @patch('llm_context_exporter.web.beta.BetaManager.remove_beta_user')
    def test_remove_beta_user(self, mock_remove_beta):
        """Test removing beta user."""
        manager = PaymentManager()
        
        manager.remove_beta_user('beta@example.com')
        
        mock_remove_beta.assert_called_once_with('beta@example.com')


class TestPaymentManagerIntegration:
    """Integration tests for PaymentManager with real components."""
    
    def test_beta_manager_integration(self):
        """Test integration with BetaManager."""
        manager = PaymentManager()
        
        # Add a beta user
        manager.add_beta_user('test@example.com', 'Test integration')
        
        # Check if user is beta
        assert manager.is_beta_user('test@example.com')
        
        # Test payment requirement
        user_context = {'source': 'web', 'email': 'test@example.com'}
        assert not manager.requires_payment(user_context)
        
        # Remove beta user
        manager.remove_beta_user('test@example.com')
        
        # Check if user is no longer beta
        assert not manager.is_beta_user('test@example.com')
        
        # Test payment requirement after removal
        assert manager.requires_payment(user_context)