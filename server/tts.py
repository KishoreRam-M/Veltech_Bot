import threading

def speak_async(text: str) -> None:
    def _speak():
        try:
            import pyttsx3
            eng = pyttsx3.init()
            eng.setProperty("rate", 165)
            eng.setProperty("volume", 0.9)
            voices = eng.getProperty("voices")
            if voices:
                eng.setProperty("voice", voices[0].id)
            eng.say(text)
            eng.runAndWait()
        except Exception as e:
            print(f"[TTS] Error: {e}")
    t = threading.Thread(target=_speak, daemon=True)
    t.start()
