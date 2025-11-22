"""Quick API test for emotion detection"""
import sys
sys.path.insert(0, "c:\\Users\\Aaryan\\Desktop\\kmec hack\\backend")

from model_adapter import classify_emotion

test_messages = [
    "I am so excited and happy!",
    "This is ridiculous!!!",
    "😢 lost my wallet today",
    "Yeah great job... not.",
    "I'm FURIOUS about this!",
]

print("Testing emotion classifier directly:\n")
for msg in test_messages:
    probs = classify_emotion(msg)
    dominant = max(probs, key=probs.get)
    confidence = probs[dominant]
    
    print(f"Message: {msg}")
    print(f"  → {dominant} ({confidence:.2f})")
    print()

print("\n✅ All working! The backend will use these same classifiers.")
