#!/usr/bin/env python3
"""
Library Usage Example

This example demonstrates how to use the LLM Context Exporter as a Python library
for integrating context export functionality into your own applications.
"""

import os
import sys
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_context_exporter import ExportHandler, ExportConfig
from llm_context_exporter.parsers.chatgpt import ChatGPTParser
from llm_context_exporter.core.extractor import ContextExtractor
from llm_context_exporter.formatters.gemini import GeminiFormatter
from llm_context_exporter.formatters.ollama import OllamaFormatter
from llm_context_exporter.core.filter import FilterEngine
from llm_context_exporter.models.core import FilterConfig
from llm_context_exporter.validation.generator import ValidationGenerator
from llm_context_exporter.security import SecurityManager


def example_1_simple_export():
    """Example 1: Simple export using the high-level API."""
    print("=" * 60)
    print("EXAMPLE 1: Simple Export")
    print("=" * 60)
    
    # This would be your actual ChatGPT export file
    input_file = "chatgpt_export.zip"  # Replace with actual file
    
    if not os.path.exists(input_file):
        print(f"⚠️  Skipping Example 1: {input_file} not found")
        print("   To run this example, place your ChatGPT export file in the current directory")
        return
    
    try:
        # Create export configuration
        config = ExportConfig(
            input_path=input_file,
            target_platform="gemini",
            output_path="./example_output",
            interactive=False
        )
        
        # Perform export
        handler = ExportHandler()
        results = handler.export(config)
        
        if results["success"]:
            print("✅ Export completed successfully!")
            print(f"📁 Output files: {results['output_files']}")
            print(f"📊 Projects found: {results['metadata'].get('projects_extracted', 'N/A')}")
            print(f"🔧 Languages detected: {results['metadata'].get('languages_found', 'N/A')}")
        else:
            print("❌ Export failed!")
            for error in results["errors"]:
                print(f"   Error: {error}")
                
    except Exception as e:
        print(f"❌ Exception during export: {e}")


