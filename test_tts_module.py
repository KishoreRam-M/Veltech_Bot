import asyncio
from server.tts import generate_tts_audio

async def test():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    res = await generate_tts_audio("Hello world", "en")
    print("Result:", res)

asyncio.run(test())
