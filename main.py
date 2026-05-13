"""Pyodide-side chat backend.

Runs inside the browser via Pyodide (WASM). Modern Pyodide (>= 0.27.2) ships
`openai`, `httpx`, and `urllib3` as bundled packages with built-in
Emscripten/Fetch transports, so no custom HTTP transport is needed anymore.
"""

import asyncio

import httpx
import openai
from pyodide.ffi import create_proxy

import js_module

MODEL = "openai/gpt-5.4-mini"
SYSTEM_PROMPT = (
    "You are a concise, friendly assistant running inside a Pyodide-powered "
    "browser chat. Keep answers short unless the user asks for detail."
)

# OpenRouter's CORS preflight rejects the openai SDK's auto-injected
# x-stainless-* headers. Strip them with an httpx request hook before send.
_STAINLESS_HEADERS = {
    "x-stainless-lang",
    "x-stainless-package-version",
    "x-stainless-os",
    "x-stainless-arch",
    "x-stainless-runtime",
    "x-stainless-runtime-version",
    "x-stainless-async",
    "x-stainless-retry-count",
    "x-stainless-read-timeout",
}


async def _strip_stainless(request: httpx.Request) -> None:
    request.headers = httpx.Headers(
        {k: v for k, v in request.headers.items() if k.lower() not in _STAINLESS_HEADERS}
    )


_http_client = httpx.AsyncClient(event_hooks={"request": [_strip_stainless]})

openai_client: openai.AsyncOpenAI = openai.AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="placeholder",
    http_client=_http_client,
    default_headers={
        "HTTP-Referer": "http://localhost",
        "X-Title": "Pyodide Chat GPT2",
    },
)

history: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

message_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
loop: asyncio.AbstractEventLoop | None = None


async def handle_message(api_key: str, message: str) -> None:
    openai_client.api_key = api_key
    history.append({"role": "user", "content": message})
    try:
        response = await openai_client.chat.completions.create(
            model=MODEL,
            messages=history,
            max_completion_tokens=1024,
            temperature=0.2,
        )
        reply = response.choices[0].message.content or ""
        history.append({"role": "assistant", "content": reply})
        await js_module.displayResponse(reply)
    except Exception as exc:
        # Roll back the just-appended user turn so a retry doesn't duplicate it.
        if history and history[-1].get("role") == "user":
            history.pop()
        await js_module.displayError(f"{type(exc).__name__}: {exc}")


async def receiver() -> None:
    while True:
        api_key, message = await message_queue.get()
        await handle_message(api_key, message)


def sender(api_key: str, message: str) -> None:
    message_queue.put_nowait((api_key, message))


async def main() -> None:
    global loop

    loop = asyncio.get_running_loop()
    loop.create_task(receiver())
    while True:
        await asyncio.sleep(0.1)


sender_message_proxy = create_proxy(sender)
