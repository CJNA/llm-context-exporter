"""
Integration tests for the web interface.

Tests the complete web interface functionality including HTML rendering,
JavaScript functionality, and API integration.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from src.llm_context_exporter.web.app import create_app


class TestWebIntegration:
    """Test web interface integration."""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        config = {
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key',
            'WTF_CSRF_ENABLED': False,
        }
        return create_app(config)
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_web_interface_loads(self, client):
        """Test that the web interface loads with all required elements."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for main page elements
        assert b'LLM Context Exporter' in response.data
        assert b'Export Your ChatGPT Context' in response.data
        assert b'Google Gemini' in response.data
        assert b'Local LLM (Ollama)' in response.data
        assert b'Get Started' in response.data
        
        # Check for CSS and JS includes
        assert b'styles.css' in response.data
        assert b'app.js' in response.data
        assert b'stripe.com/v3' in response.data
    
    def test_responsive_design_elements(self, client):
        """Test that responsive design elements are present."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for viewport meta tag
        assert b'viewport' in response.data
        assert b'device-width' in response.data
        
        # Check for responsive CSS classes
        assert b'app-container' in response.data
        assert b'main-content' in response.data
        assert b'page-actions' in response.data
    
    def test_accessibility_features(self, client):
        """Test accessibility features in the HTML."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for semantic HTML
        assert b'<main' in response.data
        assert b'<header' in response.data
        assert b'lang="en"' in response.data
        
        # Check for form labels
        assert b'<label for=' in response.data
        
        # Check for proper heading structure
        assert b'<h1' in response.data
        assert b'<h2' in response.data
    
    def test_all_pages_present(self, client):
        """Test that all required pages are present in the HTML."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for all page sections
        pages = [
            b'welcome-page',
            b'upload-page', 
            b'target-page',
            b'review-page',
            b'payment-page',
            b'results-page'
        ]
        
        for page in pages:
            assert page in response.data
    
    def test_form_elements_present(self, client):
        """Test that all required form elements are present."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for file upload
        assert b'type="file"' in response.data
        assert b'accept=".zip,.json"' in response.data
        
        # Check for radio buttons
        assert b'type="radio"' in response.data
        assert b'name="target"' in response.data
        
        # Check for email input
        assert b'type="email"' in response.data
        
        # Check for textarea
        assert b'<textarea' in response.data
        
        # Check for range input (relevance slider)
        assert b'type="range"' in response.data
    
    def test_javascript_functionality_elements(self, client):
        """Test that JavaScript functionality elements are present."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for JavaScript event handlers (via IDs)
        js_elements = [
            b'id="get-started-btn"',
            b'id="file-input"',
            b'id="upload-zone"',
            b'id="continue-to-target"',
            b'id="pay-button"',
            b'id="download-zip"'
        ]
        
        for element in js_elements:
            assert element in response.data
    
    def test_loading_and_feedback_elements(self, client):
        """Test loading indicators and feedback elements."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for loading overlay
        assert b'loading-overlay' in response.data
        assert b'loading-spinner' in response.data
        
        # Check for toast notifications
        assert b'toast-container' in response.data
        
        # Check for progress indicators
        assert b'progress-bar' in response.data
        assert b'progress-fill' in response.data
    
    def test_platform_comparison_content(self, client):
        """Test platform comparison content is present."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check Gemini features
        assert b'Cloud-based processing' in response.data
        assert b'Saved Info' in response.data
        
        # Check Ollama features  
        assert b'Complete privacy' in response.data
        assert b'runs locally' in response.data
        
        # Check privacy notices
        assert b'Privacy First' in response.data
        assert b'locally on your machine' in response.data
    
    def test_instructions_and_help_content(self, client):
        """Test that help and instruction content is present."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for ChatGPT export instructions
        assert b'ChatGPT Settings' in response.data
        assert b'Export data' in response.data
        
        # Check for validation section
        assert b'Validation Tests' in response.data
        assert b'verify your context' in response.data
        
        # Check for feedback form
        assert b'Beta Feedback' in response.data
        assert b'star-rating' in response.data
    
    @patch('src.llm_context_exporter.web.app.ChatGPTParser')
    @patch('src.llm_context_exporter.web.app.ContextExtractor')
    def test_upload_flow_integration(self, mock_extractor, mock_parser, client):
        """Test the upload flow integration between frontend and backend."""
        # Mock the parser and extractor
        mock_parsed_export = Mock()
        mock_parsed_export.conversations = [Mock()]
        mock_parsed_export.export_date = Mock()
        mock_parsed_export.export_date.isoformat.return_value = '2024-01-01T00:00:00'
        mock_parsed_export.format_version = '1.0'
        mock_parsed_export.model_dump.return_value = {'conversations': []}
        
        mock_parser.return_value.parse_export.return_value = mock_parsed_export
        
        mock_context_pack = Mock()
        mock_context_pack.projects = [Mock(), Mock()]  # 2 projects
        mock_context_pack.model_dump.return_value = {'projects': []}
        
        mock_extractor.return_value.extract_context.return_value = mock_context_pack
        
        # Create a test file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(b'{"test": "data"}')
            temp_file = f.name
        
        try:
            # Test file upload
            with open(temp_file, 'rb') as test_file:
                response = client.post('/api/upload', data={
                    'file': (test_file, 'test_export.json')
                })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['conversations_count'] == 1
            assert data['projects_count'] == 2
            
        finally:
            os.unlink(temp_file)
    
    def test_error_handling_elements(self, client):
        """Test that error handling elements are present."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for error display elements
        assert b'toast' in response.data
        assert b'loading-overlay' in response.data
        
        # Check for progress indicators
        assert b'progress' in response.data
    
    def test_beta_user_elements(self, client):
        """Test beta user specific elements."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for beta user notice
        assert b'beta-notice' in response.data
        assert b'Beta User' in response.data
        
        # Check for feedback form
        assert b'feedback-form' in response.data
        assert b'feedback-text' in response.data
    
    def test_payment_elements(self, client):
        """Test payment related elements."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for payment form
        assert b'payment-form' in response.data
        assert b'stripe-payment-element' in response.data
        
        # Check for pricing information
        assert b'$3.00' in response.data
        assert b'One-time payment' in response.data
        
        # Check for free alternative
        assert b'Free Alternative' in response.data
        assert b'command-line interface' in response.data
    
    def test_download_and_results_elements(self, client):
        """Test download and results page elements."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for download buttons
        assert b'download-zip' in response.data
        assert b'Download All Files' in response.data
        
        # Check for copy functionality
        assert b'copy-gemini-text' in response.data
        assert b'Copy Gemini Text' in response.data
        
        # Check for setup instructions
        assert b'setup-instructions' in response.data
        assert b'Next Steps' in response.data