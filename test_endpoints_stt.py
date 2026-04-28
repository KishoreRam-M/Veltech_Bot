import requests

try:
    with open("test_pitch.mp3", "rb") as f:
        res = requests.post("http://127.0.0.1:8000/api/stt", files={"file": ("test.mp3", f, "audio/mpeg")})
        print("STT:", res.status_code, res.text)
except Exception as e:
    print("STT test error:", e)
