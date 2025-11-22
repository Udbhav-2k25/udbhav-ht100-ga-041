"""
Storage Layer for The Empathy Engine
In-memory database with JSON persistence
Production: Replace with PostgreSQL, MongoDB, or Redis
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import uuid

from models import (
    ChatMetadata,
    ChatSession,
    AnalyzedMessage,
    ChatHistoryItem,
    EmotionType,
    ConfidenceLevel
)


class ChatStorage:
    """
    Thread-safe in-memory storage with optional JSON persistence.
    
    Data Structure:
    - chats: Dict[chatId, ChatSession]
    - user_chats: Dict[userId, List[chatId]]
    - emotion_cache: Dict[chatId, EmotionSummary]
    """
    
    def __init__(self, persist_path: Optional[str] = None):
        self.chats: Dict[str, Dict] = {}
        self.user_chats: Dict[str, List[str]] = defaultdict(list)
        self.emotion_cache: Dict[str, Dict] = {}
        self.persist_path = persist_path
        
        if persist_path and os.path.exists(persist_path):
            self._load_from_disk()
    
    # ========================================================================
    # CREATE OPERATIONS
    # ========================================================================
    
    def create_chat(self, user_id: str, initial_message: Optional[str] = None) -> Tuple[str, str]:
        """
        Create new chat session.
        
        Returns:
            Tuple[chatId, createdAt]
        """
        chat_id = self._generate_chat_id()
        created_at = datetime.utcnow().isoformat() + "Z"
        
        snippet = initial_message[:50] + "..." if initial_message and len(initial_message) > 50 else (initial_message or "New chat")
        title = self._generate_title(initial_message) if initial_message else "New Chat"
        
        chat_data = {
            "metadata": {
                "chatId": chat_id,
                "id": chat_id,
                "userId": user_id,
                "title": title,
                "createdAt": created_at,
                "lastUpdatedAt": created_at,
                "snippet": snippet,
                "dominant_emotion": "neutral",
                "messageCount": 0
            },
            "messages": [],
            "emotionTimeline": {emotion.value: [] for emotion in EmotionType}
        }
        
        self.chats[chat_id] = chat_data
        self.user_chats[user_id].append(chat_id)
        
        self._persist()
        return chat_id, created_at
    
    # ========================================================================
    # READ OPERATIONS
    # ========================================================================
    
    def get_chat(self, chat_id: str) -> Optional[Dict]:
        """Get complete chat session"""
        return self.chats.get(chat_id)
    
    def get_user_chats(
        self,
        user_id: str,
        limit: int = 20,
        cursor: Optional[str] = None
    ) -> Tuple[List[ChatHistoryItem], Optional[str], int]:
        """
        Get paginated chat history for user.
        
        Returns:
            Tuple[chats, next_cursor, total]
        """
        chat_ids = self.user_chats.get(user_id, [])
        total = len(chat_ids)
        
        # Sort by lastUpdatedAt descending
        sorted_ids = sorted(
            chat_ids,
            key=lambda cid: self.chats[cid]["metadata"]["lastUpdatedAt"],
            reverse=True
        )
        
        # Handle pagination
        start_idx = 0
        if cursor:
            try:
                start_idx = int(cursor.split("_")[1])
            except (IndexError, ValueError):
                start_idx = 0
        
        end_idx = start_idx + limit
        page_ids = sorted_ids[start_idx:end_idx]
        
        # Build response items
        history_items = []
        for cid in page_ids:
            chat = self.chats[cid]
            history_items.append(ChatHistoryItem(
                chatId=cid,
                id=cid,
                title=chat["metadata"]["title"],
                createdAt=chat["metadata"]["createdAt"],
                lastUpdatedAt=chat["metadata"]["lastUpdatedAt"],
                snippet=chat["metadata"]["snippet"],
                dominant_emotion=chat["metadata"]["dominant_emotion"],
                messageCount=chat["metadata"]["messageCount"]
            ))
        
        # Next cursor
        next_cursor = f"cursor_{end_idx}" if end_idx < total else None
        
        return history_items, next_cursor, total
    
    def chat_exists(self, chat_id: str) -> bool:
        """Check if chat exists"""
        return chat_id in self.chats
    
    # ========================================================================
    # UPDATE OPERATIONS
    # ========================================================================
    
    def add_message(
        self,
        chat_id: str,
        speaker: str,
        text: str,
        probs: Dict[str, float],
        dominant: str,
        entropy: float,
        confidence: str
    ) -> None:
        """Add analyzed message to chat"""
        if chat_id not in self.chats:
            raise ValueError(f"Chat {chat_id} not found")
        
        chat = self.chats[chat_id]
        message_id = len(chat["messages"]) + 1
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        message = {
            "id": message_id,
            "speaker": speaker,
            "text": text,
            "ts": timestamp,
            "probs": probs,
            "dominant": dominant,
            "entropy": entropy,
            "confidence": confidence
        }
        
        chat["messages"].append(message)
        chat["metadata"]["lastUpdatedAt"] = timestamp
        chat["metadata"]["messageCount"] = len(chat["messages"])
        
        # Update timeline
        for emotion, prob in probs.items():
            chat["emotionTimeline"][emotion].append(prob)
        
        # Update dominant emotion (aggregate)
        self._update_dominant_emotion(chat_id)
        
        # Update snippet if first user message
        if speaker == "user" and message_id == 1:
            snippet = text[:50] + "..." if len(text) > 50 else text
            chat["metadata"]["snippet"] = snippet
            chat["metadata"]["title"] = self._generate_title(text)
        
        self._persist()
    
    def update_chat_title(self, chat_id: str, title: str) -> None:
        """Update chat title"""
        if chat_id not in self.chats:
            raise ValueError(f"Chat {chat_id} not found")
        
        self.chats[chat_id]["metadata"]["title"] = title
        self.chats[chat_id]["metadata"]["lastUpdatedAt"] = datetime.utcnow().isoformat() + "Z"
        self._persist()
    
    # ========================================================================
    # DELETE OPERATIONS
    # ========================================================================
    
    def delete_chat(self, chat_id: str, user_id: str) -> bool:
        """Delete chat session"""
        if chat_id not in self.chats:
            return False
        
        # Verify ownership
        if self.chats[chat_id]["metadata"]["userId"] != user_id:
            return False
        
        del self.chats[chat_id]
        self.user_chats[user_id].remove(chat_id)
        
        if chat_id in self.emotion_cache:
            del self.emotion_cache[chat_id]
        
        self._persist()
        return True
    
    # ========================================================================
    # EMOTION AGGREGATION
    # ========================================================================
    
    def get_emotion_summary(
        self,
        chat_id: str,
        include_summary_text: bool = True
    ) -> Optional[Dict]:
        """
        Calculate aggregated emotion summary for chat.
        Deterministic based on message emotions.
        """
        if chat_id not in self.chats:
            return None
        
        chat = self.chats[chat_id]
        messages = chat["messages"]
        
        if not messages:
            # Empty chat
            return {
                "chatId": chat_id,
                "id": chat_id,
                "dominant_emotion": "neutral",
                "scores": {emotion.value: 0.1 for emotion in EmotionType},
                "confidence": 0.0,
                "summary_text": "No messages yet." if include_summary_text else None,
                "generatedAt": datetime.utcnow().isoformat() + "Z"
            }
        
        # Aggregate emotion scores (average across all messages)
        emotion_sums = defaultdict(float)
        total_messages = len(messages)
        
        for msg in messages:
            for emotion, prob in msg["probs"].items():
                emotion_sums[emotion] += prob
        
        # Normalize
        scores = {
            emotion: emotion_sums[emotion] / total_messages
            for emotion in emotion_sums
        }
        
        # Find dominant
        dominant = max(scores, key=scores.get)
        
        # Calculate confidence (inverse of entropy)
        avg_entropy = sum(msg["entropy"] for msg in messages) / total_messages
        confidence = 1.0 - avg_entropy
        
        # Generate summary text
        summary_text = None
        if include_summary_text:
            summary_text = self._generate_summary_text(dominant, scores, confidence)
        
        result = {
            "chatId": chat_id,
            "id": chat_id,
            "dominant_emotion": dominant,
            "scores": scores,
            "confidence": round(confidence, 2),
            "summary_text": summary_text,
            "generatedAt": datetime.utcnow().isoformat() + "Z"
        }
        
        # Cache result
        self.emotion_cache[chat_id] = result
        
        return result
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _generate_chat_id(self) -> str:
        """Generate unique chat ID"""
        return str(uuid.uuid4())[:8]
    
    def _generate_title(self, text: str) -> str:
        """Generate title from first message"""
        # Simple heuristic: first 5 words
        words = text.split()[:5]
        title = " ".join(words)
        if len(text.split()) > 5:
            title += "..."
        return title
    
    def _update_dominant_emotion(self, chat_id: str) -> None:
        """Update chat's dominant emotion based on all messages"""
        chat = self.chats[chat_id]
        messages = chat["messages"]
        
        if not messages:
            return
        
        # Count emotion occurrences
        emotion_counts = defaultdict(int)
        for msg in messages:
            emotion_counts[msg["dominant"]] += 1
        
        # Most frequent emotion
        dominant = max(emotion_counts, key=emotion_counts.get)
        chat["metadata"]["dominant_emotion"] = dominant
    
    def _generate_summary_text(
        self,
        dominant: str,
        scores: Dict[str, float],
        confidence: float
    ) -> str:
        """Generate human-readable summary"""
        # Get top 2 emotions
        sorted_emotions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_emotions = sorted_emotions[:2]
        
        primary = dominant
        secondary = top_emotions[1][0] if len(top_emotions) > 1 and top_emotions[1][1] > 0.1 else None
        
        # Build summary
        if confidence > 0.7:
            summary = f"The conversation is strongly dominated by {primary}"
        elif confidence > 0.4:
            summary = f"The conversation shows {primary}"
        else:
            summary = f"The conversation has mixed emotions with some {primary}"
        
        if secondary and secondary != primary:
            summary += f", with occasional {secondary}"
        
        summary += "."
        return summary
    
    def _persist(self) -> None:
        """Save to disk (optional)"""
        if not self.persist_path:
            return
        
        try:
            data = {
                "chats": self.chats,
                "user_chats": dict(self.user_chats),
                "emotion_cache": self.emotion_cache
            }
            with open(self.persist_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to persist data: {e}")
    
    def _load_from_disk(self) -> None:
        """Load from disk"""
        try:
            with open(self.persist_path, "r") as f:
                data = json.load(f)
            
            self.chats = data.get("chats", {})
            self.user_chats = defaultdict(list, data.get("user_chats", {}))
            self.emotion_cache = data.get("emotion_cache", {})
            
            print(f"[INFO] Loaded {len(self.chats)} chats from {self.persist_path}")
        except Exception as e:
            print(f"[WARNING] Failed to load data: {e}")


# Global storage instance
storage = ChatStorage(persist_path="data/chats.json")
