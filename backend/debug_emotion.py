"""Direct test of model_adapter with full debug output"""
import sys
sys.path.insert(0, '.')

# Force reload env
from dotenv import load_dotenv
load_dotenv()

import os
print(f"API Key from env: {os.getenv('GROQ_API_KEY')[:30]}...")

from model_adapter import classify_emotion

message = "I am so excited and happy today!"
print(f"\nTesting: {message}")
print("="*60)

result = classify_emotion(message)
print(f"\nResult: {result}")
print(f"Dominant: {max(result, key=result.get)}")

if result.get('joy', 0) > 0.5:
    print("\n🎉 SUCCESS - Joy detected!")
else:
    print(f"\n⚠️ PROBLEM - Got {max(result, key=result.get)} instead of joy")
