"""Quick test script that won't interfere with running server"""
import requests
import json

# Test the analyze endpoint
url = "http://localhost:8000/analyze"
payload = {
    "session_id": "test-verify",
    "messages": [
        {
            "id": 1,
            "speaker": "user",
            "text": "I am so excited and happy!",
            "ts": "2025-11-22T10:00:00Z"
        }
    ],
    "smoothing_window": 3
}

try:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    print("\n✅ BACKEND TEST SUCCESSFUL!")
    print(f"Detected emotion: {data['messages'][0]['dominant']}")
    print(f"Confidence: {data['messages'][0]['confidence']}")
    print(f"\nEmotion probabilities:")
    probs = data['messages'][0]['probs']
    for emotion, prob in sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]:
        if prob > 0:
            print(f"  {emotion}: {prob*100:.1f}%")
    
    if data['messages'][0]['dominant'] != 'neutral':
        print("\n🎉 Emotion detection is working correctly!")
    else:
        print("\n⚠️ Still returning neutral - check backend logs")
        
except requests.exceptions.ConnectionError:
    print("\n❌ Cannot connect to backend at http://localhost:8000")
    print("Make sure the backend server is running")
except Exception as e:
    print(f"\n❌ Test failed: {e}")
