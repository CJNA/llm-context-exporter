"""
Gemini formatter implementation.

This module formats UniversalContextPack data for Google Gemini Gems.
Gems are custom AI personas that persist context across conversations.
"""

import copy
from typing import Dict, Any, List
from datetime import datetime
from ..models import UniversalContextPack, GeminiOutput, ValidationSuite, ValidationQuestion
from .base import PlatformFormatter, FormattingError, SizeLimitExceededError


class GeminiFormatter(PlatformFormatter):
    """
    Formatter for Google Gemini Gems.
    
    Converts UniversalContextPack into instruction format optimized for
    Gemini Gems - custom AI personas with persistent context.
    """
    
    target_platform = "gemini"
    MAX_TEXT_LENGTH = 50000  # Gem instructions can be longer than Saved Info
    RECOMMENDED_LENGTH = int(MAX_TEXT_LENGTH * 0.8)
    
    def format_context(self, context: UniversalContextPack) -> GeminiOutput:
        """
        Format context pack for Gemini Gems.
        
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
            gem_description = self._generate_gem_description(working_context)
            instructions = self._generate_instructions(gem_description)
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
                    "created_at": datetime.now().isoformat(),
                    "gem_description": gem_description
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
        # Create a deep copy to avoid modifying the original
        prioritized = copy.deepcopy(context)
        prioritized.projects = []
        
        # Sort projects by relevance score (descending) and recency
        sorted_projects = sorted(
            context.projects,
            key=lambda p: (p.relevance_score, p.last_discussed),
            reverse=True
        )
        
        # Add projects one by one until we approach the size limit
        for project in sorted_projects:
            # Create temporary context with this project added
            temp_context = copy.deepcopy(prioritized)
            temp_context.projects = prioritized.projects + [project]
            
            # Check if adding this project would exceed the limit
            temp_text = self._generate_formatted_text(temp_context)
            if len(temp_text) <= max_size:
                prioritized.projects.append(project)
            else:
                # Try adding a shortened version of the project
                shortened_project = self._shorten_project(project)
                temp_context.projects = prioritized.projects + [shortened_project]
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
        """Generate the Gem Instructions text optimized for Gemini Gems."""
        sections = []
        
        # Preamble - sets the persona
        sections.append("You are my personal technical assistant and pair programmer. Use the following context about my skills, active projects, and preferences to tailor all your responses to my specific situation.")
        sections.append("")
        
        # User Profile Section
        if context.user_profile.expertise_areas or context.user_profile.background_summary:
            sections.append("## About the User")
            
            if context.user_profile.role:
                sections.append(f"Role: {context.user_profile.role}")
            
            if context.user_profile.background_summary:
                sections.append(f"Background: {context.user_profile.background_summary}")
            
            if context.user_profile.expertise_areas:
                # Deduplicate and normalize
                expertise = list(set(area.strip() for area in context.user_profile.expertise_areas))
                sections.append(f"Expertise: {', '.join(expertise)}")
            
            sections.append("")
        
        # Technical Context Section
        if any([context.technical_context.languages, context.technical_context.frameworks, 
                context.technical_context.tools, context.technical_context.domains]):
            sections.append("## Technical Stack")
            
            if context.technical_context.languages:
                # Deduplicate case-insensitively
                langs = list({lang.lower(): lang for lang in context.technical_context.languages}.values())
                sections.append(f"Languages: {', '.join(sorted(langs))}")
            
            if context.technical_context.frameworks:
                frameworks = list({fw.lower(): fw for fw in context.technical_context.frameworks}.values())
                sections.append(f"Frameworks: {', '.join(sorted(frameworks))}")
            
            if context.technical_context.tools:
                tools = list({t.lower(): t for t in context.technical_context.tools}.values())
                sections.append(f"Tools: {', '.join(sorted(tools))}")
            
            if context.technical_context.domains:
                domains = list({d.lower(): d for d in context.technical_context.domains}.values())
                sections.append(f"Domains: {', '.join(sorted(domains))}")
            
            sections.append("")
        
        # Active Projects Section - limit to most recent/relevant
        if context.projects:
            sections.append("## Active Projects")
            
            # Sort by recency and take top 20
            sorted_projects = sorted(
                context.projects,
                key=lambda p: p.last_discussed,
                reverse=True
            )[:20]
            
            for project in sorted_projects:
                project_line = f"- **{project.name}**"
                if project.tech_stack:
                    tech = ", ".join(project.tech_stack[:5])
                    project_line += f" ({tech})"
                if project.description and project.description != f"Project involving development":
                    # Only add description if it's meaningful
                    desc = project.description[:100]
                    if len(project.description) > 100:
                        desc += "..."
                    project_line += f": {desc}"
                sections.append(project_line)
            
            if len(context.projects) > 20:
                sections.append(f"- ... and {len(context.projects) - 20} more projects")
            
            sections.append("")
        
        # Preferences Section
        if any([context.preferences.coding_style, context.preferences.communication_style,
                context.preferences.preferred_tools, context.preferences.work_patterns]):
            sections.append("## Preferences")
            
            if context.preferences.communication_style:
                sections.append(f"Communication: {context.preferences.communication_style}")
            
            if context.preferences.coding_style:
                style_items = [f"{k}: {v}" for k, v in context.preferences.coding_style.items()]
                sections.append(f"Coding style: {'; '.join(style_items)}")
            
            if context.preferences.preferred_tools:
                tools = ", ".join(context.preferences.preferred_tools)
                sections.append(f"Preferred tools: {tools}")
            
            sections.append("")
        
        # Behavioral instructions
        sections.append("## How to Assist")
        sections.append("- Reference my specific projects and tech stack when relevant")
        sections.append("- Provide solutions aligned with my expertise level")
        sections.append("- Be concise and actionable")
        sections.append("- When I mention a project by name, recall its context")
        sections.append("- Suggest improvements based on my preferred tools and patterns")
        
        return "\n".join(sections)
    
    def _generate_instructions(self, gem_description: str) -> str:
        """Generate step-by-step instructions for creating a Gemini Gem."""
        return f"""# How to Create Your Gemini Gem

