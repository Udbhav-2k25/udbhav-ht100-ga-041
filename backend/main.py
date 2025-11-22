"""
FastAPI Backend for The Empathy Engine
Complete emotion analysis API with timeline, smoothing, and peak detection.
Enhanced with chat history, user management, and emotion summarization.
"""

# Load environment variables FIRST before any imports
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import math
import os

from model_adapter import classify_emotion, summarize_conversation, generate_reply
from storage import storage
from models import (
    CreateChatRequest,
    CreateChatResponse,
    SummarizeEmotionRequest,
    EmotionSummary,
    AddMessageRequest,
    UpdateChatTitleRequest,
    ChatHistoryResponse,
    ChatSession
)

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="The Empathy Engine API",
    description="Emotional insight for chat conversations using free AI models",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# IN-MEMORY SESSION STORE
# Replace with Redis in production: redis.Redis(host='localhost', port=6379)
# ============================================================================

sessions: Dict[str, Dict] = {}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class Message(BaseModel):
    id: int
    speaker: str
    text: str
    ts: str  # ISO timestamp


class AnalyzeRequest(BaseModel):
    session_id: str
    messages: List[Message]
    smoothing_window: Optional[int] = 3  # Moving average window


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


# ============================================================================
# BUSINESS LOGIC: EMOTION ANALYSIS
# ============================================================================

def calculate_entropy(probs: Dict[str, float]) -> float:
    """
    Calculate Shannon entropy for emotion distribution.
    Higher entropy = more uncertainty/ambiguity.
    
    Returns: float 0-1 (normalized)
    """
    entropy = 0.0
    for p in probs.values():
        if p > 0:
            entropy -= p * math.log2(p)
    
    # Normalize to 0-1 (max entropy for 10 emotions is log2(10) ≈ 3.32)
    max_entropy = math.log2(len(probs))
    return entropy / max_entropy if max_entropy > 0 else 0.0


def get_confidence_bucket(entropy: float) -> str:
    """
    Map entropy to confidence level.
    
    Low entropy (0-0.3) → high confidence (clear emotion)
    Medium entropy (0.3-0.6) → medium confidence
    High entropy (0.6-1.0) → low confidence (ambiguous)
    """
    if entropy < 0.3:
        return "high"
    elif entropy < 0.6:
        return "medium"
    else:
        return "low"


def get_dominant_emotion(probs: Dict[str, float]) -> str:
    """Get emotion with highest probability."""
    return max(probs.items(), key=lambda x: x[1])[0]


