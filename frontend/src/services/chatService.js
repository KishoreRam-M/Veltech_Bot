/**
 * Chat API service — wraps WebSocket lifecycle and HTTP fallback.
 *
 * Consumers call connectWebSocket() to get a WS instance, then
 * sendMessage() to dispatch queries. The HTTP fallback is used
 * automatically when the socket is closed.
 */

const WS_PROTOCOL = location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL      = import.meta.env.VITE_WS_URL || `${WS_PROTOCOL}//${location.host}/ws/chat/`;

/**
 * Open a new WebSocket connection to the backend.
 *
 * @param {function} onSession    - Called with session_id string on first connect
 * @param {function} onMessage    - Called with response payload object
 * @param {function} onDisconnect - Called when socket closes (for reconnect)
 * @returns {WebSocket}
 */
export function connectWebSocket(onSession, onMessage, onDisconnect) {
  const ws = new WebSocket(WS_URL);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'session') {
      onSession(data.session_id);
    } else if (data.type === 'response' || data.type === 'done') {
      onMessage({ text: data.text || data.response, meta: data });
    } else if (data.type === 'error') {
      onMessage({ text: data.text || 'An error occurred.', meta: { intent: 'error' } });
    }
  };

  ws.onclose = onDisconnect;

  return ws;
}

/**
 * Send a chat query over WebSocket, or fall back to HTTP POST if closed.
 *
 * @param {WebSocket|null} ws        - Active WebSocket instance (or null)
 * @param {string}         query     - User message text
 * @param {string}         language  - Active language code
 * @param {string|null}    sessionId - Existing session ID for HTTP fallback
 * @returns {Promise<object|null>} HTTP response payload, or null if WS was used
 */
export async function sendMessage(ws, query, language, sessionId) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ query, language }));
    return null; // response arrives via ws.onmessage
  }

  // HTTP fallback when WebSocket is unavailable
  const API_URL = import.meta.env.VITE_API_URL || '/api';
  const response = await fetch(`${API_URL}/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, language, session_id: sessionId }),
  });

  if (!response.ok) throw new Error(`Chat HTTP ${response.status}`);
  return response.json();
}

/**
 * Upload a recorded audio blob and return the transcript string.
 *
 * @param {Blob}   audioBlob  - Recorded audio data
 * @param {string} mimeType   - Blob MIME type (determines file extension)
 * @returns {Promise<string>} Transcript text, or empty string on failure
 */
export async function transcribeAudio(audioBlob, mimeType) {
  let ext = 'webm';
  if (mimeType.includes('ogg')) ext = 'ogg';
  else if (mimeType.includes('mp4')) ext = 'mp4';

  const formData = new FormData();
  formData.append('file', audioBlob, `recording.${ext}`);

  const API_URL = import.meta.env.VITE_API_URL || '/api';
  const response = await fetch(`${API_URL}/stt/`, { method: 'POST', body: formData });
  if (!response.ok) throw new Error(`STT HTTP ${response.status}`);
  const data = await response.json();
  return data.transcript?.trim() ?? '';
}
