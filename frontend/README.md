# 🧠 The Empathy Engine — Frontend

**Professional, production-ready React + TypeScript + Vite frontend** for emotional intelligence chat analysis.

## ✨ Features

### 🎨 Components
- **Chat**: Real-time conversation with emotion badges, intensity bars, and safety escalation
- **Timeline**: Interactive emotion intensity graph with smoothing controls and peak detection
- **EmpathyOrb**: 3D sphere (React Three Fiber) that pulses and changes color based on emotions
- **SummaryCard**: Conversation summary with JSON/PNG export

### 🔧 Technical Highlights
- **Typed API wrapper** with mock mode fallback
- **React Query** for data fetching/caching
- **Framer Motion** for smooth animations
- **Tailwind CSS** with custom emotion color palette
- **WebGL fallback** to SVG when 3D not supported
- **Accessible** and responsive design

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env
# VITE_API_BASE_URL=http://localhost:8000
# VITE_MOCK_MODE=false
```

### 3. Run Development Server

```bash
npm run dev
```

Frontend runs at: **http://localhost:3000**

---

## 🔌 Backend Integration

### API Endpoints Used

The frontend integrates with these backend endpoints:

#### `POST /analyze`
Analyzes conversation for emotion probabilities and timeline.

**Request:**
```json
{
  "session_id": "demo-1",
  "messages": [
    {
      "id": 1,
      "speaker": "user",
      "text": "I can't believe this happened.",
      "ts": "2025-11-21T10:00:00Z"
    }
  ],
  "smoothing_window": 3
}
```

**Response:**
```json
{
  "messages": [
    {
      "id": 1,
      "speaker": "user",
      "text": "I can't believe this happened.",
      "ts": "2025-11-21T10:00:00Z",
      "probs": {
        "joy": 0.05,
        "sadness": 0.65,
        "anger": 0.20,
        "fear": 0.05,
        "surprise": 0.03,
        "neutral": 0.02
      },
      "dominant": "sadness",
      "entropy": 0.45,
      "confidence": "medium"
    }
  ],
  "timeline": {
    "raw": [0.65],
    "smoothed": [0.65],
    "peaks": [0]
  },
  "session_confidence": "medium"
}
```

#### `POST /chat`
Gets empathetic reply suggestions.

**Request:**
```json
{
  "session_id": "demo-1",
  "message": "I'm so frustrated!"
}
```

**Response:**
```json
{
  "reply": "I'm sorry that happened — that sounds frustrating. Want to walk through it?",
  "emotion": "anger",
  "confidence": "high",
  "safety_flag": false
}
```

#### `POST /summary`
Generates conversation summary.

**Request:**
```json
{
  "session_id": "demo-1"
}
```

**Response:**
```json
{
  "summary": {
    "dominant_emotion": "sadness",
    "confidence": "high",
    "style": "reflective and processing disappointment",
    "highlights": [
      "Initial frustration about project rejection",
      "Self-doubt emerged",
      "Shift to constructive mindset"
    ],
    "advice": "Your emotional journey shows resilience."
  }
}
```

---

## 🛠️ Configuration

### Environment Variables

Create `.env` file:

```bash
# Backend API base URL
VITE_API_BASE_URL=http://localhost:8000

# Enable mock mode (true = no backend required)
VITE_MOCK_MODE=false
```

### Mock Mode

When `VITE_MOCK_MODE=true` or backend is unreachable:
- Uses rule-based emotion classification
- Simulates timeline data locally
- Returns demo replies and summaries

Perfect for:
- Frontend development without backend
- Demos and presentations
- Testing UI flows

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api.ts                 # Typed API wrapper with mock mode
│   ├── App.tsx                # Main app orchestration
│   ├── main.tsx               # React entry point
│   ├── index.css              # Tailwind + custom styles
│   ├── components/
│   │   ├── Chat.tsx           # Chat UI with emotion badges
│   │   ├── Timeline.tsx       # Interactive emotion timeline
│   │   ├── EmpathyOrb.tsx     # 3D emotion orb
│   │   └── SummaryCard.tsx    # Summary with export
│   └── hooks/
│       └── useOrbColor.ts     # Emotion → color/scale mapping
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

---

## 🎨 Design System

### Emotion Colors

Defined in `tailwind.config.js`:

```javascript
joy: '#FCD34D',      // Yellow
sadness: '#60A5FA',  // Blue
anger: '#F87171',    // Red
fear: '#A78BFA',     // Purple
surprise: '#FB923C', // Orange
neutral: '#9CA3AF',  // Gray
```

### Brand Colors

```javascript
empathy: {
  50: '#F0F4FF',
  500: '#6B7CF9',  // Primary
  700: '#4C4BD9',
}
```

---

## 🧪 Testing

Run tests:

```bash
npm run test
```

---

## 📦 Build for Production

```bash
# Build optimized bundle
npm run build

