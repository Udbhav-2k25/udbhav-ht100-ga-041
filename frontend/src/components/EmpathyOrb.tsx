/**
 * EmpathyOrb Component
 * 3D sphere that visualizes emotion through color and pulsing animation
 * Includes WebGL fallback to SVG
 */

import React, { Suspense, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial } from '@react-three/drei';
import { motion } from 'framer-motion';
import * as THREE from 'three';
import { EmotionProbs } from '@/api';
import { useOrbColor, hexToRgb } from '@/hooks/useOrbColor';

interface EmpathyOrbProps {
  emotionProbs: EmotionProbs;
  className?: string;
}

export const EmpathyOrb: React.FC<EmpathyOrbProps> = ({ emotionProbs, className }) => {
  const [webGLSupported, setWebGLSupported] = useState(true);
  const orbData = useOrbColor(emotionProbs);

  // Check WebGL support
  const checkWebGL = () => {
    try {
      const canvas = document.createElement('canvas');
      return !!(
        window.WebGLRenderingContext &&
        (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
      );
    } catch (e) {
      return false;
    }
  };

  React.useEffect(() => {
    setWebGLSupported(checkWebGL());
  }, []);

  if (!webGLSupported) {
    return <SVGOrbFallback color={orbData.color} scale={orbData.scale} className={className} />;
  }

  return (
    <div className={className}>
      <Suspense fallback={<SVGOrbFallback color={orbData.color} scale={orbData.scale} />}>
        <Canvas camera={{ position: [0, 0, 5], fov: 50 }}>
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 10, 5]} intensity={1} />
          <pointLight position={[-10, -10, -5]} intensity={0.5} />
          <AnimatedOrb
            color={orbData.color}
            intensity={orbData.intensity}
            emotion={orbData.dominantEmotion}
          />
        </Canvas>
      </Suspense>

      {/* Emotion label */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
        <motion.div
          key={orbData.dominantEmotion}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="px-4 py-2 bg-white/90 backdrop-blur-sm rounded-full shadow-lg"
        >
          <p className="text-sm font-semibold capitalize" style={{ color: orbData.color }}>
            {orbData.dominantEmotion}
          </p>
          <p className="text-xs text-gray-500 text-center">
            {Math.round(orbData.intensity * 100)}% intensity
          </p>
        </motion.div>
      </div>
    </div>
  );
};

// ============================================================================
// ANIMATED 3D ORB
// ============================================================================

interface AnimatedOrbProps {
  color: string;
  intensity: number;
  emotion: string;
}

const AnimatedOrb: React.FC<AnimatedOrbProps> = ({ color, intensity, emotion }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const rgb = hexToRgb(color);

  useFrame((state) => {
    if (!meshRef.current) return;

    // Gentle rotation
    meshRef.current.rotation.x = state.clock.getElapsedTime() * 0.1;
    meshRef.current.rotation.y = state.clock.getElapsedTime() * 0.15;

    // Pulse based on intensity
    const pulse = 1 + Math.sin(state.clock.getElapsedTime() * 2) * 0.1 * intensity;
    meshRef.current.scale.setScalar(pulse);
  });

  return (
    <Sphere ref={meshRef} args={[1.5, 64, 64]}>
      <MeshDistortMaterial
        color={new THREE.Color(rgb[0], rgb[1], rgb[2])}
        distort={0.3 + intensity * 0.2} // More distortion for stronger emotions
        speed={1 + intensity * 0.5}
        roughness={0.2}
        metalness={0.8}
      />
    </Sphere>
  );
};

// ============================================================================
// SVG FALLBACK (NO WEBGL)
// ============================================================================

interface SVGOrbFallbackProps {
  color: string;
  scale: number;
  className?: string;
}

const SVGOrbFallback: React.FC<SVGOrbFallbackProps> = ({ color, scale, className }) => {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <motion.div
        animate={{
          scale: [scale, scale * 1.1, scale],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="relative"
      >
        <svg width="200" height="200" viewBox="0 0 200 200">
          <defs>
            <radialGradient id="orbGradient">
              <stop offset="0%" stopColor={color} stopOpacity="1" />
              <stop offset="100%" stopColor={color} stopOpacity="0.6" />
            </radialGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="4" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <circle
            cx="100"
            cy="100"
            r="80"
            fill="url(#orbGradient)"
            filter="url(#glow)"
          />
        </svg>

        {/* Pulse rings */}
        <motion.div
          className="absolute inset-0 rounded-full border-2"
          style={{ borderColor: color }}
          animate={{
            scale: [1, 1.3],
            opacity: [0.8, 0],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeOut',
          }}
        />
      </motion.div>
    </div>
  );
};
