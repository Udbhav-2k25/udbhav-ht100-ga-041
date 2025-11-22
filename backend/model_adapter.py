"""
Model Adapter for Empathy Engine

Integrates Gemini 2.0 Flash for emotion classification, text generation,
and conversation summarization with anti-neutral bias enforcement.
"""

import os
import re
import google.generativeai as genai
from typing import Dict, List, Tuple

# Configure Gemini with API key from environment
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Gemini model
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Valid emotions for the system
EMOTIONS = ["joy", "sadness", "anger", "fear", "surprise", "stress", "tension", "disgust", "anticipation", "neutral"]

# Emotion keywords for anti-neutral bias
EMOTION_KEYWORDS = {
    "joy": ["happy", "excited", "wonderful", "amazing", "love", "fantastic", "excellent", "thrilled", "delighted", "glad", "joyful"],
    "sadness": ["sad", "depressed", "unhappy", "miserable", "heartbroken", "devastated", "lonely", "hurt", "crying", "low", "down", "blue"],
    "anger": ["angry", "mad", "furious", "irritated", "annoyed", "pissed", "hate", "ridiculous", "outrageous", "dislike", "frustrat"],
    "fear": ["scared", "afraid", "terrified", "anxious", "worried", "nervous", "frightened", "panic"],
    "surprise": ["surprised", "shocked", "amazed", "unexpected", "wow", "omg", "incredible"],
    "disgust": ["disgusted", "gross", "sick", "revolting", "nasty", "eww", "yuck", "idiot", "stupid", "dumb", "moron"],
    "stress": ["stressed", "overwhelmed", "pressure", "tense", "exhausted", "burned out"],
    "tension": ["tension", "awkward", "uncomfortable", "uneasy"],
    "anticipation": ["looking forward", "can't wait", "eager", "anticipating", "hopeful", "expecting"]
}

# Emotion emojis for anti-neutral bias
EMOTION_EMOJIS = {
    "joy": ["😊", "😃", "😄", "😁", "😆", "🤗", "🥰", "😍", "🎉", "✨"],
    "sadness": ["😢", "😭", "😔", "😞", "💔", "😿"],
    "anger": ["😡", "😠", "🤬", "😤", "💢"],
    "fear": ["😱", "😨", "😰", "😧", "😦"],
    "surprise": ["😲", "😮", "😯", "🤯"],
    "disgust": ["🤢", "🤮", "😖", "😣"],
    "stress": ["😫", "😩", "😓", "😰"],
    "anticipation": ["🤩", "😍", "🥳"]
}

# Punctuation indicators (multiple exclamation/question marks suggest emotion)
EMPHASIS_PATTERNS = [
    r"!!+",  # Multiple exclamation marks
    r"\?\?+",  # Multiple question marks
    r"[A-Z]{3,}",  # All caps words
]


def _has_emotion_signal(text: str) -> Tuple[bool, str]:
    """
    Check if text contains emotional keywords, emojis, or emphasis patterns.
    Returns (has_signal, detected_emotion_or_reason).
    """
    text_lower = text.lower()
    
    # Check for emotion keywords with word boundary awareness
    # Priority order: disgust/anger (insults) > sadness > fear > joy
    emotion_priority = ["disgust", "anger", "sadness", "fear", "surprise", "joy", "stress", "tension", "anticipation"]
    
    for emotion in emotion_priority:
        keywords = EMOTION_KEYWORDS.get(emotion, [])
        for keyword in keywords:
            # Use word boundary for better matching
            if re.search(r'\b' + re.escape(keyword), text_lower):
                return True, emotion
    
    # Check for emojis
    for emotion, emojis in EMOTION_EMOJIS.items():
        for emoji in emojis:
            if emoji in text:
                return True, emotion
    
    # Check for emphasis patterns (multiple punctuation, caps)
    for pattern in EMPHASIS_PATTERNS:
        if re.search(pattern, text):
            return True, "emphasis_detected"
    
    return False, "no_signal"


def _parse_emotion_response(response_text: str) -> Dict[str, float]:
    """
    Parse Gemini's emotion classification response.
    Expected format: "joy: 0.8, sadness: 0.1, anger: 0.05, fear: 0.05"
    """
    emotion_probs = {emotion: 0.0 for emotion in EMOTIONS}
    
    try:
        # Extract emotion:value pairs
        pairs = response_text.lower().strip().split(',')
        for pair in pairs:
            if ':' in pair:
                emotion, prob = pair.split(':')
                emotion = emotion.strip()
                prob = float(prob.strip())
                
                if emotion in EMOTIONS:
                    emotion_probs[emotion] = max(0.0, min(1.0, prob))
        
        # Normalize to sum to 1.0
        total = sum(emotion_probs.values())
        if total > 0:
            emotion_probs = {k: v/total for k, v in emotion_probs.items()}
        else:
            # If parsing failed, return uniform distribution (avoid pure neutral)
            emotion_probs = {emotion: 1.0/len(EMOTIONS) for emotion in EMOTIONS}
            
    except Exception as e:
        print(f"Error parsing emotion response: {e}")
        # Fallback to uniform distribution
        emotion_probs = {emotion: 1.0/len(EMOTIONS) for emotion in EMOTIONS}
    
    return emotion_probs


