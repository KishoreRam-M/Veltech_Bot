import requests
import sys

try:
    res = requests.post("http://127.0.0.1:8000/api/tts", json={"text": "Hello world", "lang": "en"})
    print("TTS:", res.status_code, res.text)
except Exception as e:
    print("TTS error:", e)
