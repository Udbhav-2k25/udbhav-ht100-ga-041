/**
 * API Client for The Empathy Engine
 * Typed wrapper for backend endpoints with mock mode fallback
 */

import axios, { AxiosInstance } from 'axios';

// ============================================================================
// TYPE DEFINITIONS (matching backend schema exactly)
// ============================================================================

export interface Message {
  id: number;
  speaker: 'user' | 'assistant';
  text: string;
  ts: string; // ISO timestamp
}

export interface AnalyzedMessage extends Message {
  probs: EmotionProbs;
  dominant: EmotionType;
  entropy: number;
  confidence: 'high' | 'medium' | 'low';
}

export interface EmotionProbs {
  joy: number;
  sadness: number;
  anger: number;
  fear: number;
  surprise: number;
  stress: number;
  tension: number;
  disgust: number;
  anticipation: number;
  neutral: number;
}

export type EmotionType = keyof EmotionProbs;

export interface Timeline {
  raw: number[];
  smoothed: number[];
  peaks: number[];
}

// ============================================================================
// REQUEST/RESPONSE TYPES
// ============================================================================

/**
 * POST /analyze Request
 * Example:
 * {
 *   "session_id": "demo-1",
 *   "messages": [
 *     {
 *       "id": 1,
 *       "speaker": "user",
 *       "text": "I can't believe this happened.",
 *       "ts": "2025-11-21T10:00:00Z"
 *     }
 *   ],
 *   "smoothing_window": 3
 * }
 */
export interface AnalyzeRequest {
  session_id: string;
  messages: Message[];
  smoothing_window?: number;
}

/**
 * POST /analyze Response
 * Example:
 * {
 *   "messages": [
 *     {
 *       "id": 1,
 *       "speaker": "user",
 *       "text": "I can't believe this happened.",
 *       "ts": "2025-11-21T10:00:00Z",
 *       "probs": { "joy": 0.05, "sadness": 0.65, "anger": 0.20, "fear": 0.05, "surprise": 0.03, "neutral": 0.02 },
 *       "dominant": "sadness",
 *       "entropy": 0.45,
 *       "confidence": "medium"
 *     }
 *   ],
 *   "timeline": {
 *     "raw": [0.65],
 *     "smoothed": [0.65],
 *     "peaks": [0]
 *   },
 *   "session_confidence": "medium"
 * }
 */
export interface AnalyzeResponse {
  messages: AnalyzedMessage[];
  timeline: Timeline;
  session_confidence: 'high' | 'medium' | 'low';
}

/**
 * POST /chat Request
 */
export interface ChatRequest {
  session_id: string;
  message: string;
}

/**
 * POST /chat Response
 */
export interface ChatResponse {
  reply: string;
  emotion: EmotionType;
  confidence: 'high' | 'medium' | 'low';
  safety_flag: boolean;
}

/**
 * POST /summary Request
 */
export interface SummaryRequest {
  session_id: string;
}

/**
 * POST /summary Response
 */
export interface SummaryResponse {
  summary: {
    dominant_emotion: EmotionType;
    confidence: 'high' | 'medium' | 'low';
    style: string;
    highlights: string[];
    advice: string;
  };
}

// ============================================================================
// API CLIENT
// ============================================================================

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const USE_MOCK = import.meta.env.VITE_MOCK_MODE === 'true';

class EmpathyAPI {
  private client: AxiosInstance;
  private useMock: boolean;

