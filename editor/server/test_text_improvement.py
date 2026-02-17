#!/usr/bin/env python3
"""
Test script for the text improvement endpoint
"""
import requests
import json

# Server URL
BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/v1/improve-text"

def test_text_improvement():
    """Test the text improvement endpoint with various scenarios."""
    
    test_cases = [
        {
            "name": "Grammar improvement with Jinja tags",
            "text": "Du gehst in {{ ort }} und siehst einen mann.",
            "instruction": "Verbessere die Grammatik und Rechtschreibung",
            "include_comment": True
        },
        {
            "name": "Translation with Jinja conditional",
            "text": "{% if health > 0 %}Du lebst noch und hast {{ health }} Lebenspunkte.{% endif %}",
            "instruction": "Übersetze ins Englische",
            "include_comment": True
        },
        {
            "name": "Style improvement with multiple Jinja tags",
            "text": "der held {{ name }} geht nach {{ ziel }} um dort {{ aktion }} zu machen.",
            "instruction": "Mache den Text dramatischer und epischer",
            "include_comment": True
        },
        {
            "name": "Simple text without Jinja",
            "text": "das ist ein test text mit fehler",
            "instruction": "Korrigiere Rechtschreibung und Großschreibung",
            "include_comment": False
        }
    ]
    
    print("=" * 80)
    print("TEXT IMPROVEMENT ENDPOINT TEST")
    print("=" * 80)
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST CASE {i}: {test_case['name']}")
        print(f"{'=' * 80}")
        print(f"\nOriginal Text:\n{test_case['text']}")
        print(f"\nInstruction: {test_case['instruction']}")
        print(f"Include Comment: {test_case['include_comment']}")
        
        try:
            response = requests.post(
                ENDPOINT,
                json={
                    "text": test_case['text'],
                    "instruction": test_case['instruction'],
                    "include_comment": test_case['include_comment']
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✓ SUCCESS")
                print(f"\nImproved Text:\n{result['improved_text']}")
                print(f"\nModel: {result['model']}")
                
                if 'comment' in result:
                    print(f"\nComment:\n{result['comment']}")
                
            else:
                print(f"\n✗ ERROR: Status {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"\n✗ ERROR: Could not connect to server at {BASE_URL}")
            print("Make sure the server is running (cd editor/server && python src/main.py)")
            break
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
    
    print(f"\n{'=' * 80}")
    print("TEST COMPLETED")
    print(f"{'=' * 80}\n")

if __name__ == "__main__":
    test_text_improvement()