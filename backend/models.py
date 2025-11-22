"""
Data Models for The Empathy Engine
Enhanced models with chat history, user management, and emotion tracking
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class EmotionType(str, Enum):
    joy = "joy"
    sadness = "sadness"
    anger = "anger"
    fear = "fear"
    surprise = "surprise"
    stress = "stress"
    tension = "tension"
    disgust = "disgust"
    anticipation = "anticipation"
    neutral = "neutral"


class ConfidenceLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


# ============================================================================
# CORE MESSAGE MODELS
# ============================================================================

class Message(BaseModel):
    id: int
    speaker: str
    text: str
    ts: str  # ISO timestamp


class AnalyzedMessage(Message):
    probs: Dict[str, float]
    dominant: EmotionType
    entropy: float
    confidence: ConfidenceLevel


# ============================================================================
# CHAT SESSION MODELS
# ============================================================================

class ChatMetadata(BaseModel):
    """Metadata for a chat session"""
    chatId: str = Field(..., description="Unique chat identifier")
    id: str = Field(..., description="Alias for chatId (backward compat)")
    userId: str = Field(..., description="User identifier")
    title: str = Field(..., description="Chat title/summary")
    createdAt: str = Field(..., description="ISO timestamp of creation")
    lastUpdatedAt: str = Field(..., description="ISO timestamp of last update")
    snippet: str = Field(..., description="First message preview")
    dominant_emotion: EmotionType = Field(..., description="Primary emotion in chat")
    messageCount: int = Field(default=0, description="Total messages in chat")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chatId": "abc123",
                "id": "abc123",
                "userId": "jdoe",
                "title": "Billing issue",
                "createdAt": "2025-11-20T09:00:00Z",
                "lastUpdatedAt": "2025-11-20T11:00:00Z",
                "snippet": "I've been charged twice...",
                "dominant_emotion": "anger",
                "messageCount": 12
            }
        }


class ChatSession(BaseModel):
    """Complete chat session with messages"""
    metadata: ChatMetadata
    messages: List[AnalyzedMessage]
    emotionTimeline: Dict[str, List[float]] = Field(
        default_factory=dict,
        description="Timeline of emotion intensities"
    )


# ============================================================================
# EMOTION SUMMARY MODELS
# ============================================================================

class EmotionSummary(BaseModel):
    """Aggregated emotion analysis for a chat"""
    chatId: str
    id: str = Field(..., description="Alias for chatId")
    dominant_emotion: EmotionType
    scores: Dict[str, float] = Field(
        ...,
        description="Normalized emotion scores (sum to 1.0)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score 0-1"
    )
    summary_text: Optional[str] = Field(
        None,
        description="Human-readable emotion summary"
    )
    generatedAt: str = Field(..., description="ISO timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chatId": "abc123",
                "id": "abc123",
                "dominant_emotion": "anger",
                "scores": {
                    "joy": 0.01,
                    "sadness": 0.21,
                    "anger": 0.62,
                    "fear": 0.03,
                    "surprise": 0.05,
                    "stress": 0.02,
                    "tension": 0.03,
                    "disgust": 0.01,
                    "anticipation": 0.01,
                    "neutral": 0.01
                },
                "confidence": 0.84,
                "summary_text": "The conversation is dominated by anger and frustration, with occasional sadness.",
                "generatedAt": "2025-11-22T12:34:56Z"
            }
        }


# ============================================================================
# USER & HISTORY MODELS
# ============================================================================

class ChatHistoryItem(BaseModel):
    """Lightweight chat entry for history lists"""
    chatId: str
    id: str = Field(..., description="Alias for chatId")
    title: str
    createdAt: str
    lastUpdatedAt: str
    snippet: str
    dominant_emotion: EmotionType
    messageCount: int = 0


class ChatHistoryResponse(BaseModel):
    """Paginated chat history"""
    userId: str
    chats: List[ChatHistoryItem]
    nextCursor: Optional[str] = Field(
        None,
        description="Cursor for next page, null if no more"
    )
    total: int = Field(..., description="Total chat count")
    
    class Config:
        json_schema_extra = {
            "example": {
                "userId": "jdoe",
                "chats": [
                    {
                        "chatId": "abc123",
                        "id": "abc123",
                        "title": "Billing issue",
                        "createdAt": "2025-11-20T09:00:00Z",
                        "lastUpdatedAt": "2025-11-20T11:00:00Z",
                        "snippet": "I've been charged twice...",
                        "dominant_emotion": "anger",
                        "messageCount": 12
                    }
                ],
                "nextCursor": "cursor_2",
                "total": 45
            }
        }


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateChatRequest(BaseModel):
    userId: str
    initialMessage: Optional[str] = None


class CreateChatResponse(BaseModel):
    chatId: str
    id: str = Field(..., description="Alias for chatId")
    userId: str
    createdAt: str
    message: str = "Chat created successfully"


class SummarizeEmotionRequest(BaseModel):
    include_summary_text: bool = Field(default=True, description="Generate text summary")


class AddMessageRequest(BaseModel):
    speaker: str = Field(..., description="'user' or 'assistant'")
    text: str


class UpdateChatTitleRequest(BaseModel):
    title: str


# ============================================================================
# EXISTING API MODELS (for backward compatibility)
# ============================================================================

class AnalyzeRequest(BaseModel):
    session_id: str
    messages: List[Message]
    smoothing_window: Optional[int] = 3


class AnalyzeResponse(BaseModel):
    messages: List[Dict]
    timeline: Dict
    session_confidence: str


class SummaryRequest(BaseModel):
    session_id: str


class SummaryResponse(BaseModel):
    summary: Dict


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    emotion: str
    confidence: str
    safety_flag: bool
