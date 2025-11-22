"""
Simple test to verify API endpoints work without external dependencies
"""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_URL = "http://localhost:8000"

def test_create_chat():
    """Test POST /api/chat"""
    data = json.dumps({"userId": "testuser", "title": "Test Chat"}).encode('utf-8')
    req = Request(f"{BASE_URL}/api/chat", data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Created chat: {result['chatId']}")
            return result['chatId']
    except HTTPError as e:
        print(f"❌ Create chat failed: {e}")
        return None

def test_get_user_chats(user_id, chat_id):
    """Test GET /api/user/{userId}/chats"""
    try:
        with urlopen(f"{BASE_URL}/api/user/{user_id}/chats") as response:
            result = json.loads(response.read().decode('utf-8'))
            found = any(chat['chatId'] == chat_id for chat in result['chats'])
            if found:
                print(f"✅ Found chat in user history")
            else:
                print(f"❌ Chat not found in history")
    except HTTPError as e:
        print(f"❌ Get user chats failed: {e}")

def test_add_message(chat_id):
    """Test POST /api/chat/{chatId}/message"""
    data = json.dumps({
        "speaker": "user",
        "text": "I am feeling really stressed and anxious today!"
    }).encode('utf-8')
    req = Request(f"{BASE_URL}/api/chat/{chat_id}/message", data=data, 
                  headers={'Content-Type': 'application/json'})
    
    try:
        with urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Added message {result['messageId']} to chat")
            return True
    except HTTPError as e:
        print(f"❌ Add message failed: {e}")
        error_body = e.read().decode('utf-8')
        print(f"   Error details: {error_body}")
        return False

def test_summarize_emotions(chat_id):
    """Test POST /api/chat/{chatId}/summarize-emotion"""
    data = json.dumps({}).encode('utf-8')
    req = Request(f"{BASE_URL}/api/chat/{chat_id}/summarize-emotion", data=data,
                  headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Emotion summary - Dominant: {result['dominant_emotion']}, Confidence: {result['confidence']:.2f}")
            if result.get('summary_text'):
                print(f"   Summary: {result['summary_text']}")
    except HTTPError as e:
        print(f"❌ Summarize emotions failed: {e}")

def test_health_check():
    """Test GET /"""
    try:
        with urlopen(f"{BASE_URL}/") as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ API responding: {result['service']} ({result['status']})")
            return True
    except Exception as e:
        print(f"❌ API check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing The Empathy Engine API")
    print("=" * 50)
    
    # Test health first
    if not test_health_check():
        print("\n❌ Server not responding. Make sure it's running on http://localhost:8000")
        exit(1)
    
    # Test chat creation
    chat_id = test_create_chat()
    if not chat_id:
        print("\n❌ Failed to create chat")
        exit(1)
    
    # Test other endpoints
    if test_add_message(chat_id):
        test_summarize_emotions(chat_id)
    test_get_user_chats("testuser", chat_id)
    
    print("\n" + "=" * 50)
    print("✅ All basic tests passed!")
    print("\n📚 For more testing:")
    print("   - Open http://localhost:8000/docs for interactive API docs")
    print("   - Import postman_collection.json into Postman")
    print("   - Check INTEGRATION_README.md for TypeScript examples")
