#!/usr/bin/env python3
"""
Demo script for beta user management functionality.

This script demonstrates the BetaManager class and admin CLI functionality
for managing beta users, tracking usage, and collecting feedback.
"""

import tempfile
import os
from datetime import datetime
from llm_context_exporter.web.beta import BetaManager


def main():
    """Demonstrate beta user management functionality."""
    print("🚀 LLM Context Exporter - Beta User Management Demo")
    print("=" * 60)
    
    # Create temporary database for demo
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    db_path = temp_db.name
    
    try:
        # Initialize BetaManager
        print("\n1. Initializing BetaManager")
        manager = BetaManager(db_path)
        print(f"   Database: {db_path}")
        print("   ✓ BetaManager initialized")
        
        # Add beta users
        print("\n2. Adding Beta Users")
        test_users = [
            ("alice@example.com", "Early adopter, power user"),
            ("bob@example.com", "Developer, interested in Ollama"),
            ("carol@example.com", "Designer, prefers Gemini"),
        ]
        
        for email, notes in test_users:
            manager.add_beta_user(email, notes)
            print(f"   ✓ Added: {email}")
        
        # List beta users
        print("\n3. Listing Beta Users")
        users = manager.get_beta_users()
        print(f"   Total beta users: {len(users)}")
        for user in users:
            print(f"   • {user.email} (added: {user.added_date.strftime('%Y-%m-%d')})")
            if user.notes:
                print(f"     Notes: {user.notes}")
        
        # Simulate some exports
        print("\n4. Simulating Export Activity")
        export_activities = [
            ("alice@example.com", "gemini", 45, 3.2),
            ("alice@example.com", "ollama", 32, 2.8),
            ("bob@example.com", "ollama", 28, 2.1),
            ("carol@example.com", "gemini", 52, 4.1),
        ]
        
        for email, platform, conversations, size_mb in export_activities:
            manager.record_export(email, platform, conversations, size_mb)
            print(f"   ✓ Recorded export: {email} → {platform} ({conversations} conversations, {size_mb}MB)")
        
        # Simulate feedback
        print("\n5. Collecting Feedback")
        feedback_data = [
            ("alice@example.com", "Great tool! Love the privacy-first approach.", 5, "export_001", "gemini"),
            ("alice@example.com", "Ollama setup was a bit tricky but works well.", 4, "export_002", "ollama"),
            ("bob@example.com", "Perfect for my local development workflow.", 5, "export_003", "ollama"),
            ("carol@example.com", "Easy to use, good Gemini integration.", 4, "export_004", "gemini"),
        ]
        
        for email, feedback_text, rating, export_id, platform in feedback_data:
            manager.record_feedback(email, feedback_text, rating, export_id, platform)
            print(f"   ✓ Feedback from {email}: {rating}⭐ ({platform})")
        
        # Show detailed statistics (refresh user list to get updated feedback counts)
        print("\n6. User Statistics")
        users = manager.get_beta_users()  # Refresh to get updated feedback counts
        for user in users:
            stats = manager.get_usage_stats(user.email)
            print(f"\n   📊 {user.email}:")
            print(f"      Total exports: {stats.total_exports}")
            print(f"      Conversations processed: {stats.total_conversations_processed}")
            print(f"      Average export size: {stats.average_export_size_mb:.1f}MB")
            print(f"      Last export: {stats.last_export_date.strftime('%Y-%m-%d %H:%M') if stats.last_export_date else 'Never'}")
            print(f"      Feedback count: {user.feedback_count}")
            
            if stats.exports_by_target:
                print(f"      Platform usage:")
                for platform, count in stats.exports_by_target.items():
                    print(f"        • {platform.title()}: {count} exports")
        
        # Show all feedback
        print("\n7. All Feedback")
        all_feedback = manager.get_all_feedback()
        print(f"   Total feedback entries: {len(all_feedback)}")
        
        for i, fb in enumerate(all_feedback, 1):
            print(f"\n   📝 Feedback #{i}:")
            print(f"      User: {fb.email}")
            print(f"      Rating: {'⭐' * fb.rating} ({fb.rating}/5)")
            print(f"      Platform: {fb.target_platform.title()}")
            print(f"      Date: {fb.timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"      Text: {fb.feedback_text}")
        
        # Test beta user checking
        print("\n8. Beta User Verification")
        test_emails = ["alice@example.com", "nonbeta@example.com"]
        for email in test_emails:
            is_beta = manager.is_beta_user(email)
            status = "✓ Beta user" if is_beta else "✗ Not beta user"
            print(f"   {email}: {status}")
        
        # Generate summary report
        print("\n9. Summary Report")
        total_users = len(users)
        total_exports = sum(user.total_exports for user in users)
        total_feedback = len(all_feedback)
        active_users = len([user for user in users if user.total_exports > 0])
        
        # Platform breakdown
        platform_stats = {}
        for user in users:
            user_stats = manager.get_usage_stats(user.email)
            for platform, count in user_stats.exports_by_target.items():
                platform_stats[platform] = platform_stats.get(platform, 0) + count
        
        # Rating breakdown
        rating_stats = {}
        for fb in all_feedback:
            rating_stats[fb.rating] = rating_stats.get(fb.rating, 0) + 1
        
        print(f"   📈 Beta Program Summary:")
        print(f"      Total beta users: {total_users}")
        print(f"      Active users: {active_users}")
        print(f"      Total exports: {total_exports}")
        print(f"      Total feedback: {total_feedback}")
        print(f"      Avg exports per user: {total_exports/total_users:.1f}")
        feedback_rate = (total_feedback/total_exports*100) if total_exports > 0 else 0
        print(f"      Feedback rate: {feedback_rate:.1f}%")
        
        if platform_stats:
            print(f"      Platform usage:")
            for platform, count in platform_stats.items():
                percentage = (count / total_exports * 100) if total_exports > 0 else 0
                print(f"        • {platform.title()}: {count} exports ({percentage:.1f}%)")
        
        if rating_stats:
            print(f"      Rating distribution:")
            for rating in range(1, 6):
                count = rating_stats.get(rating, 0)
                if count > 0:
                    percentage = (count / total_feedback * 100) if total_feedback > 0 else 0
                    stars = "⭐" * rating
                    print(f"        • {stars} ({rating}): {count} ({percentage:.1f}%)")
        
        # Test user removal
        print("\n10. User Management")
        print("    Removing one user for demonstration...")
        manager.remove_beta_user("carol@example.com")
        print("    ✓ Removed carol@example.com")
        
        remaining_users = manager.get_beta_users()
        print(f"    Remaining users: {len(remaining_users)}")
        for user in remaining_users:
            print(f"      • {user.email}")
        
        print("\n✅ Demo completed successfully!")
        print("\n💡 Admin CLI Usage:")
        print("   llm-context-export admin list-users")
        print("   llm-context-export admin add-user --email user@example.com --notes 'New beta user'")
        print("   llm-context-export admin user-stats --email user@example.com")
        print("   llm-context-export admin feedback --rating 5")
        print("   llm-context-export admin report --output beta_report.csv")
        print("   llm-context-export admin remove-user --email user@example.com")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up temporary database
        if os.path.exists(db_path):
            os.unlink(db_path)
            print(f"\n🧹 Cleaned up temporary database: {db_path}")


if __name__ == "__main__":
    main()