Gemini Gems are custom AI personas that remember your context across all conversations.

## Requirements
- Gemini Advanced subscription (required for Gems)

## Step 1: Open Gem Manager
1. Go to https://gemini.google.com
2. Look for the **Gem Manager** in the left sidebar
3. Click **"New Gem"**

## Step 2: Configure Your Gem

### Name
```
My Dev Partner
```
(or choose your own name)

### Description
Copy from `gem_description.txt` or use:
```
{gem_description}
```

### Instructions
Copy the entire contents of `gemini_gem_instructions.txt` and paste it into the Instructions field.

## Step 3: Optional - Add Knowledge Files
You can upload `context_pack.json` to the Knowledge section for the Gem to reference detailed project information.

## Step 4: Save and Test
1. Click **Save**
2. Open your new Gem from the sidebar
3. Test with questions like:
   - "What projects am I working on?"
   - "What's my tech stack?"
   - "Help me with my Carvis project"

## Tips
- The Gem persists across sessions - no need to re-paste context
- You can create multiple Gems for different purposes (work, personal, specific projects)
- Edit the Instructions anytime to update your context

## Updating Your Gem
When you export new conversations, re-run the export and update the Instructions field with the new content."""
    
    def _generate_gem_description(self, context: UniversalContextPack) -> str:
        """Generate a concise description for the Gem."""
        parts = []
        
        # Add role if available
        if context.user_profile.role:
            parts.append(f"Technical assistant for {context.user_profile.role}")
        else:
            parts.append("Personal dev partner")
        
        # Add top languages (max 4)
        if context.technical_context.languages:
            langs = list({lang.lower(): lang for lang in context.technical_context.languages}.values())[:4]
            parts.append(f"with expertise in {', '.join(sorted(langs))}")
        
        # Add project count
        project_count = len(context.projects)
        if project_count > 0:
            parts.append(f"Knows {project_count}+ projects")
        
        # Add key project names (find notable ones)
        notable_projects = []
        for p in context.projects[:50]:  # Check first 50
            name_lower = p.name.lower()
            # Look for project names that seem significant
            if any(kw in name_lower for kw in ['carvis', 'app', 'api', 'service', 'platform', 'system']):
                notable_projects.append(p.name)
                if len(notable_projects) >= 2:
                    break
        
        if notable_projects:
            parts.append(f"including {', '.join(notable_projects)}")
        
        # Add source info
        parts.append("Imported from ChatGPT history.")
        
        return " ".join(parts)
    
    def _generate_validation_tests(self, context: UniversalContextPack) -> ValidationSuite:
        """Generate validation tests for the context."""
        from ..validation.generator import ValidationGenerator
        
        generator = ValidationGenerator()
        return generator.generate_tests(context, self.target_platform)