def classify_emotion(text: str, chat_history: List[Dict] = None) -> Dict[str, float]:
    """
    Classify emotion in text with keyword-based detection + Gemini fallback.
    Anti-neutral bias: keyword detection takes priority over API.
    
    Args:
        text: The message to classify
        chat_history: Previous messages for context (last 5 messages)
    
    Returns:
        Dictionary mapping emotion names to probabilities
    """
    
    # STEP 1: Check for emotion signals (keywords, emojis, emphasis)
    has_signal, signal_type = _has_emotion_signal(text)
    
    # STEP 2: Keyword-based classification (fast, no API calls, no quotas!)
    if has_signal and signal_type in EMOTIONS:
        # Strong keyword match - return high confidence for detected emotion
        print(f"Keyword detection: {signal_type} in '{text[:50]}...'")
        emotion_probs = {emotion: 0.02 for emotion in EMOTIONS}
        emotion_probs[signal_type] = 0.80
        emotion_probs["neutral"] = 0.01
        
        # Add secondary emotions for richer detection
        if signal_type == "disgust":
            emotion_probs["anger"] = 0.12
        elif signal_type == "anger":
            emotion_probs["disgust"] = 0.08
        elif signal_type == "sadness":
            emotion_probs["fear"] = 0.05
        
        # Normalize
        total = sum(emotion_probs.values())
        emotion_probs = {k: v/total for k, v in emotion_probs.items()}
        return emotion_probs
    
    # STEP 3: Check for sarcasm patterns (e.g., "Yeah great... not", "Sure, whatever")
    sarcasm_patterns = [
        r"yeah\s+(right|sure|great|okay).*not",
        r"oh\s+(great|wonderful|fantastic).*\.\.\.",
        r"sure\s*[,.]?\s*whatever",
        r"fine\s*[.!]+\s*$",
    ]
    
    text_lower = text.lower()
    for pattern in sarcasm_patterns:
        if re.search(pattern, text_lower):
            print(f"Sarcasm detected in '{text[:50]}...'")
            emotion_probs = {emotion: 0.05 for emotion in EMOTIONS}
            emotion_probs["anger"] = 0.5
            emotion_probs["disgust"] = 0.2
            emotion_probs["neutral"] = 0.05
            return emotion_probs
    
    # STEP 4: Try Gemini API (may hit rate limits)
    try:
        # Build context from recent chat history
        context_str = ""
        if chat_history and len(chat_history) > 0:
            recent = chat_history[-5:]  # Last 5 messages
            context_str = "\n\nRecent conversation context:\n"
            for msg in recent:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                context_str += f"{role}: {content}\n"
        
        # Construct prompt with anti-neutral instructions
        prompt = f"""Analyze the emotional content of this message and classify it into one or more of these emotions:
joy, sadness, anger, fear, surprise, stress, tension, disgust, anticipation, neutral

CRITICAL RULES:
1. NEVER classify as neutral if the text contains:
   - Emotion words (angry, sad, happy, scared, etc.)
   - Emojis (😢, 😡, 😊, etc.)
   - Multiple exclamation marks (!!!)
   - ALL CAPS WORDS
   - Sarcasm or passive-aggressive tone
   
2. For short responses ("Ok.", "Sure.", "Fine."), inherit emotion from previous context if available.

3. Only return neutral when:
   - Confidence in all other emotions < 0.40
   - No emotion keywords, emojis, or emphasis detected
   - Text is purely factual/informational
   
4. Sarcasm ("Yeah great job... not") should map to anger or disgust, NOT neutral.

{context_str}

Current message to analyze: "{text}"

Respond with ONLY emotion probabilities in this exact format:
joy: X.XX, sadness: X.XX, anger: X.XX, fear: X.XX, surprise: X.XX, stress: X.XX, tension: X.XX, disgust: X.XX, anticipation: X.XX, neutral: X.XX

Probabilities must sum to 1.0."""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse the response
        emotion_probs = _parse_emotion_response(response_text)
        
        # Anti-neutral enforcement
        max_non_neutral = max([v for k, v in emotion_probs.items() if k != "neutral"], default=0.0)
        if emotion_probs["neutral"] > 0.5 and max_non_neutral >= 0.30:
            # Swap: reduce neutral, boost highest emotion
            non_neutral = {k: v for k, v in emotion_probs.items() if k != "neutral"}
            max_emotion = max(non_neutral, key=non_neutral.get)
            
            emotion_probs[max_emotion] = 0.6
            emotion_probs["neutral"] = 0.2
            remaining = 0.2
            for emotion in emotion_probs:
                if emotion not in [max_emotion, "neutral"]:
                    emotion_probs[emotion] = remaining / (len(EMOTIONS) - 2)
        
        print(f"Gemini API: {max(emotion_probs, key=emotion_probs.get)} for '{text[:50]}...'")
        return emotion_probs
        
    except Exception as e:
        print(f"Gemini API error (using keyword fallback): {e}")
        pass  # Fall through to fallback
    
    # STEP 5: Fallback - analyze text length and punctuation for neutral detection
    # Only return neutral if text is truly informational
    if len(text.strip()) < 10 and "?" not in text and "!" not in text:
        # Very short, no punctuation -> likely neutral acknowledgment
        return {emotion: 0.1 for emotion in EMOTIONS}
    
    # Default: truly ambiguous - distribute fairly evenly
    return {
        "joy": 0.10,
        "sadness": 0.10,
        "anger": 0.10,
        "fear": 0.10,
        "surprise": 0.10,
        "stress": 0.08,
        "tension": 0.08,
        "disgust": 0.08,
        "anticipation": 0.10,
        "neutral": 0.16
    }


