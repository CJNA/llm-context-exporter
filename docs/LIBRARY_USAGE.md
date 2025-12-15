# Library Usage Guide

This guide demonstrates how to use the LLM Context Exporter as a Python library in your own applications.

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Core Components](#core-components)
- [Advanced Usage](#advanced-usage)
- [Security Features](#security-features)
- [Web Integration](#web-integration)
- [Custom Adapters](#custom-adapters)
- [Error Handling](#error-handling)
- [Performance Optimization](#performance-optimization)

## Installation

```bash
# Install the library
pip install llm-context-exporter

# For development features
pip install llm-context-exporter[dev]

# For all optional dependencies
pip install llm-context-exporter[dev,test]
```

## Basic Usage

### Simple Export

```python
from llm_context_exporter import ExportHandler, ExportConfig

# Create export configuration
config = ExportConfig(
    input_path="chatgpt_export.zip",
    target_platform="gemini",
    output_path="./output",
    interactive=False
)

# Perform export
handler = ExportHandler()
results = handler.export(config)

if results["success"]:
    print(f"Export completed! Files: {results['output_files']}")
    print(f"Projects found: {results['metadata']['projects_extracted']}")
else:
    print(f"Export failed: {results['errors']}")
```

### Quick Context Extraction

```python
from llm_context_exporter.parsers.chatgpt import ChatGPTParser
from llm_context_exporter.core.extractor import ContextExtractor

# Parse ChatGPT export
parser = ChatGPTParser()
parsed_export = parser.parse_export("chatgpt_export.zip")

# Extract context
extractor = ContextExtractor()
context_pack = extractor.extract_context(parsed_export.conversations)

print(f"Found {len(context_pack.projects)} projects")
print(f"User role: {context_pack.user_profile.role}")
print(f"Languages: {context_pack.technical_context.languages}")
```

## Core Components

### 1. Parsing ChatGPT Exports

```python
from llm_context_exporter.parsers.chatgpt import ChatGPTParser
from llm_context_exporter.core.compatibility import CompatibilityManager

# Initialize parser
parser = ChatGPTParser()

# Check format compatibility first
compatibility = CompatibilityManager()
diagnostic = compatibility.detect_format_with_diagnostics("export.zip", ChatGPTParser)

print(f"Format version: {diagnostic.detected_version}")
print(f"Compatibility: {diagnostic.compatibility_level}")

if diagnostic.compatibility_level.value in ['full', 'partial']:
    # Parse the export
    parsed_export = parser.parse_export("export.zip")
    
    print(f"Conversations: {len(parsed_export.conversations)}")
    print(f"Export date: {parsed_export.export_date}")
    print(f"Format version: {parsed_export.format_version}")
else:
    print("Export format not supported")
    for issue in diagnostic.issues:
        print(f"Issue: {issue}")
```

### 2. Context Extraction

```python
from llm_context_exporter.core.extractor import ContextExtractor
from datetime import datetime, timedelta

# Initialize extractor
extractor = ContextExtractor()

# Extract context from conversations
context_pack = extractor.extract_context(parsed_export.conversations)

# Access extracted information
print("User Profile:")
print(f"  Role: {context_pack.user_profile.role}")
print(f"  Expertise: {context_pack.user_profile.expertise_areas}")
print(f"  Background: {context_pack.user_profile.background_summary}")

print("\nProjects:")
for project in context_pack.projects:
    print(f"  - {project.name}: {project.description[:50]}...")
    print(f"    Tech stack: {', '.join(project.tech_stack)}")
    print(f"    Status: {project.current_status}")
    print(f"    Relevance: {project.relevance_score:.2f}")

print("\nTechnical Context:")
print(f"  Languages: {context_pack.technical_context.languages}")
print(f"  Frameworks: {context_pack.technical_context.frameworks}")
print(f"  Tools: {context_pack.technical_context.tools}")

print("\nPreferences:")
print(f"  Coding style: {context_pack.preferences.coding_style}")
print(f"  Communication: {context_pack.preferences.communication_style}")
print(f"  Preferred tools: {context_pack.preferences.preferred_tools}")
```

### 3. Filtering and Selection

```python
from llm_context_exporter.core.filter import FilterEngine
from llm_context_exporter.models.core import FilterConfig
from datetime import datetime, timedelta

# Create filter configuration
filter_config = FilterConfig(
    excluded_conversation_ids=["conv_123", "conv_456"],
    excluded_topics=["personal", "private", "casual"],
    date_range=(
        datetime.now() - timedelta(days=365),  # Last year only
        datetime.now()
    ),
    min_relevance_score=0.6
)

# Apply filters
filter_engine = FilterEngine()
filtered_context = filter_engine.apply_filters(context_pack, filter_config)

print(f"Original projects: {len(context_pack.projects)}")
print(f"Filtered projects: {len(filtered_context.projects)}")

# Save filter preferences for future use
filter_engine.save_filter_preferences(filter_config)

# Load saved preferences
saved_filters = filter_engine.load_filter_preferences()
```

### 4. Platform Formatting

#### Gemini Formatter

```python
from llm_context_exporter.formatters.gemini import GeminiFormatter

# Initialize formatter
formatter = GeminiFormatter()

# Format for Gemini
gemini_output = formatter.format_for_gemini(context_pack)

print("Gemini Output:")
print(f"Text length: {len(gemini_output.formatted_text)} characters")
print(f"Instructions: {len(gemini_output.instructions)} steps")

# Check size limits
size_check = formatter.check_size_limits(gemini_output.formatted_text)
if not size_check.within_limits:
    print(f"Content too large by {size_check.excess_chars} characters")
    
    # Prioritize content to fit limits
    prioritized_context = formatter.prioritize_content(
        context_pack, 
        size_check.max_size
    )
    gemini_output = formatter.format_for_gemini(prioritized_context)

# Save formatted output
with open("gemini_context.txt", "w", encoding="utf-8") as f:
    f.write(gemini_output.formatted_text)

with open("gemini_instructions.txt", "w", encoding="utf-8") as f:
    f.write(gemini_output.instructions)
```

#### Ollama Formatter

```python
from llm_context_exporter.formatters.ollama import OllamaFormatter

# Initialize formatter
formatter = OllamaFormatter()

# Format for Ollama
ollama_output = formatter.format_for_ollama(context_pack, base_model="qwen")

print("Ollama Output:")
print(f"Modelfile length: {len(ollama_output.modelfile_content)} characters")
print(f"Setup commands: {len(ollama_output.setup_commands)}")
print(f"Test commands: {len(ollama_output.test_commands)}")

# Handle large contexts
if len(ollama_output.supplementary_files) > 0:
    print(f"Large context split into {len(ollama_output.supplementary_files)} files")

# Save Modelfile
with open("Modelfile", "w", encoding="utf-8") as f:
    f.write(ollama_output.modelfile_content)

# Save supplementary files
for filename, content in ollama_output.supplementary_files.items():
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

# Print setup instructions
print("\nSetup Commands:")
for cmd in ollama_output.setup_commands:
    print(f"  {cmd}")

print("\nTest Commands:")
for cmd in ollama_output.test_commands:
    print(f"  {cmd}")
```

### 5. Validation Generation

```python
from llm_context_exporter.validation.generator import ValidationGenerator

# Initialize validator
validator = ValidationGenerator()

# Generate validation tests
validation_suite = validator.generate_tests(context_pack, "gemini")

print(f"Generated {len(validation_suite.questions)} validation questions")

# Organize questions by category
categories = {}
for question in validation_suite.questions:
    if question.category not in categories:
        categories[question.category] = []
    categories[question.category].append(question)

for category, questions in categories.items():
    print(f"\n{category.upper()} Questions:")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q.question}")
        print(f"     Expected: {q.expected_answer_summary}")

# Access platform-specific artifacts
if validation_suite.target_platform == "gemini":
    checklist = validation_suite.platform_artifacts["checklist"]
    print(f"\nGemini Checklist ({len(checklist)} items):")
    for item in checklist:
        print(f"  {item['check']} {item['action']}")

elif validation_suite.target_platform == "ollama":
    commands = validation_suite.platform_artifacts["commands"]
    print(f"\nOllama Commands ({len(commands)} commands):")
    for cmd in commands:
        print(f"  {cmd['command']}")
```

## Advanced Usage

### Incremental Updates

```python
from llm_context_exporter.core.incremental import IncrementalUpdater
from llm_context_exporter.parsers.chatgpt import ChatGPTParser
from llm_context_exporter.core.extractor import ContextExtractor

# Initialize components
updater = IncrementalUpdater()
parser = ChatGPTParser()
extractor = ContextExtractor()

# Load previous context
previous_context = updater.load_previous_context("previous_context.json")

# Parse new export
new_export = parser.parse_export("new_chatgpt_export.zip")
new_context = extractor.extract_context(new_export.conversations)

# Detect new conversations
new_conversations = updater.detect_new_conversations(
    previous_context, 
    new_export.conversations
)

print(f"Found {len(new_conversations)} new conversations")

# Merge contexts
merged_context = updater.merge_contexts(previous_context, new_context)

print(f"Previous projects: {len(previous_context.projects)}")
print(f"New projects: {len(new_context.projects)}")
print(f"Merged projects: {len(merged_context.projects)}")

# Generate delta package
delta_package = updater.generate_delta_package(previous_context, new_context)

print(f"Delta contains {len(delta_package.projects)} new/updated projects")

# Save updated context
updater.save_context_pack(merged_context, "updated_context.json")
updater.save_context_pack(delta_package, "delta_package.json")
```

### Custom Context Processing

```python
from llm_context_exporter.models.core import (
    UniversalContextPack, UserProfile, ProjectBrief, 
    UserPreferences, TechnicalContext
)
from datetime import datetime

# Create custom context pack
custom_context = UniversalContextPack(
    version="1.0.0",
    created_at=datetime.now(),
    source_platform="custom",
    user_profile=UserProfile(
        role="Senior Data Scientist",
        expertise_areas=["Python", "Machine Learning", "Statistics"],
        background_summary="Experienced data scientist with focus on NLP"
    ),
    projects=[
        ProjectBrief(
            name="Customer Sentiment Analysis",
            description="ML pipeline for analyzing customer feedback sentiment",
            tech_stack=["Python", "TensorFlow", "BERT", "Apache Kafka"],
            key_challenges=["Real-time processing", "Model accuracy"],
            current_status="In production",
            last_discussed=datetime.now(),
            relevance_score=0.9
        )
    ],
    preferences=UserPreferences(
        coding_style={
            "primary_language": "Python",
            "style_guide": "PEP 8",
            "preferences": ["clean", "well-documented"]
        },
        communication_style="Technical and detailed",
        preferred_tools=["Jupyter", "VS Code", "Git", "Docker"],
        work_patterns={
            "methodology": "Agile",
            "testing_approach": "Unit testing",
            "documentation_level": "Comprehensive"
        }
    ),
    technical_context=TechnicalContext(
        languages=["Python", "R", "SQL"],
        frameworks=["TensorFlow", "PyTorch", "Scikit-learn"],
        tools=["Jupyter", "Docker", "Kubernetes", "MLflow"],
        domains=["Machine Learning", "Natural Language Processing", "Statistics"]
    ),
    metadata={"source": "custom_creation"}
)

# Use with formatters
from llm_context_exporter.formatters.gemini import GeminiFormatter

formatter = GeminiFormatter()
output = formatter.format_for_gemini(custom_context)

print("Custom context formatted for Gemini:")
print(output.formatted_text[:200] + "...")
```

## Security Features

### Sensitive Data Detection and Redaction

```python
from llm_context_exporter.security import (
    SensitiveDataDetector, 
    SecurityManager,
    prompt_for_redaction_approval
)

# Initialize security components
detector = SensitiveDataDetector()
security_manager = SecurityManager(
    enable_network_monitoring=True,
    enable_interactive_redaction=True
)

# Detect sensitive data in content
content = """
Project configuration:
Database: postgresql://user:secret123@localhost/mydb
API Key: sk-1234567890abcdef1234567890abcdef
Admin email: admin@company.com
"""

detections = detector.detect_sensitive_data(content)
print(f"Found {len(detections)} sensitive items:")
for detection in detections:
    print(f"  {detection['type']}: {detection['value']}")

# Automatic redaction
redacted_content = detector.redact_sensitive_data(content)
print("\nRedacted content:")
print(redacted_content)

# Interactive redaction with user approval
if detector.has_sensitive_data(content):
    approved_redactions = prompt_for_redaction_approval(detections)
    custom_redacted = detector.redact_with_approval(content, approved_redactions)

# Use security manager for comprehensive protection
with security_manager:
    result = security_manager.process_with_security(
        content,
        context="Project configuration",
        encrypt_output=True
    )

print(f"Sensitive data detected: {result['sensitive_data_detected']}")
print(f"Redaction applied: {result['redaction_applied']}")
print(f"Content encrypted: {result['encrypted']}")
print(f"Network violations: {len(result['network_violations'])}")
```

### File Encryption

```python
from llm_context_exporter.security.encryption import FileEncryption
import tempfile
import os

# Initialize encryption
encryption = FileEncryption()

# Create test file
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
    f.write('{"sensitive": "data", "api_key": "secret123"}')
    test_file = f.name

try:
    # Encrypt file
    password = "secure_password_123"
    encrypted_file = encryption.encrypt_file(test_file, password)
    
    print(f"File encrypted: {encrypted_file}")
    print(f"Is encrypted: {encryption.is_encrypted_file(encrypted_file)}")
    
    # Decrypt file
    decrypted_file = encrypted_file.replace('.enc', '_decrypted.json')
    encryption.decrypt_file(encrypted_file, password, decrypted_file)
    
    # Verify content
    with open(decrypted_file, 'r') as f:
        decrypted_content = f.read()
    
    print(f"Decryption successful: {decrypted_content}")
    
finally:
    # Clean up
    for f in [test_file, encrypted_file, decrypted_file]:
        if os.path.exists(f):
            os.unlink(f)
```

### Network Monitoring

```python
from llm_context_exporter.security.network_monitor import NetworkActivityMonitor

# Initialize monitor
monitor = NetworkActivityMonitor()

# Monitor network activity during processing
monitor.start_monitoring()

try:
    # Your processing code here
    # Any network calls will be detected
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.close()
    
finally:
    monitor.stop_monitoring()

# Check for network activity
calls = monitor.get_network_calls()
if calls:
    print(f"Warning: {len(calls)} network calls detected:")
    for call in calls:
        print(f"  {call['type']}: {call.get('args', '')}")
else:
    print("No network activity detected - processing was local-only")

# Use context manager for strict monitoring
try:
    with monitor.monitor_context(strict=True):
        # This will raise an exception if any network activity occurs
        # Your processing code here
        pass
    print("Processing completed with no network activity")
except Exception as e:
    print(f"Network activity detected: {e}")
```

## Web Integration

### Flask Integration

```python
from flask import Flask, request, jsonify
from llm_context_exporter import ExportHandler, ExportConfig
from llm_context_exporter.core.payment import PaymentManager
import tempfile
import os

app = Flask(__name__)

# Initialize components
export_handler = ExportHandler()
payment_manager = PaymentManager()

@app.route('/api/export', methods=['POST'])
def api_export():
    """API endpoint for context export."""
    try:
        # Get uploaded file
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        target = request.form.get('target', 'gemini')
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            file.save(tmp.name)
            input_path = tmp.name
        
        # Create output directory
        output_dir = tempfile.mkdtemp()
        
        try:
            # Check payment requirements
            user_context = {
                'source': 'web',
                'email': request.form.get('email', '')
            }
            
            if payment_manager.requires_payment(user_context):
                payment_intent_id = request.form.get('payment_intent_id')
                if not payment_intent_id or not payment_manager.verify_payment(payment_intent_id):
                    return jsonify({'error': 'Payment required'}), 402
            
            # Perform export
            config = ExportConfig(
                input_path=input_path,
                target_platform=target,
                output_path=output_dir,
                interactive=False
            )
            
            results = export_handler.export(config)
            
            if results['success']:
                return jsonify({
                    'success': True,
                    'output_files': results['output_files'],
                    'metadata': results['metadata']
                })
            else:
                return jsonify({
                    'success': False,
                    'errors': results['errors']
                }), 400
                
        finally:
            # Clean up temporary files
            os.unlink(input_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment/create', methods=['POST'])
def create_payment():
    """Create payment intent."""
    try:
        amount = request.json.get('amount', 300)  # $3.00 default
        currency = request.json.get('currency', 'usd')
        
        payment_intent = payment_manager.create_payment_intent(amount, currency)
        
        return jsonify({
            'client_secret': payment_intent.client_secret,
            'payment_intent_id': payment_intent.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
```

### Django Integration

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from llm_context_exporter import ExportHandler, ExportConfig
import json
import tempfile
import os

@csrf_exempt
@require_http_methods(["POST"])
def export_context(request):
    """Django view for context export."""
    try:
        # Parse request
        data = json.loads(request.body)
        target = data.get('target', 'gemini')
        
        # Handle file upload (assuming file is base64 encoded)
        file_content = data.get('file_content')
        if not file_content:
            return JsonResponse({'error': 'No file content provided'}, status=400)
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            tmp.write(base64.b64decode(file_content))
            input_path = tmp.name
        
        # Create output directory
        output_dir = tempfile.mkdtemp()
        
        try:
            # Perform export
            handler = ExportHandler()
            config = ExportConfig(
                input_path=input_path,
                target_platform=target,
                output_path=output_dir,
                interactive=False
            )
            
            results = handler.export(config)
            
            return JsonResponse({
                'success': results['success'],
                'output_files': results.get('output_files', []),
                'metadata': results.get('metadata', {}),
                'errors': results.get('errors', [])
            })
            
        finally:
            # Clean up
            os.unlink(input_path)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

## Custom Adapters

### Creating a Custom Parser

```python
from llm_context_exporter.parsers.base import PlatformParser
from llm_context_exporter.models.core import ParsedExport, Conversation, Message
from datetime import datetime
import json

class CustomPlatformParser(PlatformParser):
    """Parser for custom platform export files."""
    
    def parse_export(self, file_path: str) -> ParsedExport:
        """Parse custom platform export file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conversations = []
        for conv_data in data.get('conversations', []):
            messages = []
            for msg_data in conv_data.get('messages', []):
                message = Message(
                    role=msg_data['role'],
                    content=msg_data['content'],
                    timestamp=datetime.fromisoformat(msg_data['timestamp']),
                    metadata=msg_data.get('metadata', {})
                )
                messages.append(message)
            
            conversation = Conversation(
                id=conv_data['id'],
                title=conv_data.get('title', 'Untitled'),
                created_at=datetime.fromisoformat(conv_data['created_at']),
                updated_at=datetime.fromisoformat(conv_data['updated_at']),
                messages=messages
            )
            conversations.append(conversation)
        
        return ParsedExport(
            format_version=data.get('version', '1.0'),
            export_date=datetime.fromisoformat(data['export_date']),
            conversations=conversations,
            metadata=data.get('metadata', {})
        )
    
    def detect_format_version(self, file_path: str) -> str:
        """Detect export format version."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('version', '1.0')
        except:
            return 'unknown'

# Usage
parser = CustomPlatformParser()
parsed_export = parser.parse_export('custom_export.json')
print(f"Parsed {len(parsed_export.conversations)} conversations")
```

### Creating a Custom Formatter

```python
from llm_context_exporter.formatters.base import PlatformFormatter
from llm_context_exporter.models.core import UniversalContextPack

class CustomPlatformFormatter(PlatformFormatter):
    """Formatter for custom platform context format."""
    
    def format_context(self, context: UniversalContextPack) -> dict:
        """Format context for custom platform."""
        
        # Create custom format
        formatted_content = self._create_custom_format(context)
        
        return {
            'formatted_content': formatted_content,
            'setup_instructions': self._generate_setup_instructions(),
            'validation_tests': self._generate_validation_tests(context),
            'metadata': {
                'format_version': '1.0',
                'created_at': context.created_at.isoformat(),
                'projects_count': len(context.projects)
            }
        }
    
    def _create_custom_format(self, context: UniversalContextPack) -> str:
        """Create custom platform-specific format."""
        sections = []
        
        # User profile section
        sections.append("# User Profile")
        sections.append(f"Role: {context.user_profile.role}")
        sections.append(f"Expertise: {', '.join(context.user_profile.expertise_areas)}")
        sections.append(f"Background: {context.user_profile.background_summary}")
        sections.append("")
        
        # Projects section
        sections.append("# Projects")
        for project in context.projects:
            sections.append(f"## {project.name}")
            sections.append(f"Description: {project.description}")
            sections.append(f"Tech Stack: {', '.join(project.tech_stack)}")
            sections.append(f"Status: {project.current_status}")
            sections.append("")
        
        # Technical context
        sections.append("# Technical Skills")
        sections.append(f"Languages: {', '.join(context.technical_context.languages)}")
        sections.append(f"Frameworks: {', '.join(context.technical_context.frameworks)}")
        sections.append(f"Tools: {', '.join(context.technical_context.tools)}")
        sections.append("")
        
        return "\n".join(sections)
    
    def _generate_setup_instructions(self) -> list:
        """Generate setup instructions for custom platform."""
        return [
            "1. Copy the formatted content below",
            "2. Open your custom platform settings",
            "3. Navigate to the 'Context' or 'Profile' section",
            "4. Paste the content into the appropriate field",
            "5. Save the settings",
            "6. Test with the validation questions"
        ]
    
    def _generate_validation_tests(self, context: UniversalContextPack) -> list:
        """Generate validation tests for custom platform."""
        tests = []
        
        # Project-based questions
        for project in context.projects[:3]:  # Top 3 projects
            tests.append({
                'question': f"What do you know about my {project.name} project?",
                'expected': f"Should mention {project.description[:50]}... and tech stack: {', '.join(project.tech_stack[:3])}"
            })
        
        # Technical questions
        if context.technical_context.languages:
            tests.append({
                'question': "What programming languages do I use?",
                'expected': f"Should mention {', '.join(context.technical_context.languages[:3])}"
            })
        
        return tests

# Usage
formatter = CustomPlatformFormatter()
output = formatter.format_context(context_pack)

print("Custom format output:")
print(output['formatted_content'][:200] + "...")
print(f"\nSetup instructions: {len(output['setup_instructions'])} steps")
print(f"Validation tests: {len(output['validation_tests'])} questions")
```

## Error Handling

### Comprehensive Error Handling

```python
from llm_context_exporter import ExportHandler, ExportConfig
from llm_context_exporter.parsers.chatgpt import ChatGPTParser
from llm_context_exporter.core.exceptions import (
    ParseError, 
    UnsupportedFormatError, 
    ValidationError,
    SecurityError
)
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_export(input_path: str, target: str, output_path: str):
    """Safely perform export with comprehensive error handling."""
    try:
        # Validate inputs
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if target not in ['gemini', 'ollama']:
            raise ValueError(f"Unsupported target platform: {target}")
        
        # Create configuration
        config = ExportConfig(
            input_path=input_path,
            target_platform=target,
            output_path=output_path,
            interactive=False
        )
        
        # Perform export
        handler = ExportHandler()
        results = handler.export(config)
        
        if results['success']:
            logger.info(f"Export completed successfully: {results['output_files']}")
            return results
        else:
            logger.error(f"Export failed: {results['errors']}")
            return results
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return {'success': False, 'errors': [str(e)]}
        
    except UnsupportedFormatError as e:
        logger.error(f"Unsupported format: {e}")
        return {'success': False, 'errors': [f"Export format not supported: {e}"]}
        
    except ParseError as e:
        logger.error(f"Parse error: {e}")
        return {'success': False, 'errors': [f"Failed to parse export file: {e}"]}
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return {'success': False, 'errors': [f"Context validation failed: {e}"]}
        
    except SecurityError as e:
        logger.error(f"Security error: {e}")
        return {'success': False, 'errors': [f"Security violation detected: {e}"]}
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {'success': False, 'errors': [f"Unexpected error: {e}"]}

# Usage
result = safe_export("chatgpt_export.zip", "gemini", "./output")
if result['success']:
    print("Export completed successfully!")
else:
    print(f"Export failed: {result['errors']}")
```

### Retry Logic

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1.0, backoff=2.0):
    """Decorator to retry operations on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        raise e
                    
                    wait_time = delay * (backoff ** (retries - 1))
                    logger.warning(f"Attempt {retries} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3, delay=2.0)
def robust_parse_export(file_path: str):
    """Parse export with retry logic."""
    parser = ChatGPTParser()
    return parser.parse_export(file_path)

# Usage
try:
    parsed_export = robust_parse_export("chatgpt_export.zip")
    print(f"Successfully parsed {len(parsed_export.conversations)} conversations")
except Exception as e:
    print(f"Failed to parse after retries: {e}")
```

## Performance Optimization

### Batch Processing

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from llm_context_exporter import ExportHandler, ExportConfig
import os
from pathlib import Path

def process_single_export(input_file: str, target: str, output_dir: str):
    """Process a single export file."""
    try:
        config = ExportConfig(
            input_path=input_file,
            target_platform=target,
            output_path=os.path.join(output_dir, Path(input_file).stem),
            interactive=False
        )
        
        handler = ExportHandler()
        results = handler.export(config)
        
        return {
            'file': input_file,
            'success': results['success'],
            'output_files': results.get('output_files', []),
            'errors': results.get('errors', [])
        }
        
    except Exception as e:
        return {
            'file': input_file,
            'success': False,
            'errors': [str(e)]
        }

def batch_process_exports(input_files: list, target: str, output_dir: str, max_workers: int = 4):
    """Process multiple export files in parallel."""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_single_export, file, target, output_dir): file
            for file in input_files
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
                
                if result['success']:
                    print(f"✓ Processed {file}")
                else:
                    print(f"✗ Failed {file}: {result['errors']}")
                    
            except Exception as e:
                print(f"✗ Exception processing {file}: {e}")
                results.append({
                    'file': file,
                    'success': False,
                    'errors': [str(e)]
                })
    
    return results

# Usage
export_files = [
    "export1.zip",
    "export2.zip", 
    "export3.zip"
]

results = batch_process_exports(export_files, "gemini", "./batch_output", max_workers=2)

successful = [r for r in results if r['success']]
failed = [r for r in results if not r['success']]

print(f"\nBatch processing complete:")
print(f"Successful: {len(successful)}")
print(f"Failed: {len(failed)}")
```

### Memory-Efficient Processing

```python
from llm_context_exporter.parsers.chatgpt import ChatGPTParser
from llm_context_exporter.core.extractor import ContextExtractor
import gc

def memory_efficient_processing(file_path: str, chunk_size: int = 100):
    """Process large exports in chunks to manage memory usage."""
    parser = ChatGPTParser()
    extractor = ContextExtractor()
    
    # Parse export
    parsed_export = parser.parse_export(file_path)
    total_conversations = len(parsed_export.conversations)
    
    print(f"Processing {total_conversations} conversations in chunks of {chunk_size}")
    
    all_projects = []
    all_technical_context = []
    
    # Process conversations in chunks
    for i in range(0, total_conversations, chunk_size):
        chunk_end = min(i + chunk_size, total_conversations)
        chunk_conversations = parsed_export.conversations[i:chunk_end]
        
        print(f"Processing chunk {i//chunk_size + 1}: conversations {i+1}-{chunk_end}")
        
        # Extract context from chunk
        chunk_context = extractor.extract_context(chunk_conversations)
        
        # Accumulate results
        all_projects.extend(chunk_context.projects)
        all_technical_context.append(chunk_context.technical_context)
        
        # Force garbage collection
        del chunk_conversations
        del chunk_context
        gc.collect()
    
    print(f"Processed {len(all_projects)} total projects")
    return all_projects, all_technical_context

# Usage
projects, tech_contexts = memory_efficient_processing("large_export.zip", chunk_size=50)
```

This comprehensive library usage guide covers all the major functionality and integration patterns for using the LLM Context Exporter as a Python library in your own applications.