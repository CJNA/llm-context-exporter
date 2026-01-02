"""
Context extraction engine for analyzing conversations and extracting domain knowledge.

This module contains the core logic for identifying projects, user preferences,
and technical context from conversation history.
"""

from typing import List, Dict, Any
from datetime import datetime
import re
from collections import defaultdict, Counter

from .models import (
    Conversation, 
    UniversalContextPack, 
    UserProfile, 
    ProjectBrief, 
    UserPreferences, 
    TechnicalContext
)


class ContextExtractor:
    """
    Analyzes conversations and extracts structured domain knowledge.
    
    Uses heuristics and pattern matching to identify:
    - User projects and their details
    - Technical expertise and preferences
    - Working patterns and communication style
    """
    
    def __init__(self):
        """Initialize the context extractor with pattern matchers."""
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Set up regex patterns for extraction."""
        # Programming languages
        self.language_patterns = re.compile(
            r'\b(python|javascript|typescript|java|c\+\+|c#|go|rust|ruby|php|swift|kotlin|scala|r|matlab|sql)\b',
            re.IGNORECASE
        )
        
        # Frameworks and libraries
        self.framework_patterns = re.compile(
            r'\b(react|vue|angular|django|flask|fastapi|spring|express|rails|laravel|tensorflow|pytorch|pandas|numpy)\b',
            re.IGNORECASE
        )
        
        # Tools (moved docker here from frameworks)
        self.tool_patterns = re.compile(
            r'\b(git|github|gitlab|vscode|vs code|pycharm|intellij|aws|azure|gcp|postgres|postgresql|mysql|mongodb|redis|nginx|apache|docker|kubernetes)\b',
            re.IGNORECASE
        )
        
        # Project indicators
        self.project_indicators = [
            r'\bi\'?m working on\b',
            r'\bmy project\b',
            r'\bbuilding\b.*\b(app|application|system|tool|website|service)\b',
            r'\bdeveloping\b',
            r'\bcreating\b.*\b(for|to)\b',
            r'\bproject\s+called\b',
            r'\bproject\s+named\b',
            r'\bworking\s+with\b.*\b(team|client|company)\b',
            r'\bstarted\b.*\b(project|app|system)\b',
        ]
        
        # Role indicators - order matters, longer phrases first
        self.role_patterns = re.compile(
            r'\bi\'?m\s+a\s+(senior\s+software\s+engineer|junior\s+software\s+engineer|senior\s+data\s+scientist|junior\s+data\s+scientist|senior\s+architect|junior\s+developer|senior\s+engineer|data\s+scientist|software\s+engineer|product\s+manager|senior\s+developer|junior\s+engineer|lead\s+developer|tech\s+lead|software\s+architect|system\s+architect|developer|architect|analyst|programmer|engineer|scientist|manager|designer|student|researcher|consultant|lead|senior|junior|intern)',
            re.IGNORECASE
        )
    
    def extract_context(self, conversations: List[Conversation]) -> UniversalContextPack:
        """
        Extract domain knowledge from conversations.
        
        Args:
            conversations: List of parsed conversations
            
        Returns:
            UniversalContextPack with profile, projects, and preferences
        """
        # Extract individual components
        user_profile = self.extract_profile(conversations)
        projects = self.extract_projects(conversations)
        preferences = self.extract_preferences(conversations)
        technical_context = self.extract_technical_context(conversations)
        
        return UniversalContextPack(
            version="1.0",
            created_at=datetime.now(),
            source_platform="chatgpt",
            user_profile=user_profile,
            projects=projects,
            preferences=preferences,
            technical_context=technical_context,
            metadata={
                "total_conversations": len(conversations),
                "extraction_date": datetime.now().isoformat(),
                "extractor_version": "1.0"
            }
        )
    
    def extract_projects(self, conversations: List[Conversation]) -> List[ProjectBrief]:
        """
        Identify and summarize user projects.
        
        Args:
            conversations: List of conversations to analyze
            
        Returns:
            List of identified projects
        """
        projects = []
        project_conversations = defaultdict(list)
        
        # Group conversations by potential projects
        for conv in conversations:
            project_name = self._identify_project_in_conversation(conv)
            if project_name:
                project_conversations[project_name].append(conv)
        
        # Create project briefs
        for project_name, convs in project_conversations.items():
            project = self._create_project_brief(project_name, convs)
            if project:
                projects.append(project)
        
        # Sort by relevance score (most recent and frequently discussed first)
        projects.sort(key=lambda p: p.relevance_score, reverse=True)
        
        return projects
    
    def extract_profile(self, conversations: List[Conversation]) -> UserProfile:
        """
        Extract user background and role.
        
        Args:
            conversations: List of conversations to analyze
            
        Returns:
            UserProfile with role and expertise
        """
        all_text = self._get_user_messages_text(conversations)
        
        # Extract role
        role_match = self.role_patterns.search(all_text)
        role = role_match.group(1) if role_match else None
        
        # Extract expertise areas (most mentioned technologies)
        tech_mentions = Counter()
        tech_mentions.update(self.language_patterns.findall(all_text))
        tech_mentions.update(self.framework_patterns.findall(all_text))
        
        expertise_areas = [tech for tech, count in tech_mentions.most_common(10) if count >= 1]
        
        # Generate background summary
        background_summary = self._generate_background_summary(conversations, role, expertise_areas)
        
        return UserProfile(
            role=role,
            expertise_areas=expertise_areas,
            background_summary=background_summary
        )
    
    def extract_preferences(self, conversations: List[Conversation]) -> UserPreferences:
        """
        Extract user working patterns and preferences.
        
        Args:
            conversations: List of conversations to analyze
            
        Returns:
            UserPreferences with coding style and patterns
        """
        all_text = self._get_user_messages_text(conversations)
        
        # Extract coding style preferences
        coding_style = {}
        
        # Determine primary language based on frequency
        language_mentions = Counter(self.language_patterns.findall(all_text))
        if language_mentions:
            primary_lang = language_mentions.most_common(1)[0][0]
            coding_style['primary_language'] = primary_lang.title()
        
        # Extract style preferences
        if 'functional' in all_text.lower():
            coding_style['paradigm'] = 'functional'
        elif 'object-oriented' in all_text.lower() or 'oop' in all_text.lower():
            coding_style['paradigm'] = 'object-oriented'
        
        # Extract testing preferences
        if 'test-driven' in all_text.lower() or 'tdd' in all_text.lower():
            coding_style['testing_approach'] = 'test-driven'
        elif 'unit test' in all_text.lower():
            coding_style['testing_approach'] = 'unit testing'
        
        # Extract preferred tools
        tool_mentions = self.tool_patterns.findall(all_text)
        preferred_tools = list(set(tool_mentions))
        
        # Analyze communication style
        communication_style = self._analyze_communication_style(conversations)
        
        # Extract work patterns
        work_patterns = self._extract_work_patterns(conversations)
        
        return UserPreferences(
            coding_style=coding_style,
            communication_style=communication_style,
            preferred_tools=preferred_tools,
            work_patterns=work_patterns
        )
    
    def extract_technical_context(self, conversations: List[Conversation]) -> TechnicalContext:
        """
        Extract technical knowledge and expertise.
        
        Args:
            conversations: List of conversations to analyze
            
        Returns:
            TechnicalContext with languages, frameworks, tools, and domains
        """
        all_text = self._get_user_messages_text(conversations)
        
        languages = list(set(self.language_patterns.findall(all_text)))
        frameworks = list(set(self.framework_patterns.findall(all_text)))
        tools = list(set(self.tool_patterns.findall(all_text)))
        
        # Identify domains based on conversation topics
        domains = self._identify_domains(conversations)
        
        return TechnicalContext(
            languages=languages,
            frameworks=frameworks,
            tools=tools,
            domains=domains
        )
    
    def _get_user_messages_text(self, conversations: List[Conversation]) -> str:
        """Extract all user message content as a single string."""
        user_messages = []
        for conv in conversations:
            for msg in conv.messages:
                if msg.role == 'user':
                    user_messages.append(msg.content)
        return ' '.join(user_messages)
    
    def _identify_project_in_conversation(self, conversation: Conversation) -> str:
        """Try to identify a project name from conversation title and content."""
        # First check if there are any user messages at all
        user_messages = [msg for msg in conversation.messages if msg.role == 'user']
        if not user_messages:
            return None
            
        # Check conversation title first
        title = conversation.title.lower()
        
        # Skip generic titles
        generic_titles = ['new chat', 'untitled', 'conversation', 'chat']
        if any(generic in title for generic in generic_titles):
            # Look for project indicators in messages
            for msg in conversation.messages[:5]:  # Check first few messages
                if msg.role == 'user':
                    for pattern in self.project_indicators:
                        if re.search(pattern, msg.content, re.IGNORECASE):
                            # Extract potential project name
                            return self._extract_project_name_from_text(msg.content)
            return None
        
        return title.title()
    
    def _extract_project_name_from_text(self, text: str) -> str:
        """Extract a potential project name from text."""
        # This is a simplified heuristic - could be improved with NLP
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in ['building', 'creating', 'developing', 'working', 'project', 'app', 'application', 'system']:
                # Look for the next few words that might be a project name
                if i + 1 < len(words):
                    potential_name = ' '.join(words[i+1:i+4])
                    # Clean up common words
                    potential_name = re.sub(r'\b(a|an|the|for|to|with|on|called|named)\b', '', potential_name, flags=re.IGNORECASE)
                    potential_name = potential_name.strip()
                    if potential_name:
                        return potential_name.title()
        
        # If no specific pattern found, look for capitalized words that might be project names
        capitalized_words = [word for word in words if word[0].isupper() and len(word) > 2]
        if capitalized_words:
            return ' '.join(capitalized_words[:3])
            
        return "Unnamed Project"
    
    def _create_project_brief(self, project_name: str, conversations: List[Conversation]) -> ProjectBrief:
        """Create a project brief from related conversations."""
        if not conversations:
            return None
        
        # Extract tech stack from conversations
        all_text = ' '.join([
            msg.content for conv in conversations 
            for msg in conv.messages if msg.role == 'user'
        ])
        
        tech_stack = list(set(
            self.language_patterns.findall(all_text) + 
            self.framework_patterns.findall(all_text)
        ))
        
        # Generate description (simplified)
        description = f"Project involving {', '.join(tech_stack[:3]) if tech_stack else 'development'}"
        
        # Calculate relevance score based on recency and frequency
        last_discussed = max(conv.updated_at for conv in conversations)
        days_since_last = (datetime.now() - last_discussed).days
        # Higher score for more recent and more frequent discussions
        # Clamp to [0.0, 1.0] range to satisfy Pydantic validation
        relevance_score = min(1.0, len(conversations) * 0.1 + max(0, 1.0 - (days_since_last / 365.0)))
        
        # Extract key challenges
        key_challenges = self._extract_challenges_from_conversations(conversations)
        
        return ProjectBrief(
            name=project_name,
            description=description,
            tech_stack=tech_stack,
            key_challenges=key_challenges,
            current_status="Active",
            last_discussed=last_discussed,
            relevance_score=relevance_score
        )
    
    def _generate_background_summary(self, conversations: List[Conversation], role: str, expertise: List[str]) -> str:
        """Generate a background summary from extracted information."""
        summary_parts = []
        
        if role:
            summary_parts.append(f"Works as a {role}")
        
        if expertise:
            summary_parts.append(f"with expertise in {', '.join(expertise[:5])}")
        
        # Add conversation-based insights
        total_conversations = len(conversations)
        if total_conversations > 50:
            summary_parts.append(f"Active user with {total_conversations} conversations")
        
        return '. '.join(summary_parts) + '.' if summary_parts else "No background information available."
    
    def _analyze_communication_style(self, conversations: List[Conversation]) -> str:
        """Analyze user's communication style from messages."""
        user_messages = [
            msg.content for conv in conversations 
            for msg in conv.messages if msg.role == 'user'
        ]
        
        if not user_messages:
            return "Unknown"
        
        # Simple heuristics for communication style
        avg_length = sum(len(msg.split()) for msg in user_messages) / len(user_messages)
        
        if avg_length > 50:
            return "Detailed and thorough"
        elif avg_length > 20:
            return "Clear and comprehensive"
        else:
            return "Concise and direct"
    
    def _identify_domains(self, conversations: List[Conversation]) -> List[str]:
        """Identify technical domains from conversation topics."""
        domains = set()
        
        all_text = ' '.join([
            conv.title + ' ' + ' '.join([msg.content for msg in conv.messages])
            for conv in conversations
        ]).lower()
        
        # Domain keywords mapping
        domain_keywords = {
            'web development': ['web', 'frontend', 'backend', 'html', 'css', 'javascript', 'react', 'vue', 'angular'],
            'data science': ['data', 'analysis', 'pandas', 'numpy', 'machine learning', 'ml', 'ai', 'statistics'],
            'mobile development': ['mobile', 'ios', 'android', 'swift', 'kotlin', 'react native', 'flutter'],
            'devops': ['docker', 'kubernetes', 'aws', 'azure', 'deployment', 'ci/cd', 'infrastructure'],
            'database': ['database', 'sql', 'postgres', 'mysql', 'mongodb', 'redis'],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                domains.add(domain)
        
        return list(domains)
    
    def _extract_challenges_from_conversations(self, conversations: List[Conversation]) -> List[str]:
        """Extract key challenges mentioned in conversations."""
        challenges = []
        
        # Challenge indicators
        challenge_patterns = [
            r'\bproblem\s+with\b',
            r'\bissue\s+with\b',
            r'\bstruggling\s+with\b',
            r'\bdifficulty\s+with\b',
            r'\bchallenge\s+with\b',
            r'\berror\s+with\b',
            r'\bbug\s+in\b',
            r'\bfailing\s+to\b',
            r'\bcan\'t\s+get\b',
            r'\bhaving\s+trouble\b',
        ]
        
        for conv in conversations:
            for msg in conv.messages:
                if msg.role == 'user':
                    for pattern in challenge_patterns:
                        matches = re.finditer(pattern, msg.content, re.IGNORECASE)
                        for match in matches:
                            # Extract the context around the challenge
                            start = max(0, match.start() - 20)
                            end = min(len(msg.content), match.end() + 50)
                            context = msg.content[start:end].strip()
                            
                            # Clean up and add if not too generic
                            if len(context) > 10 and len(context) < 100:
                                challenges.append(context)
        
        # Remove duplicates and limit to top 3
        unique_challenges = list(set(challenges))[:3]
        return unique_challenges
    
    def _extract_work_patterns(self, conversations: List[Conversation]) -> Dict[str, Any]:
        """Extract work patterns and habits from conversations."""
        patterns = {}
        
        # Analyze conversation timing to infer work schedule
        timestamps = []
        for conv in conversations:
            for msg in conv.messages:
                if msg.role == 'user':
                    timestamps.append(msg.timestamp)
        
        if timestamps:
            # Find most common hours
            hours = [ts.hour for ts in timestamps]
            hour_counter = Counter(hours)
            most_active_hour = hour_counter.most_common(1)[0][0]
            
            if 9 <= most_active_hour <= 17:
                patterns['work_schedule'] = 'business_hours'
            elif 18 <= most_active_hour <= 23:
                patterns['work_schedule'] = 'evening'
            else:
                patterns['work_schedule'] = 'flexible'
        
        # Analyze conversation frequency
        if len(conversations) > 100:
            patterns['usage_frequency'] = 'heavy'
        elif len(conversations) > 20:
            patterns['usage_frequency'] = 'regular'
        else:
            patterns['usage_frequency'] = 'occasional'
        
        return patterns