(() => {
    // ── DOM Elements ────────────────────────────────────────────────────────
    const DOM = {
        chatMessages: document.getElementById("chat-messages"),
        chatInput: document.getElementById("chat-input"),
        sendBtn: document.getElementById("send-btn"),
        voiceBtn: document.getElementById("voice-btn"),
        welcomeCard: document.getElementById("welcome-card"),
        welcomeTitle: document.getElementById("welcome-title"),
        welcomeText: document.getElementById("welcome-text"),
        statusDot: document.querySelector(".status-dot"),
        statusText: document.querySelector(".status-text"),
        langBadge: document.getElementById("lang-badge"),
        chatArea: document.getElementById("chat-area"),
        langOverlay: document.getElementById("lang-modal-overlay"),
        muteToggle: document.getElementById("mute-toggle"),
        muteIconOn: document.querySelector(".mute-icon-on"),
        muteIconOff: document.querySelector(".mute-icon-off"),
        toastContainer: document.getElementById("toast-container"),
    };

    // ── State ────────────────────────────────────────────────────────────────
    let ws = null;
    let sessionId = null;
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let currentStreamEl = null;
    let streamBuffer = "";
    let reconnectAttempts = 0;
    const MAX_RECONNECT = 5;
    const MAX_RECORDING_MS = 30000;
    let recordingTimeout = null;

    let selectedLanguage = null;
    let isMuted = false;

    // ── AudioContext — unlock on first user gesture ─────────────────────────
    let audioCtx = null;

    function ensureAudioContext() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === "suspended") {
            audioCtx.resume().catch(() => {});
        }
        return audioCtx;
    }

    // ── MIME Type Negotiation ────────────────────────────────────────────────
    function getSupportedMimeType() {
        const types = [
            "audio/webm;codecs=opus",
            "audio/webm",
            "audio/ogg;codecs=opus",
            "audio/ogg",
            "audio/mp4",
        ];
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        return "";
    }

    // ── Language Selection ───────────────────────────────────────────────────

    const WELCOME_DATA = {
        en: {
            title: "Your Dream Career Starts Here! 🚀",
            text: "I'm VelBot — your personal AI Admission Counselor. Let me show you why Vel Tech Multi Tech is the BEST choice for your future!",
        },
        ta: {
            title: "உங்கள் கனவு வாழ்க்கை இங்கே தொடங்குகிறது! 🚀",
            text: "நான் VelBot — உங்கள் AI Admission Counselor. Vel Tech Multi Tech உங்கள் எதிர்காலத்திற்கு ஏன் சிறந்த தேர்வு என்று காட்டுகிறேன்!",
        },
        tanglish: {
            title: "Unga Dream Future Starts Here da! 🚀🔥",
            text: "Naan VelBot — unga personal AI Admission Counselor. Vel Tech Multi Tech yenna oru vera level college nu naan solren, nee paaru!",
        },
    };

    document.querySelectorAll(".lang-choice-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            ensureAudioContext();

            selectedLanguage = btn.dataset.lang;
            DOM.langBadge.textContent = selectedLanguage === "ta" ? "TA" :
                                        selectedLanguage === "tanglish" ? "TG" : "EN";
            DOM.langOverlay.classList.add("hidden");

            const data = WELCOME_DATA[selectedLanguage] || WELCOME_DATA.en;
            DOM.welcomeTitle.textContent = data.title;
            DOM.welcomeText.textContent = data.text;

            DOM.chatInput.disabled = false;
            DOM.chatInput.focus();

            connectWS();
        });
    });

    DOM.chatInput.disabled = true;

    // ── Mute Toggle ──────────────────────────────────────────────────────────

    DOM.muteToggle.addEventListener("click", () => {
        isMuted = !isMuted;
        DOM.muteToggle.classList.toggle("muted", isMuted);
        DOM.muteIconOn.classList.toggle("hidden", isMuted);
        DOM.muteIconOff.classList.toggle("hidden", !isMuted);
        if (isMuted) {
            if (currentAudio) {
                currentAudio.pause();
                currentAudio = null;
            }
            ttsQueue = [];
            isSpeaking = false;
            showToast("🔇 Audio muted", "info");
        } else {
            showToast("🔊 Audio enabled", "info");
        }
    });

    // ── Toast Notifications ──────────────────────────────────────────────────

    function showToast(message, type = "info", duration = 3000) {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.textContent = message;
        DOM.toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.add("toast-exit");
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // ── WebSocket ────────────────────────────────────────────────────────────

    function connectWS() {
        const protocol = location.protocol === "https:" ? "wss:" : "ws:";
        ws = new WebSocket(`${protocol}//${location.host}/ws/chat`);

        ws.onopen = () => {
            reconnectAttempts = 0;
            setStatus("connected", "Online");
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWSMessage(data);
        };

        ws.onclose = () => {
            setStatus("error", "Disconnected");
            if (reconnectAttempts < MAX_RECONNECT) {
                reconnectAttempts++;
                setTimeout(connectWS, 2000 * reconnectAttempts);
            }
        };

        ws.onerror = () => {
            setStatus("error", "Error");
        };
    }

    function handleWSMessage(data) {
        switch (data.type) {
            case "session":
                sessionId = data.session_id;
                break;
            case "response":
                removeTypingIndicator();
                addBotMessage(data.text, data);
                autoSpeak(data.text, data.language);
                break;
            case "stream":
                if (!currentStreamEl) {
                    removeTypingIndicator();
                    currentStreamEl = createStreamBubble();
                    streamBuffer = "";
                }
                streamBuffer += data.token;
                updateStreamBubble(currentStreamEl, streamBuffer);
                scrollToBottom();
                break;
            case "done":
                if (currentStreamEl) {
                    finalizeStreamBubble(currentStreamEl, data.text || streamBuffer, data);
                    autoSpeak(data.text || streamBuffer, data.language);
                    currentStreamEl = null;
                    streamBuffer = "";
                } else {
                    removeTypingIndicator();
                    addBotMessage(data.text, data);
                    autoSpeak(data.text, data.language);
                }
                break;
            case "error":
                removeTypingIndicator();
                addBotMessage(data.text || "Something went wrong. Please try again.", { intent: "error", cache: "none" });
                break;
        }
    }

    function setStatus(state, text) {
        DOM.statusDot.className = "status-dot " + state;
        DOM.statusText.textContent = text;
    }

    // ── TTS — Auto speak each bot response ───────────────────────────────────

    let currentAudio = null;
    let ttsQueue = [];
    let isSpeaking = false;

    function processTtsQueue() {
        if (ttsQueue.length > 0) {
            const next = ttsQueue.shift();
            isSpeaking = true;
            playTTS(next.text, next.language);
        } else {
            isSpeaking = false;
        }
    }

    async function playTTS(text, language) {
        const clean = text.replace(/[*_#"`~]/g, "").replace(/[🎓🌟🚀💪✨🎯🏆💰🔥👋🙏📚📝💼🏠🏛️⭐🎉⚡🧠🔇🔊₹━•\-]/g, "").trim();
        if (!clean) {
            processTtsQueue();
            return;
        }

        const langParam = language || selectedLanguage || "en";

        try {
            const res = await fetch("/api/tts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: clean, lang: langParam }),
            });

            if (!res.ok) {
                console.log("TTS generation failed:", res.status);
                processTtsQueue();
                return;
            }

            const data = await res.json();
            if (!data.audio_url) {
                processTtsQueue();
                return;
            }

            if (currentAudio) {
                currentAudio.pause();
                currentAudio.removeAttribute("src");
                currentAudio.load();
                currentAudio = null;
            }

            ensureAudioContext();

            currentAudio = new Audio(data.audio_url);
            currentAudio.addEventListener("ended", () => {
                currentAudio = null;
                processTtsQueue();
            });
            currentAudio.addEventListener("error", (e) => {
                console.log("Audio playback error:", e);
                currentAudio = null;
                processTtsQueue();
            });

            try {
                await currentAudio.play();
            } catch (playErr) {
                console.log("Autoplay blocked:", playErr.message);
                currentAudio = null;
                processTtsQueue();
            }
        } catch (e) {
            console.log("TTS error:", e);
            processTtsQueue();
        }
    }

    function splitSentences(text) {
        return text.split(/(?<=[.?!])\s+|\n+/).filter(s => s.trim().length > 0);
    }

    function autoSpeak(text, language) {
        if (isMuted || !text) return;
        
        const sentences = splitSentences(text);
        
        sentences.forEach(sentence => {
            let sentenceLang = language;
            if (language === "tanglish") {
                sentenceLang = /[\u0B80-\u0BFF]/.test(sentence) ? "ta" : "en";
            }
            ttsQueue.push({ text: sentence, language: sentenceLang });
        });
        
        if (!isSpeaking) {
            processTtsQueue();
        }
    }

    function replaySpeak(text, language) {
        if (!text) return;
        ensureAudioContext();
        ttsQueue = [];
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.removeAttribute("src");
            currentAudio.load();
            currentAudio = null;
        }
        isSpeaking = false;
        autoSpeak(text, language);
    }

    // ── Send Message ──────────────────────────────────────────────────────────

    function sendMessage(text) {
        if (!text.trim()) return;
        if (!selectedLanguage) {
            showToast("Please select a language first! 🌐", "warning");
            return;
        }
        ensureAudioContext();
        DOM.welcomeCard?.classList.add("hidden");
        addUserMessage(text);
        showTypingIndicator();

        const isTamil = /[\u0B80-\u0BFF]/.test(text);
        if (isTamil) DOM.langBadge.textContent = "TA";

        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                query: text,
                language: selectedLanguage,
            }));
        } else {
            fetchChat(text);
        }
        DOM.chatInput.value = "";
        DOM.chatInput.focus();
    }

    async function fetchChat(query) {
        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query,
                    session_id: sessionId || "anon",
                    language: selectedLanguage,
                }),
            });
            const data = await res.json();
            removeTypingIndicator();
            if (data.session_id) sessionId = data.session_id;
            addBotMessage(data.response, data);
            autoSpeak(data.response, data.language);
        } catch (e) {
            removeTypingIndicator();
            addBotMessage("Unable to connect to the server. Please try again later.", { intent: "error", cache: "none" });
        }
    }

    // ── Message Rendering ─────────────────────────────────────────────────────

    function addUserMessage(text) {
        const msg = document.createElement("div");
        msg.className = "message user";
        msg.innerHTML = `
            <div class="msg-avatar">👤</div>
            <div class="msg-content"><p>${escapeHTML(text)}</p></div>
        `;
        DOM.chatMessages.appendChild(msg);
        scrollToBottom();
    }

    function addBotMessage(text, meta = {}) {
        const msg = document.createElement("div");
        msg.className = "message bot";
        const metaHTML = buildMetaHTML(meta);
        const speakerBtn = buildSpeakerBtn(text, meta.language);
        msg.innerHTML = `
            <div class="msg-avatar">🤖</div>
            <div class="msg-content">
                ${formatMarkdown(text)}
                <div class="msg-footer">
                    ${metaHTML}
                    ${speakerBtn}
                </div>
            </div>
        `;
        DOM.chatMessages.appendChild(msg);

        const spkBtn = msg.querySelector(".msg-speaker-btn");
        if (spkBtn) {
            spkBtn.addEventListener("click", () => {
                replaySpeak(text, meta.language || selectedLanguage);
            });
        }

        scrollToBottom();
    }

    function buildSpeakerBtn(text, language) {
        return `<button class="msg-speaker-btn" title="Replay audio" data-lang="${language || 'en'}">🔊</button>`;
    }

    function createStreamBubble() {
        const msg = document.createElement("div");
        msg.className = "message bot";
        msg.innerHTML = `
            <div class="msg-avatar">🤖</div>
            <div class="msg-content"><p class="stream-text"></p></div>
        `;
        DOM.chatMessages.appendChild(msg);
        return msg;
    }

    function updateStreamBubble(el, text) {
        const streamText = el.querySelector(".stream-text");
        if (streamText) {
            streamText.innerHTML = formatMarkdown(text);
        }
    }

    function finalizeStreamBubble(el, finalText, meta = {}) {
        const content = el.querySelector(".msg-content");
        const metaHTML = buildMetaHTML(meta);
        const speakerBtn = buildSpeakerBtn(finalText, meta.language);
        content.innerHTML = `${formatMarkdown(finalText)}<div class="msg-footer">${metaHTML}${speakerBtn}</div>`;

        const spkBtn = content.querySelector(".msg-speaker-btn");
        if (spkBtn) {
            spkBtn.addEventListener("click", () => {
                replaySpeak(finalText, meta.language || selectedLanguage);
            });
        }
    }

    function buildMetaHTML(meta) {
        if (!meta || !meta.intent) return "";
        let cacheClass = "none";
        let cacheLabel = "Generated";
        if (meta.cache === "L1") { cacheClass = "l1"; cacheLabel = "⚡ Cached"; }
        else if (meta.cache === "L2") { cacheClass = "l2"; cacheLabel = "🧠 Semantic"; }
        else if (meta.cache === "agent") { cacheClass = "agent"; cacheLabel = "🤖 Agent"; }
        const ms = meta.ms ? `${meta.ms}ms` : "";
        const strategyBadge = meta.strategy ?
            `<span class="strategy-badge">${meta.strategy.replace(/_/g, " ")}</span>` : "";
        return `<div class="msg-meta">
            <span class="cache-badge ${cacheClass}">${cacheLabel}</span>
            ${strategyBadge}
            ${ms ? `<span>${ms}</span>` : ""}
        </div>`;
    }

    // ── Typing Indicator ──────────────────────────────────────────────────────

    function showTypingIndicator() {
        removeTypingIndicator();
        const el = document.createElement("div");
        el.className = "typing-indicator";
        el.id = "typing-indicator";
        el.innerHTML = `
            <div class="msg-avatar" style="background:linear-gradient(135deg,#6366f1,#8b5cf6)">🤖</div>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        DOM.chatMessages.appendChild(el);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        document.getElementById("typing-indicator")?.remove();
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            DOM.chatArea.scrollTop = DOM.chatArea.scrollHeight;
        });
    }

    // ── Markdown Formatting ───────────────────────────────────────────────────

    function formatMarkdown(text) {
        if (!text) return "<p></p>";
        let html = escapeHTML(text);
        html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
        html = html.replace(/`(.*?)`/g, "<code>$1</code>");
        const lines = html.split("\n");
        let result = "";
        let inList = false;
        let listType = "ul";
        for (const line of lines) {
            const trimmed = line.trim();
            if (/^[-•]\s/.test(trimmed)) {
                if (!inList) { result += "<ul>"; inList = true; listType = "ul"; }
                result += `<li>${trimmed.replace(/^[-•]\s/, "")}</li>`;
            } else if (/^\d+\.\s/.test(trimmed)) {
                if (!inList) { result += "<ol>"; inList = true; listType = "ol"; }
                result += `<li>${trimmed.replace(/^\d+\.\s/, "")}</li>`;
            } else {
                if (inList) { result += listType === "ul" ? "</ul>" : "</ol>"; inList = false; }
                if (trimmed) result += `<p>${trimmed}</p>`;
            }
        }
        if (inList) result += listType === "ul" ? "</ul>" : "</ol>";
        return result || "<p></p>";
    }

    function escapeHTML(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    // ── Voice Input — MediaRecorder with MIME negotiation ─────────────────────

    function initVoice() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            DOM.voiceBtn.title = "Voice not supported in this browser";
            DOM.voiceBtn.style.opacity = "0.3";
            DOM.voiceBtn.style.cursor = "default";
            return;
        }
    }

    function showVoiceWarning(msg = null) {
        msg = msg || "Voice input issue/network error. Please type your question! ✏️";
        showToast(msg, "warning", 4000);
        DOM.chatInput.focus();
    }

    function stopRecordingCleanup(stream) {
        if (recordingTimeout) {
            clearTimeout(recordingTimeout);
            recordingTimeout = null;
        }
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        isRecording = false;
        DOM.voiceBtn.classList.remove("recording");
    }

    async function toggleRecording() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showVoiceWarning("Browser doesn't support audio recording.");
            return;
        }
        if (!selectedLanguage) {
            showToast("Please select a language first! 🌐", "warning");
            return;
        }

        ensureAudioContext();

        if (isRecording) {
            if (mediaRecorder && mediaRecorder.state === "recording") {
                mediaRecorder.stop();
            }
            isRecording = false;
            DOM.voiceBtn.classList.remove("recording");
            DOM.statusText.textContent = "Processing Audio...";
        } else {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        sampleRate: 16000,
                    },
                });

                const mimeType = getSupportedMimeType();
                const recorderOptions = mimeType ? { mimeType } : {};

                mediaRecorder = new MediaRecorder(stream, recorderOptions);
                audioChunks = [];

                mediaRecorder.addEventListener("dataavailable", event => {
                    if (event.data && event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                });

                mediaRecorder.addEventListener("stop", async () => {
                    stopRecordingCleanup(stream);

                    if (audioChunks.length === 0) {
                        showVoiceWarning("No audio captured. Try again!");
                        DOM.statusText.textContent = "Online";
                        return;
                    }

                    const actualMime = mediaRecorder.mimeType || mimeType || "audio/webm";
                    const audioBlob = new Blob(audioChunks, { type: actualMime });

                    if (audioBlob.size < 1000) {
                        showVoiceWarning("Recording too short. Hold the mic button longer!");
                        DOM.statusText.textContent = "Online";
                        return;
                    }

                    DOM.statusDot.className = "status-dot connected";
                    DOM.statusText.textContent = "Transcribing...";

                    const ext = actualMime.includes("ogg") ? ".ogg" :
                                actualMime.includes("mp4") ? ".mp4" : ".webm";

                    const formData = new FormData();
                    formData.append("file", audioBlob, `recording${ext}`);

                    try {
                        const res = await fetch("/api/stt", {
                            method: "POST",
                            body: formData,
                        });
                        if (!res.ok) throw new Error("STT failed");
                        const data = await res.json();
                        if (data.transcript && data.transcript.trim()) {
                            sendMessage(data.transcript.trim());
                        } else {
                            showVoiceWarning("Couldn't hear clearly. Try again! 🎤");
                        }
                    } catch (e) {
                        showVoiceWarning();
                    } finally {
                        DOM.statusDot.className = "status-dot connected";
                        DOM.statusText.textContent = "Online";
                    }
                });

                mediaRecorder.addEventListener("error", () => {
                    stopRecordingCleanup(stream);
                    showVoiceWarning("Recording error. Please try again.");
                    DOM.statusText.textContent = "Online";
                });

                mediaRecorder.start(250);
                isRecording = true;
                DOM.voiceBtn.classList.add("recording");
                DOM.statusDot.className = "status-dot connected";
                DOM.statusText.textContent = "Recording...";

                recordingTimeout = setTimeout(() => {
                    if (isRecording && mediaRecorder && mediaRecorder.state === "recording") {
                        mediaRecorder.stop();
                        showToast("Recording stopped (30s limit)", "info");
                    }
                }, MAX_RECORDING_MS);

            } catch (e) {
                if (e.name === "NotAllowedError" || e.name === "PermissionDeniedError") {
                    showVoiceWarning("Microphone access denied. Please allow mic permissions in your browser settings.");
                } else if (e.name === "NotFoundError") {
                    showVoiceWarning("No microphone found. Please connect a mic.");
                } else {
                    showVoiceWarning("Microphone error: " + e.message);
                }
            }
        }
    }

    // ── Event Listeners ───────────────────────────────────────────────────────

    DOM.sendBtn.addEventListener("click", () => sendMessage(DOM.chatInput.value));
    DOM.chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage(DOM.chatInput.value);
        }
    });
    DOM.voiceBtn.addEventListener("click", toggleRecording);

    document.querySelectorAll(".quick-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            ensureAudioContext();
            sendMessage(btn.dataset.query);
        });
    });

    DOM.langBadge.addEventListener("click", () => {
        DOM.langOverlay.classList.remove("hidden");
    });

    initVoice();
})();
