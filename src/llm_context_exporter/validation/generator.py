"""
Validation test generator.

This module creates test questions to validate successful context transfer.
"""

from typing import List, Dict, Any
from ..models.core import UniversalContextPack
from ..models.output import ValidationSuite, ValidationQuestion


class ValidationGenerator:
    """
    Generates validation tests for exported context.
    
    Creates questions that can be used to verify that the target LLM
    has successfully incorporated the exported context.
    """
    
    def generate_tests(self, context: UniversalContextPack, target: str) -> ValidationSuite:
        """
        Generate validation tests for the target platform.
        
        Args:
            context: The exported context
            target: 'gemini' or 'ollama'
            
        Returns:
            ValidationSuite with questions and expected answers
        """
        questions = []
        
        # Generate project-related questions
        questions.extend(self._generate_project_questions(context))
        
        # Generate preference questions
        questions.extend(self._generate_preference_questions(context))
        
        # Generate technical questions
        questions.extend(self._generate_technical_questions(context))
        
        # If no questions were generated, add a basic context check question
        if not questions:
            questions.append(ValidationQuestion(
                question="Do you have any information about my background or projects?",
                expected_answer_summary="Should indicate limited or no specific context available",
                category="technical"
            ))
        
        # Create validation suite with platform-specific artifacts
        validation_suite = ValidationSuite(
            questions=questions,
            target_platform=target
        )
        
        # Add platform-specific validation artifacts
        if target == 'gemini':
            validation_suite.platform_artifacts = self._generate_gemini_checklist(questions)
        elif target == 'ollama':
            validation_suite.platform_artifacts = self._generate_ollama_commands(questions)
        
        return validation_suite
    
    def _generate_project_questions(self, context: UniversalContextPack) -> List[ValidationQuestion]:
        """Generate questions about user projects."""
        questions = []
        
        if context.projects:
            # General project question
            project_names = [p.name for p in context.projects[:3]]
            questions.append(ValidationQuestion(
                question="What projects am I currently working on?",
                expected_answer_summary=f"Should mention: {', '.join(project_names)}",
                category="project"
            ))
            
            # Specific project questions
            for project in context.projects[:2]:
                if project.tech_stack:
                    questions.append(ValidationQuestion(
                        question=f"What technologies am I using in {project.name}?",
                        expected_answer_summary=f"Should mention: {', '.join(project.tech_stack[:3])}",
                        category="project"
                    ))
        
        return questions
    
    def _generate_preference_questions(self, context: UniversalContextPack) -> List[ValidationQuestion]:
        """Generate questions about user preferences."""
        questions = []
        
        if context.preferences.preferred_tools:
            questions.append(ValidationQuestion(
                question="What are my preferred development tools?",
                expected_answer_summary=f"Should mention: {', '.join(context.preferences.preferred_tools[:3])}",
                category="preference"
            ))
        
        if context.user_profile.role:
            questions.append(ValidationQuestion(
                question="What is my professional role?",
                expected_answer_summary=f"Should identify as: {context.user_profile.role}",
                category="preference"
            ))
        
        return questions
    
    def _generate_technical_questions(self, context: UniversalContextPack) -> List[ValidationQuestion]:
        """Generate questions about technical expertise."""
        questions = []
        
        if context.technical_context.languages:
            questions.append(ValidationQuestion(
                question="What programming languages do I use?",
                expected_answer_summary=f"Should mention: {', '.join(context.technical_context.languages[:3])}",
                category="technical"
            ))
        
        if context.technical_context.domains:
            questions.append(ValidationQuestion(
                question="What technical domains do I work in?",
                expected_answer_summary=f"Should mention: {', '.join(context.technical_context.domains[:2])}",
                category="technical"
            ))
        
        return questions
    
    def _generate_gemini_checklist(self, questions: List[ValidationQuestion]) -> Dict[str, Any]:
        """
        Generate a validation checklist for manual testing with Gemini.
        
        Args:
            questions: List of validation questions
            
        Returns:
            Dictionary containing checklist items and instructions
        """
        checklist_items = []
        
        for i, question in enumerate(questions, 1):
            checklist_items.append({
                "step": i,
                "action": f"Ask Gemini: '{question.question}'",
                "expected": question.expected_answer_summary,
                "category": question.category,
                "check": "□"  # Empty checkbox for manual checking
            })
        
        return {
            "type": "manual_checklist",
            "title": "Gemini Context Validation Checklist",
            "instructions": [
                "1. Open Google Gemini and ensure your context has been added to Saved Info",
                "2. Start a new conversation with Gemini",
                "3. Ask each question below and verify the response matches expectations",
                "4. Check the box (□ → ☑) for each successful validation",
                "5. If any responses are incorrect, review your Saved Info content"
            ],
            "checklist": checklist_items,
            "success_criteria": f"All {len(questions)} questions should receive appropriate responses"
        }
    
    def _generate_ollama_commands(self, questions: List[ValidationQuestion]) -> Dict[str, Any]:
        """
        Generate CLI commands to query the Ollama model with test questions.
        
        Args:
            questions: List of validation questions
            
        Returns:
            Dictionary containing CLI commands and instructions
        """
        commands = []
        
        for i, question in enumerate(questions, 1):
            # Escape quotes for shell command
            escaped_question = question.question.replace('"', '\\"')
            commands.append({
                "step": i,
                "command": f'ollama run your-custom-model "{escaped_question}"',
                "expected": question.expected_answer_summary,
                "category": question.category,
                "description": f"Test {question.category} knowledge"
            })
        
        return {
            "type": "cli_commands",
            "title": "Ollama Model Validation Commands",
            "instructions": [
                "1. Ensure your custom Ollama model has been created successfully",
                "2. Replace 'your-custom-model' with your actual model name",
                "3. Run each command below and verify the response",
                "4. The model should demonstrate knowledge from your exported context",
                "5. If responses are generic, check your Modelfile system prompt"
            ],
            "commands": commands,
            "setup_note": "Make sure to replace 'your-custom-model' with the actual name you used when creating your model",
            "success_criteria": f"Model should provide contextually relevant answers to all {len(questions)} questions"
        }