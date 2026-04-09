(() => {
    const DOM = {
        chatMessages: document.getElementById("chat-messages"),
        chatInput: document.getElementById("chat-input"),
        sendBtn: document.getElementById("send-btn"),
        voiceBtn: document.getElementById("voice-btn"),
        welcomeCard: document.getElementById("welcome-card"),
        statusDot: document.querySelector(".status-dot"),
        statusText: document.querySelector(".status-text"),
        langBadge: document.getElementById("lang-badge"),
        chatArea: document.getElementById("chat-area"),
    };

    let ws = null;
    let sessionId = null;
    let isRecording = false;
    let recognition = null;
    let currentStreamEl = null;
    let streamBuffer = "";
    let reconnectAttempts = 0;
    const MAX_RECONNECT = 5;

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
                    currentStreamEl = null;
                    streamBuffer = "";
                } else {
                    removeTypingIndicator();
                    addBotMessage(data.text, data);
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

    function sendMessage(text) {
        if (!text.trim()) return;
        DOM.welcomeCard?.classList.add("hidden");
        addUserMessage(text);
        showTypingIndicator();
        const isTamil = /[\u0B80-\u0BFF]/.test(text);
        DOM.langBadge.textContent = isTamil ? "TA" : "EN";
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ query: text }));
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
                body: JSON.stringify({ query, session_id: sessionId || "anon" }),
            });
            const data = await res.json();
            removeTypingIndicator();
            if (data.session_id) sessionId = data.session_id;
            addBotMessage(data.response, data);
        } catch (e) {
            removeTypingIndicator();
            addBotMessage("Unable to connect to the server. Please try again later.", { intent: "error", cache: "none" });
        }
    }

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
        msg.innerHTML = `
            <div class="msg-avatar">🤖</div>
            <div class="msg-content">
                ${formatMarkdown(text)}
                ${metaHTML}
            </div>
        `;
        DOM.chatMessages.appendChild(msg);
        scrollToBottom();
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
        content.innerHTML = `${formatMarkdown(finalText)}${metaHTML}`;
    }

    function buildMetaHTML(meta) {
        if (!meta || !meta.intent) return "";
        let cacheClass = "none";
        let cacheLabel = "Generated";
        if (meta.cache === "L1") { cacheClass = "l1"; cacheLabel = "⚡ Cached"; }
        else if (meta.cache === "L2") { cacheClass = "l2"; cacheLabel = "🧠 Semantic"; }
        const ms = meta.ms ? `${meta.ms}ms` : "";
        return `<div class="msg-meta">
            <span class="cache-badge ${cacheClass}">${cacheLabel}</span>
            ${ms ? `<span>${ms}</span>` : ""}
        </div>`;
    }

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

    function formatMarkdown(text) {
        if (!text) return "<p></p>";
        let html = escapeHTML(text);
        html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
        html = html.replace(/`(.*?)`/g, "<code>$1</code>");
        const lines = html.split("\n");
        let result = "";
        let inList = false;
        for (const line of lines) {
            const trimmed = line.trim();
            if (/^[-•]\s/.test(trimmed)) {
                if (!inList) { result += "<ul>"; inList = true; }
                result += `<li>${trimmed.replace(/^[-•]\s/, "")}</li>`;
            } else if (/^\d+\.\s/.test(trimmed)) {
                if (!inList) { result += "<ol>"; inList = true; }
                result += `<li>${trimmed.replace(/^\d+\.\s/, "")}</li>`;
            } else {
                if (inList) { result += inList ? "</ul>" : "</ol>"; inList = false; }
                if (trimmed) result += `<p>${trimmed}</p>`;
            }
        }
        if (inList) result += "</ul>";
        return result || "<p></p>";
    }

    function escapeHTML(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function initVoice() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            DOM.voiceBtn.title = "Voice not supported in this browser";
            DOM.voiceBtn.style.opacity = "0.3";
            return;
        }
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "en-IN";

        recognition.onresult = (event) => {
            const text = event.results[0][0].transcript;
            DOM.chatInput.value = text;
            sendMessage(text);
        };

        recognition.onend = () => {
            isRecording = false;
            DOM.voiceBtn.classList.remove("recording");
        };

        recognition.onerror = () => {
            isRecording = false;
            DOM.voiceBtn.classList.remove("recording");
        };
    }

    function toggleRecording() {
        if (!recognition) return;
        if (isRecording) {
            recognition.stop();
            isRecording = false;
            DOM.voiceBtn.classList.remove("recording");
        } else {
            const isTamil = DOM.langBadge.textContent === "TA";
            recognition.lang = isTamil ? "ta-IN" : "en-IN";
            recognition.start();
            isRecording = true;
            DOM.voiceBtn.classList.add("recording");
        }
    }

    function speakText(text) {
        if (!window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        const isTamil = /[\u0B80-\u0BFF]/.test(text);
        utterance.lang = isTamil ? "ta-IN" : "en-IN";
        utterance.rate = 0.95;
        window.speechSynthesis.speak(utterance);
    }

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
            sendMessage(btn.dataset.query);
        });
    });

    initVoice();
    connectWS();
})();
