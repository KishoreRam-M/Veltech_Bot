import edge_tts
import asyncio
import os

async def test():
    os.makedirs("data/audio", exist_ok=True)
    try:
        c = edge_tts.Communicate("Hello this is a test", "en-IN-NeerjaExpressiveNeural", rate="+0%")
        await c.save("data/audio/test_tts.mp3")
        size = os.path.getsize("data/audio/test_tts.mp3")
        print(f"[TTS-TEST] NeerjaExpressive OK, size={size}")
    except Exception as e:
        print(f"[TTS-TEST] NeerjaExpressive FAILED: {e}")
    
    try:
        c2 = edge_tts.Communicate("Hello this is a test", "en-IN-NeerjaNeural", rate="+0%")
        await c2.save("data/audio/test_tts2.mp3")
        size2 = os.path.getsize("data/audio/test_tts2.mp3")
        print(f"[TTS-TEST] NeerjaNeural OK, size={size2}")
    except Exception as e2:
        print(f"[TTS-TEST] NeerjaNeural FAILED: {e2}")

    try:
        c3 = edge_tts.Communicate("Hello this is a test", "ta-IN-PallaviNeural", rate="+0%")
        await c3.save("data/audio/test_tts3.mp3")
        size3 = os.path.getsize("data/audio/test_tts3.mp3")
        print(f"[TTS-TEST] PallaviNeural OK, size={size3}")
    except Exception as e3:
        print(f"[TTS-TEST] PallaviNeural FAILED: {e3}")

asyncio.run(test())
