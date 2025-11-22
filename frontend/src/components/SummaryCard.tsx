/**
 * SummaryCard Component
 * Displays conversation summary with export functionality (JSON/PNG)
 */

import React, { useRef } from 'react';
import { motion } from 'framer-motion';
import { Download, FileJson, Image as ImageIcon, RefreshCw } from 'lucide-react';
import html2canvas from 'html2canvas';
import { SummaryResponse, EmotionType } from '@/api';
import { getEmotionColor } from '@/hooks/useOrbColor';
import { clsx } from 'clsx';

interface SummaryCardProps {
  summary: SummaryResponse['summary'];
  sessionConfidence: 'high' | 'medium' | 'low';
  onReanalyze?: () => void;
  className?: string;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  summary,
  sessionConfidence,
  onReanalyze,
  className,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);

  // Export as JSON
  const exportJSON = () => {
    const data = {
      summary,
      sessionConfidence,
      exportedAt: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `empathy-summary-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Export as PNG
  const exportPNG = async () => {
    if (!cardRef.current) return;

    try {
      const canvas = await html2canvas(cardRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });

      canvas.toBlob((blob) => {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `empathy-summary-${Date.now()}.png`;
        link.click();
        URL.revokeObjectURL(url);
      });
    } catch (error) {
      console.error('PNG export failed:', error);
    }
  };

  const emotionColor = getEmotionColor(summary.dominant_emotion);

  return (
    <div className={className}>
      {/* Export controls */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Conversation Summary</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={exportJSON}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            title="Export as JSON"
          >
            <FileJson className="w-4 h-4" />
            JSON
          </button>
          <button
            onClick={exportPNG}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            title="Export as PNG"
          >
            <ImageIcon className="w-4 h-4" />
            PNG
          </button>
          {onReanalyze && (
            <button
              onClick={onReanalyze}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-empathy-700 bg-empathy-50 hover:bg-empathy-100 rounded-lg transition-colors"
              title="Re-run analysis"
            >
              <RefreshCw className="w-4 h-4" />
              Re-analyze
            </button>
          )}
        </div>
      </div>

      {/* Summary card */}
      <motion.div
        ref={cardRef}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl border-2 border-gray-200 p-6 shadow-lg"
      >
        {/* Header: Dominant emotion */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <p className="text-sm font-medium text-gray-500 mb-1">Dominant Emotion</p>
            <div className="flex items-center gap-3">
              <div
                className="w-12 h-12 rounded-full flex items-center justify-center"
                style={{ backgroundColor: emotionColor + '20' }}
              >
                <span className="text-2xl">{getEmotionEmoji(summary.dominant_emotion)}</span>
              </div>
              <div>
                <p
                  className="text-2xl font-bold capitalize"
                  style={{ color: emotionColor }}
                >
                  {summary.dominant_emotion}
                </p>
                <ConfidenceBadge confidence={summary.confidence} />
              </div>
            </div>
          </div>

          {/* Session confidence */}
          <div className="text-right">
            <p className="text-sm font-medium text-gray-500 mb-1">Session</p>
            <ConfidenceBadge confidence={sessionConfidence} />
          </div>
        </div>

        {/* Style */}
        <div className="mb-6">
          <p className="text-sm font-medium text-gray-500 mb-2">Conversation Style</p>
          <p className="text-base text-gray-900 italic">"{summary.style}"</p>
        </div>

        {/* Highlights */}
        <div className="mb-6">
          <p className="text-sm font-medium text-gray-500 mb-3">Key Moments</p>
          <ul className="space-y-2">
            {summary.highlights.map((highlight, idx) => (
              <motion.li
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="flex items-start gap-3"
              >
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                  style={{ backgroundColor: emotionColor + '20' }}
                >
                  <span className="text-xs font-bold" style={{ color: emotionColor }}>
                    {idx + 1}
                  </span>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{highlight}</p>
              </motion.li>
            ))}
          </ul>
        </div>

        {/* Advice */}
        <div className="pt-6 border-t border-gray-200">
          <p className="text-sm font-medium text-gray-500 mb-2">💡 Insight</p>
          <p className="text-base text-gray-900 leading-relaxed">{summary.advice}</p>
        </div>
      </motion.div>
    </div>
  );
};

// ============================================================================
// CONFIDENCE BADGE
// ============================================================================

interface ConfidenceBadgeProps {
  confidence: 'high' | 'medium' | 'low';
}

const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ confidence }) => {
  const styles = {
    high: 'bg-green-100 text-green-800 border-green-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-red-100 text-red-800 border-red-200',
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border capitalize',
        styles[confidence]
      )}
    >
      {confidence} confidence
    </span>
  );
};

// ============================================================================
// HELPERS
// ============================================================================

function getEmotionEmoji(emotion: EmotionType): string {
  const emojis: Record<EmotionType, string> = {
    joy: '😊',
    sadness: '😢',
    anger: '😠',
    fear: '😰',
    surprise: '😲',
    neutral: '😐',
  };
  return emojis[emotion] || '😐';
}
