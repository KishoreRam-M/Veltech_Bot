import asyncio
import edge_tts

async def test():
    try:
        c = edge_tts.Communicate("Hello world", "en-IN-NeerjaExpressiveNeural", rate="+0%", pitch="+0Hz")
        await c.save("test_pitch.mp3")
        print("Success")
    except Exception as e:
        print("Failed:", e)

asyncio.run(test())
