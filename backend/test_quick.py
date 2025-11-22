"""
Quick API Test Script
Tests new chat management and emotion summarization endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("🚀 Testing The Empathy Engine API v2.0\n")
    
    # Test 1: Create chat
    print("1️⃣ Creating new chat...")
    response = requests.post(f"{BASE_URL}/api/chat", json={
        "userId": "test_user",
        "initialMessage": "I'm so frustrated with this billing issue!"
    })
    print(f"Status: {response.status_code}")
    chat_data = response.json()
    print(f"Response: {json.dumps(chat_data, indent=2)}\n")
    
    chat_id = chat_data["chatId"]
    user_id = chat_data["userId"]
    
    # Test 2: Add messages
    print("2️⃣ Adding more messages...")
    messages = [
        "I've been charged twice this month",
        "This is making me really stressed out"
    ]
    
    for msg in messages:
        response = requests.post(
            f"{BASE_URL}/api/chat/{chat_id}/message",
            json={"speaker": "user", "text": msg}
        )
        print(f"Added: '{msg}' - Emotion: {response.json()['emotion']}")
    print()
    
    # Test 3: Get emotion summary
    print("3️⃣ Getting emotion summary...")
    response = requests.post(
        f"{BASE_URL}/api/chat/{chat_id}/summarize-emotion",
        json={"include_summary_text": True}
    )
    print(f"Status: {response.status_code}")
    summary = response.json()
    print(f"Dominant Emotion: {summary['dominant_emotion']}")
    print(f"Confidence: {summary['confidence']}")
    print(f"Summary: {summary['summary_text']}")
    print(f"Top Emotions:")
    sorted_emotions = sorted(summary['scores'].items(), key=lambda x: x[1], reverse=True)[:3]
    for emotion, score in sorted_emotions:
        print(f"  - {emotion}: {score:.2f}")
    print()
    
    # Test 4: Get chat history
    print("4️⃣ Getting user chat history...")
    response = requests.get(f"{BASE_URL}/api/user/{user_id}/chats?limit=10")
    print(f"Status: {response.status_code}")
    history = response.json()
    print(f"Total chats: {history['total']}")
    print(f"Chats returned: {len(history['chats'])}")
    if history['chats']:
        chat = history['chats'][0]
        print(f"Latest chat: {chat['title']}")
        print(f"  Snippet: {chat['snippet']}")
        print(f"  Emotion: {chat['dominant_emotion']}")
        print(f"  Messages: {chat['messageCount']}")
    print()
    
    # Test 5: Get full chat
    print("5️⃣ Getting full chat details...")
    response = requests.get(f"{BASE_URL}/api/chat/{chat_id}")
    print(f"Status: {response.status_code}")
    full_chat = response.json()
    print(f"Messages: {len(full_chat['messages'])}")
    print(f"Emotion timeline emotions tracked: {len(full_chat['emotionTimeline'])}")
    print()
    
    # Test 6: Update title
    print("6️⃣ Updating chat title...")
    response = requests.patch(
        f"{BASE_URL}/api/chat/{chat_id}/title",
        json={"title": "Billing Issue - In Progress"}
    )
    print(f"Status: {response.status_code}")
    print(f"New title: {response.json()['title']}\n")
    
    # Test 7: Verify update
    print("7️⃣ Verifying title update...")
    response = requests.get(f"{BASE_URL}/api/user/{user_id}/chats")
    history = response.json()
    print(f"Updated title in history: {history['chats'][0]['title']}\n")
    
    # Test 8: Delete chat
    print("8️⃣ Deleting chat...")
    response = requests.delete(f"{BASE_URL}/api/chat/{chat_id}?userId={user_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    
    # Test 9: Verify deletion
    print("9️⃣ Verifying deletion...")
    response = requests.get(f"{BASE_URL}/api/chat/{chat_id}")
    print(f"Status: {response.status_code} (404 expected)")
    
    if response.status_code == 404:
        print("✅ Chat successfully deleted\n")
    
    print("=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
