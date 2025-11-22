/**
 * Timeline Component
 * Interactive emotion intensity timeline with smoothing controls
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
} from 'recharts';
import { Sliders } from 'lucide-react';
import { AnalyzedMessage, Timeline as TimelineData, EmotionType } from '@/api';
import { getEmotionColor } from '@/hooks/useOrbColor';

interface TimelineProps {
  messages: AnalyzedMessage[];
  timeline: TimelineData;
  onPeakClick?: (messageIndex: number) => void;
  onSmoothingChange?: (window: number) => void;
  className?: string;
}

export const Timeline: React.FC<TimelineProps> = ({
  messages,
  timeline,
  onPeakClick,
  onSmoothingChange,
  className,
}) => {
  const [smoothingWindow, setSmoothingWindow] = useState(3);
  const [showSmoothing, setShowSmoothing] = useState(true);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // Prepare chart data
  const chartData = messages.map((msg, idx) => ({
    index: idx,
    id: msg.id,
    text: msg.text,
    emotion: msg.dominant,
    raw: timeline.raw[idx] || 0,
    smoothed: timeline.smoothed[idx] || 0,
    intensity: msg.probs[msg.dominant],
    isPeak: timeline.peaks.includes(idx),
  }));

  const handleSmoothingChange = (value: number) => {
    setSmoothingWindow(value);
    onSmoothingChange?.(value);
  };

  const handlePointClick = (data: any) => {
    if (data && data.activePayload?.[0]) {
      const index = data.activePayload[0].payload.index;
      onPeakClick?.(index);
    }
  };

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Emotion Timeline</h3>
          <p className="text-sm text-gray-500">
            Track emotional intensity across the conversation
          </p>
        </div>

        {/* Smoothing toggle */}
        <button
          onClick={() => setShowSmoothing(!showSmoothing)}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
        >
          <Sliders className="w-4 h-4" />
          {showSmoothing ? 'Smoothed' : 'Raw'}
        </button>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart
            data={chartData}
            onClick={handlePointClick}
            onMouseMove={(e: any) => {
              if (e?.activeTooltipIndex !== undefined) {
                setHoveredIndex(e.activeTooltipIndex);
              }
            }}
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="index"
              label={{ value: 'Message', position: 'insideBottom', offset: -5 }}
              stroke="#9CA3AF"
            />
            <YAxis
              domain={[0, 1]}
              label={{ value: 'Intensity', angle: -90, position: 'insideLeft' }}
              stroke="#9CA3AF"
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Raw line (faded) */}
            {!showSmoothing && (
              <Line
                type="monotone"
                dataKey="raw"
                stroke="#9CA3AF"
                strokeWidth={2}
                dot={{ fill: '#9CA3AF', r: 4 }}
                activeDot={{ r: 6 }}
              />
            )}

            {/* Smoothed line */}
            {showSmoothing && (
              <Line
                type="monotone"
                dataKey="smoothed"
                stroke="#6B7CF9"
                strokeWidth={3}
                dot={(props: any) => {
                  const color = getEmotionColor(chartData[props.index].emotion);
                  return (
                    <circle
                      cx={props.cx}
                      cy={props.cy}
                      r={props.payload.isPeak ? 6 : 4}
                      fill={color}
                      stroke={props.payload.isPeak ? '#fff' : color}
                      strokeWidth={props.payload.isPeak ? 2 : 0}
                    />
                  );
                }}
                activeDot={{ r: 8 }}
              />
            )}

            {/* Peak markers */}
            {timeline.peaks.map((peakIdx) => {
              const point = chartData[peakIdx];
              if (!point) return null;
              return (
                <ReferenceDot
                  key={peakIdx}
                  x={peakIdx}
                  y={showSmoothing ? point.smoothed : point.raw}
                  r={10}
                  fill="transparent"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  isFront={true}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Smoothing control */}
      <div className="mt-4 p-4 bg-gray-50 rounded-xl">
        <label className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            Smoothing Window: {smoothingWindow}
          </span>
          <span className="text-xs text-gray-500">
            {smoothingWindow === 1 ? 'No smoothing' : `${smoothingWindow} messages`}
          </span>
        </label>
        <input
          type="range"
          min={1}
          max={7}
          step={2}
          value={smoothingWindow}
          onChange={(e) => handleSmoothingChange(parseInt(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-empathy-500"
        />
        <div className="flex justify-between mt-1 text-xs text-gray-500">
          <span>Raw</span>
          <span>More smoothing</span>
        </div>
      </div>

      {/* Peak legend */}
      {timeline.peaks.length > 0 && (
        <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-xl">
          <p className="text-sm font-medium text-amber-900 mb-2">
            🔥 {timeline.peaks.length} Emotional Peak{timeline.peaks.length > 1 ? 's' : ''}{' '}
            Detected
          </p>
          <div className="flex flex-wrap gap-2">
            {timeline.peaks.map((peakIdx) => {
              const msg = messages[peakIdx];
              return (
                <button
                  key={peakIdx}
                  onClick={() => onPeakClick?.(peakIdx)}
                  className="px-3 py-1 bg-white border border-amber-300 rounded-lg text-xs font-medium text-amber-900 hover:bg-amber-100 transition-colors"
                >
                  Message #{peakIdx + 1}: {msg.dominant}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// CUSTOM TOOLTIP
// ============================================================================

const CustomTooltip: React.FC<any> = ({ active, payload }) => {
  if (!active || !payload?.[0]) return null;

  const data = payload[0].payload;
  const color = getEmotionColor(data.emotion);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border-2 border-gray-200 rounded-xl p-4 shadow-xl max-w-xs"
    >
      {/* Message preview */}
      <div className="mb-3">
        <p className="text-xs font-semibold text-gray-500 mb-1">Message #{data.index + 1}</p>
        <p className="text-sm text-gray-900 line-clamp-2">{data.text}</p>
      </div>

      {/* Emotion badge */}
      <div className="flex items-center gap-2 mb-2">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: color }}
        />
        <span className="text-sm font-medium capitalize" style={{ color }}>
          {data.emotion}
        </span>
        {data.isPeak && (
          <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-900 rounded-full font-medium">
            Peak
          </span>
        )}
      </div>

      {/* Intensity */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Intensity:</span>
          <span className="font-semibold text-gray-900">
            {Math.round(data.intensity * 100)}%
          </span>
        </div>
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all"
            style={{
              width: `${data.intensity * 100}%`,
              backgroundColor: color,
            }}
          />
        </div>
      </div>
    </motion.div>
  );
};
