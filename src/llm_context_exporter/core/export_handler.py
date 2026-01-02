"""
Export handler that orchestrates the complete export process.

This module coordinates parsing, extraction, filtering, formatting,
and incremental updates to provide a complete export workflow.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..parsers.chatgpt import ChatGPTParser
from .extractor import ContextExtractor
from .filter import FilterEngine
from .incremental import IncrementalUpdater
from ..formatters.gemini import GeminiFormatter
from ..formatters.ollama import OllamaFormatter
from ..validation.generator import ValidationGenerator
from .models import (
    ExportConfig,
    FilterConfig,
    UniversalContextPack,
    ParsedExport,
    GeminiOutput,
    OllamaOutput
)


class ExportHandler:
    """
    Orchestrates the complete export process from ChatGPT to target platforms.
    
    Handles:
    - Parsing ChatGPT exports
    - Extracting context
    - Applying filters
    - Incremental updates
    - Formatting for target platforms
    - Generating validation tests
    """
    
    def __init__(self):
        """Initialize the export handler with required components."""
        self.parser = ChatGPTParser()
        self.extractor = ContextExtractor()
        self.filter_engine = FilterEngine()
        self.incremental_updater = IncrementalUpdater()
        self.gemini_formatter = GeminiFormatter()
        self.ollama_formatter = OllamaFormatter()
        self.validation_generator = ValidationGenerator()
    
    def export(self, config: ExportConfig) -> Dict[str, Any]:
        """
        Perform complete export process.
        
        Args:
            config: Export configuration
            
        Returns:
            Dictionary with export results and metadata
        """
        results = {
            "success": False,
            "output_files": [],
            "metadata": {},
            "errors": []
        }
        
        try:
            # Step 1: Parse input file
            print(f"Parsing ChatGPT export: {config.input_path}")
            parsed_export = self.parser.parse_export(config.input_path)
            results["metadata"]["conversations_parsed"] = len(parsed_export.conversations)
            
            # Step 2: Handle incremental updates if requested
            if config.incremental and config.previous_context_path:
                print("Processing incremental update...")
                context_pack = self._handle_incremental_update(parsed_export, config)
            else:
                print("Extracting context from conversations...")
                context_pack = self.extractor.extract_context(parsed_export.conversations)
            
            results["metadata"]["projects_extracted"] = len(context_pack.projects)
            results["metadata"]["languages_found"] = len(context_pack.technical_context.languages)
            
            # Step 3: Apply filters if specified
            if config.filters:
                print("Applying filters...")
                context_pack = self.filter_engine.apply_filters(context_pack, config.filters)
                results["metadata"]["filtered"] = True
            
            # Step 4: Format for target platform
            print(f"Formatting for {config.target_platform}...")
            if config.target_platform == "gemini":
                output = self.gemini_formatter.format_context(context_pack)
                output_files = self._save_gemini_output(output, config.output_path)
            elif config.target_platform == "ollama":
                base_model = config.base_model or "qwen"
                output = self.ollama_formatter.format_context(context_pack, base_model)
                output_files = self._save_ollama_output(output, config.output_path)
            else:
                raise ValueError(f"Unsupported target platform: {config.target_platform}")
            
            results["output_files"] = output_files
            
            # Step 5: Generate validation tests
            print("Generating validation tests...")
            validation_suite = self.validation_generator.generate_tests(
                context_pack, 
                config.target_platform
            )
            validation_file = self._save_validation_tests(validation_suite, config.output_path)
            results["output_files"].append(validation_file)
            
            # Step 6: Save context pack for future incremental updates
            context_file = os.path.join(config.output_path, "context_pack.json")
            self.incremental_updater.save_context_pack(context_pack, context_file)
            results["output_files"].append(context_file)
            
            # Step 7: Update version history
            self.incremental_updater.save_version_history(context_pack, config.output_path)
            
            results["success"] = True
            results["metadata"]["export_completed"] = datetime.now().isoformat()
            
            print(f"Export completed successfully! Files saved to: {config.output_path}")
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            print(f"Error: {error_msg}")
            results["errors"].append(error_msg)
        
        return results
    
    def _handle_incremental_update(
        self, 
        current_export: ParsedExport, 
        config: ExportConfig
    ) -> UniversalContextPack:
        """Handle incremental update process."""
        # Load previous context
        previous_context = self.incremental_updater.load_previous_context(
            config.previous_context_path
        )
        
        if not previous_context:
            print("Warning: Could not load previous context, performing full export")
            return self.extractor.extract_context(current_export.conversations)
        
        # Load previous export if available
        previous_export_path = os.path.join(
            os.path.dirname(config.previous_context_path),
            "parsed_export.json"
        )
        
        if os.path.exists(previous_export_path):
            # Detect new conversations
            try:
                import json
                with open(previous_export_path, 'r') as f:
                    prev_data = json.load(f)
                
                # Reconstruct previous export (simplified)
                from .models import Conversation, Message
                prev_conversations = []
                for conv_data in prev_data.get('conversations', []):
                    messages = [
                        Message(
                            role=msg['role'],
                            content=msg['content'],
                            timestamp=datetime.fromisoformat(msg['timestamp']),
                            metadata=msg.get('metadata', {})
                        )
                        for msg in conv_data['messages']
                    ]
                    
                    prev_conversations.append(Conversation(
                        id=conv_data['id'],
                        title=conv_data['title'],
                        created_at=datetime.fromisoformat(conv_data['created_at']),
                        updated_at=datetime.fromisoformat(conv_data['updated_at']),
                        messages=messages
                    ))
                
                previous_export = ParsedExport(
                    format_version=prev_data['format_version'],
                    export_date=datetime.fromisoformat(prev_data['export_date']),
                    conversations=prev_conversations,
                    metadata=prev_data.get('metadata', {})
                )
                
                new_conversations = self.incremental_updater.detect_new_conversations(
                    current_export, previous_export
                )
                
                print(f"Found {len(new_conversations)} new or updated conversations")
                
                if new_conversations:
                    # Extract context from new conversations
                    new_context = self.extractor.extract_context(new_conversations)
                    
                    # Merge with existing context
                    merged_context = self.incremental_updater.merge_contexts(
                        previous_context, new_context
                    )
                    
                    # Generate delta package
                    delta_package = self.incremental_updater.generate_delta_package(
                        previous_context, new_context
                    )
                    
                    # Save delta package
                    delta_path = os.path.join(config.output_path, "delta_package.json")
                    self.incremental_updater.save_context_pack(delta_package, delta_path)
                    
                    return merged_context
                else:
                    print("No new conversations found, using existing context")
                    return previous_context
                    
            except Exception as e:
                print(f"Warning: Could not process incremental update: {e}")
                print("Falling back to full export")
        
        # Fallback to full export
        return self.extractor.extract_context(current_export.conversations)
    
    def _save_gemini_output(self, output: GeminiOutput, output_dir: str) -> list:
        """Save Gemini Gem-formatted output to files."""
        os.makedirs(output_dir, exist_ok=True)
        files = []
        
        # Save Gem instructions (main file to paste into Gem)
        instructions_file = os.path.join(output_dir, "gemini_gem_instructions.txt")
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(output.formatted_text)
        files.append(instructions_file)
        
        # Save Gem description (separate file for easy copy-paste)
        if output.metadata.get("gem_description"):
            description_file = os.path.join(output_dir, "gem_description.txt")
            with open(description_file, 'w', encoding='utf-8') as f:
                f.write(output.metadata["gem_description"])
            files.append(description_file)
        
        # Save setup guide
        guide_file = os.path.join(output_dir, "gem_setup_guide.md")
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(output.instructions)
        files.append(guide_file)
        
        return files
    
    def _save_ollama_output(self, output: OllamaOutput, output_dir: str) -> list:
        """Save Ollama-formatted output to files."""
        os.makedirs(output_dir, exist_ok=True)
        files = []
        
        # Save Modelfile
        modelfile_path = os.path.join(output_dir, "Modelfile")
        with open(modelfile_path, 'w', encoding='utf-8') as f:
            f.write(output.modelfile_content)
        files.append(modelfile_path)
        
        # Save supplementary files
        for filename, content in output.supplementary_files.items():
            file_path = os.path.join(output_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            files.append(file_path)
        
        # Save setup commands
        setup_file = os.path.join(output_dir, "setup_commands.sh")
        with open(setup_file, 'w', encoding='utf-8') as f:
            f.write("#!/bin/bash\n")
            f.write("# Ollama Model Setup Commands\n\n")
            for cmd in output.setup_commands:
                f.write(f"{cmd}\n")
        files.append(setup_file)
        
        # Save test commands
        test_file = os.path.join(output_dir, "test_commands.sh")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("#!/bin/bash\n")
            f.write("# Ollama Model Test Commands\n\n")
            for cmd in output.test_commands:
                f.write(f"{cmd}\n")
        files.append(test_file)
        
        return files
    
    def _save_validation_tests(self, validation_suite, output_dir: str) -> str:
        """Save validation tests to file."""
        os.makedirs(output_dir, exist_ok=True)
        
        validation_file = os.path.join(output_dir, "validation_tests.md")
        with open(validation_file, 'w', encoding='utf-8') as f:
            f.write(f"# Validation Tests for {validation_suite.target_platform.upper()}\n\n")
            f.write("Use these questions to validate that your context was successfully transferred.\n\n")
            
            for i, question in enumerate(validation_suite.questions, 1):
                f.write(f"## Question {i} ({question.category})\n\n")
                f.write(f"**Question:** {question.question}\n\n")
                f.write(f"**Expected Answer:** {question.expected_answer_summary}\n\n")
                f.write("---\n\n")
        
        return validation_file
    
    def get_filterable_items(self, input_path: str) -> Dict[str, Any]:
        """
        Get filterable items from an export for interactive filtering.
        
        Args:
            input_path: Path to ChatGPT export file
            
        Returns:
            Dictionary with filterable conversations and topics
        """
        try:
            # Parse export
            parsed_export = self.parser.parse_export(input_path)
            
            # Extract context to get projects/topics
            context_pack = self.extractor.extract_context(parsed_export.conversations)
            
            # Get filterable items
            filterable_items = self.filter_engine.get_filterable_items(context_pack)
            
            return {
                "conversations": [
                    {
                        "id": conv.id,
                        "title": conv.title,
                        "created_at": conv.created_at.isoformat(),
                        "message_count": len(conv.messages)
                    }
                    for conv in parsed_export.conversations
                ],
                "projects": [
                    {
                        "name": project.name,
                        "description": project.description,
                        "relevance_score": project.relevance_score
                    }
                    for project in context_pack.projects
                ],
                "topics": list(set(
                    context_pack.technical_context.languages +
                    context_pack.technical_context.frameworks +
                    context_pack.technical_context.domains
                )),
                "filterable_items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "category": item.category,
                        "description": item.description
                    }
                    for item in filterable_items
                ]
            }
            
        except Exception as e:
            return {"error": str(e)}