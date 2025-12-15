#!/usr/bin/env python3
"""
Payment Manager Demo

This example demonstrates how to use the PaymentManager class
for handling payments and beta user management.
"""

import os
from llm_context_exporter import PaymentManager


def main():
    """Demonstrate PaymentManager functionality."""
    print("=== LLM Context Exporter Payment Manager Demo ===\n")
    
    # Initialize PaymentManager
    # In production, set STRIPE_SECRET_KEY environment variable
    print("1. Initializing PaymentManager...")
    manager = PaymentManager()
    print("   ✓ PaymentManager initialized\n")
    
    # Demo beta user management
    print("2. Beta User Management:")
    test_email = "demo@example.com"
    
    # Add beta user
    print(f"   Adding beta user: {test_email}")
    manager.add_beta_user(test_email, "Demo user for testing")
    print("   ✓ Beta user added")
    
    # Check if user is beta
    is_beta = manager.is_beta_user(test_email)
    print(f"   Is beta user: {is_beta}")
    
    # Test payment requirements
    print("\n3. Payment Requirements:")
    
    # CLI user (no payment required)
    cli_context = {'source': 'cli'}
    cli_requires_payment = manager.requires_payment(cli_context)
    print(f"   CLI user requires payment: {cli_requires_payment}")
    
    # Beta web user (no payment required)
    beta_web_context = {'source': 'web', 'email': test_email}
    beta_requires_payment = manager.requires_payment(beta_web_context)
    print(f"   Beta web user requires payment: {beta_requires_payment}")
    
    # Regular web user (payment required)
    regular_web_context = {'source': 'web', 'email': 'regular@example.com'}
    regular_requires_payment = manager.requires_payment(regular_web_context)
    print(f"   Regular web user requires payment: {regular_requires_payment}")
    
    # Demo export recording for beta user
    print("\n4. Export Recording:")
    print(f"   Recording export for beta user: {test_email}")
    manager.record_export(test_email, 'gemini', conversations_processed=25, export_size_mb=2.1)
    print("   ✓ Export recorded")
    
    # Demo payment intent creation (requires Stripe key)
    print("\n5. Payment Intent Creation:")
    stripe_key = os.environ.get('STRIPE_SECRET_KEY')
    if stripe_key:
        try:
            print("   Creating payment intent for $3.00...")
            payment_intent = manager.create_payment_intent(300, 'usd')  # $3.00 in cents
            print(f"   ✓ Payment intent created: {payment_intent.id}")
            print(f"   Status: {payment_intent.status}")
            print(f"   Amount: ${payment_intent.amount/100:.2f} {payment_intent.currency.upper()}")
        except Exception as e:
            print(f"   ✗ Payment intent creation failed: {e}")
    else:
        print("   Skipping payment intent creation (no STRIPE_SECRET_KEY)")
        print("   To test payment functionality, set STRIPE_SECRET_KEY environment variable")
    
    # Clean up
    print("\n6. Cleanup:")
    print(f"   Removing beta user: {test_email}")
    manager.remove_beta_user(test_email)
    
    # Verify removal
    is_beta_after_removal = manager.is_beta_user(test_email)
    print(f"   Is beta user after removal: {is_beta_after_removal}")
    print("   ✓ Cleanup complete")
    
    print("\n=== Demo Complete ===")
    print("\nKey Features Demonstrated:")
    print("• PaymentManager initialization")
    print("• Beta user management (add/remove/check)")
    print("• Payment requirement logic (CLI vs Web vs Beta)")
    print("• Export recording for beta users")
    print("• Payment intent creation (with Stripe)")
    print("\nFor production use:")
    print("• Set STRIPE_SECRET_KEY environment variable")
    print("• Set STRIPE_WEBHOOK_SECRET for webhook handling")
    print("• Configure PAYMENT_AMOUNT_CENTS and PAYMENT_CURRENCY as needed")


if __name__ == "__main__":
    main()