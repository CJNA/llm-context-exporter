"""
Ollama formatter implementation.

This module formats UniversalContextPack data for Ollama Modelfiles.
"""

from typing import Dict, Any, List, Tuple
from ..models.core import UniversalContextPack
from ..models.output import OllamaOutput, ValidationSuite
from ..validation.generator import ValidationGenerator
from .base import PlatformFormatter, FormattingError, SizeLimitExceededError


class OllamaFormatter(PlatformFormatter):
    """
    Formatter for Ollama Modelfiles.
    
    Converts UniversalContextPack into Modelfile format with embedded
    system prompt optimized for local LLMs like Qwen.
    """
    
    target_platform = "ollama"
    MAX_SYSTEM_PROMPT_LENGTH = 100000  # Approximate limit for system prompts
    MAX_MODELFILE_SIZE = 150000  # Total Modelfile size limit
    
    def format_context(self, context: UniversalContextPack, base_model: str = "qwen") -> OllamaOutput:
        """
        Format context pack for Ollama Modelfile.
        
        Args:
            context: Universal context pack to format
            base_model: Base Ollama model to customize
            
        Returns:
            OllamaOutput with Modelfile and setup instructions
            
        Raises:
            FormattingError: If formatting fails
            SizeLimitExceededError: If output exceeds platform limits
        """
        try:
            # Check if context needs to be split due to size constraints
            size_check = self.check_size_constraints(context)
            
            if not size_check["fits"]:
                # Split large context into base Modelfile and supplementary files
                modelfile_content, supplementary_files = self.split_large_context(context, base_model)
            else:
                # Generate standard Modelfile
                modelfile_content = self._generate_modelfile(context, base_model)
                supplementary_files = {}
            
            setup_commands = self._generate_setup_commands(base_model)
            test_commands = self._generate_test_commands(base_model)
            validation_tests = self._generate_validation_tests(context)
            
            return OllamaOutput(
                modelfile_content=modelfile_content,
                supplementary_files=supplementary_files,
                setup_commands=setup_commands,
                test_commands=test_commands,
                validation_tests=validation_tests
            )
            
        except Exception as e:
            raise FormattingError(f"Failed to format context for Ollama: {str(e)}") from e
    
    def get_size_limits(self) -> Dict[str, Any]:
        """Get size limits for Ollama platform."""
        return {
            "max_system_prompt_length": self.MAX_SYSTEM_PROMPT_LENGTH,
            "max_modelfile_size": self.MAX_MODELFILE_SIZE,
            "recommended_length": int(self.MAX_SYSTEM_PROMPT_LENGTH * 0.8),
            "unit": "characters"
        }
    
    def check_size_constraints(self, context: UniversalContextPack) -> Dict[str, Any]:
        """
        Check if context fits within Ollama size constraints.
        
        Args:
            context: Context pack to check
            
        Returns:
            Dictionary with size check results
        """
        # Generate a test system prompt to estimate size
        test_prompt = self._generate_system_prompt(context)
        estimated_size = len(test_prompt)
        fits = estimated_size <= self.MAX_SYSTEM_PROMPT_LENGTH
        
        suggestions = []
        if not fits:
            suggestions.extend([
                "Consider splitting into supplementary files",
                "Reduce number of projects included",
                "Summarize project descriptions"
            ])
        
        return {
            "fits": fits,
            "current_size": estimated_size,
            "max_size": self.MAX_SYSTEM_PROMPT_LENGTH,
            "suggestions": suggestions
        }
    
    def prioritize_content(self, context: UniversalContextPack, max_size: int) -> UniversalContextPack:
        """
        Trim context to fit size constraints while preserving most important info.
        
        Args:
            context: Original context pack
            max_size: Maximum allowed size
            
        Returns:
            Trimmed context pack that fits within size limits
        """
        # Create a copy to avoid modifying the original
        trimmed_context = UniversalContextPack(
            version=context.version,
            created_at=context.created_at,
            source_platform=context.source_platform,
            user_profile=context.user_profile,
            projects=[],
            preferences=context.preferences,
            technical_context=context.technical_context,
            metadata=context.metadata
        )
        
        # Sort projects by relevance score (descending) and recency
        sorted_projects = sorted(
            context.projects,
            key=lambda p: (p.relevance_score, p.last_discussed),
            reverse=True
        )
        
        # Add projects until we approach the size limit
        for project in sorted_projects:
            test_context = UniversalContextPack(
                version=trimmed_context.version,
                created_at=trimmed_context.created_at,
                source_platform=trimmed_context.source_platform,
                user_profile=trimmed_context.user_profile,
                projects=trimmed_context.projects + [project],
                preferences=trimmed_context.preferences,
                technical_context=trimmed_context.technical_context,
                metadata=trimmed_context.metadata
            )
            
            test_prompt = self._generate_system_prompt(test_context)
            if len(test_prompt) <= max_size:
                trimmed_context.projects.append(project)
            else:
                break
        
        return trimmed_context
    
    def _generate_modelfile(self, context: UniversalContextPack, base_model: str) -> str:
        """Generate the Modelfile content."""
        system_prompt = self._generate_system_prompt(context)
        
        # Escape quotes in the system prompt
        escaped_prompt = system_prompt.replace('"""', '\\"\\"\\"').replace('"', '\\"')
        
        modelfile = f"""FROM {base_model}

SYSTEM \"\"\"
{escaped_prompt}
\"\"\"

# Optimized parameters for Qwen models
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096

# Custom template for better conversation flow
TEMPLATE \"\"\"{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
<|im_start|>assistant
{{{{ end }}}}{{{{ .Response }}}}<|im_end|>
\"\"\"
"""
        
        return modelfile
    
    def _generate_system_prompt(self, context: UniversalContextPack) -> str:
        """Generate system prompt optimized for Qwen architecture."""
        prompt_parts = []
        
        # Introduction and role
        intro = "You are an AI assistant with detailed knowledge about the user's background, projects, and preferences."
        if context.user_profile.role:
            intro += f" The user is a {context.user_profile.role}."
        prompt_parts.append(intro)
        
        # User profile and expertise
        if context.user_profile.expertise_areas or context.user_profile.background_summary:
            profile_section = "## User Background"
            if context.user_profile.background_summary:
                profile_section += f"\n{context.user_profile.background_summary}"
            if context.user_profile.expertise_areas:
                areas = ", ".join(context.user_profile.expertise_areas)
                profile_section += f"\n\nExpertise areas: {areas}"
            prompt_parts.append(profile_section)
        
        # Technical context
        if any([context.technical_context.languages, context.technical_context.frameworks, 
                context.technical_context.tools, context.technical_context.domains]):
            tech_section = "## Technical Context"
            
            if context.technical_context.languages:
                languages = ", ".join(context.technical_context.languages)
                tech_section += f"\nProgramming languages: {languages}"
            
            if context.technical_context.frameworks:
                frameworks = ", ".join(context.technical_context.frameworks)
                tech_section += f"\nFrameworks and libraries: {frameworks}"
            
            if context.technical_context.tools:
                tools = ", ".join(context.technical_context.tools)
                tech_section += f"\nDevelopment tools: {tools}"
            
            if context.technical_context.domains:
                domains = ", ".join(context.technical_context.domains)
                tech_section += f"\nTechnical domains: {domains}"
            
            prompt_parts.append(tech_section)
        
        # Projects
        if context.projects:
            projects_section = "## Current Projects"
            
            # Sort projects by relevance and recency
            sorted_projects = sorted(
                context.projects,
                key=lambda p: (p.relevance_score, p.last_discussed),
                reverse=True
            )
            
            for i, project in enumerate(sorted_projects[:10], 1):  # Limit to top 10 projects
                project_info = f"\n{i}. **{project.name}**"
                if project.description:
                    project_info += f"\n   Description: {project.description}"
                if project.tech_stack:
                    tech_stack = ", ".join(project.tech_stack)
                    project_info += f"\n   Tech stack: {tech_stack}"
                if project.current_status:
                    project_info += f"\n   Status: {project.current_status}"
                if project.key_challenges:
                    challenges = "; ".join(project.key_challenges[:3])  # Limit challenges
                    project_info += f"\n   Key challenges: {challenges}"
                
                projects_section += project_info
            
            prompt_parts.append(projects_section)
        
        # Preferences and working patterns
        if (context.preferences.coding_style or context.preferences.communication_style or 
            context.preferences.preferred_tools or context.preferences.work_patterns):
            prefs_section = "## User Preferences"
            
            if context.preferences.communication_style:
                prefs_section += f"\nCommunication style: {context.preferences.communication_style}"
            
            if context.preferences.coding_style:
                style_items = [f"{k}: {v}" for k, v in context.preferences.coding_style.items()]
                prefs_section += f"\nCoding preferences: {'; '.join(style_items)}"
            
            if context.preferences.preferred_tools:
                tools = ", ".join(context.preferences.preferred_tools)
                prefs_section += f"\nPreferred tools: {tools}"
            
            if context.preferences.work_patterns:
                pattern_items = [f"{k}: {v}" for k, v in context.preferences.work_patterns.items()]
                prefs_section += f"\nWork patterns: {'; '.join(pattern_items)}"
            
            prompt_parts.append(prefs_section)
        
        # Instructions for behavior
        instructions = """## Instructions
When responding to the user:
1. Reference their specific projects, technologies, and preferences when relevant
2. Provide solutions that align with their technical stack and expertise level
3. Consider their working patterns and communication style
4. Build upon their existing knowledge and project context
5. Be specific and actionable in your recommendations"""
        
        prompt_parts.append(instructions)
        
        return "\n\n".join(prompt_parts)
    
    def split_large_context(self, context: UniversalContextPack, base_model: str) -> Tuple[str, Dict[str, str]]:
        """
        Split oversized context into base Modelfile and supplementary files.
        
        Args:
            context: Original context pack
            base_model: Base Ollama model
            
        Returns:
            Tuple of (base_modelfile_content, supplementary_files_dict)
        """
        # Create a minimal context for the base Modelfile
        minimal_context = UniversalContextPack(
            version=context.version,
            created_at=context.created_at,
            source_platform=context.source_platform,
            user_profile=context.user_profile,
            projects=context.projects[:3],  # Only top 3 projects
            preferences=context.preferences,
            technical_context=context.technical_context,
            metadata=context.metadata
        )
        
        # Generate base Modelfile with minimal context
        base_modelfile = self._generate_modelfile(minimal_context, base_model)
        
        # Create supplementary files for additional projects
        supplementary_files = {}
        
        if len(context.projects) > 3:
            additional_projects = context.projects[3:]
            projects_content = "# Additional Projects\n\n"
            
            for i, project in enumerate(additional_projects, 4):
                projects_content += f"## {i}. {project.name}\n"
                if project.description:
                    projects_content += f"Description: {project.description}\n"
                if project.tech_stack:
                    projects_content += f"Tech stack: {', '.join(project.tech_stack)}\n"
                if project.current_status:
                    projects_content += f"Status: {project.current_status}\n"
                if project.key_challenges:
                    projects_content += f"Challenges: {'; '.join(project.key_challenges)}\n"
                projects_content += "\n"
            
            supplementary_files["additional_projects.md"] = projects_content
        
        return base_modelfile, supplementary_files
    
    def _generate_setup_commands(self, base_model: str) -> List[str]:
        """Generate shell commands for model creation."""
        model_name = f"{base_model}-contextualized"
        
        return [
            "# Create the custom contextualized model",
            f"ollama create {model_name} -f Modelfile",
            "",
            "# Verify the model was created successfully",
            f"ollama list | grep {model_name}",
            "",
            "# Pull the base model if not already available",
            f"ollama pull {base_model}",
        ]
    
    def _generate_test_commands(self, base_model: str) -> List[str]:
        """Generate commands to test the contextualized model."""
        model_name = f"{base_model}-contextualized"
        
        return [
            "# Test basic context awareness",
            f"ollama run {model_name} \"What projects am I working on?\"",
            "",
            "# Test technical context",
            f"ollama run {model_name} \"What programming languages do I use?\"",
            "",
            "# Test preference awareness",
            f"ollama run {model_name} \"What are my preferred development tools?\"",
            "",
            "# Compare with base model (should show difference)",
            f"ollama run {base_model} \"What projects am I working on?\"",
        ]
    
    def _generate_validation_tests(self, context: UniversalContextPack) -> ValidationSuite:
        """Generate validation tests for the context."""
        generator = ValidationGenerator()
        return generator.generate_tests(context, self.target_platform)