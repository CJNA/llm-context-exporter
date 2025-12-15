# LLM Context Exporter

A privacy-focused, open-source tool for migrating your accumulated context from ChatGPT to other LLM platforms like Google Gemini or local models via Ollama. Break free from vendor lock-in while maintaining the personalized assistance you've built up over time.

## 🚀 Features

- **🔒 Privacy-First**: All processing happens locally on your machine - no data leaves your computer
- **🎯 Multiple Target Platforms**: Export to Gemini Saved Info or Ollama Modelfiles
- **🧠 Intelligent Context Extraction**: Automatically identify projects, preferences, and technical expertise
- **🎛️ Interactive Filtering**: Choose what context to include or exclude
- **🔄 Incremental Updates**: Keep your context current without re-exporting everything
- **✅ Validation Testing**: Verify successful context transfer with generated test questions
- **🌐 Web Interface**: Simple browser-based interface for non-technical users
- **⚡ CLI Tool**: Command-line interface for developers and power users
- **🔐 Security Features**: Encryption, sensitive data detection, and secure deletion
- **💰 Payment Integration**: Optional payment system for hosted web interface

## Project Structure

```
llm-context-exporter/
├── src/llm_context_exporter/
│   ├── core/                   # Core data models and processing logic
│   │   ├── models.py          # Data structures (UniversalContextPack, etc.)
│   │   ├── extractor.py       # Context extraction engine
│   │   └── filter.py          # Filtering and selection engine
│   │
│   ├── parsers/               # Platform-specific input parsers
│   │   ├── base.py           # Abstract parser interface
│   │   └── chatgpt.py        # ChatGPT export parser
│   │
│   ├── formatters/            # Platform-specific output formatters
│   │   ├── base.py           # Abstract formatter interface
│   │   ├── gemini.py         # Gemini Saved Info formatter
│   │   └── ollama.py         # Ollama Modelfile formatter
│   │
│   ├── validation/            # Validation test generation
│   │   └── generator.py      # Test question generator
│   │
│   ├── security/              # Privacy and security features
│   │   ├── encryption.py     # File encryption utilities
│   │   ├── detection.py      # Sensitive data detection
│   │   └── deletion.py       # Secure file deletion
│   │
│   ├── web/                   # Web interface components
│   │   ├── app.py            # Flask application
│   │   ├── payment.py        # Stripe payment processing
│   │   └── beta.py           # Beta user management
│   │
│   └── cli/                   # Command-line interface
│       └── main.py           # CLI implementation
│
├── tests/                     # Test suite
│   ├── conftest.py           # Pytest fixtures
│   └── test_models.py        # Model tests
│
├── requirements.txt           # Python dependencies
├── setup.py                  # Package configuration
├── pytest.ini               # Test configuration
└── README.md                 # This file
```

## 📦 Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install llm-context-exporter
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/llm-context-exporter/llm-context-exporter.git
cd llm-context-exporter

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Option 3: Using pipx (Isolated Installation)

```bash
pipx install llm-context-exporter
```

### System Requirements

- **Python**: 3.10 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: At least 1GB RAM (more for large exports)
- **Storage**: 100MB for installation + space for your exports

### Optional Dependencies

For **Ollama target platform**:
```bash
# Install Ollama (visit https://ollama.ai for platform-specific instructions)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the Qwen model (recommended)
ollama pull qwen
```

For **development**:
```bash
pip install llm-context-exporter[dev,test]
```

## 🚀 Quick Start

### Step 1: Export Your ChatGPT Data

