# VelBot Frontend

React + Vite single-page application for VelBot AI Admissions Counselor.

## Component Tree

```
App.jsx                     ← Root orchestrator (state, WS, audio)
├── LanguageModal.jsx        ← Language picker shown before chat starts
├── ChatHeader.jsx           ← Header bar (status, mute, language badge)
├── MessageList.jsx          ← Chat history + welcome card + typing indicator
└── ChatInput.jsx            ← Text input + voice toggle + send button

services/
├── chatService.js           ← WebSocket + HTTP chat + STT API calls
└── audioService.js          ← AudioContext, TTS playback queue, speech splitter
```

## Setup

```bash
npm install
npm run dev      # development server (Vite HMR, proxies API to :8000)
npm run build    # production build → dist/ (served by Django)
```

## Environment Variables

Create `frontend/.env.local` (Vite reads it automatically):

```
VITE_API_BASE=http://localhost:8000   # override if backend is on a different port
```

## Props Reference

### `<LanguageModal onSelect(lang) />`
| Prop | Type | Description |
|------|------|-------------|
| `onSelect` | `(lang: 'en'|'ta'|'tanglish') => void` | Called when user picks a language |

### `<ChatHeader status isMuted onMute language onLangReset />`
| Prop | Type | Description |
|------|------|-------------|
| `status` | `{ state: string, text: string }` | Connection status for the indicator dot |
| `isMuted` | `boolean` | Current mute state |
| `onMute` | `() => void` | Toggle mute |
| `language` | `string` | Active language code |
| `onLangReset` | `() => void` | Reset language to show the picker again |

### `<MessageList messages isTyping language onSend onReplay welcomeData chatEndRef />`
| Prop | Type | Description |
|------|------|-------------|
| `messages` | `Array<{role, text, meta}>` | Full chat history |
| `isTyping` | `boolean` | Show/hide the typing indicator |
| `language` | `string` | Active language (used for replay) |
| `onSend` | `(text: string) => void` | Send a quick-action prompt |
| `onReplay` | `(text, lang) => void` | Replay TTS for a message |
| `welcomeData` | `{ title, text }` | Welcome card content |
| `chatEndRef` | `React.Ref` | Ref for auto-scroll anchor |

### `<ChatInput value onChange onSend onVoice isRecording disabled />`
| Prop | Type | Description |
|------|------|-------------|
| `value` | `string` | Controlled input value |
| `onChange` | `(v: string) => void` | Input change handler |
| `onSend` | `() => void` | Submit current input |
| `onVoice` | `() => void` | Toggle voice recording |
| `isRecording` | `boolean` | Recording state for button styling |
| `disabled` | `boolean` | Disabled until language is selected |
