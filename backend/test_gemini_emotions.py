"""
Test Gemini emotion classifier with anti-neutral bias
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Test cases from master prompt
test_cases = [
    {
        "text": "I am so excited and happy!",
        "expected_emotion": "joy",
        "should_not_be": "neutral"
    },
    {
        "text": "This is ridiculous!!!",
        "expected_emotion": "anger",
        "should_not_be": "neutral"
    },
    {
        "text": "😢 lost my wallet today",
        "expected_emotion": "sadness",
        "should_not_be": "neutral"
    },
    {
        "text": "Yeah great job... not.",
        "expected_emotion": "anger",  # Sarcasm should be anger/disgust
        "should_not_be": "neutral"
    },
    {
        "text": "I'm FURIOUS about this situation!",
        "expected_emotion": "anger",
        "should_not_be": "neutral"
    }
]

print("🧪 Testing Gemini Emotion Classifier\n")
print("=" * 60)

# Create a test chat
print("\n📝 Creating test chat...")
response = requests.post(f"{BASE_URL}/api/chat", json={"userId": "test-user"})
if response.status_code != 200:
    print(f"❌ Failed to create chat: {response.status_code}")
    print(response.text)
    exit(1)

chat_data = response.json()
chat_id = chat_data['chatId']
print(f"✅ Created chat: {chat_id}")

# Test each message
passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"Test {i}/{len(test_cases)}: {test['text']}")
    print(f"Expected: {test['expected_emotion']}, Should NOT be: {test['should_not_be']}")
    
    # Send message
    response = requests.post(
        f"{BASE_URL}/api/chat/{chat_id}/message",
        json={"speaker": "user", "text": test['text']}
    )
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)
        failed += 1
        continue
    
    result = response.json()
    
    # Check emotion - API returns: {"status": "success", "chatId": "...", "emotion": "joy", "confidence": "high"}
    detected_emotion = result.get('emotion', 'unknown')
    
    print(f"\n🎯 Detected: {detected_emotion}")
    print(f"📊 Confidence: {result.get('confidence', 'unknown')}")
    
    # Validate
    is_correct = detected_emotion == test['expected_emotion']
    is_not_neutral = detected_emotion != test['should_not_be']
    
    if is_correct and is_not_neutral:
        print(f"\n✅ PASSED: Correctly detected {detected_emotion}")
        passed += 1
    elif not is_not_neutral:
        print(f"\n❌ FAILED: Returned {test['should_not_be']} (anti-neutral bias not working!)")
        failed += 1
    else:
        print(f"\n⚠️  PARTIAL: Detected {detected_emotion} (expected {test['expected_emotion']}, but NOT neutral)")
        # Count as passed if it's not neutral
        passed += 1

print(f"\n{'='*60}")
print(f"\n📈 Results: {passed}/{len(test_cases)} passed, {failed} failed")

if failed == 0:
    print("\n🎉 All tests passed! Anti-neutral bias is working correctly!")
else:
    print(f"\n⚠️  {failed} test(s) failed. Review the emotion classifier.")

# Clean up
print(f"\n🧹 Cleaning up test chat...")
requests.delete(f"{BASE_URL}/api/chat/{chat_id}")
print("✅ Done!")