1. Go to [ChatGPT Settings](https://chat.openai.com/settings) → **Data Export**
2. Click **"Export data"** and wait for the email
3. Download the ZIP file when ready

### Step 2: Choose Your Target Platform

```bash
# Compare platforms to help you decide
llm-context-export compare
```

### Step 3: Export Your Context

**For Gemini (Cloud-based):**
```bash
llm-context-export export -i chatgpt_export.zip -t gemini -o ./gemini_output
```

**For Ollama (Local LLM):**
```bash
llm-context-export export -i chatgpt_export.zip -t ollama -o ./ollama_output
```

### Step 4: Use Your Exported Context

**Gemini**: Copy the generated text and paste it into [Gemini Saved Info](https://gemini.google.com)

**Ollama**: Create your custom model:
```bash
ollama create my-context -f ./ollama_output/Modelfile
ollama run my-context
```

### Step 5: Validate the Transfer

```bash
llm-context-export validate -c ./output -t gemini --interactive
```

## 💻 Usage Examples

### Basic Export
```bash
# Simple export to Gemini
llm-context-export export -i chatgpt_export.zip -t gemini -o ./output

# Export to Ollama with specific model
llm-context-export export -i chatgpt_export.zip -t ollama -m qwen -o ./output
```

### Interactive Mode
```bash
# Choose what to include/exclude interactively
llm-context-export export -i chatgpt_export.zip -t gemini -o ./output --interactive
```

### Advanced Filtering
```bash
# Exclude specific topics and set minimum relevance
llm-context-export export -i chatgpt_export.zip -t ollama -o ./output \
  --exclude-topics "personal,private" --min-relevance 0.5
```

### Incremental Updates
```bash
# Add new conversations to existing context
llm-context-export export -i new_export.zip -t gemini -o ./updated \
  --update ./previous/context.json
```

### Web Interface
```bash
# Start local web interface (great for non-technical users)
llm-context-export web
# Open http://localhost:8080 in your browser
```

### Validation and Testing
```bash
# Generate validation questions
llm-context-export validate -c ./output -t gemini

# Interactive validation with step-by-step testing
llm-context-export validate -c ./output -t gemini --interactive
```

### Compatibility Checking
```bash
# Check if your export file is compatible
llm-context-export compatibility -f chatgpt_export.zip -t ollama

# Check Ollama installation
llm-context-export compatibility -t ollama
```

### Delta Packages (Incremental Updates)
```bash
# Generate package with only new information
llm-context-export delta -c new_export.zip -p ./old_context.json -o ./delta
```

## 📋 Context Schema

The LLM Context Exporter uses a standardized **Universal Context Pack** format that's platform-agnostic and designed for maximum portability:

```json
{
  "version": "1.0.0",
  "created_at": "2024-01-15T10:30:00Z",
  "source_platform": "chatgpt",
  "user_profile": {
    "role": "Senior Software Engineer",
    "expertise_areas": ["Python", "Machine Learning", "Web Development"],
    "background_summary": "Experienced full-stack developer with ML expertise"
  },
  "projects": [
    {
      "name": "E-commerce Platform",
      "description": "Building a scalable e-commerce platform with microservices",
      "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL"],
      "key_challenges": ["Performance optimization", "Payment integration"],
      "current_status": "In production",
      "relevance_score": 0.95
    }
  ],
  "preferences": {
    "coding_style": {"language": "Python", "style": "clean and readable"},
    "communication_style": "Direct and technical",
    "preferred_tools": ["VS Code", "Git", "Docker"],
    "work_patterns": {"methodology": "Agile", "testing": "TDD"}
  },
  "technical_context": {
    "languages": ["Python", "JavaScript", "SQL"],
    "frameworks": ["FastAPI", "React", "TensorFlow"],
    "tools": ["Docker", "Kubernetes", "Git"],
    "domains": ["Web Development", "Machine Learning"]
  }
}
```

### Schema Components

- **User Profile**: Role, expertise areas, and background summary
- **Projects**: Detailed project information with tech stacks and challenges
- **Preferences**: Coding style, communication preferences, and work patterns
- **Technical Context**: Languages, frameworks, tools, and domain expertise
- **Metadata**: Version info, timestamps, and processing details

## 🛠️ CLI Reference

### Main Commands

| Command | Description | Example |
|---------|-------------|---------|
| `export` | Export ChatGPT context to target platform | `llm-context-export export -i export.zip -t gemini -o ./output` |
| `validate` | Generate validation tests | `llm-context-export validate -c ./output -t gemini` |
| `compare` | Compare target platforms | `llm-context-export compare` |
| `delta` | Generate incremental update package | `llm-context-export delta -c new.zip -p old.json -o ./delta` |
| `web` | Start web interface | `llm-context-export web --port 8080` |
| `compatibility` | Check platform compatibility | `llm-context-export compatibility -f export.zip -t ollama` |
| `info` | Show platform information | `llm-context-export info --verbose` |
| `examples` | Show usage examples | `llm-context-export examples` |

### Export Command Options

```bash
llm-context-export export [OPTIONS]

Options:
  -i, --input PATH              ChatGPT export file (ZIP or JSON) [required]
  -t, --target [gemini|ollama]  Target platform [required]
  -o, --output PATH             Output directory [required]
  -m, --model TEXT              Base model for Ollama (default: qwen)
  --interactive                 Enable interactive filtering
  --update PATH                 Previous context for incremental update
  --exclude-conversations TEXT  Comma-separated conversation IDs to exclude
  --exclude-topics TEXT         Comma-separated topics to exclude
  --min-relevance FLOAT         Minimum relevance score (0.0-1.0)
  --dry-run                     Preview without creating files
  --help                        Show help message
```

### Admin Commands (Beta Management)

```bash
llm-context-export admin [COMMAND]

Commands:
  list-users                    List all beta users
  add-user                      Add new beta user
  remove-user                   Remove beta user
  user-stats                    Show user statistics
  feedback                      View feedback by rating
  report                        Generate usage report
```

## 📚 Documentation

### Complete Documentation
For comprehensive guides and references, see our [documentation directory](docs/):

- **[CLI Usage Guide](docs/CLI_USAGE_GUIDE.md)** - Complete command-line reference with examples
- **[Library Usage Guide](docs/LIBRARY_USAGE.md)** - Python library integration and API reference  
- **[Context Schema](docs/CONTEXT_SCHEMA.md)** - Universal Context Pack format specification
- **[Admin Guide](docs/ADMIN_GUIDE.md)** - Beta user management and administration
- **[Privacy Policy](docs/PRIVACY_POLICY.md)** - Data handling and privacy practices
- **[Terms of Service](docs/TERMS_OF_SERVICE.md)** - Usage terms and conditions

### Quick Library Example

```python
from llm_context_exporter import ExportHandler, ExportConfig

# Simple export
config = ExportConfig(
    input_path="chatgpt_export.zip",
    target_platform="gemini", 
    output_path="./output"
)

handler = ExportHandler()
results = handler.export(config)

if results["success"]:
    print(f"Export completed! Files: {results['output_files']}")
```

### Code Examples

See the [examples directory](examples/) for comprehensive demonstrations:

- **[library_usage_example.py](examples/library_usage_example.py)** - Complete library integration examples
- **[transfer_examples.py](examples/transfer_examples.py)** - Successful vs unsuccessful transfer scenarios
- **[admin_demo.py](examples/admin_demo.py)** - Beta user management examples
- **[security_demo.py](examples/security_demo.py)** - Security features demonstration
- **[validation_demo.py](examples/validation_demo.py)** - Validation test generation
- **[payment_demo.py](examples/payment_demo.py)** - Payment system integration

## ✅ Examples of Successful Transfers

### What Transfers Well

**Project Context:**
```
✅ "I'm building an e-commerce platform using FastAPI and React"
✅ "The main challenge is handling payment processing with Stripe"
✅ "We're using PostgreSQL for the database and Redis for caching"
```

**Technical Preferences:**
```
✅ "I prefer Python for backend development"
✅ "I use VS Code with the Python extension"
✅ "I follow TDD methodology and write tests first"
```

**Domain Expertise:**
```
✅ "I have experience with machine learning using TensorFlow"
✅ "I'm familiar with Docker and Kubernetes deployment"
✅ "I work primarily in web development and data science"
```

### What May Not Transfer Well

**ChatGPT-Specific Features:**
```
❌ "Use the web browsing feature to check the latest React docs"
❌ "Generate an image of a database schema"
❌ "Run this code in the code interpreter"
```

**Temporal/Contextual References:**
```
❌ "As we discussed earlier in this conversation..."
❌ "Based on the file you uploaded..."
❌ "Following up on yesterday's question..."
```

**Personal/Sensitive Information:**
```
⚠️  "My API key is sk-1234567890abcdef..." (will be detected and redacted)
⚠️  "My email is john@company.com" (will prompt for redaction)
⚠️  "The database password is secret123" (will be flagged)
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/llm_context_exporter --cov-report=html

# Run specific test categories
pytest -m "not integration"  # Unit tests only
pytest -m integration        # Integration tests only
pytest -k "test_parser"      # Parser tests only
```

### Property-Based Testing

The project uses Hypothesis for property-based testing to ensure correctness:

```bash
# Run property-based tests
pytest tests/test_*_properties.py

# Run with more examples
pytest --hypothesis-max-examples=1000
```

### Test Your Own Export

```bash
# Test compatibility of your ChatGPT export
llm-context-export compatibility -f your_export.zip

# Dry run to see what would be extracted
llm-context-export export -i your_export.zip -t gemini -o ./test --dry-run
```

## Architecture

The project follows a modular architecture with clear separation of concerns:

- **Core Layer**: Platform-agnostic data models and processing logic
- **Parser Layer**: Platform-specific input handling (ChatGPT, Claude, etc.)
- **Formatter Layer**: Platform-specific output generation (Gemini, Ollama, etc.)
- **Interface Layer**: CLI and web interfaces for user interaction
- **Security Layer**: Privacy protection and secure file handling

This design enables easy extension to support additional platforms in the future.

## 🔒 Privacy & Security

### Privacy-First Design

- **🏠 Local Processing**: All data processing happens on your machine
- **🚫 No Cloud Dependencies**: No data is sent to external services during processing
- **🔐 Encryption at Rest**: Context files are encrypted when saved locally
- **🕵️ Sensitive Data Detection**: Automatic detection and optional redaction of PII
- **🗑️ Secure Deletion**: Multi-pass overwriting of temporary files
- **📡 Network Monitoring**: Ensures no unexpected network activity during processing

### What We Collect (Web Interface Only)

**CLI Tool**: Collects no data whatsoever.

**Web Interface** (if you use the hosted version):
- **Payment Information**: Processed by Stripe (we never see your credit card details)
- **Usage Statistics**: Number of exports, file sizes (for beta users only)
- **Feedback**: Optional feedback you provide (beta users only)
- **No Personal Data**: We don't store your ChatGPT conversations or extracted context

### Data Retention

- **Local Files**: You control all local files and can delete them anytime
- **Web Interface**: Session data is automatically deleted after 1 hour
- **Payment Records**: Handled by Stripe according to their retention policy
- **Beta Feedback**: Stored until beta program ends, then deleted

### Security Measures

- **AES-256-GCM Encryption**: Military-grade encryption for stored context files
- **PBKDF2 Key Derivation**: Secure password-based encryption keys
- **Sensitive Data Patterns**: Detects 15+ types of sensitive information
- **Network Isolation**: Monitors and prevents unexpected network calls
- **Secure File Deletion**: Multi-pass overwriting prevents data recovery

## 📜 Terms of Service

### Acceptable Use

✅ **Allowed:**
- Export your own ChatGPT conversation data
- Use for personal context migration
- Integrate into your own projects (open source)
- Modify and distribute (subject to license)

❌ **Not Allowed:**
- Export other people's conversation data without permission
- Use for commercial data harvesting
- Attempt to reverse-engineer ChatGPT's algorithms
- Violate any platform's terms of service

### Disclaimers

- **No Warranty**: Software provided "as is" without warranty
- **Platform Changes**: Target platforms may change their APIs/features
- **Context Quality**: Results depend on your conversation content quality
- **Compatibility**: We can't guarantee compatibility with all export formats

### Liability

- **Your Responsibility**: You're responsible for your data and its use
- **Platform Compliance**: Ensure you comply with target platform terms
- **Data Accuracy**: We don't guarantee perfect context extraction
- **Service Availability**: Web interface availability not guaranteed

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Clone the repository
git clone https://github.com/llm-context-exporter/llm-context-exporter.git
cd llm-context-exporter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest
```

### Contribution Guidelines

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Write** tests for your changes
4. **Ensure** all tests pass: `pytest`
5. **Format** code: `black src tests && isort src tests`
6. **Commit** changes: `git commit -m "Add amazing feature"`
7. **Push** to branch: `git push origin feature/amazing-feature`
8. **Open** a Pull Request

### Areas for Contribution

- **New Platform Adapters**: Add support for Claude, Perplexity, etc.
- **Enhanced Context Extraction**: Improve project and preference detection
- **UI/UX Improvements**: Better web interface design
- **Documentation**: Tutorials, guides, and examples
- **Testing**: More test coverage and edge cases
- **Performance**: Optimization for large exports

## 🐛 Troubleshooting

### Common Issues

**"Export file not found"**
```bash
# Check file path and permissions
ls -la your_export.zip
llm-context-export compatibility -f your_export.zip
```

**"Ollama not found"**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
ollama pull qwen
```

**"Permission denied"**
```bash
# Check output directory permissions
mkdir -p ./output
chmod 755 ./output
```

**"Context too large"**
```bash
# Use filtering to reduce size
llm-context-export export -i export.zip -t gemini -o ./output \
  --min-relevance 0.7 --exclude-topics "personal,casual"
```

### Getting Help

- **Documentation**: Check this README and `llm-context-export --help`
- **Examples**: Run `llm-context-export examples`
- **Issues**: [GitHub Issues](https://github.com/llm-context-exporter/llm-context-exporter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/llm-context-exporter/llm-context-exporter/discussions)

## 📊 Beta Program

Interested in early access to new features? Join our beta program!

### Beta Benefits

- **Free Access**: No payment required for web interface
- **Early Features**: Access to new features before public release
- **Direct Feedback**: Help shape the product development
- **Priority Support**: Faster response to issues and questions

### How to Join

1. **Email us**: Send a request to beta@llm-context-exporter.com
2. **Include**: Brief description of your use case
3. **Get Access**: We'll add you to the beta whitelist
4. **Provide Feedback**: Help us improve the tool

### Beta User Responsibilities

- **Test Features**: Try new functionality and report issues
- **Provide Feedback**: Share your experience and suggestions
- **Report Bugs**: Help us identify and fix problems
- **Respect Privacy**: Don't share beta features publicly

## 📈 Roadmap

### Phase 1: Core Functionality ✅
- [x] ChatGPT export parsing
- [x] Context extraction and filtering
- [x] Gemini and Ollama formatters
- [x] CLI interface
- [x] Security features
- [x] Validation testing

### Phase 2: Enhanced Experience 🚧
- [x] Web interface
- [x] Payment integration
- [x] Beta user management
- [ ] Advanced filtering options
- [ ] Context analytics dashboard
- [ ] Batch processing

### Phase 3: Platform Expansion 📋
- [ ] Claude export support
- [ ] Perplexity export support
- [ ] Anthropic Claude target
- [ ] OpenAI Assistant API target
- [ ] Custom LLM targets

### Phase 4: Advanced Features 🔮
- [ ] Team collaboration features
- [ ] Context sharing and templates
- [ ] API for third-party integrations
- [ ] Context version control
- [ ] Multi-platform sync

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### What this means:
- ✅ **Commercial use** allowed
- ✅ **Modification** allowed
- ✅ **Distribution** allowed
- ✅ **Private use** allowed
- ❌ **No warranty** provided
- ❌ **No liability** accepted

## 🙏 Acknowledgments

- **OpenAI** for ChatGPT and the inspiration for context portability
- **Google** for Gemini and the Saved Info feature
- **Ollama Team** for making local LLMs accessible
- **Open Source Community** for the amazing tools and libraries
- **Beta Testers** for their valuable feedback and bug reports

### Built With

- **[Pydantic](https://pydantic.dev/)** - Data validation and parsing
- **[Click](https://click.palletsprojects.com/)** - Command-line interface
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal output
- **[Flask](https://flask.palletsprojects.com/)** - Web interface
- **[Stripe](https://stripe.com/)** - Payment processing
- **[Cryptography](https://cryptography.io/)** - Security and encryption
- **[Hypothesis](https://hypothesis.readthedocs.io/)** - Property-based testing

## 📞 Contact

- **Website**: [llm-context-exporter.com](https://llm-context-exporter.com)
- **Email**: contact@llm-context-exporter.com
- **GitHub**: [llm-context-exporter/llm-context-exporter](https://github.com/llm-context-exporter/llm-context-exporter)
- **Issues**: [Report a Bug](https://github.com/llm-context-exporter/llm-context-exporter/issues)
- **Discussions**: [Community Forum](https://github.com/llm-context-exporter/llm-context-exporter/discussions)

---

**Made with ❤️ for the AI community**

*Break free from vendor lock-in. Your context, your choice.*