def example_2_step_by_step_processing():
    """Example 2: Step-by-step processing with custom logic."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Step-by-Step Processing")
    print("=" * 60)
    
    # Create a mock ChatGPT export for demonstration
    mock_export_data = {
        "version": "1.0",
        "export_date": "2024-01-15T10:30:00Z",
        "conversations": [
            {
                "id": "conv_1",
                "title": "Python Web Development Help",
                "created_at": "2024-01-10T09:00:00Z",
                "updated_at": "2024-01-10T10:30:00Z",
                "messages": [
                    {
                        "role": "user",
                        "content": "I'm building a FastAPI application with PostgreSQL. Can you help me with database connection setup?",
                        "timestamp": "2024-01-10T09:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "I'd be happy to help you set up a database connection for your FastAPI application with PostgreSQL. Here's a comprehensive approach using SQLAlchemy...",
                        "timestamp": "2024-01-10T09:05:00Z"
                    },
                    {
                        "role": "user",
                        "content": "Great! I'm also using Docker for containerization. How should I handle database migrations?",
                        "timestamp": "2024-01-10T09:15:00Z"
                    }
                ]
            },
            {
                "id": "conv_2", 
                "title": "Machine Learning Model Deployment",
                "created_at": "2024-01-12T14:00:00Z",
                "updated_at": "2024-01-12T15:30:00Z",
                "messages": [
                    {
                        "role": "user",
                        "content": "I have a TensorFlow model for image classification. What's the best way to deploy it as a REST API?",
                        "timestamp": "2024-01-12T14:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "For deploying a TensorFlow image classification model as a REST API, I recommend using FastAPI with TensorFlow Serving...",
                        "timestamp": "2024-01-12T14:10:00Z"
                    }
                ]
            }
        ]
    }
    
    # Save mock data to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_export_data, f, indent=2)
        mock_file = f.name
    
    try:
        # Step 1: Parse the export
        print("📖 Step 1: Parsing ChatGPT export...")
        parser = ChatGPTParser()
        parsed_export = parser.parse_export(mock_file)
        
        print(f"   ✅ Parsed {len(parsed_export.conversations)} conversations")
        print(f"   📅 Export date: {parsed_export.export_date}")
        print(f"   🔢 Format version: {parsed_export.format_version}")
        
        # Step 2: Extract context
        print("\n🧠 Step 2: Extracting context...")
        extractor = ContextExtractor()
        context_pack = extractor.extract_context(parsed_export.conversations)
        
        print(f"   👤 User role: {context_pack.user_profile.role or 'Not specified'}")
        print(f"   🎯 Expertise areas: {', '.join(context_pack.user_profile.expertise_areas)}")
        print(f"   📋 Projects found: {len(context_pack.projects)}")
        print(f"   💻 Languages: {', '.join(context_pack.technical_context.languages)}")
        print(f"   🔧 Frameworks: {', '.join(context_pack.technical_context.frameworks)}")
        
        # Display project details
        for i, project in enumerate(context_pack.projects, 1):
            print(f"   📁 Project {i}: {project.name}")
            print(f"      Description: {project.description[:60]}...")
            print(f"      Tech stack: {', '.join(project.tech_stack)}")
            print(f"      Relevance: {project.relevance_score:.2f}")
        
        # Step 3: Apply filters (optional)
        print("\n🔍 Step 3: Applying filters...")
        filter_config = FilterConfig(
            excluded_topics=["casual", "off-topic"],
            min_relevance_score=0.5
        )
        
        filter_engine = FilterEngine()
        filtered_context = filter_engine.apply_filters(context_pack, filter_config)
        
        print(f"   📊 Original projects: {len(context_pack.projects)}")
        print(f"   📊 Filtered projects: {len(filtered_context.projects)}")
        
        # Step 4: Format for target platforms
        print("\n🎯 Step 4: Formatting for target platforms...")
        
        # Format for Gemini
        gemini_formatter = GeminiFormatter()
        gemini_output = gemini_formatter.format_for_gemini(filtered_context)
        
        print(f"   🟢 Gemini format: {len(gemini_output.formatted_text)} characters")
        print(f"   📋 Instructions: {len(gemini_output.instructions)} steps")
        
        # Format for Ollama
        ollama_formatter = OllamaFormatter()
        ollama_output = ollama_formatter.format_for_ollama(filtered_context, base_model="qwen")
        
        print(f"   🟡 Ollama Modelfile: {len(ollama_output.modelfile_content)} characters")
        print(f"   ⚙️  Setup commands: {len(ollama_output.setup_commands)}")
        print(f"   🧪 Test commands: {len(ollama_output.test_commands)}")
        
        # Step 5: Generate validation tests
        print("\n✅ Step 5: Generating validation tests...")
        validator = ValidationGenerator()
        
        gemini_validation = validator.generate_tests(filtered_context, "gemini")
        ollama_validation = validator.generate_tests(filtered_context, "ollama")
        
        print(f"   🟢 Gemini validation: {len(gemini_validation.questions)} questions")
        print(f"   🟡 Ollama validation: {len(ollama_validation.questions)} questions")
        
        # Display sample validation questions
        print("\n   Sample validation questions:")
        for i, question in enumerate(gemini_validation.questions[:2], 1):
            print(f"   {i}. {question.question}")
            print(f"      Expected: {question.expected_answer_summary}")
        
        print("\n✅ Step-by-step processing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during step-by-step processing: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up temporary file
        if os.path.exists(mock_file):
            os.unlink(mock_file)


def example_3_security_features():
    """Example 3: Using security features."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Security Features")
    print("=" * 60)
    
    # Sample content with sensitive data
    sensitive_content = """
    Project Configuration:
    Database URL: postgresql://user:secret123@localhost:5432/myapp
    API Key: sk-1234567890abcdef1234567890abcdef
    Admin Email: admin@mycompany.com
    AWS Access Key: AKIAIOSFODNN7EXAMPLE
    
    This is my main e-commerce project using FastAPI and React.
    """
    
    try:
        # Initialize security manager
        security_manager = SecurityManager(
            enable_network_monitoring=True,
            enable_interactive_redaction=False  # Disable for demo
        )
        
        print("🔒 Processing content with security features...")
        
        # Process content with security
        with security_manager:
            result = security_manager.process_with_security(
                sensitive_content,
                context="Project configuration notes",
                encrypt_output=False  # Disable encryption for demo
            )
        
        print(f"   🕵️  Sensitive data detected: {result['sensitive_data_detected']}")
        print(f"   ✂️  Redaction applied: {result['redaction_applied']}")
        print(f"   🔐 Content encrypted: {result['encrypted']}")
        print(f"   🌐 Network violations: {len(result['network_violations'])}")
        
        if result['sensitive_data_detected']:
            print("\n   🚨 Sensitive data found:")
            for detection in result['detections']:
                print(f"      {detection['type']}: {detection['value']}")
        
        if result['redacted_content']:
            print("\n   ✂️  Redacted content preview:")
            print("   " + result['redacted_content'][:200] + "...")
        
        print("\n✅ Security processing completed!")
        
    except Exception as e:
        print(f"❌ Error during security processing: {e}")