def apply_smoothing(values: List[float], window: int) -> List[float]:
    """
    Apply moving average smoothing to timeline values.
    
    Args:
        values: List of emotion intensities
        window: Window size (default 3)
    
    Returns:
        Smoothed values (same length as input)
    """
    if window < 1:
        return values
    
    smoothed = []
    for i in range(len(values)):
        start = max(0, i - window // 2)
        end = min(len(values), i + window // 2 + 1)
        smoothed.append(sum(values[start:end]) / (end - start))
    
    return smoothed


def detect_peaks(values: List[float], threshold: float = 0.7) -> List[int]:
    """
    Detect emotion intensity peaks in timeline.
    
    Args:
        values: Smoothed emotion values
        threshold: Minimum value to be considered a peak
    
    Returns:
        List of message IDs where peaks occur
    """
    peaks = []
    for i in range(1, len(values) - 1):
        if values[i] > threshold and values[i] > values[i-1] and values[i] > values[i+1]:
            peaks.append(i)
    
    # Also include final value if it's high
    if len(values) > 0 and values[-1] > threshold:
        peaks.append(len(values) - 1)
    
    return peaks


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "The Empathy Engine",
        "models": "FREE Groq API (llama-3.1-70b-versatile)"
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_conversation(request: AnalyzeRequest):
    """
    Analyze conversation for emotion probabilities, timeline, and peaks.
    
    Process:
    1. Classify emotions for each message
    2. Calculate entropy and confidence
    3. Apply smoothing to timeline
    4. Detect emotional peaks
    5. Store session data
    
    Returns:
        - messages: List with emotion probs, dominant emotion, entropy
        - timeline: Smoothed values and peak indices
        - session_confidence: Overall confidence level
    """
    try:
        analyzed_messages = []
        raw_intensities = []
        
        # Step 1: Classify each message
        for msg in request.messages:
            probs = classify_emotion(msg.text)
            entropy = calculate_entropy(probs)
            dominant = get_dominant_emotion(probs)
            confidence = get_confidence_bucket(entropy)
            
            analyzed_messages.append({
                "id": msg.id,
                "speaker": msg.speaker,
                "text": msg.text,
                "ts": msg.ts,
                "probs": probs,
                "dominant": dominant,
                "entropy": round(entropy, 3),
                "confidence": confidence
            })
            
            # Track dominant emotion intensity for timeline
            raw_intensities.append(probs[dominant])
        
        # Step 2: Apply smoothing
        smoothed = apply_smoothing(raw_intensities, request.smoothing_window)
        
        # Step 3: Detect peaks
        peaks = detect_peaks(smoothed)
        
        # Step 4: Calculate session-level confidence
        avg_entropy = sum(msg["entropy"] for msg in analyzed_messages) / len(analyzed_messages)
        session_confidence = get_confidence_bucket(avg_entropy)
        
        # Step 5: Store in session (for summary/chat endpoints)
        sessions[request.session_id] = {
            "messages": analyzed_messages,
            "last_updated": datetime.now().isoformat()
        }
        
        return AnalyzeResponse(
            messages=analyzed_messages,
            timeline={
                "raw": [round(v, 3) for v in raw_intensities],
                "smoothed": [round(v, 3) for v in smoothed],
                "peaks": peaks
            },
            session_confidence=session_confidence
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/summary", response_model=SummaryResponse)
def get_summary(request: SummaryRequest):
    """
    Generate conversation summary card.
    
    Requires:
        - Session must exist (call /analyze first)
    
    Returns:
        - dominant_emotion: Overall conversation emotion
        - confidence: high/medium/low
        - style: Conversation tone description
        - highlights: Key emotional moments
        - advice: Empathetic guidance
    """
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Call /analyze first.")
    
    try:
        messages = sessions[request.session_id]["messages"]
        summary = summarize_conversation(messages)
        
        return SummaryResponse(summary=summary)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
def chat_reply(request: ChatRequest):
    """
    Generate empathetic reply with emotion matching.
    
    Process:
    1. Classify emotion of user message
    2. Determine confidence level
    3. Generate tone-matched reply
    4. Check safety flags
    
    Tone matching rules:
        - High confidence → match emotion tone
        - Medium confidence → hedge with clarifying questions
        - Low confidence → neutral, exploratory response
    
    Safety:
        - Detects self-harm keywords
        - Returns crisis resources if flagged
    """
    try:
        # Classify incoming message
        probs = classify_emotion(request.message)
        entropy = calculate_entropy(probs)
        dominant = get_dominant_emotion(probs)
        confidence = get_confidence_bucket(entropy)
        
        # Generate empathetic reply
        result = generate_reply(request.message, dominant, confidence)
        
        # Update session if exists
        if request.session_id in sessions:
            sessions[request.session_id]["last_message"] = {
                "text": request.message,
                "emotion": dominant,
                "confidence": confidence,
                "ts": datetime.now().isoformat()
            }
        
        return ChatResponse(
            reply=result["reply"],
            emotion=dominant,
            confidence=confidence,
            safety_flag=result["safety_flag"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat reply failed: {str(e)}")


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    """
    Delete session data (privacy/cleanup).
    In production, implement TTL with Redis.
    """
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "deleted", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


# ============================================================================
# NEW API ENDPOINTS: CHAT HISTORY & EMOTION SUMMARIZATION
# ============================================================================

@app.post("/api/chat", response_model=CreateChatResponse, tags=["Chat Management"])
def create_new_chat(request: CreateChatRequest):
    """
    Create a new chat session.
    
    Example:
    ```
    POST /api/chat
    Body: { "userId": "jdoe", "initialMessage": "Hello!" }
    
    Response: {
      "chatId": "abc123",
      "id": "abc123",
      "userId": "jdoe",
      "createdAt": "2025-11-22T12:00:00Z",
      "message": "Chat created successfully"
    }
    ```
    """
    try:
        chat_id, created_at = storage.create_chat(
            user_id=request.userId,
            initial_message=request.initialMessage
        )
        
        # If initial message provided, analyze it
        if request.initialMessage:
            probs = classify_emotion(request.initialMessage)
            dominant = max(probs, key=probs.get)
            entropy = calculate_entropy(probs)
            confidence = get_confidence_bucket(entropy)
            
            storage.add_message(
                chat_id=chat_id,
                speaker="user",
                text=request.initialMessage,
                probs=probs,
                dominant=dominant,
                entropy=entropy,
                confidence=confidence
            )
        
        return CreateChatResponse(
            chatId=chat_id,
            id=chat_id,
            userId=request.userId,
            createdAt=created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/{userId}/chats", response_model=ChatHistoryResponse, tags=["Chat Management"])
def get_user_chat_history(
    userId: str = Path(..., description="User identifier"),
    limit: int = Query(20, ge=1, le=100, description="Number of chats per page"),
    cursor: Optional[str] = Query(None, description="Pagination cursor")
):
    """
    Get paginated chat history for a user.
    
    Example:
    ```
    GET /api/user/jdoe/chats?limit=2
    
    Response: {
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
    ```
    """
    try:
        chats, next_cursor, total = storage.get_user_chats(
            user_id=userId,
            limit=limit,
            cursor=cursor
        )
        
        return ChatHistoryResponse(
            userId=userId,
            chats=chats,
            nextCursor=next_cursor,
            total=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/{chatId}", response_model=Dict, tags=["Chat Management"])
def get_chat_by_id(chatId: str = Path(..., description="Chat identifier")):
    """
    Get complete chat session with all messages.
    
    Example:
    ```
    GET /api/chat/abc123
    
    Response: {
      "metadata": {
        "chatId": "abc123",
        "id": "abc123",
        "userId": "jdoe",
        "title": "Billing issue",
        "createdAt": "2025-11-20T09:00:00Z",
        "lastUpdatedAt": "2025-11-20T11:00:00Z",
        "snippet": "I've been charged twice...",
        "dominant_emotion": "anger",
        "messageCount": 12
      },
      "messages": [...],
      "emotionTimeline": {...}
    }
    ```
    """
    chat = storage.get_chat(chatId)
    if not chat:
        raise HTTPException(status_code=404, detail=f"Chat {chatId} not found")
    
    return chat


@app.post("/api/chat/{chatId}/message", tags=["Chat Management"])
def add_message_to_chat(
    chatId: str = Path(..., description="Chat identifier"),
    request: AddMessageRequest = None
):
    """
    Add a new message to an existing chat.
    
    Example:
    ```
    POST /api/chat/abc123/message
    Body: { "speaker": "user", "text": "This is frustrating!" }
    
    Response: {
      "status": "success",
      "chatId": "abc123",
      "messageId": 5
    }
    ```
    """
    if not storage.chat_exists(chatId):
        raise HTTPException(status_code=404, detail=f"Chat {chatId} not found")
    
    try:
        # Analyze emotion
        probs = classify_emotion(request.text)
        dominant = max(probs, key=probs.get)
        entropy = calculate_entropy(probs)
        confidence = get_confidence_bucket(entropy)
        
        # Store message
        storage.add_message(
            chat_id=chatId,
            speaker=request.speaker,
            text=request.text,
            probs=probs,
            dominant=dominant,
            entropy=entropy,
            confidence=confidence
        )
        
        chat = storage.get_chat(chatId)
        message_id = len(chat["messages"])
        
        return {
            "status": "success",
            "chatId": chatId,
            "messageId": message_id,
            "emotion": dominant,
            "confidence": confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/{chatId}/summarize-emotion", response_model=EmotionSummary, tags=["Emotion Analysis"])
def summarize_chat_emotion(
    chatId: str = Path(..., description="Chat identifier"),
    request: SummarizeEmotionRequest = SummarizeEmotionRequest()
):
    """
    Generate aggregated emotion summary for a chat.
    
    Example:
    ```
    POST /api/chat/abc123/summarize-emotion
    Body: { "include_summary_text": true }
    
    Response: {
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
    ```
    """
    summary = storage.get_emotion_summary(
        chat_id=chatId,
        include_summary_text=request.include_summary_text
    )
    
    if not summary:
        raise HTTPException(status_code=404, detail=f"Chat {chatId} not found")
    
    return EmotionSummary(**summary)


@app.patch("/api/chat/{chatId}/title", tags=["Chat Management"])
def update_chat_title_endpoint(
    chatId: str = Path(..., description="Chat identifier"),
    request: UpdateChatTitleRequest = None
):
    """
    Update chat title.
    
    Example:
    ```
    PATCH /api/chat/abc123/title
    Body: { "title": "Billing Issue - Resolved" }
    
    Response: {
      "status": "success",
      "chatId": "abc123",
      "title": "Billing Issue - Resolved"
    }
    ```
    """
    if not storage.chat_exists(chatId):
        raise HTTPException(status_code=404, detail=f"Chat {chatId} not found")
    
    try:
        storage.update_chat_title(chatId, request.title)
        return {
            "status": "success",
            "chatId": chatId,
            "title": request.title
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/{chatId}", tags=["Chat Management"])
def delete_chat_endpoint(
    chatId: str = Path(..., description="Chat identifier"),
    userId: str = Query(..., description="User identifier for verification")
):
    """
    Delete a chat session.
    
    Example:
    ```
    DELETE /api/chat/abc123?userId=jdoe
    
    Response: {
      "status": "deleted",
      "chatId": "abc123"
    }
    ```
    """
    success = storage.delete_chat(chatId, userId)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Chat {chatId} not found or unauthorized"
        )
    
    return {"status": "deleted", "chatId": chatId}


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    port = int(os.getenv("PORT", 8000))
    print(f"""
    ╔════════════════════════════════════════╗
    ║   THE EMPATHY ENGINE - Backend API    ║
    ║   Using FREE Groq API (llama-3.3)     ║
    ╚════════════════════════════════════════╝
    
    Server running on: http://localhost:{port}
    Docs: http://localhost:{port}/docs
    API Docs: http://localhost:{port}/redoc
    
    New Endpoints:
    - POST   /api/chat (Create chat)
    - GET    /api/user/:userId/chats (List chats)
    - GET    /api/chat/:chatId (Get chat)
    - POST   /api/chat/:chatId/message (Add message)
    - POST   /api/chat/:chatId/summarize-emotion (Summarize)
    - PATCH  /api/chat/:chatId/title (Update title)
    - DELETE /api/chat/:chatId (Delete chat)
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=port)
