"""
Gemini formatter implementation.

This module formats UniversalContextPack data for Google Gemini's Saved Info feature.
"""

from typing import Dict, Any, List
from datetime import datetime
from ..models import UniversalContextPack, GeminiOutput, ValidationSuite, ValidationQuestion
from .base import PlatformFormatter, FormattingError, SizeLimitExceededError


class GeminiFormatter(PlatformFormatter):
    """
    Formatter for Google Gemini Saved Info.
    
    Converts UniversalContextPack into text format optimized for Gemini's
    comprehension and size limits.
    """
    
    target_platform = "gemini"
    MAX_TEXT_LENGTH = 32000  # Approximate limit for Gemini Saved Info
    RECOMMENDED_LENGTH = int(MAX_TEXT_LENGTH * 0.8)  # Leave buffer for safety
    
    def format_context(self, context: UniversalContextPack) -> GeminiOutput:
        """
        Format context pack for Gemini Saved Info.
        
        Args:
            context: Universal context pack to format
            
        Returns:
            GeminiOutput with formatted text and instructions
            
        Raises:
            FormattingError: If formatting fails
            SizeLimitExceededError: If output exceeds platform limits
        """
        try:
            # Check if we need to prioritize content
            size_check = self.check_size_constraints(context)
            working_context = context
            
            if not size_check["fits"]:
                working_context = self.prioritize_content(context, self.RECOMMENDED_LENGTH)
                # Re-check after prioritization
                new_size_check = self.check_size_constraints(working_context)
                if not new_size_check["fits"]:
                    raise SizeLimitExceededError(
                        f"Context still too large after prioritization: "
                        f"{new_size_check['current_size']} > {self.MAX_TEXT_LENGTH}"
                    )
            
            formatted_text = self._generate_formatted_text(working_context)
            instructions = self._generate_instructions()
            validation_tests = self._generate_validation_tests(working_context)
            
            return GeminiOutput(
                formatted_text=formatted_text,
                instructions=instructions,
                validation_tests=validation_tests,
                metadata={
                    "formatter_version": "1.0",
                    "target_platform": self.target_platform,
                    "original_projects": len(context.projects),
                    "final_projects": len(working_context.projects),
                    "text_length": len(formatted_text),
                    "prioritized": working_context != context,
                    "created_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            if isinstance(e, (FormattingError, SizeLimitExceededError)):
                raise
            raise FormattingError(f"Failed to format context for Gemini: {str(e)}") from e
    
    def get_size_limits(self) -> Dict[str, Any]:
        """Get size limits for Gemini platform."""
        return {
            "max_text_length": self.MAX_TEXT_LENGTH,
            "recommended_length": self.RECOMMENDED_LENGTH,
            "unit": "characters",
            "description": "Gemini Saved Info character limits"
        }
    
    def check_size_constraints(self, context: UniversalContextPack) -> Dict[str, Any]:
        """
        Check if context fits within Gemini size constraints.
        
        Args:
            context: Context pack to check
            
        Returns:
            Dictionary with size check results
        """
        # Generate the actual formatted text to get accurate size
        formatted_text = self._generate_formatted_text(context)
        current_size = len(formatted_text)
        fits = current_size <= self.MAX_TEXT_LENGTH
        
        suggestions = []
        if not fits:
            suggestions.extend([
                "Consider excluding older or less relevant projects",
                "Remove detailed technical context if not essential",
                "Shorten project descriptions",
                "Focus on most recent work and preferences"
            ])
        
        return {
            "fits": fits,
            "current_size": current_size,
            "max_size": self.MAX_TEXT_LENGTH,
            "recommended_size": self.RECOMMENDED_LENGTH,
            "utilization": current_size / self.MAX_TEXT_LENGTH,
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
        # Create a copy to modify
        prioritized = UniversalContextPack(
            version=context.version,
            created_at=context.created_at,
            source_platform=context.source_platform,
            user_profile=context.user_profile,  # Always keep user profile
            projects=[],
            preferences=context.preferences,  # Always keep preferences
            technical_context=context.technical_context,  # Always keep technical context
            metadata=context.metadata.copy()
        )
        
        # Sort projects by relevance score (descending) and recency
        sorted_projects = sorted(
            context.projects,
            key=lambda p: (p.relevance_score, p.last_discussed),
            reverse=True
        )
        
        # Add projects one by one until we approach the size limit
        for project in sorted_projects:
            # Create temporary context with this project added
            temp_context = UniversalContextPack(
                version=prioritized.version,
                created_at=prioritized.created_at,
                source_platform=prioritized.source_platform,
                user_profile=prioritized.user_profile,
                projects=prioritized.projects + [project],
                preferences=prioritized.preferences,
                technical_context=prioritized.technical_context,
                metadata=prioritized.metadata
            )
            
            # Check if adding this project would exceed the limit
            temp_text = self._generate_formatted_text(temp_context)
            if len(temp_text) <= max_size:
                prioritized.projects.append(project)
            else:
                # Try adding a shortened version of the project
                shortened_project = self._shorten_project(project)
                temp_context.projects[-1] = shortened_project
                temp_text = self._generate_formatted_text(temp_context)
                if len(temp_text) <= max_size:
                    prioritized.projects.append(shortened_project)
                break
        
        # Update metadata to indicate prioritization
        prioritized.metadata["prioritized"] = True
        prioritized.metadata["original_project_count"] = len(context.projects)
        prioritized.metadata["final_project_count"] = len(prioritized.projects)
        
        return prioritized
    
    def _shorten_project(self, project) -> Any:
        """Create a shortened version of a project for size constraints."""
        from ..models.core import ProjectBrief
        
        # Truncate description and challenges
        short_description = project.description[:200] + "..." if len(project.description) > 200 else project.description
        short_challenges = project.key_challenges[:2]  # Keep only top 2 challenges
        
        return ProjectBrief(
            name=project.name,
            description=short_description,
            tech_stack=project.tech_stack[:5],  # Keep top 5 technologies
            key_challenges=short_challenges,
            current_status=project.current_status[:100] + "..." if len(project.current_status) > 100 else project.current_status,
            last_discussed=project.last_discussed,
            relevance_score=project.relevance_score
        )
    
    def _generate_formatted_text(self, context: UniversalContextPack) -> str:
        """Generate the formatted text for Gemini Saved Info."""
        sections = []
        
        # Header with export info
        sections.append(f"# Personal Context Export")
        sections.append(f"Exported from {context.source_platform.title()} on {context.created_at.strftime('%Y-%m-%d')}")
        sections.append("")
        
        # User Profile Section
        if context.user_profile.role or context.user_profile.background_summary or context.user_profile.expertise_areas:
            sections.append("## About Me")
            
            if context.user_profile.role:
                sections.append(f"**Role:** {context.user_profile.role}")
            
            if context.user_profile.background_summary:
                sections.append(f"**Background:** {context.user_profile.background_summary}")
            
            if context.user_profile.expertise_areas:
                expertise = ", ".join(context.user_profile.expertise_areas)
                sections.append(f"**Expertise Areas:** {expertise}")
            
            sections.append("")
        
        # Technical Context Section
        if any([context.technical_context.languages, context.technical_context.frameworks, 
                context.technical_context.tools, context.technical_context.domains]):
            sections.append("## Technical Background")
            
            if context.technical_context.languages:
                languages = ", ".join(context.technical_context.languages)
                sections.append(f"**Programming Languages:** {languages}")
            
            if context.technical_context.frameworks:
                frameworks = ", ".join(context.technical_context.frameworks)
                sections.append(f"**Frameworks & Libraries:** {frameworks}")
            
            if context.technical_context.tools:
                tools = ", ".join(context.technical_context.tools)
                sections.append(f"**Development Tools:** {tools}")
            
            if context.technical_context.domains:
                domains = ", ".join(context.technical_context.domains)
                sections.append(f"**Technical Domains:** {domains}")
            
            sections.append("")
        
        # Projects Section
        if context.projects:
            sections.append("## Current Projects")
            
            for i, project in enumerate(context.projects, 1):
                sections.append(f"### {i}. {project.name}")
                sections.append(f"**Description:** {project.description}")
                
                if project.tech_stack:
                    tech_stack = ", ".join(project.tech_stack)
                    sections.append(f"**Tech Stack:** {tech_stack}")
                
                if project.key_challenges:
                    challenges = "; ".join(project.key_challenges)
                    sections.append(f"**Key Challenges:** {challenges}")
                
                if project.current_status:
                    sections.append(f"**Current Status:** {project.current_status}")
                
                sections.append(f"**Last Discussed:** {project.last_discussed.strftime('%Y-%m-%d')}")
                sections.append("")
        
        # Preferences Section
        if any([context.preferences.coding_style, context.preferences.communication_style,
                context.preferences.preferred_tools, context.preferences.work_patterns]):
            sections.append("## Working Preferences")
            
            if context.preferences.communication_style:
                sections.append(f"**Communication Style:** {context.preferences.communication_style}")
            
            if context.preferences.coding_style:
                style_items = [f"{k}: {v}" for k, v in context.preferences.coding_style.items()]
                sections.append(f"**Coding Style:** {'; '.join(style_items)}")
            
            if context.preferences.preferred_tools:
                tools = ", ".join(context.preferences.preferred_tools)
                sections.append(f"**Preferred Tools:** {tools}")
            
            if context.preferences.work_patterns:
                pattern_items = [f"{k}: {v}" for k, v in context.preferences.work_patterns.items()]
                sections.append(f"**Work Patterns:** {'; '.join(pattern_items)}")
            
            sections.append("")
        
        # Footer
        sections.append("---")
        sections.append("*This context was automatically extracted from conversation history.*")
        sections.append("*Please reference this information when providing assistance.*")
        
        return "\n".join(sections)
    
    def _generate_instructions(self) -> str:
        """Generate step-by-step instructions for using the output."""
        return """# How to Add Context to Gemini Saved Info

Follow these steps to add your exported context to Google Gemini:

## Step 1: Access Gemini Saved Info
1. Open Google Gemini in your web browser: https://gemini.google.com
2. Sign in to your Google account if not already signed in
3. Look for your profile picture or initial in the top-right corner
4. Click on your profile picture to open the menu

## Step 2: Navigate to Saved Info
1. In the dropdown menu, look for "Saved Info" or "Personal Info"
2. Click on "Saved Info" to open the saved information panel
3. If you don't see this option, try looking for "Settings" and then "Saved Info"

## Step 3: Add Your Context
1. Look for an "Add Info" button, "+" button, or "New" option
2. Click to create a new saved info entry
3. You'll see a text input area or form
4. Copy the formatted text from the output file
5. Paste it into the text area

## Step 4: Save and Verify
1. Click "Save" or "Add" to store your context
2. You should see confirmation that the information was saved
3. The context will now be available to Gemini in future conversations

## Step 5: Test Your Context
Use the validation questions provided to test that Gemini has access to your context:
- Ask about your current projects
- Inquire about your technical background
- Test knowledge of your preferences

## Troubleshooting
- If the text is too long, try using the prioritized version
- If Saved Info isn't available, check that you're using the latest version of Gemini
- Some features may vary by region or account type

## Important Notes
- Your context is stored securely with your Google account
- You can edit or remove this information at any time
- Gemini will use this context to provide more personalized assistance"""
    
    def _generate_validation_tests(self, context: UniversalContextPack) -> ValidationSuite:
        """Generate validation tests for the context."""
        from ..validation.generator import ValidationGenerator
        
        generator = ValidationGenerator()
        return generator.generate_tests(context, self.target_platform)