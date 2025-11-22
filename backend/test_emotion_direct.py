"""Test emotion classification directly"""
from model_adapter import classify_emotion

# Test with a happy message
message = "I am so excited and happy today!"
print(f"Testing message: {message}")
print("="*50)

result = classify_emotion(message)
print(f"\nResult: {result}")
print(f"Dominant: {max(result, key=result.get)}")
