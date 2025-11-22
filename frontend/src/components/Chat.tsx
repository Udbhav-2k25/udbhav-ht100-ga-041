/**
 * Chat Component
 * Displays conversation with per-message emotion analysis
 * Supports assistant reply suggestions and safety escalation
 */

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, AlertTriangle, Loader2 } from 'lucide-react';
import { Message, AnalyzedMessage, EmotionType, ChatResponse } from '@/api';
import { getEmotionColor } from '@/hooks/useOrbColor';
import { clsx } from 'clsx';

interface ChatProps {
  messages: AnalyzedMessage[];
  onSendMessage: (text: string) => Promise<void>;
  onRequestReply: (message: string) => Promise<ChatResponse>;
  focusedMessageId?: number | null;
  className?: string;
}

export const Chat: React.FC<ChatProps> = ({
  messages,
  onSendMessage,
  onRequestReply,
  focusedMessageId,
  className,
}) => {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestedReply, setSuggestedReply] = useState<ChatResponse | null>(null);
  const [showSafety, setShowSafety] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  // Scroll to focused message
  useEffect(() => {
    if (focusedMessageId !== null && focusedMessageId !== undefined) {
      const element = messageRefs.current.get(focusedMessageId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        element.classList.add('ring-2', 'ring-empathy-500');
        setTimeout(() => {
          element.classList.remove('ring-2', 'ring-empathy-500');
        }, 2000);
      }
    }
  }, [focusedMessageId]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const text = input;
    setInput('');
    setIsLoading(true);
    setSuggestedReply(null);
    setShowSafety(false);

    try {
      // Send message for analysis
      await onSendMessage(text);

      // Get assistant reply suggestion
      const reply = await onRequestReply(text);
      setSuggestedReply(reply);

      if (reply.safety_flag) {
        setShowSafety(true);
      }
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const acceptSuggestion = async () => {
    if (!suggestedReply || showSafety) return;
    setInput(suggestedReply.reply);
    setSuggestedReply(null);
  };

  return (
    <div className={clsx('flex flex-col h-full', className)}>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((msg, idx) => (
            <motion.div
              key={msg.id}
              ref={(el) => {
                if (el) messageRefs.current.set(msg.id, el);
              }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className={clsx(
                'flex',
                msg.speaker === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={clsx(
                  'max-w-[80%] rounded-2xl px-4 py-3 shadow-sm transition-all',
                  msg.speaker === 'user'
                    ? 'bg-empathy-500 text-white'
                    : 'bg-gray-100 text-gray-900'
                )}
              >
                {/* Message text */}
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>

                {/* Emotion badge */}
                {'probs' in msg && (
                  <div className="mt-2 flex items-center gap-2">
                    <EmotionBadge
                      emotion={msg.dominant}
                      confidence={msg.confidence}
                      intensity={msg.probs[msg.dominant]}
                    />
                    {msg.entropy > 0.7 && (
                      <span className="text-xs opacity-70">Ambiguous</span>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-gray-100 rounded-2xl px-4 py-3">
              <Loader2 className="w-5 h-5 animate-spin text-gray-500" />
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Safety warning */}
      <AnimatePresence>
        {showSafety && suggestedReply?.safety_flag && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mx-4 mb-4 p-4 bg-red-50 border-2 border-red-200 rounded-xl"
          >
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-red-900">Crisis Support Needed</p>
                <p className="text-sm text-red-800 mt-1">{suggestedReply.reply}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Suggested reply */}
      <AnimatePresence>
        {suggestedReply && !showSafety && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mx-4 mb-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-gray-500">Suggested reply:</span>
              <span
                className="text-xs px-2 py-0.5 rounded-full"
                style={{
                  backgroundColor: getEmotionColor(suggestedReply.emotion) + '20',
                  color: getEmotionColor(suggestedReply.emotion),
                }}
              >
                {suggestedReply.emotion}
              </span>
            </div>
            <button
              onClick={acceptSuggestion}
              className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-xl text-sm text-gray-700 transition-colors"
            >
              {suggestedReply.reply}
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input */}
      <div className="p-4 border-t bg-white">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            rows={1}
            disabled={isLoading}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-empathy-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="px-6 py-3 bg-empathy-500 text-white rounded-xl hover:bg-empathy-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 font-medium"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// EMOTION BADGE COMPONENT
// ============================================================================

interface EmotionBadgeProps {
  emotion: EmotionType;
  confidence: 'high' | 'medium' | 'low';
  intensity: number;
}

const EmotionBadge: React.FC<EmotionBadgeProps> = ({ emotion, confidence, intensity }) => {
  const color = getEmotionColor(emotion);

  return (
    <div className="flex items-center gap-2">
      {/* Emotion label */}
      <span
        className="text-xs font-medium px-2 py-1 rounded-full capitalize"
        style={{
          backgroundColor: color + '20',
          color: color,
        }}
      >
        {emotion}
      </span>

      {/* Intensity bar */}
      <div className="flex items-center gap-1">
        <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all"
            style={{
              width: `${intensity * 100}%`,
              backgroundColor: color,
            }}
          />
        </div>
        <span className="text-xs opacity-70">{Math.round(intensity * 100)}%</span>
      </div>

      {/* Confidence indicator */}
      {confidence === 'low' && (
        <span className="text-xs opacity-50" title="Low confidence">
          ?
        </span>
      )}
    </div>
  );
};
