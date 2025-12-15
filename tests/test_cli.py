"""
Tests for CLI interface.

This module tests the command-line interface functionality.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from llm_context_exporter.cli.main import cli


class TestCLIBasics:
    """Test basic CLI functionality."""
    
    def test_cli_help(self):
        """Test that CLI help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'LLM Context Exporter' in result.output
        assert 'export' in result.output
        assert 'validate' in result.output
    
    def test_cli_version(self):
        """Test that version option works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert '0.1.0' in result.output
    
    def test_export_help(self):
        """Test export command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['export', '--help'])
        
        assert result.exit_code == 0
        assert 'Export ChatGPT conversations' in result.output
        assert '--input' in result.output
        assert '--target' in result.output
    
    def test_validate_help(self):
        """Test validate command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['validate', '--help'])
        
        assert result.exit_code == 0
        assert 'validation tests' in result.output
        assert '--context' in result.output
    
    def test_compare_command(self):
        """Test compare command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['compare'])
        
        assert result.exit_code == 0
        assert 'Platform Comparison' in result.output
        assert 'Gemini' in result.output
        assert 'Ollama' in result.output
    
    def test_info_command(self):
        """Test info command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['info'])
        
        assert result.exit_code == 0
        assert 'Supported Source Platforms' in result.output
        assert 'ChatGPT' in result.output
    
    def test_info_verbose(self):
        """Test info command with verbose flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ['info', '--verbose'])
        
        assert result.exit_code == 0
        assert 'What Gets Extracted' in result.output
        assert 'Limitations' in result.output
    
    def test_examples_command(self):
        """Test examples command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['examples'])
        
        assert result.exit_code == 0
        assert 'Usage Examples' in result.output
        assert 'Basic Export to Gemini' in result.output


class TestCLIErrorHandling:
    """Test CLI error handling."""
    
    def test_export_missing_input_file(self):
        """Test export with missing input file."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'export', 
            '-i', 'nonexistent.zip',
            '-t', 'gemini',
            '-o', './output'
        ])
        
        assert result.exit_code == 1
        assert 'Input file not found' in result.output
    
    def test_validate_missing_context_file(self):
        """Test validate with missing context file."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'validate',
            '-c', 'nonexistent.json',
            '-t', 'gemini'
        ])
        
        assert result.exit_code == 1
        assert 'Context file not found' in result.output
    
    def test_delta_missing_files(self):
        """Test delta with missing files."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'delta',
            '-c', 'nonexistent_current.zip',
            '-p', 'nonexistent_previous.json',
            '-o', './output'
        ])
        
        assert result.exit_code == 1
        assert 'Current export file not found' in result.output


class TestCLIIntegration:
    """Test CLI integration with core components."""
    
    @patch('llm_context_exporter.cli.main.ExportHandler')
    def test_export_dry_run(self, mock_handler):
        """Test export dry run mode."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'export',
            '-i', __file__,  # Use this test file as dummy input
            '-t', 'gemini',
            '-o', './output',
            '--dry-run'
        ])
        
        # Should not call the actual export handler in dry run
        mock_handler.assert_not_called()
        assert 'Dry run complete' in result.output
    
    @patch('llm_context_exporter.cli.main.shutil.which')
    def test_ollama_check_not_installed(self, mock_which):
        """Test Ollama installation check when not installed."""
        mock_which.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'export',
            '-i', __file__,
            '-t', 'ollama',
            '-o', './output',
            '--dry-run'
        ])
        
        assert 'Ollama not found' in result.output
        assert 'https://ollama.ai' in result.output
    
    def test_web_security_check(self):
        """Test web interface security check."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'web',
            '--host', '0.0.0.0'  # Should be rejected
        ])
        
        assert result.exit_code == 1
        assert 'only supports localhost for security' in result.output


class TestCLIFiltering:
    """Test CLI filtering options."""
    
    @patch('llm_context_exporter.cli.main.ExportHandler')
    def test_export_with_filters(self, mock_handler):
        """Test export with command-line filters."""
        mock_handler.return_value.export.return_value = {
            'success': True,
            'metadata': {'conversations_parsed': 10, 'projects_extracted': 3},
            'output_files': ['test.txt']
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'export',
            '-i', __file__,
            '-t', 'gemini',
            '-o', './output',
            '--exclude-topics', 'personal,private',
            '--min-relevance', '0.5'
        ])
        
        # Check that filters were applied
        assert 'Filters applied' in result.output
        mock_handler.return_value.export.assert_called_once()
        
        # Check the config passed to export handler
        call_args = mock_handler.return_value.export.call_args[0][0]
        assert call_args.filters is not None
        assert 'personal' in call_args.filters.excluded_topics
        assert 'private' in call_args.filters.excluded_topics
        assert call_args.filters.min_relevance_score == 0.5