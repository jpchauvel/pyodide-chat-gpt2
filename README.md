# Pyodide Chat (OpenRouter + GPT-5.4 Mini)

A browser-native chatbot pet project that runs Python in WebAssembly (Pyodide) and calls OpenRouter using the OpenAI Python SDK.

## What this project does

- Runs Python **entirely in the browser** via Pyodide.
- Loads backend logic from a packaged archive: `build/app.tar.gz`.
- Uses OpenRouter endpoint (`https://openrouter.ai/api/v1`) with model:
  - `openai/gpt-5-mini`
- Supports multi-turn conversation history.
- Surfaces runtime/API errors directly in the chat UI.

## Architecture

### Frontend (`index.html` + `python.js`)

- `index.html`
  - Hosts chat UI (`#chatbox`, `#user-input`, `#send-button`)
  - Shows loading state in `#status`
  - Loads Pyodide `v0.29.4` and `python.js`

- `python.js`
  - Initializes Pyodide from CDN
  - Loads packages: `openai`, `httpx`, `ssl`
  - Fetches and unpacks `build/app.tar.gz`
  - Imports `sender_message_proxy` from `main.py`
  - Prompts user for OpenRouter key at runtime (`window.prompt`)
  - Sends messages to Python and renders replies/errors in chat

### Pyodide backend (`main.py`)

- Uses `openai.AsyncOpenAI` with OpenRouter base URL.
- Maintains in-memory conversation `history`.
- Processes queued messages asynchronously.
- Uses `max_completion_tokens` for GPT-5 family compatibility.
- Includes an `httpx` request hook to strip `x-stainless-*` headers to avoid browser CORS preflight failures with OpenRouter.

## Files

- `main.py` — Pyodide-side chat logic
- `python.js` — Browser bootstrap and message bridge
- `index.html` — UI shell
- `Makefile` — build/serve helpers
- `build/app.tar.gz` — packaged Python app archive (generated)
- `.gitignore` — secret and local artifact protections

## Quick start

## 1) Build the Python bundle

```bash
make build
```

This creates `build/app.tar.gz` from `main.py`.

## 2) Run local server

```bash
make serve
```

Serves on `http://localhost:8080`.

## 3) Open in browser

- Navigate to `http://localhost:8080`
- Wait for status to become **Ready.**
- Paste your OpenRouter API key when prompted
- Send a message

## Security notes (important)

- Do **not** commit API keys.
- This project currently requests the API key via `window.prompt` for local testing simplicity.
- For production, do not expose raw provider keys in client-side code; use a secure server-side proxy or token exchange flow.

## Troubleshooting

### CORS / `APIConnectionError`

If chat fails with browser network/CORS errors:

- Ensure `main.py` includes the `httpx` hook that strips `x-stainless-*` headers.
- Rebuild bundle after changes:

```bash
make build
```

- Hard refresh browser (`Cmd+Shift+R`) to bypass stale cache.

### `build/app.tar.gz` not found

- Run `make build` before serving.
- Ensure server is started from the repo root.

### Wrong model name

Use:

- `openai/gpt-5-mini`

(Do not use non-existent model IDs.)

## Known limitations

- Key entry uses browser prompt (not a polished settings UI).
- Session history lives in memory only (no persistence).
- No backend proxy; this is intentionally a browser-side demo architecture.

## License

Personal/pet-project usage unless you add your own license file.
