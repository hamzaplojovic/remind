#!/usr/bin/env python3
"""
Test script for Groq AI integration.
Input a reminder text, get AI suggestion back.

Usage:
    python infrastructure/scripts/test_ai.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps/backend/src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages/shared/src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages/database/src"))


async def main():
    """Test Groq AI with user input."""
    from remind_backend.app.ai import suggest_reminder
    from remind_backend.core.config import get_settings

    settings = get_settings()

    # Check if API key is set
    if not settings.groq_api_key:
        print("❌ Error: GROQ_API_KEY not set in .env")
        print("   Add your Groq API key to .env:")
        print("   GROQ_API_KEY=gsk_your_key_here")
        sys.exit(1)

    print("=" * 70)
    print("Groq AI Test - Remind Reminder Suggestion")
    print("=" * 70)
    print(f"Model: {settings.ai_model}")
    print(f"API Key: {settings.groq_api_key[:20]}...")
    print()

    # Get user input
    print("Enter a reminder text (or 'quit' to exit):")
    reminder_text = input("> ").strip()

    if reminder_text.lower() == "quit":
        print("Exiting...")
        sys.exit(0)

    if not reminder_text:
        print("❌ Error: Please enter a reminder text")
        sys.exit(1)

    print()
    print("Processing with Groq AI...")
    print("-" * 70)

    try:
        response = await suggest_reminder(reminder_text)

        print("✓ Response received!")
        print()
        print(f"Original:  {reminder_text}")
        print(f"Suggested: {response['suggested_text']}")
        print(f"Priority:  {response['priority'].value}")
        print(f"Due Time:  {response['due_time_suggestion'] or '(not specified)'}")
        print()
        print(f"Tokens - Input: {response['input_tokens']}, Output: {response['output_tokens']}")
        print(f"Cost: {response['cost_cents']}¢")
        print()
        print("=" * 70)
        print("✓ AI test successful!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
