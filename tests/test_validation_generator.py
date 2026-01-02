"""
Tests for the ValidationGenerator class.
"""

import pytest
from datetime import datetime
from src.llm_context_exporter.validation.generator import ValidationGenerator
from src.llm_context_exporter.models.core import (
    UniversalContextPack, UserProfile, ProjectBrief, UserPreferences, TechnicalContext
)


class TestValidationGenerator:
    """Test the ValidationGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = ValidationGenerator()
        
        # Create a sample context pack
        self.context = UniversalContextPack(
            version="1.0.0",
            created_at=datetime.now(),
            source_platform="chatgpt",
            user_profile=UserProfile(
                role="Software Engineer",
                expertise_areas=["Python", "Machine Learning"],
                background_summary="Experienced developer"
            ),
            projects=[
                ProjectBrief(
                    name="Web App",
                    description="A web application",
                    tech_stack=["Python", "Flask", "React"],
                    key_challenges=["Performance", "Scalability"],
                    current_status="In development",
                    last_discussed=datetime.now(),
                    relevance_score=0.9
                ),
                ProjectBrief(
                    name="ML Model",
                    description="Machine learning model",
                    tech_stack=["Python", "TensorFlow", "Pandas"],
                    key_challenges=["Data quality"],
                    current_status="Testing",
                    last_discussed=datetime.now(),
                    relevance_score=0.8
                )
            ],
            preferences=UserPreferences(
                coding_style={"language": "Python", "style": "functional"},
                communication_style="Direct and concise",
                preferred_tools=["VS Code", "Git", "Docker"],
                work_patterns={"hours": "9-5", "methodology": "Agile"}
            ),
            technical_context=TechnicalContext(
                languages=["Python", "JavaScript", "SQL"],
                frameworks=["Flask", "React", "TensorFlow"],
                tools=["Docker", "Git", "VS Code"],
                domains=["Web Development", "Machine Learning"]
            ),
            metadata={}
        )
    
    def test_generate_tests_gemini(self):
        """Test generating validation tests for Gemini."""
        validation_suite = self.generator.generate_tests(self.context, "gemini")
        
        assert validation_suite.target_platform == "gemini"
        assert len(validation_suite.questions) > 0
        
        # Check that we have questions from different categories
        categories = {q.category for q in validation_suite.questions}
        assert "project" in categories
        assert "preference" in categories
        assert "technical" in categories
        
        # Check platform-specific artifacts for Gemini
        assert "platform_artifacts" in validation_suite.__dict__
        artifacts = validation_suite.platform_artifacts
        assert artifacts["type"] == "manual_checklist"
        assert "checklist" in artifacts
        assert "instructions" in artifacts
        assert len(artifacts["checklist"]) == len(validation_suite.questions)
    
    def test_generate_tests_ollama(self):
        """Test generating validation tests for Ollama."""
        validation_suite = self.generator.generate_tests(self.context, "ollama")
        
        assert validation_suite.target_platform == "ollama"
        assert len(validation_suite.questions) > 0
        
        # Check platform-specific artifacts for Ollama
        artifacts = validation_suite.platform_artifacts
        assert artifacts["type"] == "cli_commands"
        assert "commands" in artifacts
        assert "instructions" in artifacts
        assert len(artifacts["commands"]) == len(validation_suite.questions)
        
        # Check that commands contain ollama run
        for cmd in artifacts["commands"]:
            assert "ollama run" in cmd["command"]
    
    def test_project_questions_generation(self):
        """Test that project questions are generated correctly."""
        questions = self.generator._generate_project_questions(self.context)
        
        assert len(questions) > 0
        
        # Should have a general project question
        project_questions = [q for q in questions if "projects" in q.question.lower()]
        assert len(project_questions) > 0
        
        # Should mention project names in expected answers
        general_question = project_questions[0]
        assert "Web App" in general_question.expected_answer_summary
        assert "ML Model" in general_question.expected_answer_summary
        
        # Should have specific project tech stack questions
        tech_questions = [q for q in questions if any(proj.name in q.question for proj in self.context.projects)]
        assert len(tech_questions) > 0
    
    def test_preference_questions_generation(self):
        """Test that preference questions are generated correctly."""
        questions = self.generator._generate_preference_questions(self.context)
        
        assert len(questions) > 0
        
        # Should have tools question
        tools_questions = [q for q in questions if "tools" in q.question.lower()]
        assert len(tools_questions) > 0
        
        # Should have role question
        role_questions = [q for q in questions if "role" in q.question.lower()]
        assert len(role_questions) > 0
        
        # Check expected answers mention the right content
        tools_question = tools_questions[0]
        assert "VS Code" in tools_question.expected_answer_summary
        
        role_question = role_questions[0]
        assert "Software Engineer" in role_question.expected_answer_summary
    
    def test_technical_questions_generation(self):
        """Test that technical questions are generated correctly."""
        questions = self.generator._generate_technical_questions(self.context)
        
        assert len(questions) > 0
        
        # Should have languages question
        lang_questions = [q for q in questions if "languages" in q.question.lower()]
        assert len(lang_questions) > 0
        
        # Should have domains question
        domain_questions = [q for q in questions if "domains" in q.question.lower()]
        assert len(domain_questions) > 0
        
        # Check expected answers
        lang_question = lang_questions[0]
        assert "Python" in lang_question.expected_answer_summary
        
        domain_question = domain_questions[0]
        assert "Web Development" in domain_question.expected_answer_summary
    
    def test_gemini_checklist_format(self):
        """Test the format of Gemini checklist artifacts."""
        questions = [
            self.generator._generate_project_questions(self.context)[0],
            self.generator._generate_preference_questions(self.context)[0]
        ]
        
        checklist = self.generator._generate_gemini_checklist(questions)
        
        assert checklist["type"] == "manual_checklist"
        assert checklist["title"] == "Gemini Context Validation Checklist"
        assert len(checklist["instructions"]) > 0
        assert len(checklist["checklist"]) == 2
        
        # Check checklist item format
        item = checklist["checklist"][0]
        assert "step" in item
        assert "action" in item
        assert "expected" in item
        assert "category" in item
        assert "check" in item
        assert item["check"] == "□"
    
    def test_ollama_commands_format(self):
        """Test the format of Ollama CLI commands artifacts."""
        questions = [
            self.generator._generate_project_questions(self.context)[0],
            self.generator._generate_technical_questions(self.context)[0]
        ]
        
        commands = self.generator._generate_ollama_commands(questions)
        
        assert commands["type"] == "cli_commands"
        assert commands["title"] == "Ollama Model Validation Commands"
        assert len(commands["instructions"]) > 0
        assert len(commands["commands"]) == 2
        
        # Check command format
        cmd = commands["commands"][0]
        assert "step" in cmd
        assert "command" in cmd
        assert "expected" in cmd
        assert "category" in cmd
        assert "description" in cmd
        assert "ollama run your-custom-model" in cmd["command"]
    
    def test_empty_context_handling(self):
        """Test handling of context with minimal data."""
        minimal_context = UniversalContextPack(
            version="1.0.0",
            created_at=datetime.now(),
            source_platform="chatgpt",
            user_profile=UserProfile(),
            projects=[],
            preferences=UserPreferences(),
            technical_context=TechnicalContext(),
            metadata={}
        )
        
        validation_suite = self.generator.generate_tests(minimal_context, "gemini")
        
        # Should still create a validation suite, even if minimal
        assert validation_suite.target_platform == "gemini"
        # May have no questions if no data to validate
        assert isinstance(validation_suite.questions, list)
    
    def test_question_categories(self):
        """Test that all questions have valid categories."""
        validation_suite = self.generator.generate_tests(self.context, "gemini")
        
        valid_categories = {"project", "preference", "technical"}
        for question in validation_suite.questions:
            assert question.category in valid_categories
            assert question.question.strip()
            assert question.expected_answer_summary.strip()