def generate_reply(text: str, emotion: str, chat_history: List[Dict] = None) -> str:
    """
    Generate an empathetic reply based on detected emotion using Gemini.
    
    Args:
        text: User's message
        emotion: Detected dominant emotion
        chat_history: Previous conversation for context
    
    Returns:
        Empathetic response string
    """
    
    # Build conversation context
    context_str = ""
    if chat_history and len(chat_history) > 0:
        context_str = "Conversation history:\n"
        for msg in chat_history[-10:]:  # Last 10 messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            context_str += f"{role}: {content}\n"
    
    prompt = f"""You are an empathetic AI assistant. The user just sent you a message with detected emotion: {emotion}.

{context_str}

User's current message: "{text}"

Generate a compassionate, supportive response that:
1. Acknowledges their emotional state
2. Provides validation and understanding
3. Offers helpful perspective or support
4. Keeps response concise (2-3 sentences)
5. Matches the intensity of their emotion

Response:"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating reply: {e}")
        
        # Fallback responses based on emotion
        fallbacks = {
            "joy": "I'm so glad you're feeling happy! It's wonderful to share in your positive energy.",
            "sadness": "I hear you, and I'm here for you. It's okay to feel this way, and your feelings are valid.",
            "anger": "I understand you're frustrated. Let's work through this together. What would help most right now?",
            "fear": "I can sense your worry. Remember, you're not alone in this. Let's take it one step at a time.",
            "surprise": "That's quite unexpected! How are you feeling about it?",
            "stress": "It sounds like you're under a lot of pressure. Remember to take care of yourself.",
            "tension": "I sense some tension. Would you like to talk about what's on your mind?",
            "disgust": "I understand that doesn't sit well with you. Your feelings are completely valid.",
            "anticipation": "It sounds like you're looking forward to something! Tell me more.",
            "neutral": "I'm here and listening. What's on your mind?"
        }
        return fallbacks.get(emotion, "I'm here to support you. Tell me more about how you're feeling.")


def summarize_conversation(chat_history: List[Dict]) -> str:
    """
    Generate a summary of the conversation using Gemini.
    
    Args:
        chat_history: List of message dictionaries
    
    Returns:
        Summary string
    """
    
    if not chat_history:
        return "No conversation to summarize yet."
    
    # Build conversation text
    conversation_text = ""
    for msg in chat_history:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        emotion = msg.get('emotion', 'neutral')
        conversation_text += f"{role} ({emotion}): {content}\n"
    
    prompt = f"""Summarize this conversation, focusing on:
1. Main topics discussed
2. Emotional journey of the user
3. Key concerns or needs expressed
4. Overall tone and outcome

Conversation:
{conversation_text}

Provide a concise summary (3-4 sentences):"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Unable to generate summary at this time."


# Test function
if __name__ == "__main__":
    # Test cases from master prompt
    test_cases = [
        "I am so excited and happy!",
        "This is ridiculous!!!",
        "Yeah great job... not.",
        "😢 lost my wallet today",
        "Ok.",  # Short, needs context
        "The meeting is at 3pm",  # Truly neutral
    ]
    
    print("Testing Gemini emotion classifier with anti-neutral bias:\n")
    
    for text in test_cases:
        print(f"Text: {text}")
        emotions = classify_emotion(text)
        
        # Show top 3 emotions
        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
        print(f"  Top emotions:")
        for emotion, prob in sorted_emotions[:3]:
            print(f"    {emotion}: {prob:.3f}")
        
        # Check for anti-neutral bias working
        has_signal, signal = _has_emotion_signal(text)
        if has_signal:
            print(f"  ✓ Emotion signal detected: {signal}")
        
        print()
