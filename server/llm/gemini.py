import asyncio
import time
from google import genai
from server.config import GEMINI_API_KEY, GEMINI_MODEL, TEMPERATURE, MAX_OUTPUT_TOKENS, SYSTEM_PROMPT, GEMINI_MAX_RETRIES, GEMINI_RETRY_DELAY
from server.cache.l4_translation import l4_cache
from server.pipeline.language import is_tamil

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

async def generate_response(query: str, chunks: list[dict]) -> str:
    client = _get_client()
    context = "\n\n".join([
        f"[{chunk.get('id', 'unknown')}] {chunk['text']}"
        for chunk in chunks
    ])
    prompt = SYSTEM_PROMPT.format(context=context, query=query)
    last_error = None
    for attempt in range(GEMINI_MAX_RETRIES):
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=GEMINI_MODEL,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                ),
            )
            return response.text
        except Exception as e:
            last_error = e
            error_name = type(e).__name__
            if "ResourceExhausted" in error_name or "ServiceUnavailable" in error_name:
                wait = GEMINI_RETRY_DELAY * (2 ** attempt)
                print(f"[GEMINI] {error_name}, retry {attempt+1}/{GEMINI_MAX_RETRIES} in {wait}s")
                await asyncio.sleep(wait)
            else:
                break
    print(f"[GEMINI] All retries failed: {last_error}. Switching to FLAN-T5 fallback.")
    try:
        from server.llm.fallback_llm import fallback_generate
        return await fallback_generate(query, chunks)
    except Exception as fb_err:
        return f"I'm having trouble connecting right now. Please try again or contact 044-2684 0070. (Error: {fb_err})"

async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    lang_pair = f"{source_lang}→{target_lang}"
    cached = await l4_cache.get(text, lang_pair)
    if cached:
        return cached
    client = _get_client()
    lang_names = {"en": "English", "ta": "Tamil"}
    prompt = f"""Translate the following text from {lang_names.get(source_lang, source_lang)} to {lang_names.get(target_lang, target_lang)}.
Preserve all proper nouns, course names (B.Tech, M.Tech, etc.), numbers, URLs, and acronyms exactly as-is.
Only output the translation, nothing else.

Text: {text}"""
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=GEMINI_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            ),
        )
        result = response.text
        await l4_cache.put(text, lang_pair, result)
        return result
    except Exception:
        return text

async def generate_streaming(query: str, chunks: list[dict]):
    client = _get_client()
    context = "\n\n".join([
        f"[{chunk.get('id', 'unknown')}] {chunk['text']}"
        for chunk in chunks
    ])
    prompt = SYSTEM_PROMPT.format(context=context, query=query)

    def _sync_stream():
        return list(client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            ),
        ))

    try:
        chunks_list = await asyncio.to_thread(_sync_stream)
        for chunk in chunks_list:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        print(f"[GEMINI] Streaming failed: {e}. Using fallback.")
        try:
            from server.llm.fallback_llm import fallback_generate
            result = await fallback_generate(query, chunks)
            yield result
        except Exception as fb_err:
            yield f"I'm having trouble right now. Please contact 044-2684 0070. (Error: {fb_err})"