  constructor(baseURL: string, useMock: boolean = false) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    this.useMock = useMock;
  }

  /**
   * Analyze conversation for emotion probabilities and timeline
   */
  async analyzeConversation(
    sessionId: string,
    messages: Message[],
    smoothingWindow: number = 3
  ): Promise<AnalyzeResponse> {
    if (this.useMock) {
      return this.mockAnalyze(messages, smoothingWindow);
    }

    try {
      const response = await this.client.post<AnalyzeResponse>('/analyze', {
        session_id: sessionId,
        messages,
        smoothing_window: smoothingWindow,
      });
      return response.data;
    } catch (error) {
      console.error('API Error (analyze):', error);
      // Fallback to mock on network error
      return this.mockAnalyze(messages, smoothingWindow);
    }
  }

  /**
   * Send chat message and get empathetic reply
   */
  async sendChat(sessionId: string, message: string): Promise<ChatResponse> {
    if (this.useMock) {
      return this.mockChat(message);
    }

    try {
      const response = await this.client.post<ChatResponse>('/chat', {
        session_id: sessionId,
        message,
      });
      return response.data;
    } catch (error) {
      console.error('API Error (chat):', error);
      return this.mockChat(message);
    }
  }

  /**
   * Get conversation summary
   */
  async getSummary(sessionId: string): Promise<SummaryResponse> {
    if (this.useMock) {
      return this.mockSummary();
    }

    try {
      const response = await this.client.post<SummaryResponse>('/summary', {
        session_id: sessionId,
      });
      return response.data;
    } catch (error) {
      console.error('API Error (summary):', error);
      return this.mockSummary();
    }
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    try {
      const response = await this.client.get('/');
      return response.data;
    } catch (error) {
      return { status: 'offline', service: 'mock' };
    }
  }

  // ============================================================================
  // MOCK MODE IMPLEMENTATIONS
  // ============================================================================

  private mockAnalyze(messages: Message[], smoothingWindow: number): AnalyzeResponse {
    // Simple rule-based emotion classification for demo
    const analyzedMessages: AnalyzedMessage[] = messages.map((msg) => {
      const probs = this.getMockEmotionProbs(msg.text);
      const dominant = this.getDominantEmotion(probs);
      const entropy = this.calculateEntropy(probs);
      const confidence = this.getConfidenceBucket(entropy);

      return {
        ...msg,
        probs,
        dominant,
        entropy,
        confidence,
      };
    });

    // Generate timeline
    const raw = analyzedMessages.map((m) => m.probs[m.dominant]);
    const smoothed = this.applySmoothing(raw, smoothingWindow);
    const peaks = this.detectPeaks(smoothed);

    const avgEntropy =
      analyzedMessages.reduce((sum, m) => sum + m.entropy, 0) / analyzedMessages.length;
    const sessionConfidence = this.getConfidenceBucket(avgEntropy);

    return {
      messages: analyzedMessages,
      timeline: { raw, smoothed, peaks },
      session_confidence: sessionConfidence,
    };
  }

  private mockChat(message: string): ChatResponse {
    const probs = this.getMockEmotionProbs(message);
    const dominant = this.getDominantEmotion(probs);
    const safetyFlag = this.checkSafety(message);

    const replies: Record<EmotionType, string> = {
      joy: "That's wonderful to hear! Tell me more about what's making you happy.",
      sadness: "I'm here for you. Want to talk about what's bothering you?",
      anger: "I understand you're frustrated. Let's work through this together.",
      fear: "It's okay to feel scared. I'm here to help.",
      surprise: "That sounds unexpected! How are you feeling about it?",
      neutral: "Thanks for sharing. What's on your mind?",
    };

    return {
      reply: safetyFlag
        ? "I'm really concerned about what you've shared. Please reach out to a crisis helpline: 988 (US)"
        : replies[dominant],
      emotion: dominant,
      confidence: 'medium',
      safety_flag: safetyFlag,
    };
  }

  private mockSummary(): SummaryResponse {
    return {
      summary: {
        dominant_emotion: 'sadness',
        confidence: 'high',
        style: 'reflective and processing disappointment',
        highlights: [
          'Initial frustration about project rejection',
          'Self-doubt emerged mid-conversation',
          'Positive shift towards constructive mindset',
        ],
        advice: 'Your emotional journey shows resilience. Use the feedback constructively.',
      },
    };
  }

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  private getMockEmotionProbs(text: string): EmotionProbs {
    const lower = text.toLowerCase();

    // Rule-based classification
    if (
      lower.includes('happy') ||
      lower.includes('excited') ||
      lower.includes('wonderful') ||
      lower.includes('!')
    ) {
      return { joy: 0.6, sadness: 0.05, anger: 0.05, fear: 0.05, surprise: 0.1, stress: 0.02, tension: 0.02, disgust: 0.01, anticipation: 0.05, neutral: 0.05 };
    } else if (
      lower.includes('sad') ||
      lower.includes('disappointed') ||
      lower.includes("can't believe")
    ) {
      return { joy: 0.05, sadness: 0.55, anger: 0.15, fear: 0.05, surprise: 0.05, stress: 0.05, tension: 0.03, disgust: 0.02, anticipation: 0.0, neutral: 0.05 };
    } else if (
      lower.includes('angry') ||
      lower.includes('frustrated') ||
      lower.includes('mad')
    ) {
      return { joy: 0.05, sadness: 0.1, anger: 0.6, fear: 0.05, surprise: 0.05, stress: 0.03, tension: 0.04, disgust: 0.03, anticipation: 0.0, neutral: 0.05 };
    } else if (lower.includes('scared') || lower.includes('worried') || lower.includes('afraid')) {
      return { joy: 0.05, sadness: 0.15, anger: 0.05, fear: 0.5, surprise: 0.05, stress: 0.08, tension: 0.07, disgust: 0.0, anticipation: 0.0, neutral: 0.05 };
    } else if (lower.includes('?') && lower.length < 30) {
      return { joy: 0.1, sadness: 0.1, anger: 0.05, fear: 0.1, surprise: 0.4, stress: 0.03, tension: 0.05, disgust: 0.02, anticipation: 0.05, neutral: 0.1 };
    } else {
      return { joy: 0.1, sadness: 0.1, anger: 0.05, fear: 0.08, surprise: 0.07, stress: 0.05, tension: 0.05, disgust: 0.05, anticipation: 0.05, neutral: 0.4 };
    }
  }

  private getDominantEmotion(probs: EmotionProbs): EmotionType {
    return Object.entries(probs).reduce((a, b) => (b[1] > a[1] ? b : a))[0] as EmotionType;
  }

  private calculateEntropy(probs: EmotionProbs): number {
    let entropy = 0;
    for (const p of Object.values(probs)) {
      if (p > 0) {
        entropy -= p * Math.log2(p);
      }
    }
    return entropy / Math.log2(10); // Normalize to 0-1
  }

  private getConfidenceBucket(entropy: number): 'high' | 'medium' | 'low' {
    if (entropy < 0.3) return 'high';
    if (entropy < 0.6) return 'medium';
    return 'low';
  }

  private applySmoothing(values: number[], window: number): number[] {
    if (window < 1) return values;

    return values.map((_, i) => {
      const start = Math.max(0, i - Math.floor(window / 2));
      const end = Math.min(values.length, i + Math.floor(window / 2) + 1);
      const sum = values.slice(start, end).reduce((a, b) => a + b, 0);
      return sum / (end - start);
    });
  }

  private detectPeaks(values: number[], threshold: number = 0.7): number[] {
    const peaks: number[] = [];
    for (let i = 1; i < values.length - 1; i++) {
      if (values[i] > threshold && values[i] > values[i - 1] && values[i] > values[i + 1]) {
        peaks.push(i);
      }
    }
    if (values.length > 0 && values[values.length - 1] > threshold) {
      peaks.push(values.length - 1);
    }
    return peaks;
  }

  private checkSafety(message: string): boolean {
    const keywords = [
      'kill myself',
      'end it all',
      'suicide',
      'want to die',
      'self harm',
      'hurt myself',
    ];
    const lower = message.toLowerCase();
    return keywords.some((kw) => lower.includes(kw));
  }
}

// Export singleton instance
export const api = new EmpathyAPI(BASE_URL, USE_MOCK);

// Export class for testing
export default EmpathyAPI;
