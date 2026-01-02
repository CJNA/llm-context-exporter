#!/usr/bin/env python3
"""
Demonstration of the ValidationGenerator functionality.

This script shows how to use the ValidationGenerator to create
platform-specific validation tests for exported context.
"""

import json
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_context_exporter.models.core import (
    UniversalContextPack, UserProfile, ProjectBrief, UserPreferences, TechnicalContext
)
from llm_context_exporter.validation.generator import ValidationGenerator


def create_sample_context():
    """Create a sample context pack for demonstration."""
    return UniversalContextPack(
        version="1.0.0",
        created_at=datetime.now(),
        source_platform="chatgpt",
        user_profile=UserProfile(
            role="Senior Software Engineer",
            expertise_areas=["Python", "Machine Learning", "Web Development"],
            background_summary="Experienced full-stack developer with ML expertise"
        ),
        projects=[
            ProjectBrief(
                name="E-commerce Platform",
                description="Building a scalable e-commerce platform with microservices",
                tech_stack=["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
                key_challenges=["Performance optimization", "Payment integration"],
                current_status="In production",
                last_discussed=datetime.now(),
                relevance_score=0.95
            ),
            ProjectBrief(
                name="ML Recommendation Engine",
                description="Machine learning system for product recommendations",
                tech_stack=["Python", "TensorFlow", "Apache Kafka", "Redis"],
                key_challenges=["Real-time inference", "Model drift detection"],
                current_status="Testing phase",
                last_discussed=datetime.now(),
                relevance_score=0.85
            )
        ],
        preferences=UserPreferences(
            coding_style={"language": "Python", "style": "clean and readable"},
            communication_style="Direct and technical",
            preferred_tools=["VS Code", "Git", "Docker", "Jupyter"],
            work_patterns={"methodology": "Agile", "testing": "TDD"}
        ),
        technical_context=TechnicalContext(
            languages=["Python", "JavaScript", "SQL", "Go"],
            frameworks=["FastAPI", "React", "TensorFlow", "Django"],
            tools=["Docker", "Kubernetes", "Git", "Jenkins"],
            domains=["Web Development", "Machine Learning", "DevOps"]
        ),
        metadata={"export_source": "demo"}
    )


def demonstrate_gemini_validation():
    """Demonstrate validation generation for Gemini."""
    print("=" * 60)
    print("GEMINI VALIDATION DEMONSTRATION")
    print("=" * 60)
    
    context = create_sample_context()
    generator = ValidationGenerator()
    
    # Generate validation suite for Gemini
    validation_suite = generator.generate_tests(context, "gemini")
    
    print(f"Generated {len(validation_suite.questions)} validation questions for Gemini")
    print(f"Target platform: {validation_suite.target_platform}")
    print()
    
    # Show questions by category
    categories = {}
    for question in validation_suite.questions:
        if question.category not in categories:
            categories[question.category] = []
        categories[question.category].append(question)
    
    for category, questions in categories.items():
        print(f"📋 {category.upper()} QUESTIONS ({len(questions)}):")
        for i, q in enumerate(questions, 1):
            print(f"  {i}. {q.question}")
            print(f"     Expected: {q.expected_answer_summary}")
        print()
    
    # Show platform-specific artifacts (Gemini checklist)
    artifacts = validation_suite.platform_artifacts
    print("🔍 GEMINI VALIDATION CHECKLIST:")
    print(f"Title: {artifacts['title']}")
    print("\nInstructions:")
    for instruction in artifacts['instructions']:
        print(f"  {instruction}")
    
    print(f"\nChecklist ({len(artifacts['checklist'])} items):")
    for item in artifacts['checklist']:
        print(f"  {item['check']} Step {item['step']}: {item['action']}")
        print(f"      Expected: {item['expected']}")
    print()


def demonstrate_ollama_validation():
    """Demonstrate validation generation for Ollama."""
    print("=" * 60)
    print("OLLAMA VALIDATION DEMONSTRATION")
    print("=" * 60)
    
    context = create_sample_context()
    generator = ValidationGenerator()
    
    # Generate validation suite for Ollama
    validation_suite = generator.generate_tests(context, "ollama")
    
    print(f"Generated {len(validation_suite.questions)} validation questions for Ollama")
    print(f"Target platform: {validation_suite.target_platform}")
    print()
    
    # Show platform-specific artifacts (Ollama CLI commands)
    artifacts = validation_suite.platform_artifacts
    print("⚡ OLLAMA VALIDATION COMMANDS:")
    print(f"Title: {artifacts['title']}")
    print("\nInstructions:")
    for instruction in artifacts['instructions']:
        print(f"  {instruction}")
    
    print(f"\nCommands ({len(artifacts['commands'])} commands):")
    for cmd in artifacts['commands']:
        print(f"  Step {cmd['step']}: {cmd['description']}")
        print(f"    Command: {cmd['command']}")
        print(f"    Expected: {cmd['expected']}")
        print()
    
    print(f"Setup note: {artifacts['setup_note']}")
    print(f"Success criteria: {artifacts['success_criteria']}")
    print()


def demonstrate_json_export():
    """Demonstrate exporting validation suite as JSON."""
    print("=" * 60)
    print("JSON EXPORT DEMONSTRATION")
    print("=" * 60)
    
    context = create_sample_context()
    generator = ValidationGenerator()
    
    # Generate for both platforms
    gemini_suite = generator.generate_tests(context, "gemini")
    ollama_suite = generator.generate_tests(context, "ollama")
    
    # Convert to JSON-serializable format
    def suite_to_dict(suite):
        return {
            "target_platform": suite.target_platform,
            "questions": [
                {
                    "question": q.question,
                    "expected_answer_summary": q.expected_answer_summary,
                    "category": q.category
                }
                for q in suite.questions
            ],
            "platform_artifacts": suite.platform_artifacts
        }
    
    export_data = {
        "gemini": suite_to_dict(gemini_suite),
        "ollama": suite_to_dict(ollama_suite),
        "generated_at": datetime.now().isoformat(),
        "context_summary": {
            "projects": len(context.projects),
            "languages": len(context.technical_context.languages),
            "tools": len(context.preferences.preferred_tools)
        }
    }
    
    print("Validation suites exported as JSON:")
    print(json.dumps(export_data, indent=2))


if __name__ == "__main__":
    print("🚀 LLM Context Exporter - Validation Generator Demo")
    print()
    
    demonstrate_gemini_validation()
    demonstrate_ollama_validation()
    demonstrate_json_export()
    
    print("✅ Demo completed successfully!")