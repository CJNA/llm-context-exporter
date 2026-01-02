"""
User prompting for sensitive data redaction.

This module provides interactive prompting to get user approval
for redacting sensitive information.
"""

import sys
from typing import List, Dict, Any, Optional, Tuple
from .detection import SensitiveDataDetector


class RedactionPrompter:
    """
    Handles user interaction for sensitive data redaction approval.
    
    Presents detected sensitive data to the user and gets approval
    for redaction before processing continues.
    """
    
    def __init__(self, detector: Optional[SensitiveDataDetector] = None):
        """
        Initialize the redaction prompter.
        
        Args:
            detector: Sensitive data detector instance
        """
        self.detector = detector or SensitiveDataDetector()
    
    def prompt_for_redaction(self, text: str, context: str = "") -> Tuple[str, bool]:
        """
        Prompt user for redaction approval and return processed text.
        
        Args:
            text: Text content to check for sensitive data
            context: Context description for the user (e.g., "conversation from 2023-01-15")
            
        Returns:
            Tuple of (processed_text, user_approved_redaction)
        """
        detections = self.detector.detect_sensitive_data(text)
        
        if not detections:
            return text, False
        
        print(f"\n{'='*60}")
        print("SENSITIVE DATA DETECTED")
        print(f"{'='*60}")
        
        if context:
            print(f"Context: {context}")
            print()
        
        print(f"Found {len(detections)} potentially sensitive item(s):")
        print()
        
        # Group detections by type
        by_type = {}
        for detection in detections:
            data_type = detection['type']
            if data_type not in by_type:
                by_type[data_type] = []
            by_type[data_type].append(detection)
        
        # Display grouped detections
        for data_type, items in by_type.items():
            print(f"  {data_type.upper()} ({len(items)} found):")
            for i, item in enumerate(items[:3]):  # Show max 3 examples
                print(f"    {i+1}. {item['value']}")
                print(f"       Context: ...{item['context']}...")
            
            if len(items) > 3:
                print(f"    ... and {len(items) - 3} more")
            print()
        
        # Get user choice
        while True:
            print("What would you like to do?")
            print("  1. Redact all sensitive data (recommended)")
            print("  2. Keep sensitive data (not recommended)")
            print("  3. Review each item individually")
            print("  4. Skip this content entirely")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                redacted_text = self.detector.redact_sensitive_data(text)
                print("\n✓ All sensitive data has been redacted.")
                return redacted_text, True
            
            elif choice == '2':
                print("\n⚠ WARNING: Sensitive data will be included in the export.")
                confirm = input("Are you sure? (yes/no): ").strip().lower()
                if confirm in ['yes', 'y']:
                    return text, False
                # Continue loop if not confirmed
            
            elif choice == '3':
                return self._interactive_redaction(text, detections)
            
            elif choice == '4':
                print("\n✓ Content will be skipped.")
                return "", True
            
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
    
    def _interactive_redaction(self, text: str, detections: List[Dict[str, Any]]) -> Tuple[str, bool]:
        """
        Handle interactive redaction of individual items.
        
        Args:
            text: Original text
            detections: List of detected sensitive items
            
        Returns:
            Tuple of (processed_text, any_redacted)
        """
        print(f"\n{'='*60}")
        print("INTERACTIVE REDACTION")
        print(f"{'='*60}")
        
        redacted_text = text
        any_redacted = False
        
        # Sort detections by position (reverse order to maintain positions)
        detections.sort(key=lambda x: x['start'], reverse=True)
        
        for i, detection in enumerate(detections):
            print(f"\nItem {len(detections) - i} of {len(detections)}:")
            print(f"Type: {detection['type'].upper()}")
            print(f"Value: {detection['value']}")
            print(f"Context: ...{detection['context']}...")
            
            while True:
                choice = input("Redact this item? (y/n/skip): ").strip().lower()
                
                if choice in ['y', 'yes']:
                    # Redact this specific item
                    start, end = detection['start'], detection['end']
                    redacted_text = (
                        redacted_text[:start] + 
                        "[REDACTED]" + 
                        redacted_text[end:]
                    )
                    any_redacted = True
                    print("✓ Item redacted.")
                    break
                
                elif choice in ['n', 'no']:
                    print("✓ Item kept.")
                    break
                
                elif choice == 'skip':
                    print("✓ Remaining items kept.")
                    return redacted_text, any_redacted
                
                else:
                    print("Please enter 'y' for yes, 'n' for no, or 'skip' to keep remaining items.")
        
        print(f"\n✓ Interactive redaction complete. {sum(1 for d in detections if '[REDACTED]' in redacted_text)} items redacted.")
        return redacted_text, any_redacted
    
    def batch_prompt_for_redaction(self, content_items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Prompt for redaction across multiple content items.
        
        Args:
            content_items: List of dicts with 'text' and 'context' keys
            
        Returns:
            List of processed items with redaction info
        """
        results = []
        
        print(f"\n{'='*60}")
        print("BATCH SENSITIVE DATA REVIEW")
        print(f"{'='*60}")
        print(f"Checking {len(content_items)} items for sensitive data...")
        
        # First pass: detect all sensitive data
        items_with_detections = []
        total_detections = 0
        
        for item in content_items:
            detections = self.detector.detect_sensitive_data(item['text'])
            if detections:
                items_with_detections.append({
                    'item': item,
                    'detections': detections
                })
                total_detections += len(detections)
        
        if not items_with_detections:
            print("✓ No sensitive data detected in any items.")
            return [{'text': item['text'], 'context': item['context'], 'redacted': False} 
                   for item in content_items]
        
        print(f"\nFound sensitive data in {len(items_with_detections)} of {len(content_items)} items.")
        print(f"Total sensitive items detected: {total_detections}")
        
        # Get global choice
        while True:
            print("\nBatch processing options:")
            print("  1. Redact all sensitive data (recommended)")
            print("  2. Keep all sensitive data (not recommended)")
            print("  3. Review each item individually")
            print("  4. Skip all items with sensitive data")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                # Redact all
                for item in content_items:
                    redacted_text = self.detector.redact_sensitive_data(item['text'])
                    results.append({
                        'text': redacted_text,
                        'context': item['context'],
                        'redacted': redacted_text != item['text']
                    })
                print(f"\n✓ All sensitive data redacted in {len(items_with_detections)} items.")
                return results
            
            elif choice == '2':
                # Keep all
                print("\n⚠ WARNING: All sensitive data will be included in the export.")
                confirm = input("Are you sure? (yes/no): ").strip().lower()
                if confirm in ['yes', 'y']:
                    return [{'text': item['text'], 'context': item['context'], 'redacted': False} 
                           for item in content_items]
                # Continue loop if not confirmed
            
            elif choice == '3':
                # Individual review
                return self._batch_interactive_redaction(content_items, items_with_detections)
            
            elif choice == '4':
                # Skip items with sensitive data
                print(f"\n✓ Skipping {len(items_with_detections)} items with sensitive data.")
                for item in content_items:
                    has_sensitive = any(
                        self.detector.has_sensitive_data(item['text']) 
                        for sensitive_item in items_with_detections 
                        if sensitive_item['item'] == item
                    )
                    results.append({
                        'text': "" if has_sensitive else item['text'],
                        'context': item['context'],
                        'redacted': has_sensitive
                    })
                return results
            
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
    
    def _batch_interactive_redaction(self, content_items: List[Dict[str, str]], 
                                   items_with_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle batch interactive redaction."""
        results = []
        
        print(f"\n{'='*60}")
        print("BATCH INTERACTIVE REDACTION")
        print(f"{'='*60}")
        
        # Create lookup for items with detections
        sensitive_lookup = {id(item['item']): item for item in items_with_detections}
        
        for item in content_items:
            if id(item) in sensitive_lookup:
                print(f"\nProcessing item: {item['context']}")
                processed_text, redacted = self.prompt_for_redaction(item['text'], item['context'])
                results.append({
                    'text': processed_text,
                    'context': item['context'],
                    'redacted': redacted
                })
            else:
                results.append({
                    'text': item['text'],
                    'context': item['context'],
                    'redacted': False
                })
        
        return results


def prompt_for_redaction_approval(text: str, context: str = "") -> Tuple[str, bool]:
    """
    Convenience function for prompting redaction approval.
    
    Args:
        text: Text to check for sensitive data
        context: Context description
        
    Returns:
        Tuple of (processed_text, was_redacted)
    """
    prompter = RedactionPrompter()
    return prompter.prompt_for_redaction(text, context)