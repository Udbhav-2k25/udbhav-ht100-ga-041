/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Emotion colors
        joy: '#FCD34D',
        sadness: '#60A5FA',
        anger: '#F87171',
        fear: '#A78BFA',
        surprise: '#FB923C',
        stress: '#F59E0B',
        tension: '#EC4899',
        disgust: '#10B981',
        anticipation: '#3B82F6',
        neutral: '#9CA3AF',
        
        // Brand colors (subtle, professional)
        empathy: {
          50: '#F0F4FF',
          100: '#E0EAFF',
          200: '#C7D7FE',
          300: '#A4BCFD',
          400: '#8B9FFC',
          500: '#6B7CF9',
          600: '#5B5FEE',
          700: '#4C4BD9',
          800: '#3E3CB0',
          900: '#353589',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
      },
    },
  },
  plugins: [],
}
