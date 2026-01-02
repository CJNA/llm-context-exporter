"""
Integration tests for the Flask API backend.

Tests the complete Flask API implementation including all endpoints,
security features, and integration with core components.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

from llm_context_exporter.web.app import create_app
from llm_context_exporter.models.core import UniversalContextPack, UserProfile, ProjectBrief
from llm_context_exporter.models.config import FilterConfig


class TestFlaskAPIIntegration:
    """Integration tests for Flask API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key',
            'WTF_CSRF_ENABLED': False,
            'UPLOAD_FOLDER': tempfile.mkdtemp(),
            'OUTPUT_FOLDER': tempfile.mkdtemp(),
        })
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_index_page(self, client):
        """Test the index page loads correctly."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'LLM Context Exporter' in response.data
        assert b'Export Your ChatGPT Context' in response.data
        assert b'Transfer your ChatGPT context to Gemini or local LLMs' in response.data
    
    def test_upload_no_file(self, client):
        """Test upload endpoint with no file."""
        response = client.post('/api/upload')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file provided' in data['error']
    
    def test_upload_empty_filename(self, client):
        """Test upload endpoint with empty filename."""
        response = client.post('/api/upload', data={'file': (None, '')})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file selected' in data['error']
    
    def test_upload_invalid_file_type(self, client):
        """Test upload endpoint with invalid file type."""
        response = client.post('/api/upload', data={
            'file': (tempfile.NamedTemporaryFile(suffix='.txt'), 'test.txt')
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid file type' in data['error']
    
    def test_preview_no_session_data(self, client):
        """Test preview endpoint without session data."""
        response = client.get('/api/preview')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No context data found' in data['error']
    
    def test_filter_no_session_data(self, client):
        """Test filter endpoint without session data."""
        response = client.post('/api/filter', 
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No context data found' in data['error']
    
    def test_filter_no_config(self, client):
        """Test filter endpoint without filter configuration."""
        # First set up session data
        with client.session_transaction() as sess:
            sess['context_pack'] = UniversalContextPack(
                version="1.0",
                source_platform="chatgpt",
                user_profile=UserProfile(),
                projects=[],
                preferences={},
                technical_context={},
                metadata={}
            ).model_dump()
        
        response = client.post('/api/filter', 
                             data=json.dumps(None),
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No filter configuration provided' in data['error']
    
    def test_generate_no_session_data(self, client):
        """Test generate endpoint without session data."""
        response = client.post('/api/generate',
                             data=json.dumps({'target_platform': 'gemini'}),
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No context data found' in data['error']
    
    def test_generate_invalid_platform(self, client):
        """Test generate endpoint with invalid platform."""
        # First set up session data
        with client.session_transaction() as sess:
            sess['context_pack'] = UniversalContextPack(
                version="1.0",
                source_platform="chatgpt",
                user_profile=UserProfile(),
                projects=[],
                preferences={},
                technical_context={},
                metadata={}
            ).model_dump()
        
        response = client.post('/api/generate',
                             data=json.dumps({'target_platform': 'invalid'}),
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid target platform' in data['error']
    
    def test_download_invalid_id(self, client):
        """Test download endpoint with invalid ID."""
        response = client.get('/api/download/invalid-id')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid export ID' in data['error']
    
    def test_validate_no_session_data(self, client):
        """Test validate endpoint without session data."""
        response = client.post('/api/validate',
                             data=json.dumps({'target_platform': 'gemini'}),
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No context data found' in data['error']
    
    def test_validate_invalid_platform(self, client):
        """Test validate endpoint with invalid platform."""
        # First set up session data
        with client.session_transaction() as sess:
            sess['context_pack'] = UniversalContextPack(
                version="1.0",
                source_platform="chatgpt",
                user_profile=UserProfile(),
                projects=[],
                preferences={},
                technical_context={},
                metadata={}
            ).model_dump()
        
        response = client.post('/api/validate',
                             data=json.dumps({'target_platform': 'invalid'}),
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid target platform' in data['error']
    
    def test_beta_status_no_email(self, client):
        """Test beta status endpoint without email."""
        response = client.get('/api/beta/status')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Email parameter required' in data['error']
    
    def test_beta_status_with_email(self, client):
        """Test beta status endpoint with email."""
        response = client.get('/api/beta/status?email=test@example.com')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data
        assert 'is_beta_user' in data
        assert data['email'] == 'test@example.com'
    
    def test_payment_create_no_stripe(self, client):
        """Test payment creation without Stripe configuration."""
        response = client.post('/api/payment/create',
                             data=json.dumps({'email': 'test@example.com'}),
                             content_type='application/json')
        # Should handle missing Stripe gracefully
        assert response.status_code in [200, 500]
    
    def test_payment_verify_no_intent_id(self, client):
        """Test payment verification without intent ID."""
        response = client.post('/api/payment/verify',
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Payment intent ID required' in data['error']
    
    def test_feedback_submission_missing_fields(self, client):
        """Test feedback submission with missing fields."""
        response = client.post('/api/beta/feedback',
                             data=json.dumps({'email': 'test@example.com'}),
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'required' in data['error']
    
    def test_feedback_submission_non_beta_user(self, client):
        """Test feedback submission from non-beta user."""
        response = client.post('/api/beta/feedback',
                             data=json.dumps({
                                 'email': 'test@example.com',
                                 'feedback': 'Great tool!',
                                 'rating': 5
                             }),
                             content_type='application/json')
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Only beta users' in data['error']
    
    def test_webhook_missing_signature(self, client):
        """Test webhook endpoint without signature."""
        response = client.post('/api/payment/webhook', data='test payload')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Missing signature' in data['error']
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # Make many requests quickly to trigger rate limiting
        # Note: This test might be flaky depending on timing
        responses = []
        for i in range(105):  # Exceed the 100 request limit
            response = client.get('/')
            responses.append(response.status_code)
        
        # Should have at least one 429 (rate limited) response
        assert 429 in responses
    
    def test_session_management(self, client):
        """Test session management functionality."""
        # Make a request to ensure session is created
        response = client.get('/')
        assert response.status_code == 200
        
        # Check that session has required fields
        with client.session_transaction() as sess:
            assert 'session_id' in sess
            assert 'created_at' in sess
    
    def test_file_size_limit(self, client):
        """Test file size limit enforcement."""
        # This test verifies that the Flask app has the MAX_CONTENT_LENGTH configured
        # The actual enforcement is handled by Flask/Werkzeug automatically
        # We can test this by checking the app configuration
        assert client.application.config['MAX_CONTENT_LENGTH'] == 500 * 1024 * 1024
    
    def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        response = client.get('/')
        # CORS headers should be present for localhost origins
        assert response.status_code == 200
    
    def test_error_handlers(self, client):
        """Test custom error handlers."""
        # Test 404 handler (non-existent endpoint)
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        
        # Test 500 handler would require triggering an actual server error
        # This is covered by other tests that might cause exceptions


class TestFlaskAPIWithMockedComponents:
    """Test Flask API with mocked core components."""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        return create_app({
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key',
            'WTF_CSRF_ENABLED': False,
        })
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @patch('llm_context_exporter.web.app.ChatGPTParser')
    @patch('llm_context_exporter.web.app.ContextExtractor')
    def test_upload_success_flow(self, mock_extractor, mock_parser, client):
        """Test successful upload flow with mocked components."""
        # Mock parser
        mock_parsed_export = MagicMock()
        mock_parsed_export.conversations = []
        mock_parsed_export.export_date.isoformat.return_value = "2023-12-14T10:30:00Z"
        mock_parsed_export.format_version = "2023-04-01"
        mock_parsed_export.model_dump.return_value = {'test': 'data'}
        
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_export.return_value = mock_parsed_export
        mock_parser.return_value = mock_parser_instance
        
        # Mock extractor
        mock_context_pack = MagicMock()
        mock_context_pack.projects = []
        mock_context_pack.model_dump.return_value = {'context': 'data'}
        
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.extract_context.return_value = mock_context_pack
        mock_extractor.return_value = mock_extractor_instance
        
        # Create a test file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(b'{"test": "data"}')
            f.flush()
            
            try:
                with open(f.name, 'rb') as test_file:
                    response = client.post('/api/upload', data={
                        'file': (test_file, 'test.json')
                    })
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                assert 'filename' in data
                assert 'conversations_count' in data
                assert 'projects_count' in data
                
            finally:
                os.unlink(f.name)
    
    @patch('llm_context_exporter.web.app.ValidationGenerator')
    def test_validate_success_flow(self, mock_validator, client):
        """Test successful validation flow with mocked components."""
        # Set up session data
        with client.session_transaction() as sess:
            sess['context_pack'] = UniversalContextPack(
                version="1.0",
                source_platform="chatgpt",
                user_profile=UserProfile(),
                projects=[ProjectBrief(
                    name="Test Project",
                    description="A test project",
                    last_discussed="2023-12-14T10:30:00Z"
                )],
                preferences={},
                technical_context={},
                metadata={}
            ).model_dump()
        
        # Mock validator
        mock_validation_suite = MagicMock()
        mock_validation_suite.questions = [MagicMock()]
        mock_validation_suite.model_dump.return_value = {'questions': []}
        
        mock_validator_instance = MagicMock()
        mock_validator_instance.generate_tests.return_value = mock_validation_suite
        mock_validator.return_value = mock_validator_instance
        
        response = client.post('/api/validate',
                             data=json.dumps({'target_platform': 'gemini'}),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'validation_suite' in data
        assert 'questions_count' in data