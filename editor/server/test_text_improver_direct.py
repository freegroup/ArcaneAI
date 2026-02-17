#!/usr/bin/env python3
"""
Direct test of TextImprover class without server
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from text_improver import TextImprover

def test_text_improver():
    """Test TextImprover directly."""
    
    print("=" * 80)
    print("TEXT IMPROVER DIRECT TEST")
    print("=" * 80)
    print()
    
    # Initialize TextImprover
    print("Initializing TextImprover...")
    improver = TextImprover()
    print("✓ TextImprover initialized\n")
    
    # Test cases
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
            "include_comment": False
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{'=' * 80}")
        print(f"TEST CASE {i}: {test_case['name']}")
        print(f"{'=' * 80}")
        print(f"\nOriginal Text:\n{test_case['text']}")
        print(f"\nInstruction: {test_case['instruction']}")
        print(f"Include Comment: {test_case['include_comment']}")
        
        try:
            result = improver.improve_text(
                text=test_case['text'],
                user_instruction=test_case['instruction'],
                include_comment=test_case['include_comment']
            )
            
            print(f"\n✓ SUCCESS")
            print(f"\nImproved Text:\n{result['improved_text']}")
            print(f"\nModel: {result['model']}")
            
            if 'comment' in result:
                print(f"\nComment:\n{result['comment']}")
                
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print(f"{'=' * 80}")
    print("TEST COMPLETED")
    print(f"{'=' * 80}\n")

if __name__ == "__main__":
    test_text_improver()