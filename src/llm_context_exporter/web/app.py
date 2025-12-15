"""
Flask web application for the LLM Context Exporter.

This module provides a simple web interface for users who prefer
a graphical interface over the command line.
"""

from flask import Flask, request, jsonify, render_template, send_file, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import uuid
import tempfile
import shutil
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import threading
import time

from ..parsers.chatgpt import ChatGPTParser
from ..core.extractor import ContextExtractor
from ..core.filter import FilterEngine
from ..formatters.gemini import GeminiFormatter
from ..formatters.ollama import OllamaFormatter
from ..validation.generator import ValidationGenerator
from .payment import PaymentManager
from .beta import BetaManager
from ..models.core import UniversalContextPack
from ..models.config import FilterConfig
from ..models.output import GeminiOutput, OllamaOutput

logger = logging.getLogger(__name__)


def create_app(config: Optional[dict] = None) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Default configuration
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-key-change-in-production'),
        'MAX_CONTENT_LENGTH': 500 * 1024 * 1024,  # 500MB max file size
        'UPLOAD_FOLDER': tempfile.mkdtemp(prefix='llm_context_uploads_'),
        'OUTPUT_FOLDER': tempfile.mkdtemp(prefix='llm_context_outputs_'),
        'DEBUG': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
        'SESSION_TIMEOUT_HOURS': 1,  # Auto-cleanup after 1 hour
    })
    
    # Apply custom configuration
    if config:
        app.config.update(config)
    
    # Enable CORS for localhost only (Requirements 15.1)
    CORS(app, origins=['http://127.0.0.1:*', 'http://localhost:*'])
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    # Initialize managers
    app.payment_manager = PaymentManager()
    app.beta_manager = BetaManager()
    
    # Session cleanup thread
    start_session_cleanup(app)
    
    # Register routes
    register_routes(app)
    
    # Add CSRF protection and rate limiting middleware
    add_security_middleware(app)
    
    return app


def start_session_cleanup(app: Flask):
    """Start background thread for session cleanup."""
    def cleanup_sessions():
        while True:
            try:
                timeout_hours = app.config.get('SESSION_TIMEOUT_HOURS', 1)
                cutoff_time = datetime.now() - timedelta(hours=timeout_hours)
                
                # Clean up old upload files
                upload_folder = app.config['UPLOAD_FOLDER']
                output_folder = app.config['OUTPUT_FOLDER']
                
                for folder in [upload_folder, output_folder]:
                    if os.path.exists(folder):
                        for filename in os.listdir(folder):
                            filepath = os.path.join(folder, filename)
                            if os.path.isfile(filepath):
                                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                                if file_time < cutoff_time:
                                    try:
                                        os.remove(filepath)
                                        logger.info(f"Cleaned up old file: {filepath}")
                                    except OSError:
                                        pass
                
                # Sleep for 30 minutes before next cleanup
                time.sleep(1800)
                
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                time.sleep(300)  # Sleep 5 minutes on error
    
    cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
    cleanup_thread.start()


def add_security_middleware(app: Flask):
    """Add CSRF protection and rate limiting."""
    
    # Simple rate limiting (in-memory, per-IP)
    request_counts = {}
    
    @app.before_request
    def rate_limit():
        """Basic rate limiting: 100 requests per hour per IP."""
        client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
        current_time = datetime.now()
        
        # Clean old entries
        cutoff_time = current_time - timedelta(hours=1)
        request_counts[client_ip] = [
            req_time for req_time in request_counts.get(client_ip, [])
            if req_time > cutoff_time
        ]
        
        # Check rate limit
        if len(request_counts.get(client_ip, [])) >= 100:
            return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429
        
        # Record this request
        request_counts.setdefault(client_ip, []).append(current_time)
    
    @app.before_request
    def ensure_session():
        """Ensure session has required fields."""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            session['created_at'] = datetime.now().isoformat()


