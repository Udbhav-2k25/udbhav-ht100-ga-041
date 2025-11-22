"""
Unit Tests for The Empathy Engine API
Tests for chat management, emotion summarization, and storage layer
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from storage import ChatStorage
from models import EmotionType

client = TestClient(app)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_storage():
    """Create isolated storage for tests"""
    return ChatStorage(persist_path=None)


@pytest.fixture
def sample_user_id():
    return "test_user_123"


@pytest.fixture
def sample_chat_data(test_storage, sample_user_id):
    """Create a sample chat with messages"""
    chat_id, _ = test_storage.create_chat(
        user_id=sample_user_id,
        initial_message="I'm so frustrated with this!"
    )
    
    # Add emotion data
    test_storage.add_message(
        chat_id=chat_id,
        speaker="user",
        text="I'm so frustrated with this!",
        probs={
            "joy": 0.0,
            "sadness": 0.2,
            "anger": 0.7,
            "fear": 0.05,
            "surprise": 0.0,
            "stress": 0.05,
            "tension": 0.0,
            "disgust": 0.0,
            "anticipation": 0.0,
            "neutral": 0.0
        },
        dominant="anger",
        entropy=0.5,
        confidence="high"
    )
    
    return chat_id, sample_user_id


# ============================================================================
# CHAT CREATION TESTS
# ============================================================================

def test_create_chat_without_message():
    """Test creating empty chat"""
    response = client.post(
        "/api/chat",
        json={"userId": "jdoe"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "chatId" in data
    assert data["userId"] == "jdoe"
    assert "createdAt" in data
    assert data["id"] == data["chatId"]  # Backward compat


def test_create_chat_with_initial_message():
    """Test creating chat with first message"""
    response = client.post(
        "/api/chat",
        json={
            "userId": "jdoe",
            "initialMessage": "I need help with billing"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "chatId" in data
    
    # Verify message was analyzed
    chat = client.get(f"/api/chat/{data['chatId']}")
    assert chat.status_code == 200
    chat_data = chat.json()
    assert len(chat_data["messages"]) == 1
    assert "probs" in chat_data["messages"][0]


# ============================================================================
# CHAT HISTORY TESTS
# ============================================================================

def test_get_user_chats_empty():
    """Test fetching chats for user with no chats"""
    response = client.get("/api/user/new_user/chats")
    
    assert response.status_code == 200
    data = response.json()
    assert data["userId"] == "new_user"
    assert data["chats"] == []
    assert data["total"] == 0
    assert data["nextCursor"] is None


def test_get_user_chats_with_pagination():
    """Test pagination of chat history"""
    user_id = "pagination_user"
    
    # Create 5 chats
    chat_ids = []
    for i in range(5):
        response = client.post(
            "/api/chat",
            json={
                "userId": user_id,
                "initialMessage": f"Message {i}"
            }
        )
        chat_ids.append(response.json()["chatId"])
    
    # Get first page (limit 2)
    response = client.get(f"/api/user/{user_id}/chats?limit=2")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["chats"]) == 2
    assert data["total"] == 5
    assert data["nextCursor"] is not None
    
    # Get second page
    response2 = client.get(
        f"/api/user/{user_id}/chats?limit=2&cursor={data['nextCursor']}"
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["chats"]) == 2


def test_chat_history_item_structure():
    """Test that history items have correct structure"""
    user_id = "structure_test"
    
    # Create chat
    response = client.post(
        "/api/chat",
        json={
            "userId": user_id,
            "initialMessage": "Test message for structure"
        }
    )
    
    # Get history
    history = client.get(f"/api/user/{user_id}/chats")
    data = history.json()
    
    assert len(data["chats"]) == 1
    chat = data["chats"][0]
    
    # Verify all required fields
    required_fields = [
        "chatId", "id", "title", "createdAt", "lastUpdatedAt",
        "snippet", "dominant_emotion", "messageCount"
    ]
    for field in required_fields:
        assert field in chat


# ============================================================================
# MESSAGE TESTS
# ============================================================================

def test_add_message_to_chat():
    """Test adding message to existing chat"""
    # Create chat
    create_response = client.post(
        "/api/chat",
        json={"userId": "msg_test"}
    )
    chat_id = create_response.json()["chatId"]
    
    # Add message
    response = client.post(
        f"/api/chat/{chat_id}/message",
        json={
            "speaker": "user",
            "text": "This is so stressful!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "emotion" in data
    assert "confidence" in data


def test_add_message_to_nonexistent_chat():
    """Test error handling for invalid chat"""
    response = client.post(
        "/api/chat/invalid_id/message",
        json={
            "speaker": "user",
            "text": "Test"
        }
    )
    
    assert response.status_code == 404


# ============================================================================
# EMOTION SUMMARY TESTS
# ============================================================================

def test_emotion_summary_with_text():
    """Test emotion summarization with text generation"""
    # Create chat with messages
    create_response = client.post(
        "/api/chat",
        json={
            "userId": "summary_test",
            "initialMessage": "I'm so angry about this!"
        }
    )
    chat_id = create_response.json()["chatId"]
    
    # Add more messages
    client.post(
        f"/api/chat/{chat_id}/message",
        json={"speaker": "user", "text": "This is frustrating!"}
    )
    
    # Get summary
    response = client.post(
        f"/api/chat/{chat_id}/summarize-emotion",
        json={"include_summary_text": True}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "chatId" in data
    assert "id" in data
    assert data["chatId"] == data["id"]
    assert "dominant_emotion" in data
    assert "scores" in data
    assert "confidence" in data
    assert "summary_text" in data
    assert "generatedAt" in data
    
    # Verify scores
    scores = data["scores"]
    assert len(scores) == 10  # All 10 emotions
    assert all(0 <= v <= 1 for v in scores.values())
    assert abs(sum(scores.values()) - 1.0) < 0.01  # Sum to ~1.0


def test_emotion_summary_without_text():
    """Test emotion summarization without text"""
    create_response = client.post(
        "/api/chat",
        json={"userId": "summary_no_text"}
    )
    chat_id = create_response.json()["chatId"]
    
    response = client.post(
        f"/api/chat/{chat_id}/summarize-emotion",
        json={"include_summary_text": False}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["summary_text"] is None


def test_emotion_summary_deterministic():
    """Test that summary is deterministic for same chat"""
    # Create chat
    create_response = client.post(
        "/api/chat",
        json={
            "userId": "deterministic_test",
            "initialMessage": "Test message"
        }
    )
    chat_id = create_response.json()["chatId"]
    
    # Get summary twice
    response1 = client.post(
        f"/api/chat/{chat_id}/summarize-emotion",
        json={"include_summary_text": True}
    )
    response2 = client.post(
        f"/api/chat/{chat_id}/summarize-emotion",
        json={"include_summary_text": True}
    )
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Scores should be identical
    assert data1["scores"] == data2["scores"]
    assert data1["dominant_emotion"] == data2["dominant_emotion"]


# ============================================================================
# CHAT MANAGEMENT TESTS
# ============================================================================

def test_get_chat_by_id():
    """Test fetching complete chat"""
    create_response = client.post(
        "/api/chat",
        json={"userId": "get_test", "initialMessage": "Hello"}
    )
    chat_id = create_response.json()["chatId"]
    
    response = client.get(f"/api/chat/{chat_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "metadata" in data
    assert "messages" in data
    assert "emotionTimeline" in data


def test_update_chat_title():
    """Test updating chat title"""
    create_response = client.post(
        "/api/chat",
        json={"userId": "title_test"}
    )
    chat_id = create_response.json()["chatId"]
    
    response = client.patch(
        f"/api/chat/{chat_id}/title",
        json={"title": "Updated Title"}
    )
    
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    
    # Verify update
    chat = client.get(f"/api/chat/{chat_id}")
    assert chat.json()["metadata"]["title"] == "Updated Title"


def test_delete_chat():
    """Test deleting chat"""
    user_id = "delete_test"
    create_response = client.post(
        "/api/chat",
        json={"userId": user_id}
    )
    chat_id = create_response.json()["chatId"]
    
    # Delete chat
    response = client.delete(f"/api/chat/{chat_id}?userId={user_id}")
    assert response.status_code == 200
    
    # Verify deletion
    get_response = client.get(f"/api/chat/{chat_id}")
    assert get_response.status_code == 404


def test_delete_chat_unauthorized():
    """Test that users can't delete others' chats"""
    create_response = client.post(
        "/api/chat",
        json={"userId": "owner"}
    )
    chat_id = create_response.json()["chatId"]
    
    # Try to delete with wrong user
    response = client.delete(f"/api/chat/{chat_id}?userId=attacker")
    assert response.status_code == 404


# ============================================================================
# STORAGE LAYER TESTS
# ============================================================================

def test_storage_chat_creation(test_storage):
    """Test storage layer chat creation"""
    chat_id, created_at = test_storage.create_chat(
        user_id="storage_test",
        initial_message="Test"
    )
    
    assert chat_id is not None
    assert created_at is not None
    assert test_storage.chat_exists(chat_id)


def test_storage_message_addition(test_storage):
    """Test storage layer message addition"""
    chat_id, _ = test_storage.create_chat(user_id="msg_storage_test")
    
    test_storage.add_message(
        chat_id=chat_id,
        speaker="user",
        text="Test message",
        probs={"neutral": 1.0, "joy": 0.0, "sadness": 0.0, "anger": 0.0, "fear": 0.0, "surprise": 0.0, "stress": 0.0, "tension": 0.0, "disgust": 0.0, "anticipation": 0.0},
        dominant="neutral",
        entropy=0.0,
        confidence="high"
    )
    
    chat = test_storage.get_chat(chat_id)
    assert len(chat["messages"]) == 1


def test_storage_emotion_aggregation(test_storage):
    """Test emotion aggregation logic"""
    chat_id, _ = test_storage.create_chat(user_id="agg_test")
    
    # Add multiple messages with different emotions
    emotions = [
        ("anger", 0.8),
        ("anger", 0.7),
        ("sadness", 0.6)
    ]
    
    for emotion, score in emotions:
        probs = {e.value: 0.0 for e in EmotionType}
        probs[emotion] = score
        probs["neutral"] = 1.0 - score
        
        test_storage.add_message(
            chat_id=chat_id,
            speaker="user",
            text="Test",
            probs=probs,
            dominant=emotion,
            entropy=0.3,
            confidence="high"
        )
    
    # Get summary
    summary = test_storage.get_emotion_summary(chat_id)
    
    # Anger should be dominant (2 out of 3 messages)
    assert summary["dominant_emotion"] == "anger"
    assert summary["scores"]["anger"] > summary["scores"]["sadness"]


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

def test_bulk_chat_creation_performance():
    """Test performance with many chats"""
    import time
    
    user_id = "perf_test"
    start = time.time()
    
    # Create 50 chats
    for i in range(50):
        client.post(
            "/api/chat",
            json={"userId": user_id, "initialMessage": f"Message {i}"}
        )
    
    elapsed = time.time() - start
    
    # Should complete in reasonable time (< 10 seconds)
    assert elapsed < 10.0
    
    # Verify all created
    response = client.get(f"/api/user/{user_id}/chats?limit=100")
    assert len(response.json()["chats"]) == 50


def test_pagination_performance():
    """Test pagination with large dataset"""
    import time
    
    user_id = "pagination_perf"
    
    # Create 100 chats
    for i in range(100):
        client.post("/api/chat", json={"userId": user_id})
    
    start = time.time()
    
    # Paginate through all
    cursor = None
    total_fetched = 0
    
    while True:
        url = f"/api/user/{user_id}/chats?limit=20"
        if cursor:
            url += f"&cursor={cursor}"
        
        response = client.get(url)
        data = response.json()
        
        total_fetched += len(data["chats"])
        cursor = data["nextCursor"]
        
        if not cursor:
            break
    
    elapsed = time.time() - start
    
    assert total_fetched == 100
    assert elapsed < 5.0  # Should be fast


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_chat_workflow():
    """Test complete chat lifecycle"""
    user_id = "workflow_test"
    
    # 1. Create chat
    create_response = client.post(
        "/api/chat",
        json={"userId": user_id, "initialMessage": "I need help"}
    )
    assert create_response.status_code == 200
    chat_id = create_response.json()["chatId"]
    
    # 2. Add messages
    for text in ["This is frustrating", "I'm getting angry", "Please help"]:
        msg_response = client.post(
            f"/api/chat/{chat_id}/message",
            json={"speaker": "user", "text": text}
        )
        assert msg_response.status_code == 200
    
    # 3. Get emotion summary
    summary_response = client.post(
        f"/api/chat/{chat_id}/summarize-emotion",
        json={"include_summary_text": True}
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert "dominant_emotion" in summary
    
    # 4. Update title
    title_response = client.patch(
        f"/api/chat/{chat_id}/title",
        json={"title": "Help Request - Resolved"}
    )
    assert title_response.status_code == 200
    
    # 5. Verify in history
    history_response = client.get(f"/api/user/{user_id}/chats")
    assert history_response.status_code == 200
    chats = history_response.json()["chats"]
    assert len(chats) > 0
    assert any(c["chatId"] == chat_id for c in chats)
    
    # 6. Delete chat
    delete_response = client.delete(f"/api/chat/{chat_id}?userId={user_id}")
    assert delete_response.status_code == 200
    
    # 7. Verify deletion
    get_response = client.get(f"/api/chat/{chat_id}")
    assert get_response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
