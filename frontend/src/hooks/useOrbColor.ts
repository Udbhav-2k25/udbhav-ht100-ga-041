/**
 * useOrbColor Hook
 * Maps emotion probabilities to color and scale for 3D orb
 */

import { EmotionProbs, EmotionType } from '@/api';
import { useMemo } from 'react';

// Emotion color mapping (matches Tailwind config)
const EMOTION_COLORS: Record<EmotionType, string> = {
  joy: '#FCD34D',       // yellow-300
  sadness: '#60A5FA',   // blue-400
  anger: '#F87171',     // red-400
  fear: '#A78BFA',      // purple-400
  surprise: '#FB923C',  // orange-400
  stress: '#F59E0B',    // amber-500
  tension: '#EC4899',   // pink-500
  disgust: '#10B981',   // emerald-500
  anticipation: '#3B82F6', // blue-500
  neutral: '#9CA3AF',   // gray-400
};

export interface OrbColorResult {
  color: string;
  scale: number;
  intensity: number;
  dominantEmotion: EmotionType;
}

/**
 * Calculate orb color based on emotion probabilities
 * Blends colors weighted by probabilities
 */
export function getColor(probs: EmotionProbs): OrbColorResult {
  // Find dominant emotion
  const dominant = (Object.entries(probs).reduce((a, b) =>
    b[1] > a[1] ? b : a
  )[0] as EmotionType);

  const intensity = probs[dominant];
  
  // Use dominant color (could blend multiple emotions here)
  const color = EMOTION_COLORS[dominant];
  
  // Scale: 0.8 to 1.5 based on intensity
  const scale = 0.8 + (intensity * 0.7);

  return {
    color,
    scale,
    intensity,
    dominantEmotion: dominant,
  };
}

/**
 * Get scale multiplier based on emotion intensity
 */
export function getScale(intensity: number): number {
  return 0.8 + (intensity * 0.7);
}

/**
 * React hook version for component use
 */
export function useOrbColor(probs: EmotionProbs): OrbColorResult {
  return useMemo(() => getColor(probs), [probs]);
}

/**
 * Get emotion color by type
 */
export function getEmotionColor(emotion: EmotionType): string {
  return EMOTION_COLORS[emotion];
}

/**
 * Convert hex color to RGB array for Three.js
 */
export function hexToRgb(hex: string): [number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? [
        parseInt(result[1], 16) / 255,
        parseInt(result[2], 16) / 255,
        parseInt(result[3], 16) / 255,
      ]
    : [0.5, 0.5, 0.5];
}