def example_4_custom_integration():
    """Example 4: Custom integration example."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Custom Integration")
    print("=" * 60)
    
    try:
        # Custom application that uses the library
        class MyContextMigrationApp:
            def __init__(self):
                self.export_handler = ExportHandler()
                self.security_manager = SecurityManager()
            
            def migrate_user_context(self, user_id: str, export_file: str, target: str):
                """Migrate context for a specific user."""
                print(f"🔄 Migrating context for user {user_id}...")
                
                # Create user-specific output directory
                output_dir = f"./user_exports/{user_id}"
                os.makedirs(output_dir, exist_ok=True)
                
                # Configure export
                config = ExportConfig(
                    input_path=export_file,
                    target_platform=target,
                    output_path=output_dir,
                    interactive=False
                )
                
                # Perform migration with security
                with self.security_manager:
                    results = self.export_handler.export(config)
                
                if results["success"]:
                    # Log successful migration
                    self.log_migration(user_id, target, results["metadata"])
                    return {
                        "success": True,
                        "output_files": results["output_files"],
                        "user_id": user_id,
                        "target": target
                    }
                else:
                    # Log failed migration
                    self.log_migration_error(user_id, target, results["errors"])
                    return {
                        "success": False,
                        "errors": results["errors"],
                        "user_id": user_id,
                        "target": target
                    }
            
            def log_migration(self, user_id: str, target: str, metadata: dict):
                """Log successful migration."""
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "target": target,
                    "projects_extracted": metadata.get("projects_extracted", 0),
                    "languages_found": metadata.get("languages_found", 0),
                    "status": "success"
                }
                print(f"   📝 Migration logged: {log_entry}")
            
            def log_migration_error(self, user_id: str, target: str, errors: list):
                """Log failed migration."""
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "target": target,
                    "errors": errors,
                    "status": "failed"
                }
                print(f"   📝 Error logged: {log_entry}")
        
        # Use the custom application
        app = MyContextMigrationApp()
        
        # Simulate user migration (would use real files in practice)
        print("🚀 Custom integration example:")
        print("   This demonstrates how to integrate the library into your own application")
        print("   In a real scenario, you would:")
        print("   1. Receive user export files through your application")
        print("   2. Process them using the library")
        print("   3. Store results in your database")
        print("   4. Provide download links to users")
        print("   5. Track usage and analytics")
        
        print("\n✅ Custom integration example completed!")
        
    except Exception as e:
        print(f"❌ Error in custom integration: {e}")


def example_5_batch_processing():
    """Example 5: Batch processing multiple exports."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Batch Processing")
    print("=" * 60)
    
    try:
        # Simulate batch processing scenario
        export_jobs = [
            {"user_id": "user_001", "file": "export1.zip", "target": "gemini"},
            {"user_id": "user_002", "file": "export2.zip", "target": "ollama"},
            {"user_id": "user_003", "file": "export3.zip", "target": "gemini"},
        ]
        
        print(f"📦 Processing {len(export_jobs)} export jobs...")
        
        results = []
        for i, job in enumerate(export_jobs, 1):
            print(f"\n   Job {i}/{len(export_jobs)}: {job['user_id']} → {job['target']}")
            
            # In a real scenario, you would check if the file exists
            if not os.path.exists(job['file']):
                print(f"   ⚠️  Skipping: {job['file']} not found")
                results.append({
                    "job": job,
                    "success": False,
                    "error": "File not found"
                })
                continue
            
            try:
                # Process the export
                config = ExportConfig(
                    input_path=job['file'],
                    target_platform=job['target'],
                    output_path=f"./batch_output/{job['user_id']}",
                    interactive=False
                )
                
                handler = ExportHandler()
                result = handler.export(config)
                
                results.append({
                    "job": job,
                    "success": result["success"],
                    "output_files": result.get("output_files", []),
                    "errors": result.get("errors", [])
                })
                
                if result["success"]:
                    print(f"   ✅ Completed successfully")
                else:
                    print(f"   ❌ Failed: {result['errors']}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                results.append({
                    "job": job,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        print(f"\n📊 Batch processing summary:")
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ❌ Failed: {len(failed)}")
        print(f"   📈 Success rate: {len(successful)/len(results)*100:.1f}%")
        
        print("\n✅ Batch processing example completed!")
        
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")


def main():
    """Run all library usage examples."""
    print("🚀 LLM Context Exporter - Library Usage Examples")
    print("This script demonstrates various ways to use the LLM Context Exporter")
    print("as a Python library in your own applications.\n")
    
    try:
        example_1_simple_export()
        example_2_step_by_step_processing()
        example_3_security_features()
        example_4_custom_integration()
        example_5_batch_processing()
        
        print("\n" + "=" * 60)
        print("🎉 ALL EXAMPLES COMPLETED!")
        print("=" * 60)
        print("\nKey Integration Patterns Demonstrated:")
        print("✅ High-level API for simple exports")
        print("✅ Step-by-step processing for custom logic")
        print("✅ Security features for sensitive data protection")
        print("✅ Custom application integration")
        print("✅ Batch processing for multiple users")
        print("\nFor more examples, see:")
        print("• docs/LIBRARY_USAGE.md - Comprehensive library guide")
        print("• examples/ directory - Additional example scripts")
        print("• tests/ directory - Test cases showing usage patterns")
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nExamples failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()