# CLI Usage Guide

This guide provides comprehensive examples and usage patterns for the LLM Context Exporter command-line interface.

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Export Command](#export-command)
- [Validation Command](#validation-command)
- [Delta Command](#delta-command)
- [Web Interface](#web-interface)
- [Compatibility Checking](#compatibility-checking)
- [Admin Commands](#admin-commands)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Installation

```bash
# Install from PyPI
pip install llm-context-exporter

# Or install from source
git clone https://github.com/llm-context-exporter/llm-context-exporter.git
cd llm-context-exporter
pip install -e .

# Verify installation
llm-context-export --version
```

## Basic Usage

### Getting Help

```bash
# Main help
llm-context-export --help

# Command-specific help
llm-context-export export --help
llm-context-export validate --help

# Show detailed information
llm-context-export info --verbose

# Show usage examples
llm-context-export examples
```

### Platform Comparison

```bash
# Compare Gemini vs Ollama
llm-context-export compare
```

This shows a detailed comparison table helping you choose between cloud-based Gemini and local Ollama.

## Export Command

The `export` command is the main functionality for converting ChatGPT exports to target platform formats.

### Basic Export

```bash
# Export to Gemini
llm-context-export export \
  --input chatgpt_export.zip \
  --target gemini \
  --output ./gemini_output

# Export to Ollama
llm-context-export export \
  --input chatgpt_export.zip \
  --target ollama \
  --output ./ollama_output
```

### Interactive Mode

```bash
# Interactive filtering and selection
llm-context-export export \
  --input chatgpt_export.zip \
  --target gemini \
  --output ./output \
  --interactive
```

Interactive mode allows you to:
- Review extracted projects and choose which to include
- Select technical domains to include/exclude
- Set relevance thresholds
- Apply date range filters

### Advanced Filtering

```bash
# Exclude specific topics
llm-context-export export \
  --input chatgpt_export.zip \
  --target ollama \
  --output ./output \
  --exclude-topics "personal,private,casual"

# Set minimum relevance score
llm-context-export export \
  --input chatgpt_export.zip \
  --target gemini \
  --output ./output \
  --min-relevance 0.7

# Combine multiple filters
llm-context-export export \
  --input chatgpt_export.zip \
  --target ollama \
  --output ./output \
  --exclude-topics "personal,private" \
  --min-relevance 0.5 \
  --interactive
```

### Incremental Updates

```bash
# Add new conversations to existing context
llm-context-export export \
  --input new_chatgpt_export.zip \
  --target gemini \
  --output ./updated_output \
  --update ./previous_output/context.json
```

### Dry Run Mode

```bash
# Preview what would be exported without creating files
llm-context-export export \
  --input chatgpt_export.zip \
  --target gemini \
  --output ./output \
  --dry-run
```

### Ollama-Specific Options

```bash
# Specify base model for Ollama
llm-context-export export \
  --input chatgpt_export.zip \
  --target ollama \
  --output ./output \
  --model qwen2

# Other supported models
llm-context-export export \
  --input chatgpt_export.zip \
  --target ollama \
  --output ./output \
  --model llama2
```

## Validation Command

Generate and run validation tests to verify successful context transfer.

### Basic Validation

```bash
# Generate validation questions
llm-context-export validate \
  --context ./output \
  --target gemini

# Validate specific context file
llm-context-export validate \
  --context ./output/context.json \
  --target ollama
```

### Interactive Validation

```bash
# Step-by-step interactive validation
llm-context-export validate \
  --context ./output \
  --target gemini \
  --interactive
```

Interactive validation provides:
- Test questions about your projects
- Expected answer summaries
- Platform-specific testing instructions
- Step-by-step verification process

### Validation Output Examples

**For Gemini:**
```
Question 1 (project): What is your main e-commerce project about?
Expected: Should mention FastAPI, React, PostgreSQL, and payment processing challenges

Question 2 (preference): What is your preferred programming language?
Expected: Should mention Python and clean, readable code style

Question 3 (technical): What machine learning frameworks do you use?
Expected: Should mention TensorFlow and computer vision experience
```

**For Ollama:**
```
Test your model with these commands:
ollama run my-context "What projects am I working on?"
ollama run my-context "What are my preferred development tools?"
ollama run my-context "What programming languages do I use most?"
```

## Delta Command

Generate incremental update packages containing only new information.

### Basic Delta Generation

```bash
# Generate delta package
llm-context-export delta \
  --current new_chatgpt_export.zip \
  --previous ./old_context/context.json \
  --output ./delta_package
```

### Delta with Dry Run

```bash
# Preview delta contents without creating files
llm-context-export delta \
  --current new_export.zip \
  --previous ./old_context.json \
  --output ./delta \
  --dry-run
```

The delta command shows:
- Number of new projects identified
- New technical skills and tools
- Updated project statuses
- New conversation topics

## Web Interface

Start a local web server for browser-based usage.

### Basic Web Server

```bash
# Start on default port (8080)
llm-context-export web

# Custom port
llm-context-export web --port 3000

# Debug mode (development only)
llm-context-export web --debug
```

### Web Interface Features

The web interface provides:
- **File Upload**: Drag-and-drop ChatGPT export files
- **Platform Selection**: Choose between Gemini and Ollama
- **Interactive Filtering**: Visual interface for content selection
- **Payment Processing**: Stripe integration for hosted version
- **Download Results**: Easy access to generated files
- **Validation Tests**: Browser-based validation questions

### Security Notes

- Web interface only binds to localhost (127.0.0.1) for security
- All processing happens locally on your machine
- Session data is automatically cleaned up after 1 hour
- No data is sent to external servers during processing

## Compatibility Checking

Verify platform compatibility and check system requirements.

### File Compatibility

```bash
# Check if export file is compatible
llm-context-export compatibility \
  --file chatgpt_export.zip \
  --target ollama

# Analyze file without target platform
llm-context-export compatibility \
  --file chatgpt_export.zip
```

### Platform Requirements

```bash
# Check Ollama installation
llm-context-export compatibility --target ollama

# Check Gemini requirements
llm-context-export compatibility --target gemini
```

### Compatibility Report

The compatibility command provides:
- **Format Analysis**: Export file version and structure
- **Platform Status**: Installation and configuration status
- **Feature Support**: What transfers well vs. what doesn't
- **Recommendations**: Specific actions to improve compatibility

## Admin Commands

Manage beta users and view usage statistics (for hosted deployments).

### List Beta Users

```bash
# List all beta users
llm-context-export admin list-users

# Show detailed user information
llm-context-export admin list-users --verbose
```

### Add/Remove Beta Users

```bash
# Add new beta user
llm-context-export admin add-user \
  --email user@example.com \
  --notes "Early adopter, power user"

# Remove beta user
llm-context-export admin remove-user \
  --email user@example.com
```

### User Statistics

```bash
# Show statistics for specific user
llm-context-export admin user-stats \
  --email user@example.com

# Show all user statistics
llm-context-export admin user-stats --all
```

### Feedback Management

```bash
# View feedback by rating
llm-context-export admin feedback --rating 5
llm-context-export admin feedback --rating 1

# View all feedback
llm-context-export admin feedback
```

### Generate Reports

```bash
# Generate usage report
llm-context-export admin report \
  --output beta_report.csv \
  --format csv

# Generate JSON report
llm-context-export admin report \
  --output beta_report.json \
  --format json
```

## Advanced Usage

### Chaining Commands

```bash
# Export, validate, and generate delta in sequence
llm-context-export export -i export.zip -t gemini -o ./output && \
llm-context-export validate -c ./output -t gemini && \
llm-context-export delta -c new_export.zip -p ./output/context.json -o ./delta
```

### Batch Processing

```bash
# Process multiple exports
for export in exports/*.zip; do
  echo "Processing $export"
  llm-context-export export -i "$export" -t gemini -o "./output/$(basename "$export" .zip)"
done
```

### Configuration Files

Create a configuration file for repeated use:

```bash
# Create config file
cat > export_config.json << EOF
{
  "target": "gemini",
  "exclude_topics": ["personal", "private"],
  "min_relevance": 0.6,
  "interactive": false
}
EOF

# Use config file (planned feature)
llm-context-export export -i export.zip -o ./output --config export_config.json
```

### Environment Variables

```bash
# Set default output directory
export LLM_CONTEXT_OUTPUT_DIR="./exports"

# Set default target platform
export LLM_CONTEXT_DEFAULT_TARGET="gemini"

# Enable verbose output
export LLM_CONTEXT_VERBOSE=1
```

## Troubleshooting

### Common Issues and Solutions

#### "Export file not found"

```bash
# Check file exists and permissions
ls -la chatgpt_export.zip
file chatgpt_export.zip

# Try absolute path
llm-context-export export -i /full/path/to/chatgpt_export.zip -t gemini -o ./output
```

#### "Ollama not found"

```bash
# Check Ollama installation
ollama --version

# Install Ollama if missing
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required model
ollama pull qwen

# Verify with compatibility check
llm-context-export compatibility -t ollama
```

#### "Permission denied"

```bash
# Check output directory permissions
mkdir -p ./output
chmod 755 ./output

# Use different output directory
llm-context-export export -i export.zip -t gemini -o ~/Documents/llm_export
```

#### "Context too large"

```bash
# Use filtering to reduce size
llm-context-export export -i export.zip -t gemini -o ./output \
  --min-relevance 0.8 \
  --exclude-topics "casual,personal,off-topic"

# Check what would be included first
llm-context-export export -i export.zip -t gemini -o ./output --dry-run
```

#### "Invalid export format"

```bash
# Check file format
llm-context-export compatibility -f export.zip

# Try different export format
# Re-export from ChatGPT if needed
```

### Debug Mode

```bash
# Enable verbose output
llm-context-export --verbose export -i export.zip -t gemini -o ./output

# Check logs (if available)
tail -f ~/.llm-context-exporter/logs/export.log
```

### Getting Help

```bash
# Show all available commands
llm-context-export --help

# Get help for specific command
llm-context-export export --help

# Show detailed examples
llm-context-export examples

# Check system information
llm-context-export info --verbose
```

## Performance Tips

### Large Exports

```bash
# For very large exports, use filtering
llm-context-export export -i large_export.zip -t gemini -o ./output \
  --min-relevance 0.7 \
  --exclude-topics "casual,personal"

# Process in chunks (for development)
llm-context-export export -i export.zip -t gemini -o ./output --dry-run
# Review output, then run without --dry-run
```

### Memory Usage

```bash
# Monitor memory usage during processing
top -p $(pgrep -f llm-context-export)

# Use incremental updates for regular processing
llm-context-export export -i new_export.zip -t gemini -o ./output \
  --update ./previous/context.json
```

### Disk Space

```bash
# Check available space
df -h .

# Clean up old exports
rm -rf ./old_exports/

# Use compression for storage
tar -czf context_backup.tar.gz ./output/
```

This CLI usage guide covers all the major functionality and common use cases for the LLM Context Exporter command-line interface.