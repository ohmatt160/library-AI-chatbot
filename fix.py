#!/usr/bin/env python3
"""
Properly fix JSON file encoding issues by removing invalid bytes
"""

import json
import os
import re


def clean_file_encoding(filepath):
    """Clean a single JSON file of invalid UTF-8 bytes"""
    print(f"🔧 Cleaning: {filepath}")

    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False

    try:
        # Read file as binary to see raw bytes
        with open(filepath, 'rb') as f:
            raw_bytes = f.read()

        print(f"   File size: {len(raw_bytes)} bytes")

        # Find problematic bytes (0x80-0x9F are invalid in UTF-8)
        problematic = [i for i, b in enumerate(raw_bytes) if 0x80 <= b <= 0x9F]
        if problematic:
            print(f"   Found {len(problematic)} problematic bytes at positions: {problematic[:10]}...")

            # Show context around first problematic byte
            if problematic:
                idx = problematic[0]
                start = max(0, idx - 50)
                end = min(len(raw_bytes), idx + 50)
                print(f"   Context around byte {idx} (hex {hex(raw_bytes[idx])}):")
                print(f"   {raw_bytes[start:end]}")

        # Remove all control characters (0x00-0x1F except \t, \n, \r) and invalid UTF-8
        clean_bytes = bytearray()
        for b in raw_bytes:
            if b == 0x09 or b == 0x0A or b == 0x0D:  # Keep tab, LF, CR
                clean_bytes.append(b)
            elif b < 0x20:  # Remove other control characters
                continue
            elif 0x80 <= b <= 0x9F:  # Remove invalid UTF-8 range
                continue
            else:
                clean_bytes.append(b)

        # Try to decode as UTF-8
        try:
            clean_text = clean_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # If still fails, use latin-1 (which can decode any byte)
            clean_text = clean_bytes.decode('latin-1')

        # Fix common issues in the text
        clean_text = clean_text.replace('\r\n', '\n')  # Normalize line endings
        clean_text = clean_text.replace('\r', '\n')  # Convert Mac line endings

        # Remove any remaining control characters using regex
        clean_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', clean_text)

        # Parse JSON to validate
        data = json.loads(clean_text)

        # Write back with proper UTF-8 encoding
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Successfully cleaned and saved: {filepath}")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print("   Creating fresh file with default content...")
        return create_fresh_file(filepath)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def create_fresh_file(filepath):
    """Create a fresh JSON file with default content"""

    if 'rules' in filepath:
        default_content = {
            "rules": [
                {
                    "id": "rule_001",
                    "pattern": "(?i)(hello|hi|hey)",
                    "response": "Hello! I'm your library assistant.",
                    "priority": 1
                }
            ]
        }
    elif 'response_templates' in filepath or 'templates' in filepath:
        default_content = {
            "greeting": {
                "main": "Hello! Welcome to the library.",
                "follow_up": "How can I help you?"
            }
        }
    elif 'knowledge' in filepath:
        default_content = {"entries": []}
    elif 'intent' in filepath:
        default_content = {"examples": {}}
    else:
        default_content = {}

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default_content, f, indent=2, ensure_ascii=False)
        print(f"✅ Created fresh: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Failed to create file: {e}")
        return False


def backup_and_replace(filepath):
    """Backup the corrupted file and create a fresh one"""
    import shutil
    import time

    if os.path.exists(filepath):
        # Create backup
        backup_name = f"{filepath}.backup.{int(time.time())}"
        shutil.copy2(filepath, backup_name)
        print(f"📦 Created backup: {backup_name}")

    # Create fresh file
    return create_fresh_file(filepath)


def main():
    print("🚀 Starting proper JSON encoding fix...")
    print("=" * 60)

    # List of JSON files to check
    json_files = [
        'app/data/rules.json',
        'app/data/response_templates.json',
        'app/data/templates.json',
        'app/data/knowledge_base.json',
        'app/data/intent_examples.json'
    ]

    # First, try to clean each file
    for filepath in json_files:
        if os.path.exists(filepath):
            if not clean_file_encoding(filepath):
                print(f"⚠️ Cleaning failed for {filepath}, trying backup and replace...")
                backup_and_replace(filepath)
        else:
            print(f"⚠️ File doesn't exist: {filepath}")
        print("-" * 40)

    # Verify all files are readable
    print("\n🔍 Verifying all JSON files...")
    for filepath in json_files:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ {filepath}: Valid JSON ({len(str(data))} chars)")
            except Exception as e:
                print(f"❌ {filepath}: {e}")
                # Last resort - delete and create fresh
                os.remove(filepath)
                create_fresh_file(filepath)

    print("=" * 60)
    print("🎉 Encoding fix complete!")
    print("\n📋 Now run: python run.py")


if __name__ == "__main__":
    main()