# Preview production build
npm run preview
```

Output in `dist/` directory.

---

## 🔒 Security & Privacy

- **No PII storage**: All data stays in-memory (session-based)
- **Safety detection**: Escalates self-harm keywords with crisis resources
- **No tracking**: No analytics or third-party scripts
- **HTTPS ready**: Configure reverse proxy (Nginx, Caddy)

---

## 🚧 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

Set environment variables in Vercel dashboard:
- `VITE_API_BASE_URL` → Your backend URL

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

---

## 🐛 Troubleshooting

### "Cannot connect to backend"
- Check `VITE_API_BASE_URL` in `.env`
- Ensure backend is running on http://localhost:8000
- Enable mock mode: `VITE_MOCK_MODE=true`

### WebGL not working
- EmpathyOrb auto-falls back to SVG
- Check browser WebGL support: https://get.webgl.org/

### Timeline not rendering
- Ensure messages array is not empty
- Check browser console for Recharts errors

---

## 🎯 Features by Component

### Chat.tsx
- ✅ Per-message emotion badges with intensity bars
- ✅ Suggested reply buttons from `/chat` endpoint
- ✅ Safety flag UI with crisis resources
- ✅ Auto-scroll to focused message (from timeline peaks)
- ✅ Optimistic UI updates

### Timeline.tsx
- ✅ Raw vs smoothed toggle
- ✅ Smoothing slider (1-7 window)
- ✅ Peak markers with click-to-focus
- ✅ Hover tooltips with message preview
- ✅ Color-coded by emotion

### EmpathyOrb.tsx
- ✅ 3D sphere with React Three Fiber
- ✅ Color changes based on dominant emotion
- ✅ Pulse animation based on intensity
- ✅ SVG fallback when WebGL unavailable
- ✅ Emotion label overlay

### SummaryCard.tsx
- ✅ Dominant emotion with emoji
- ✅ Confidence badges (high/medium/low)
- ✅ Key highlights with numbering
- ✅ Advice section
- ✅ JSON export
- ✅ PNG export (html2canvas)
- ✅ Re-analyze button

---

## 📚 Tech Stack

| Category | Library | Purpose |
|----------|---------|---------|
| Framework | React 18 | UI library |
| Language | TypeScript | Type safety |
| Build | Vite | Fast dev server |
| Styling | Tailwind CSS | Utility-first CSS |
| 3D | React Three Fiber | WebGL rendering |
| Animation | Framer Motion | Smooth transitions |
| Charts | Recharts | Timeline visualization |
| HTTP | Axios | API requests |
| State | React Query | Data fetching/caching |
| Icons | Lucide React | Icon library |

---

## 🤝 Integration Checklist

- [x] Typed API wrapper matching backend schema exactly
- [x] Mock mode for development without backend
- [x] Environment-based backend URL configuration
- [x] Error handling with friendly messages
- [x] Loading states for all async operations
- [x] Safety flag detection and escalation
- [x] Timeline smoothing controls
- [x] Peak detection visualization
- [x] Export functionality (JSON/PNG)
- [x] WebGL fallback for accessibility
- [x] Responsive design (mobile-friendly)

---

## 📄 License

MIT License — Free for hackathon and educational use.

---

## 🙏 Credits

Built with:
- **Groq API** (free llama-3.1 inference)
- **React Three Fiber** by Poimandres
- **Tailwind CSS** by Tailwind Labs
- **Framer Motion** by Framer

---

**Built with ❤️ for KMEC Hack 2025**

For questions or issues, check the main README at the repository root.
