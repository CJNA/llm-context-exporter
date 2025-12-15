# Context Schema Documentation

The LLM Context Exporter uses a standardized **Universal Context Pack** format designed for maximum portability across different LLM platforms. This document provides a comprehensive reference for the schema structure.

## Overview

The Universal Context Pack is a JSON-based format that captures the essential elements of a user's accumulated knowledge and preferences from their LLM interactions. It's designed to be:

- **Platform-agnostic**: Works with any target LLM platform
- **Extensible**: Can accommodate new fields and data types
- **Structured**: Organized for optimal LLM comprehension
- **Portable**: Self-contained with all necessary metadata

## Schema Structure

### Root Object

```json
{
  "version": "1.0.0",
  "created_at": "2024-01-15T10:30:00Z",
  "source_platform": "chatgpt",
  "user_profile": { ... },
  "projects": [ ... ],
  "preferences": { ... },
  "technical_context": { ... },
  "metadata": { ... }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Schema version (semantic versioning) |
| `created_at` | string (ISO 8601) | Yes | Timestamp when context was created |
| `source_platform` | string | Yes | Source platform identifier |
| `user_profile` | UserProfile | Yes | User background and role information |
| `projects` | ProjectBrief[] | Yes | Array of project summaries |
| `preferences` | UserPreferences | Yes | User preferences and patterns |
| `technical_context` | TechnicalContext | Yes | Technical skills and expertise |
| `metadata` | object | No | Additional processing metadata |

## UserProfile

Captures the user's professional background and expertise areas.

```json
{
  "role": "Senior Software Engineer",
  "expertise_areas": ["Python", "Machine Learning", "Web Development"],
  "background_summary": "Experienced full-stack developer with ML expertise",
  "years_of_experience": 8,
  "industry": "Technology",
  "education_level": "Bachelor's Degree"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | string | No | Professional role or title |
| `expertise_areas` | string[] | Yes | Areas of technical expertise |
| `background_summary` | string | Yes | Brief professional summary |
| `years_of_experience` | number | No | Years of professional experience |
| `industry` | string | No | Primary industry sector |
| `education_level` | string | No | Highest education level |

### Expertise Areas Examples

- Programming languages: "Python", "JavaScript", "Java"
- Domains: "Machine Learning", "Web Development", "DevOps"
- Specializations: "Computer Vision", "Natural Language Processing"
- Industries: "FinTech", "Healthcare", "E-commerce"

## ProjectBrief

Represents a specific project or work area discussed in conversations.

```json
{
  "name": "E-commerce Platform",
  "description": "Building a scalable e-commerce platform with microservices architecture",
  "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
  "key_challenges": [
    "Performance optimization for high traffic",
    "Payment processing integration",
    "Inventory management synchronization"
  ],
  "current_status": "In production",
  "last_discussed": "2024-01-10T15:30:00Z",
  "relevance_score": 0.95,
  "project_type": "Professional",
  "team_size": 5,
  "duration_months": 12
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Project name or identifier |
| `description` | string | Yes | Detailed project description |
| `tech_stack` | string[] | Yes | Technologies and tools used |
| `key_challenges` | string[] | Yes | Main challenges or problems |
| `current_status` | string | Yes | Current project status |
| `last_discussed` | string (ISO 8601) | Yes | Last conversation about project |
| `relevance_score` | number (0-1) | Yes | Relevance score for prioritization |
| `project_type` | string | No | Type of project (Professional, Personal, Academic) |
| `team_size` | number | No | Number of team members |
| `duration_months` | number | No | Project duration in months |

### Current Status Values

- `"Planning"` - Project in planning phase
- `"In development"` - Active development
- `"Testing"` - In testing/QA phase
- `"In production"` - Live and operational
- `"Maintenance"` - Maintenance mode
- `"On hold"` - Temporarily paused
- `"Completed"` - Finished project
- `"Cancelled"` - Cancelled project

### Relevance Score

The relevance score (0.0 to 1.0) indicates how important or frequently discussed a project is:

- `0.9-1.0`: Highly relevant, frequently discussed
- `0.7-0.8`: Moderately relevant, occasionally discussed
- `0.5-0.6`: Somewhat relevant, rarely discussed
- `0.0-0.4`: Low relevance, mentioned briefly

## UserPreferences

Captures the user's working patterns, preferences, and communication style.

```json
{
  "coding_style": {
    "primary_language": "Python",
    "style_guide": "PEP 8",
    "preferences": ["clean and readable", "well-documented", "test-driven"]
  },
  "communication_style": "Direct and technical",
  "preferred_tools": ["VS Code", "Git", "Docker", "Jupyter"],
  "work_patterns": {
    "methodology": "Agile",
    "testing_approach": "TDD",
    "documentation_level": "Comprehensive",
    "code_review_style": "Thorough"
  },
  "learning_preferences": ["hands-on", "documentation", "video tutorials"],
  "collaboration_style": "Team-oriented"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `coding_style` | object | Yes | Programming style preferences |
| `communication_style` | string | Yes | Preferred communication approach |
| `preferred_tools` | string[] | Yes | Favorite tools and software |
| `work_patterns` | object | Yes | Work methodology preferences |
| `learning_preferences` | string[] | No | Preferred learning methods |
| `collaboration_style` | string | No | Team collaboration approach |

### Coding Style Object

| Field | Type | Description |
|-------|------|-------------|
| `primary_language` | string | Most frequently used programming language |
| `style_guide` | string | Preferred coding style guide |
| `preferences` | string[] | General coding preferences |

### Work Patterns Object

| Field | Type | Description |
|-------|------|-------------|
| `methodology` | string | Development methodology (Agile, Waterfall, etc.) |
| `testing_approach` | string | Testing methodology (TDD, BDD, etc.) |
| `documentation_level` | string | Documentation preference level |
| `code_review_style` | string | Code review approach |

## TechnicalContext

Comprehensive technical skills and expertise information.

```json
{
  "languages": ["Python", "JavaScript", "SQL", "Go", "TypeScript"],
  "frameworks": ["FastAPI", "React", "TensorFlow", "Django", "Express.js"],
  "tools": ["Docker", "Kubernetes", "Git", "Jenkins", "AWS"],
  "domains": ["Web Development", "Machine Learning", "DevOps", "Data Science"],
  "databases": ["PostgreSQL", "MongoDB", "Redis", "Elasticsearch"],
  "cloud_platforms": ["AWS", "Google Cloud", "Azure"],
  "certifications": ["AWS Solutions Architect", "Google Cloud Professional"],
  "specializations": ["Computer Vision", "Natural Language Processing"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `languages` | string[] | Yes | Programming languages |
| `frameworks` | string[] | Yes | Frameworks and libraries |
| `tools` | string[] | Yes | Development tools and software |
| `domains` | string[] | Yes | Technical domains and areas |
| `databases` | string[] | No | Database technologies |
| `cloud_platforms` | string[] | No | Cloud service providers |
| `certifications` | string[] | No | Professional certifications |
| `specializations` | string[] | No | Specialized technical areas |

## Metadata

Additional information about the context extraction and processing.

```json
{
  "export_source": "chatgpt_official_export",
  "conversations_processed": 150,
  "extraction_method": "heuristic_analysis",
  "filtering_applied": true,
  "filters": {
    "excluded_topics": ["personal", "private"],
    "min_relevance_score": 0.5,
    "date_range": {
      "start": "2023-01-01T00:00:00Z",
      "end": "2024-01-15T23:59:59Z"
    }
  },
  "processing_stats": {
    "total_messages": 3420,
    "projects_identified": 8,
    "languages_detected": 12,
    "processing_time_seconds": 45.2
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `export_source` | string | Source of the original export |
| `conversations_processed` | number | Number of conversations analyzed |
| `extraction_method` | string | Method used for context extraction |
| `filtering_applied` | boolean | Whether filters were applied |
| `filters` | object | Details of applied filters |
| `processing_stats` | object | Statistics from processing |

## Schema Validation

The schema is validated using JSON Schema. Here's the validation schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "created_at", "source_platform", "user_profile", "projects", "preferences", "technical_context"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "source_platform": {
      "type": "string",
      "enum": ["chatgpt", "claude", "perplexity", "other"]
    },
    "user_profile": {
      "$ref": "#/definitions/UserProfile"
    },
    "projects": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/ProjectBrief"
      }
    },
    "preferences": {
      "$ref": "#/definitions/UserPreferences"
    },
    "technical_context": {
      "$ref": "#/definitions/TechnicalContext"
    },
    "metadata": {
      "type": "object"
    }
  }
}
```

## Version History

### Version 1.0.0 (Current)
- Initial schema definition
- Core fields for user profile, projects, preferences, and technical context
- Support for metadata and filtering information

### Planned Future Versions

#### Version 1.1.0
- Enhanced project tracking with milestones
- Team collaboration information
- Integration with external project management tools

#### Version 1.2.0
- Multi-language support for international users
- Cultural context and communication preferences
- Time zone and availability information

## Best Practices

### For Context Extraction

1. **Relevance Scoring**: Use meaningful relevance scores based on:
   - Frequency of discussion
   - Recency of mentions
   - Depth of technical detail
   - User engagement level

2. **Project Identification**: Look for:
   - Consistent naming patterns
   - Technical stack mentions
   - Problem-solving discussions
   - Status updates and progress reports

3. **Preference Detection**: Identify patterns in:
   - Tool and technology choices
   - Communication style consistency
   - Problem-solving approaches
   - Code style preferences

### For Platform Formatting

1. **Prioritization**: When context exceeds limits:
   - Prioritize by relevance score
   - Include recent projects first
   - Maintain technical context completeness
   - Preserve user preferences

2. **Adaptation**: For different platforms:
   - Adjust language and tone
   - Optimize for platform-specific features
   - Consider context window limitations
   - Maintain semantic meaning

## Examples

### Minimal Valid Context

```json
{
  "version": "1.0.0",
  "created_at": "2024-01-15T10:30:00Z",
  "source_platform": "chatgpt",
  "user_profile": {
    "expertise_areas": ["Python"],
    "background_summary": "Software developer"
  },
  "projects": [],
  "preferences": {
    "coding_style": {
      "primary_language": "Python"
    },
    "communication_style": "Technical",
    "preferred_tools": ["VS Code"],
    "work_patterns": {
      "methodology": "Agile"
    }
  },
  "technical_context": {
    "languages": ["Python"],
    "frameworks": [],
    "tools": ["VS Code"],
    "domains": ["Software Development"]
  }
}
```

### Rich Context Example

See the main README.md for a comprehensive example with all fields populated.

## Migration Guide

When updating between schema versions:

1. **Backward Compatibility**: Older versions should be readable by newer parsers
2. **Field Mapping**: New fields should have sensible defaults
3. **Validation**: Always validate against the target schema version
4. **Conversion**: Provide conversion utilities for major version changes

## Tools and Utilities

### Validation

```python
from llm_context_exporter.models.core import UniversalContextPack
import json

# Load and validate context
with open('context.json', 'r') as f:
    data = json.load(f)

context = UniversalContextPack(**data)  # Validates automatically
```

### Schema Generation

```python
from llm_context_exporter.models.core import UniversalContextPack

# Generate JSON schema
schema = UniversalContextPack.model_json_schema()
print(json.dumps(schema, indent=2))
```

### Context Merging

```python
from llm_context_exporter.core.incremental import IncrementalUpdater

updater = IncrementalUpdater()
merged_context = updater.merge_contexts(old_context, new_context)
```

This schema documentation provides the foundation for understanding and working with the Universal Context Pack format used by the LLM Context Exporter.