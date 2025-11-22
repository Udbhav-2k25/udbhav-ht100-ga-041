/**
 * Main App Component
 * Orchestrates all UI components and manages state
 */

import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Brain, Wifi, WifiOff, Plus } from 'lucide-react';
import { Chat } from './components/Chat';
import { Timeline } from './components/Timeline';
import { EmpathyOrb } from './components/EmpathyOrb';
import { SummaryCard } from './components/SummaryCard';
import { api, Message, AnalyzedMessage, AnalyzeResponse, SummaryResponse } from './api';

const queryClient = new QueryClient();

function AppContent() {
  // State
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const [messages, setMessages] = useState<Message[]>([]);
  const [analyzedData, setAnalyzedData] = useState<AnalyzeResponse | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [smoothingWindow, setSmoothingWindow] = useState(3);
  const [focusedMessageId, setFocusedMessageId] = useState<number | null>(null);
  const [isOnline, setIsOnline] = useState(true);
  const [showSummary, setShowSummary] = useState(false);

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const health = await api.healthCheck();
      setIsOnline(health.status === 'online');
    } catch {
      setIsOnline(false);
    }
  };

  // Handle new message
  const handleSendMessage = async (text: string) => {
    const newMessage: Message = {
      id: messages.length + 1,
      speaker: 'user',
      text,
      ts: new Date().toISOString(),
    };

    const updatedMessages = [...messages, newMessage];
    setMessages(updatedMessages);

    // Analyze conversation
    try {
      console.log('[DEBUG] Sending message for analysis:', text);
      const analysis = await api.analyzeConversation(
        sessionId,
        updatedMessages,
        smoothingWindow
      );
      console.log('[DEBUG] Analysis result:', analysis);
      setAnalyzedData(analysis);
    } catch (error) {
      console.error('Analysis failed:', error);
    }
  };

  // Handle chat reply request
  const handleRequestReply = async (message: string) => {
    return await api.sendChat(sessionId, message);
  };

  // Handle smoothing change
  const handleSmoothingChange = async (window: number) => {
    setSmoothingWindow(window);

    if (messages.length > 0) {
      try {
        const analysis = await api.analyzeConversation(sessionId, messages, window);
        setAnalyzedData(analysis);
      } catch (error) {
        console.error('Re-analysis failed:', error);
      }
    }
  };

  // Handle peak click
  const handlePeakClick = (messageIndex: number) => {
    const msg = analyzedData?.messages[messageIndex];
    if (msg) {
      setFocusedMessageId(msg.id);
    }
  };

  // Generate summary
  const generateSummary = async () => {
    if (messages.length === 0) return;

    try {
      const summaryData = await api.getSummary(sessionId);
      setSummary(summaryData);
      setShowSummary(true);
    } catch (error) {
      console.error('Summary generation failed:', error);
    }
  };

  // Reset chat
  const handleNewChat = () => {
    setMessages([]);
    setAnalyzedData(null);
    setSummary(null);
    setShowSummary(false);
    setFocusedMessageId(null);
  };

  // Get current emotion probs for orb
  const getCurrentEmotionProbs = () => {
    if (!analyzedData?.messages || analyzedData.messages.length === 0) {
      return {
        joy: 0.1,
        sadness: 0.1,
        anger: 0.1,
        fear: 0.1,
        surprise: 0.1,
        neutral: 0.5,
      };
    }

    const lastMsg = analyzedData.messages[analyzedData.messages.length - 1];
    return lastMsg.probs;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-empathy-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-empathy-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">The Empathy Engine</h1>
                <p className="text-xs text-gray-500">Emotional Intelligence for Chat</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4">
              {/* New Chat button */}
              {messages.length > 0 && (
                <button
                  onClick={handleNewChat}
                  className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg text-sm font-medium text-gray-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  New Chat
                </button>
              )}
              
              {/* Status indicator */}
              <div className="flex items-center gap-2">
                {isOnline ? (
                  <>
                    <Wifi className="w-4 h-4 text-green-500" />
                    <span className="text-sm text-green-600 font-medium">Connected</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4 text-amber-500" />
                    <span className="text-sm text-amber-600 font-medium">Mock Mode</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column: Chat */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 h-[600px] flex flex-col overflow-hidden">
              <Chat
                messages={analyzedData?.messages || []}
                onSendMessage={handleSendMessage}
                onRequestReply={handleRequestReply}
                focusedMessageId={focusedMessageId}
                className="flex-1"
              />
            </div>

            {/* Timeline */}
            {analyzedData && analyzedData.messages.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6"
              >
                <Timeline
                  messages={analyzedData.messages}
                  timeline={analyzedData.timeline}
                  onPeakClick={handlePeakClick}
                  onSmoothingChange={handleSmoothingChange}
                />
              </motion.div>
            )}
          </div>

          {/* Right column: Orb & Summary */}
          <div className="space-y-6">
            {/* Empathy Orb */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Live Emotion</h3>
              <EmpathyOrb
                emotionProbs={getCurrentEmotionProbs()}
                className="relative w-full h-64"
              />
            </motion.div>

            {/* Summary button */}
            {messages.length > 2 && (
              <button
                onClick={generateSummary}
                className="w-full px-4 py-3 bg-gradient-to-r from-empathy-500 to-purple-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all"
              >
                Generate Summary
              </button>
            )}

            {/* Summary card */}
            {showSummary && summary && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <SummaryCard
                  summary={summary.summary}
                  sessionConfidence={analyzedData?.session_confidence || 'medium'}
                  onReanalyze={() => handleSmoothingChange(smoothingWindow)}
                />
              </motion.div>
            )}
          </div>
        </div>

        {/* Welcome state */}
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <div className="w-16 h-16 bg-gradient-to-br from-empathy-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Brain className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Start a Conversation
            </h2>
            <p className="text-gray-600 max-w-md mx-auto">
              Type a message to begin. I'll analyze emotions in real-time and provide empathetic
              insights.
            </p>
          </motion.div>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
