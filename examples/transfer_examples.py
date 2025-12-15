#!/usr/bin/env python3
"""
Transfer Examples: Successful and Unsuccessful Scenarios

This script demonstrates what types of content transfer well between LLM platforms
and what types of content may not transfer successfully.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_context_exporter.security.detection import SensitiveDataDetector


def show_successful_transfers():
    """Demonstrate content that transfers well between platforms."""
    print("=" * 70)
    print("✅ SUCCESSFUL TRANSFER EXAMPLES")
    print("=" * 70)
    
    successful_examples = [
        {
            "category": "Project Context",
            "original": """
            I'm building an e-commerce platform using FastAPI for the backend 
            and React for the frontend. The main challenge I'm facing is 
            implementing real-time inventory updates across multiple warehouses. 
            I'm using PostgreSQL for the main database and Redis for caching.
            """,
            "why_successful": "Clear technical context with specific technologies",
            "expected_transfer": "Target LLM will understand your tech stack and current challenges"
        },
        {
            "category": "Technical Preferences",
            "original": """
            I prefer Python for backend development because of its readability 
            and extensive ecosystem. I always follow PEP 8 style guidelines 
            and write comprehensive unit tests using pytest. I use VS Code 
            with the Python extension for development.
            """,
            "why_successful": "Specific preferences and tools mentioned",
            "expected_transfer": "Target LLM will suggest Python solutions and follow your coding style"
        },
        {
            "category": "Domain Expertise",
            "original": """
            I have 5 years of experience in machine learning, specifically 
            computer vision applications. I've worked with TensorFlow and 
            PyTorch, and I'm particularly interested in object detection 
            and image segmentation tasks. I usually deploy models using 
            Docker containers.
            """,
            "why_successful": "Clear expertise areas with specific technologies",
            "expected_transfer": "Target LLM will provide ML-focused advice and understand your background"
        },
        {
            "category": "Work Patterns",
            "original": """
            I work in an Agile environment with 2-week sprints. I prefer 
            test-driven development and always write documentation for my code. 
            I like to break down complex problems into smaller, manageable tasks 
            and iterate quickly.
            """,
            "why_successful": "Clear methodology and approach preferences",
            "expected_transfer": "Target LLM will suggest solutions that fit your workflow"
        },
        {
            "category": "Problem-Solving Approach",
            "original": """
            When debugging, I start by reproducing the issue in a minimal 
            environment, then use logging and debugging tools to trace the 
            problem. I prefer to understand the root cause rather than 
            applying quick fixes.
            """,
            "why_successful": "Systematic approach that can be applied universally",
            "expected_transfer": "Target LLM will suggest debugging strategies that match your style"
        }
    ]
    
    for i, example in enumerate(successful_examples, 1):
        print(f"\n{i}. {example['category']}")
        print("-" * 50)
        print("Original Context:")
        print(example['original'].strip())
        print(f"\n✅ Why This Transfers Well:")
        print(f"   {example['why_successful']}")
        print(f"\n🎯 Expected Result:")
        print(f"   {example['expected_transfer']}")
    
    print(f"\n{'='*70}")
    print("💡 SUCCESS FACTORS:")
    print("• Specific technologies and tools mentioned")
    print("• Clear preferences and methodologies")
    print("• Concrete examples and use cases")
    print("• Technical depth and expertise areas")
    print("• Consistent patterns across conversations")


def show_unsuccessful_transfers():
    """Demonstrate content that may not transfer well."""
    print("\n\n" + "=" * 70)
    print("❌ UNSUCCESSFUL TRANSFER EXAMPLES")
    print("=" * 70)
    
    unsuccessful_examples = [
        {
            "category": "ChatGPT-Specific Features",
            "original": """
            Can you browse the web to find the latest React documentation 
            and then generate an image showing the component lifecycle? 
            Also, run this code in the code interpreter to test it.
            """,
            "why_unsuccessful": "References ChatGPT-specific capabilities",
            "what_happens": "Target LLM won't understand these feature references",
            "workaround": "Rephrase as general requests: 'Help me understand React lifecycle'"
        },
        {
            "category": "Conversational Context",
            "original": """
            As we discussed in our previous conversation, the API endpoint 
            you suggested didn't work. Can you look at the error message 
            I shared earlier and provide an alternative approach?
            """,
            "why_unsuccessful": "References previous conversation context",
            "what_happens": "Target LLM has no access to previous conversations",
            "workaround": "Include all relevant context in each new conversation"
        },
        {
            "category": "Temporal References",
            "original": """
            Following up on yesterday's question about deployment strategies, 
            I tried the Docker approach you mentioned last week, but I'm 
            running into the same issue we discussed on Monday.
            """,
            "why_unsuccessful": "Time-based references to past interactions",
            "what_happens": "Target LLM doesn't know about timing or previous discussions",
            "workaround": "Provide complete context without temporal references"
        },
        {
            "category": "File/Upload References",
            "original": """
            Based on the CSV file I uploaded, can you analyze the data 
            patterns? Also, look at the screenshot I shared showing the 
            error message and help me fix it.
            """,
            "why_unsuccessful": "References uploaded files or images",
            "what_happens": "Target LLM has no access to previously uploaded content",
            "workaround": "Describe the data/error in text or re-upload to new platform"
        },
        {
            "category": "Personal/Sensitive Information",
            "original": """
            My database connection string is postgresql://john:password123@db.company.com:5432/prod
            and my API key is sk-1234567890abcdef. Can you help me optimize the queries?
            """,
            "why_unsuccessful": "Contains sensitive information that should be redacted",
            "what_happens": "Information will be detected and redacted for security",
            "workaround": "Use placeholder values: postgresql://user:password@host:port/database"
        },
        {
            "category": "Vague or Contextual References",
            "original": """
            The thing we were working on isn't behaving as expected. 
            It's doing that weird thing again. Can you help me fix it 
            like you did before?
            """,
            "why_unsuccessful": "Too vague and context-dependent",
            "what_happens": "Target LLM can't understand what 'thing' or 'weird behavior' means",
            "workaround": "Be specific: 'My React component is re-rendering unexpectedly'"
        }
    ]
    
    for i, example in enumerate(unsuccessful_examples, 1):
        print(f"\n{i}. {example['category']}")
        print("-" * 50)
        print("Original Context:")
        print(example['original'].strip())
        print(f"\n❌ Why This Doesn't Transfer:")
        print(f"   {example['why_unsuccessful']}")
        print(f"\n🤔 What Happens:")
        print(f"   {example['what_happens']}")
        print(f"\n💡 Workaround:")
        print(f"   {example['workaround']}")
    
    print(f"\n{'='*70}")
    print("⚠️  COMMON ISSUES:")
    print("• Platform-specific feature references")
    print("• Conversational context dependencies")
    print("• Temporal or sequential references")
    print("• File upload or media references")
    print("• Sensitive information that gets redacted")
    print("• Vague or ambiguous language")


def demonstrate_sensitive_data_detection():
    """Show how sensitive data is detected and handled."""
    print("\n\n" + "=" * 70)
    print("🔒 SENSITIVE DATA DETECTION EXAMPLES")
    print("=" * 70)
    
    detector = SensitiveDataDetector()
    
    sensitive_examples = [
        {
            "content": """
            My project uses this database connection:
            postgresql://admin:secretpass123@db.mycompany.com:5432/production
            """,
            "description": "Database connection string with credentials"
        },
        {
            "content": """
            Here's my OpenAI API key for testing: sk-1234567890abcdef1234567890abcdef
            And my AWS access key: AKIAIOSFODNN7EXAMPLE
            """,
            "description": "API keys and access credentials"
        },
        {
            "content": """
            Contact me at john.doe@mycompany.com or call (555) 123-4567.
            My home directory is /Users/johndoe/Documents/secret-project/
            """,
            "description": "Personal contact information and file paths"
        },
        {
            "content": """
            For payment testing, use card 4532-1234-5678-9012
            SSN: 123-45-6789 for the demo account
            """,
            "description": "Financial and identity information"
        }
    ]
    
    for i, example in enumerate(sensitive_examples, 1):
        print(f"\n{i}. {example['description']}")
        print("-" * 50)
        print("Original Content:")
        print(example['content'].strip())
        
        # Detect sensitive data
        detections = detector.detect_sensitive_data(example['content'])
        
        if detections:
            print(f"\n🚨 Sensitive Data Detected ({len(detections)} items):")
            for detection in detections:
                print(f"   • {detection['type'].upper()}: {detection['value']}")
            
            # Show redacted version
            redacted = detector.redact_sensitive_data(example['content'])
            print(f"\n✂️  Redacted Version:")
            print(redacted.strip())
        else:
            print("\n✅ No sensitive data detected")
    
    print(f"\n{'='*70}")
    print("🛡️  PROTECTION FEATURES:")
    print("• Automatic detection of 15+ sensitive data types")
    print("• User approval required before processing sensitive content")
    print("• Secure redaction with placeholder values")
    print("• Configurable sensitivity levels")
    print("• Audit trail of redaction decisions")


def show_platform_specific_considerations():
    """Show platform-specific transfer considerations."""
    print("\n\n" + "=" * 70)
    print("🎯 PLATFORM-SPECIFIC CONSIDERATIONS")
    print("=" * 70)
    
    platforms = {
        "Gemini": {
            "strengths": [
                "Excellent at understanding structured context",
                "Good with technical documentation",
                "Handles large context windows well",
                "Strong reasoning capabilities"
            ],
            "limitations": [
                "May not retain very specific coding preferences",
                "Context can be overwritten by user",
                "No persistent memory across sessions"
            ],
            "optimization_tips": [
                "Use clear, structured formatting",
                "Include specific examples of your preferences",
                "Prioritize recent and relevant projects",
                "Use bullet points and headers for clarity"
            ]
        },
        "Ollama (Local LLMs)": {
            "strengths": [
                "Complete privacy and control",
                "Persistent context in model",
                "Can be fine-tuned for specific use cases",
                "Works offline"
            ],
            "limitations": [
                "Limited by local hardware capabilities",
                "May have smaller context windows",
                "Requires technical setup",
                "Model quality varies"
            ],
            "optimization_tips": [
                "Keep context concise due to size limits",
                "Focus on most important information",
                "Use clear, direct language",
                "Test with different base models"
            ]
        }
    }
    
    for platform, details in platforms.items():
        print(f"\n🎯 {platform}")
        print("-" * 50)
        
        print("✅ Strengths:")
        for strength in details["strengths"]:
            print(f"   • {strength}")
        
        print("\n⚠️  Limitations:")
        for limitation in details["limitations"]:
            print(f"   • {limitation}")
        
        print("\n💡 Optimization Tips:")
        for tip in details["optimization_tips"]:
            print(f"   • {tip}")
    
    print(f"\n{'='*70}")
    print("🔄 GENERAL TRANSFER TIPS:")
    print("• Test with validation questions after transfer")
    print("• Start with most important context first")
    print("• Be prepared to refine and adjust")
    print("• Keep backups of your original context")
    print("• Monitor how well the target LLM uses your context")


def show_validation_strategies():
    """Show how to validate successful context transfer."""
    print("\n\n" + "=" * 70)
    print("✅ VALIDATION STRATEGIES")
    print("=" * 70)
    
    validation_categories = {
        "Project Knowledge": [
            "What projects am I currently working on?",
            "What technologies do I use in my main project?",
            "What challenges am I facing in my current work?",
            "What is the status of my e-commerce platform project?"
        ],
        "Technical Preferences": [
            "What is my preferred programming language?",
            "What development tools do I typically use?",
            "What coding style do I follow?",
            "How do I approach testing in my projects?"
        ],
        "Domain Expertise": [
            "What areas of technology am I most experienced in?",
            "What machine learning frameworks do I use?",
            "What deployment strategies do I prefer?",
            "What databases do I have experience with?"
        ],
        "Work Patterns": [
            "What development methodology do I follow?",
            "How do I approach debugging problems?",
            "What is my preferred way of learning new technologies?",
            "How do I structure my development workflow?"
        ]
    }
    
    for category, questions in validation_categories.items():
        print(f"\n📋 {category}")
        print("-" * 50)
        for i, question in enumerate(questions, 1):
            print(f"   {i}. {question}")
    
    print(f"\n{'='*70}")
    print("🧪 VALIDATION PROCESS:")
    print("1. Ask validation questions to your target LLM")
    print("2. Compare responses with your expected answers")
    print("3. Note any missing or incorrect information")
    print("4. Refine your context based on gaps found")
    print("5. Re-test with additional questions")
    print("6. Document what works well for future transfers")
    
    print(f"\n🎯 SUCCESS INDICATORS:")
    print("• LLM mentions your specific projects and technologies")
    print("• Responses align with your preferences and style")
    print("• LLM demonstrates understanding of your expertise level")
    print("• Suggestions match your typical workflow and tools")


def main():
    """Run all transfer examples."""
    print("🚀 LLM Context Exporter - Transfer Examples")
    print("This script demonstrates what content transfers well between")
    print("LLM platforms and what content may face challenges.\n")
    
    try:
        show_successful_transfers()
        show_unsuccessful_transfers()
        demonstrate_sensitive_data_detection()
        show_platform_specific_considerations()
        show_validation_strategies()
        
        print("\n\n" + "=" * 70)
        print("🎉 TRANSFER EXAMPLES COMPLETE!")
        print("=" * 70)
        print("\n📚 Key Takeaways:")
        print("• Specific, technical context transfers best")
        print("• Avoid platform-specific or conversational references")
        print("• Sensitive data is automatically detected and protected")
        print("• Different platforms have different strengths")
        print("• Always validate your transfers with test questions")
        print("• Iterate and refine based on results")
        
        print(f"\n💡 Next Steps:")
        print("• Try exporting your own ChatGPT data")
        print("• Test with the validation questions provided")
        print("• Refine your context based on what works")
        print("• Share feedback to help improve the tool")
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nExamples failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()