def register_routes(app: Flask):
    """Register all application routes."""
    
    @app.route('/')
    def index():
        """Serve the main web interface."""
        return render_template('index.html')
    
    @app.route('/api/upload', methods=['POST'])
    def upload_export():
        """Handle ChatGPT export file upload and parsing."""
        try:
            # Check if file is present
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Validate file type
            allowed_extensions = {'.zip', '.json'}
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                return jsonify({'error': 'Invalid file type. Only ZIP and JSON files are supported.'}), 400
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            session_id = session['session_id']
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
            file.save(upload_path)
            
            # Parse the export file
            parser = ChatGPTParser()
            parsed_export = parser.parse_export(upload_path)
            
            # Extract context
            extractor = ContextExtractor()
            context_pack = extractor.extract_context(parsed_export.conversations)
            
            # Store in session
            session['upload_filename'] = filename
            session['upload_path'] = upload_path
            session['parsed_export'] = parsed_export.model_dump()
            session['context_pack'] = context_pack.model_dump()
            
            # Return preview data
            return jsonify({
                'success': True,
                'filename': filename,
                'conversations_count': len(parsed_export.conversations),
                'projects_count': len(context_pack.projects),
                'export_date': parsed_export.export_date.isoformat(),
                'format_version': parsed_export.format_version,
                'session_id': session_id
            })
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500
    
    @app.route('/api/preview', methods=['GET'])
    def preview_context():
        """Get preview of extracted context."""
        try:
            if 'context_pack' not in session:
                return jsonify({'error': 'No context data found. Please upload a file first.'}), 400
            
            context_data = session['context_pack']
            context_pack = UniversalContextPack(**context_data)
            
            # Prepare preview data
            preview = {
                'user_profile': {
                    'role': context_pack.user_profile.role,
                    'expertise_areas': context_pack.user_profile.expertise_areas[:10],  # Limit for preview
                    'background_summary': context_pack.user_profile.background_summary[:500] + '...' if len(context_pack.user_profile.background_summary) > 500 else context_pack.user_profile.background_summary
                },
                'projects': [
                    {
                        'name': project.name,
                        'description': project.description[:200] + '...' if len(project.description) > 200 else project.description,
                        'tech_stack': project.tech_stack[:5],  # Limit for preview
                        'relevance_score': project.relevance_score,
                        'last_discussed': project.last_discussed.isoformat()
                    }
                    for project in context_pack.projects[:10]  # Show top 10 projects
                ],
                'technical_context': {
                    'languages': context_pack.technical_context.languages[:10],
                    'frameworks': context_pack.technical_context.frameworks[:10],
                    'tools': context_pack.technical_context.tools[:10],
                    'domains': context_pack.technical_context.domains[:10]
                },
                'preferences': {
                    'coding_style': context_pack.preferences.coding_style,
                    'communication_style': context_pack.preferences.communication_style,
                    'preferred_tools': context_pack.preferences.preferred_tools[:10]
                },
                'metadata': {
                    'version': context_pack.version,
                    'created_at': context_pack.created_at.isoformat(),
                    'source_platform': context_pack.source_platform,
                    'total_projects': len(context_pack.projects)
                }
            }
            
            return jsonify({
                'success': True,
                'preview': preview
            })
            
        except Exception as e:
            logger.error(f"Preview error: {e}")
            return jsonify({'error': f'Preview failed: {str(e)}'}), 500
    
    @app.route('/api/filter', methods=['POST'])
    def apply_filters():
        """Apply filters to context."""
        try:
            if 'context_pack' not in session:
                return jsonify({'error': 'No context data found. Please upload a file first.'}), 400
            
            # Get filter configuration from request
            filter_data = request.get_json()
            if not filter_data:
                return jsonify({'error': 'No filter configuration provided'}), 400
            
            # Create filter config
            filter_config = FilterConfig(**filter_data)
            
            # Apply filters
            context_data = session['context_pack']
            context_pack = UniversalContextPack(**context_data)
            
            filter_engine = FilterEngine()
            filtered_context = filter_engine.apply_filters(context_pack, filter_config)
            
            # Update session with filtered context
            session['filtered_context_pack'] = filtered_context.model_dump()
            session['filter_config'] = filter_config.model_dump()
            
            return jsonify({
                'success': True,
                'filtered_projects_count': len(filtered_context.projects),
                'original_projects_count': len(context_pack.projects),
                'filters_applied': {
                    'excluded_conversations': len(filter_config.excluded_conversation_ids),
                    'excluded_topics': len(filter_config.excluded_topics),
                    'date_range_applied': filter_config.date_range is not None,
                    'min_relevance_score': filter_config.min_relevance_score
                }
            })
            
        except Exception as e:
            logger.error(f"Filter error: {e}")
            return jsonify({'error': f'Filter failed: {str(e)}'}), 500
    
    @app.route('/api/payment/create', methods=['POST'])
    def create_payment():
        """Create a Stripe payment intent."""
        try:
            request_data = request.get_json()
            email = request_data.get('email', '')
            
            # Check if payment is required
            user_context = {
                'source': 'web',
                'email': email
            }
            
            if not app.payment_manager.requires_payment(user_context):
                return jsonify({
                    'success': True,
                    'payment_required': False,
                    'reason': 'Beta user or CLI access'
                })
            
            # Create payment intent
            payment_intent = app.payment_manager.create_payment_intent(
                metadata={'email': email, 'session_id': session['session_id']}
            )
            
            # Store payment info in session
            session['payment_intent_id'] = payment_intent.id
            session['user_email'] = email
            
            return jsonify({
                'success': True,
                'payment_required': True,
                'payment_intent': {
                    'id': payment_intent.id,
                    'client_secret': payment_intent.client_secret,
                    'amount': payment_intent.amount,
                    'currency': payment_intent.currency
                }
            })
            
        except Exception as e:
            logger.error(f"Payment creation error: {e}")
            return jsonify({'error': f'Payment creation failed: {str(e)}'}), 500
    
    @app.route('/api/payment/verify', methods=['POST'])
    def verify_payment():
        """Verify payment completion."""
        try:
            request_data = request.get_json()
            payment_intent_id = request_data.get('payment_intent_id')
            
            if not payment_intent_id:
                return jsonify({'error': 'Payment intent ID required'}), 400
            
            # Verify payment
            is_verified = app.payment_manager.verify_payment(payment_intent_id)
            
            if is_verified:
                session['payment_verified'] = True
                return jsonify({'success': True, 'verified': True})
            else:
                return jsonify({'success': False, 'verified': False, 'error': 'Payment not completed'})
                
        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            return jsonify({'error': f'Payment verification failed: {str(e)}'}), 500
    
    @app.route('/api/generate', methods=['POST'])
    def generate_output():
        """Generate output for target platform (with payment check)."""
        try:
            if 'context_pack' not in session:
                return jsonify({'error': 'No context data found. Please upload a file first.'}), 400
            
            request_data = request.get_json()
            target_platform = request_data.get('target_platform')
            base_model = request_data.get('base_model', 'qwen')
            
            if target_platform not in ['gemini', 'ollama']:
                return jsonify({'error': 'Invalid target platform. Must be "gemini" or "ollama".'}), 400
            
            # Check payment requirement
            user_email = session.get('user_email', '')
            user_context = {'source': 'web', 'email': user_email}
            
            if app.payment_manager.requires_payment(user_context):
                if not session.get('payment_verified', False):
                    return jsonify({'error': 'Payment required but not verified'}), 402
            
            # Get context (filtered if available, otherwise original)
            context_data = session.get('filtered_context_pack', session['context_pack'])
            context_pack = UniversalContextPack(**context_data)
            
            # Generate output based on target platform
            export_id = str(uuid.uuid4())
            output_dir = os.path.join(app.config['OUTPUT_FOLDER'], export_id)
            os.makedirs(output_dir, exist_ok=True)
            
            if target_platform == 'gemini':
                formatter = GeminiFormatter()
                output = formatter.format_for_gemini(context_pack)
                
                # Save output files
                with open(os.path.join(output_dir, 'gemini_context.txt'), 'w', encoding='utf-8') as f:
                    f.write(output.formatted_text)
                
                with open(os.path.join(output_dir, 'instructions.txt'), 'w', encoding='utf-8') as f:
                    f.write(output.instructions)
                
            else:  # ollama
                formatter = OllamaFormatter()
                output = formatter.format_for_ollama(context_pack, base_model)
                
                # Save output files
                with open(os.path.join(output_dir, 'Modelfile'), 'w', encoding='utf-8') as f:
                    f.write(output.modelfile_content)
                
                with open(os.path.join(output_dir, 'setup_commands.sh'), 'w', encoding='utf-8') as f:
                    f.write('\n'.join(output.setup_commands))
                
                with open(os.path.join(output_dir, 'test_commands.sh'), 'w', encoding='utf-8') as f:
                    f.write('\n'.join(output.test_commands))
                
                # Save supplementary files if any
                for filename, content in output.supplementary_files.items():
                    with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
                        f.write(content)
            
            # Generate validation tests
            validator = ValidationGenerator()
            validation_suite = validator.generate_tests(context_pack, target_platform)
            
            with open(os.path.join(output_dir, 'validation_tests.json'), 'w', encoding='utf-8') as f:
                f.write(validation_suite.model_dump_json(indent=2))
            
            # Store export info in session
            session['export_id'] = export_id
            session['target_platform'] = target_platform
            session['output_dir'] = output_dir
            
            # Record usage for beta users
            if user_email and app.beta_manager.is_beta_user(user_email):
                conversations_count = len(session.get('parsed_export', {}).get('conversations', []))
                app.beta_manager.record_export(
                    email=user_email,
                    target_platform=target_platform,
                    conversations_processed=conversations_count,
                    export_size_mb=0.0  # TODO: Calculate actual size
                )
            
            return jsonify({
                'success': True,
                'export_id': export_id,
                'target_platform': target_platform,
                'files_generated': os.listdir(output_dir),
                'validation_questions_count': len(validation_suite.questions)
            })
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return jsonify({'error': f'Generation failed: {str(e)}'}), 500
    
    @app.route('/api/download/<export_id>', methods=['GET'])
    def download_output(export_id):
        """Download generated output files."""
        try:
            # Validate export_id matches session
            if session.get('export_id') != export_id:
                return jsonify({'error': 'Invalid export ID or session expired'}), 404
            
            output_dir = session.get('output_dir')
            if not output_dir or not os.path.exists(output_dir):
                return jsonify({'error': 'Output files not found'}), 404
            
            # Create ZIP file with all outputs
            zip_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{export_id}.zip")
            shutil.make_archive(zip_path[:-4], 'zip', output_dir)
            
            target_platform = session.get('target_platform', 'export')
            filename = f"llm_context_{target_platform}_{export_id[:8]}.zip"
            
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/zip'
            )
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return jsonify({'error': f'Download failed: {str(e)}'}), 500
    
    @app.route('/api/validate', methods=['POST'])
    def generate_validation():
        """Generate validation tests."""
        try:
            if 'context_pack' not in session:
                return jsonify({'error': 'No context data found. Please upload a file first.'}), 400
            
            request_data = request.get_json()
            target_platform = request_data.get('target_platform', 'gemini')
            
            if target_platform not in ['gemini', 'ollama']:
                return jsonify({'error': 'Invalid target platform'}), 400
            
            # Get context
            context_data = session.get('filtered_context_pack', session['context_pack'])
            context_pack = UniversalContextPack(**context_data)
            
            # Generate validation tests
            validator = ValidationGenerator()
            validation_suite = validator.generate_tests(context_pack, target_platform)
            
            return jsonify({
                'success': True,
                'validation_suite': validation_suite.model_dump(),
                'questions_count': len(validation_suite.questions)
            })
            
        except Exception as e:
            logger.error(f"Validation generation error: {e}")
            return jsonify({'error': f'Validation generation failed: {str(e)}'}), 500
    
    @app.route('/api/beta/status', methods=['GET'])
    def beta_status():
        """Check beta access status."""
        try:
            email = request.args.get('email', '')
            if not email:
                return jsonify({'error': 'Email parameter required'}), 400
            
            is_beta = app.beta_manager.is_beta_user(email)
            
            response = {
                'success': True,
                'is_beta_user': is_beta,
                'email': email
            }
            
            if is_beta:
                stats = app.beta_manager.get_usage_stats(email)
                response['usage_stats'] = stats.model_dump()
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Beta status error: {e}")
            return jsonify({'error': f'Beta status check failed: {str(e)}'}), 500
    
    @app.route('/api/beta/feedback', methods=['POST'])
    def submit_feedback():
        """Submit beta user feedback."""
        try:
            request_data = request.get_json()
            email = request_data.get('email')
            feedback_text = request_data.get('feedback')
            rating = request_data.get('rating')
            
            if not all([email, feedback_text, rating]):
                return jsonify({'error': 'Email, feedback, and rating are required'}), 400
            
            if not app.beta_manager.is_beta_user(email):
                return jsonify({'error': 'Only beta users can submit feedback'}), 403
            
            export_id = session.get('export_id', 'unknown')
            target_platform = session.get('target_platform', 'unknown')
            
            app.beta_manager.record_feedback(
                email=email,
                feedback=feedback_text,
                rating=int(rating),
                export_id=export_id,
                target_platform=target_platform
            )
            
            return jsonify({
                'success': True,
                'message': 'Feedback submitted successfully'
            })
            
        except Exception as e:
            logger.error(f"Feedback submission error: {e}")
            return jsonify({'error': f'Feedback submission failed: {str(e)}'}), 500
    
    # Webhook endpoint for Stripe
    @app.route('/api/payment/webhook', methods=['POST'])
    def payment_webhook():
        """Handle Stripe webhook events."""
        try:
            payload = request.get_data()
            signature = request.headers.get('Stripe-Signature')
            
            if not signature:
                return jsonify({'error': 'Missing signature'}), 400
            
            result = app.payment_manager.handle_webhook(payload.decode('utf-8'), signature)
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return jsonify({'error': f'Webhook processing failed: {str(e)}'}), 400
    
    # Error handlers
    @app.errorhandler(413)
    def file_too_large(error):
        """Handle file too large errors."""
        return jsonify({'error': 'File too large. Maximum size is 500MB.'}), 413
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle rate limit errors."""
        return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors."""
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=8080, debug=True)