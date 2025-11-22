"""Validate emotion classifier fixes"""
import sys
sys.path.insert(0, "c:\\Users\\Aaryan\\Desktop\\kmec hack\\backend")

from model_adapter import classify_emotion

# Test cases from UI screenshot
test_cases = [
    ("idiot", "disgust", "Should detect insult as disgust/anger, NOT joy"),
    ("i am very low", "sadness", "Should detect sadness, NOT anticipation"),
    ("i dislike the internet issues today", "anger", "Should detect anger/frustration, NOT anticipation"),
    ("i am really excited about todays hackathon", "joy", "Should detect joy correctly"),
]

print("=" * 80)
print("EMOTION CLASSIFIER VALIDATION")
print("=" * 80)

passed = 0
failed = 0

for text, expected, reason in test_cases:
    probs = classify_emotion(text)
    dominant = max(probs, key=probs.get)
    confidence = probs[dominant]
    
    # Check if secondary emotion >= 0.35 and higher than primary
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    secondary = sorted_probs[1] if len(sorted_probs) > 1 else (None, 0)
    
    is_correct = dominant == expected
    status = "✅ PASS" if is_correct else "❌ FAIL"
    
    print(f"\n{status} | Text: '{text}'")
    print(f"      | Expected: {expected}")
    print(f"      | Got: {dominant} ({confidence:.2%})")
    
    if secondary[1] >= 0.35 and secondary[1] > confidence:
        print(f"      | ⚠️  Secondary emotion {secondary[0]} ({secondary[1]:.2%}) is higher!")
    
    print(f"      | Top 3: {', '.join([f'{e}: {p:.1%}' for e, p in sorted_probs[:3]])}")
    print(f"      | Reason: {reason}")
    
    if is_correct:
        passed += 1
    else:
        failed += 1

print("\n" + "=" * 80)
print(f"RESULTS: {passed}/{len(test_cases)} passed, {failed} failed")

if failed == 0:
    print("🎉 All tests passed! Emotion classifier is working correctly.")
else:
    print(f"⚠️  {failed} test(s) failed. Review the classifier logic.")

print("=" * 80)
