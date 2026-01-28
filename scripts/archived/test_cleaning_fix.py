#!/usr/bin/env python3
"""
🧪 Test de la función corregida clean_thinking_tags
"""

from clean_thinking_fix import clean_thinking_tags

def test_cleaning_function():
    """Test varios casos de thinking tags"""

    test_cases = [
        {
            "name": "Deepseek-R1 normal case",
            "input": "🤔Hmm...let me think about this question.🤔The activity consists of volunteers distributing food to homeless people in Valencia.",
            "expected": "The activity consists of volunteers distributing food to homeless people in Valencia."
        },
        {
            "name": "Deepseek-R1 truncated case",
            "input": "🤔Hmm...let me think about this...🤔",
            "expected": "[Error: Respuesta eliminada por limpieza de tags thinking]"
        },
        {
            "name": "Qwen3 with thinking at start",
            "input": "Let me analyze this carefully. Based on the context provided, the meeting point is Porta de la Mar in Valencia.",
            "expected": "Based on the context provided, the meeting point is Porta de la Mar in Valencia."
        },
        {
            "name": "Normal answer without thinking",
            "input": "The activity takes place on Saturdays at 8:00 AM at Porta de la Mar in Valencia.",
            "expected": "The activity takes place on Saturdays at 8:00 AM at Porta de la Mar in Valencia."
        },
        {
            "name": "Mixed content with thinking tags",
            "input": "The meeting point is at Porta de Mar <thinking>let me verify this</thinking> and volunteers gather there before distributing food.",
            "expected": "The meeting point is at Porta de Mar  and volunteers gather there before distributing food."
        },
        {
            "name": "Multiple thinking patterns",
            "input": "🤔I need to think about this...🤔 Let me check the information. 🤔After analyzing...🤔The activity involves volunteers helping homeless people.",
            "expected": "I need to think about this... Let me check the information. After analyzing...The activity involves volunteers helping homeless people."
        }
    ]

    print("🧪 Test de función clean_thinking_tags corregida")
    print("=" * 60)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input'][:100]}...")

        result = clean_thinking_tags(test_case['input'])
        print(f"Result: {result[:100]}...")
        print(f"Expected: {test_case['expected'][:100]}...")

        # Simple check
        if result == test_case['expected']:
            print("✅ PASS")
        else:
            print("❌ FAIL")

            # Check if at least it's not empty
            if len(result) > 20 and result != "[Error: Respuesta eliminada por limpieza de tags thinking]":
                print("⚠️ Different but acceptable (not empty)")

if __name__ == "__main__":
    test_cleaning_function()