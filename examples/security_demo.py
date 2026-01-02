#!/usr/bin/env python3
"""
Security Features Demo

This script demonstrates the privacy and security features of the LLM Context Exporter,
including encryption, sensitive data detection, secure deletion, and network monitoring.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_context_exporter.security import (
    SecurityManager,
    FileEncryption,
    SensitiveDataDetector,
    SecureFileDeleter,
    NetworkActivityMonitor,
    prompt_for_redaction_approval
)


def demo_encryption():
    """Demonstrate file encryption and decryption."""
    print("=" * 60)
    print("FILE ENCRYPTION DEMO")
    print("=" * 60)
    
    encryption = FileEncryption()
    
    # Create a test file with sensitive content
    test_content = """
    Project: MyApp Development
    Database: postgresql://user:password123@localhost:5432/myapp
    API Key: sk-1234567890abcdef1234567890abcdef
    Email: developer@mycompany.com
    """
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(test_content)
        test_file = f.name
    
    print(f"Created test file: {test_file}")
    print(f"Original size: {os.path.getsize(test_file)} bytes")
    
    try:
        # Encrypt the file
        password = "demo_password_123"
        encrypted_file = encryption.encrypt_file(test_file, password)
        print(f"✓ File encrypted: {encrypted_file}")
        print(f"Encrypted size: {os.path.getsize(encrypted_file)} bytes")
        
        # Verify it's detected as encrypted
        is_encrypted = encryption.is_encrypted_file(encrypted_file)
        print(f"✓ Detected as encrypted: {is_encrypted}")
        
        # Decrypt the file
        decrypted_file = encrypted_file.replace('.enc', '_decrypted.txt')
        encryption.decrypt_file(encrypted_file, password, decrypted_file)
        print(f"✓ File decrypted: {decrypted_file}")
        
        # Verify content matches
        with open(decrypted_file, 'r') as f:
            decrypted_content = f.read()
        
        if decrypted_content == test_content:
            print("✓ Content verification: PASSED")
        else:
            print("✗ Content verification: FAILED")
        
        # Test wrong password
        try:
            encryption.decrypt_file(encrypted_file, "wrong_password")
            print("✗ Wrong password test: FAILED (should have raised error)")
        except ValueError:
            print("✓ Wrong password test: PASSED (correctly rejected)")
        
    finally:
        # Clean up files
        for f in [test_file, encrypted_file, decrypted_file]:
            if os.path.exists(f):
                os.unlink(f)
        print("✓ Cleanup completed")


def demo_sensitive_data_detection():
    """Demonstrate sensitive data detection and redaction."""
    print("\n" + "=" * 60)
    print("SENSITIVE DATA DETECTION DEMO")
    print("=" * 60)
    
    detector = SensitiveDataDetector()
    
    # Test content with various sensitive data types
    test_content = """
    Hi there! Here's my contact information:
    
    Email: john.doe@company.com
    Phone: (555) 123-4567
    API Key: sk-abcdef1234567890abcdef1234567890
    AWS Access Key: AKIAIOSFODNN7EXAMPLE
    Credit Card: 4532-1234-5678-9012
    SSN: 123-45-6789
    Home: /Users/johndoe/Documents/secret.txt
    Database URL: postgresql://user:pass@db.example.com:5432/mydb
    """
    
    print("Analyzing content for sensitive data...")
    detections = detector.detect_sensitive_data(test_content)
    
    print(f"✓ Found {len(detections)} sensitive items:")
    for detection in detections:
        print(f"  - {detection['type'].upper()}: {detection['value']}")
        print(f"    Context: ...{detection['context'][:50]}...")
    
    # Demonstrate redaction
    print("\nDemonstrating automatic redaction:")
    redacted_content = detector.redact_sensitive_data(test_content)
    print("Redacted content:")
    print("-" * 40)
    print(redacted_content)
    print("-" * 40)
    
    # Test has_sensitive_data
    print(f"\nOriginal content has sensitive data: {detector.has_sensitive_data(test_content)}")
    print(f"Redacted content has sensitive data: {detector.has_sensitive_data(redacted_content)}")


def demo_secure_deletion():
    """Demonstrate secure file deletion."""
    print("\n" + "=" * 60)
    print("SECURE DELETION DEMO")
    print("=" * 60)
    
    deleter = SecureFileDeleter(passes=2)  # Use 2 passes for demo speed
    
    # Create test files
    test_files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=f'_test{i}.txt') as f:
            f.write(f"Sensitive data file {i}: password123, api_key_secret")
            test_files.append(f.name)
    
    print(f"Created {len(test_files)} test files:")
    for f in test_files:
        print(f"  - {f} ({os.path.getsize(f)} bytes)")
    
    # Demonstrate secure deletion
    for i, test_file in enumerate(test_files):
        print(f"\nSecurely deleting file {i+1}...")
        
        if i == 0:
            # Basic secure delete
            success = deleter.secure_delete(test_file)
            print(f"✓ Basic secure delete: {'SUCCESS' if success else 'FAILED'}")
        elif i == 1:
            # Secure delete with verification
            success = deleter.secure_delete_with_verification(test_file)
            print(f"✓ Secure delete with verification: {'SUCCESS' if success else 'FAILED'}")
        else:
            # Manual verification
            success = deleter.secure_delete(test_file)
            exists_after = os.path.exists(test_file)
            print(f"✓ Secure delete: {'SUCCESS' if success else 'FAILED'}")
            print(f"✓ File exists after deletion: {exists_after}")
    
    print("\n✓ Secure deletion demo completed")


def demo_network_monitoring():
    """Demonstrate network activity monitoring."""
    print("\n" + "=" * 60)
    print("NETWORK MONITORING DEMO")
    print("=" * 60)
    
    monitor = NetworkActivityMonitor()
    
    print("Starting network monitoring...")
    monitor.start_monitoring()
    
    # Simulate some network activity
    import socket
    print("Creating socket (should be detected)...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.close()
    except:
        pass
    
    print("Attempting DNS resolution (should be detected)...")
    try:
        socket.getaddrinfo('example.com', 80)
    except:
        pass
    
    monitor.stop_monitoring()
    
    # Check results
    calls = monitor.get_network_calls()
    print(f"✓ Network calls detected: {len(calls)}")
    
    for call in calls:
        print(f"  - {call['type']}: {call.get('args', '')}")
    
    # Demonstrate context manager with strict mode
    print("\nTesting strict mode (should raise exception)...")
    try:
        with monitor.monitor_context(strict=True):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.close()
        print("✗ Strict mode test: FAILED (should have raised exception)")
    except Exception as e:
        print(f"✓ Strict mode test: PASSED (correctly raised: {type(e).__name__})")


def demo_security_manager():
    """Demonstrate the integrated security manager."""
    print("\n" + "=" * 60)
    print("SECURITY MANAGER DEMO")
    print("=" * 60)
    
    # Create security manager with monitoring disabled for demo
    manager = SecurityManager(
        enable_network_monitoring=False,
        enable_interactive_redaction=False
    )
    
    print("Security Manager initialized with settings:")
    summary = manager.get_security_summary()
    for key, value in summary.items():
        print(f"  - {key}: {value}")
    
    # Test content processing
    test_content = """
    Project Notes:
    - Database connection: postgresql://user:secret@localhost/mydb
    - Admin email: admin@mycompany.com
    - API endpoint: https://api.myservice.com/v1
    - Debug key: sk-1234567890abcdef1234567890abcdef
    """
    
    print(f"\nProcessing content ({len(test_content)} characters)...")
    
    with manager:
        result = manager.process_with_security(
            test_content,
            context="Project configuration notes",
            encrypt_output=False
        )
    
    print("Processing results:")
    print(f"  - Sensitive data detected: {result['sensitive_data_detected']}")
    print(f"  - Redaction applied: {result['redaction_applied']}")
    print(f"  - Content encrypted: {result['encrypted']}")
    print(f"  - Network violations: {len(result['network_violations'])}")
    
    if result['sensitive_data_detected']:
        print("  - Sensitive data was found but not redacted (interactive mode disabled)")


def main():
    """Run all security feature demos."""
    print("LLM Context Exporter - Security Features Demo")
    print("This demo showcases the privacy and security capabilities")
    print("of the LLM Context Exporter.\n")
    
    try:
        demo_encryption()
        demo_sensitive_data_detection()
        demo_secure_deletion()
        demo_network_monitoring()
        demo_security_manager()
        
        print("\n" + "=" * 60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nKey Security Features Demonstrated:")
        print("✓ AES-256-GCM file encryption with PBKDF2 key derivation")
        print("✓ Comprehensive sensitive data detection (15+ patterns)")
        print("✓ Multi-pass secure file deletion with verification")
        print("✓ Network activity monitoring for local-only processing")
        print("✓ Integrated security management with context managers")
        print("\nThese features ensure your ChatGPT export data remains")
        print("private and secure throughout the entire processing pipeline.")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()