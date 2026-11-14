# BhoomiVaani

BhoomiVaani is a voice-first land-buying advisor. Its main experience is a single-column conversation with Bhoomi, an animated 3D advisor whose listening, thinking, and speaking states follow the voice pipeline. Users can speak or type; spoken language is identified by Prisma and the reply uses that language. The conversation presents Bhoomi's response rather than a multi-character dashboard.

Users can also upload a PDF or text document from the conversation. Bhoomi receives the resulting rule-based text-scan findings as user-provided context, and the conversation can be downloaded as a structured PDF report covering buyer requirements, seller claims, document scan results, checks still required, risks, and next steps. The report uses standard PDF fonts; local-script text that cannot be rendered is marked for review in the original conversation. Document scans and the report do not authenticate documents or replace official/legal verification.

## Important: demonstration records

The six listings in `backend/data/lands.json`, their survey numbers, coordinates, prices, legal-risk examples, and infrastructure references are synthetic demonstration data. They are not government records and have not been independently checked. A listing with no risk entries is **not** a clear-title finding. Document scanning is a text-pattern aid, not legal analysis or title certification. Growth charts are formula-based examples, not market forecasts. If a question does not uniquely identify a parcel, the investigation returns general awareness instead of silently assigning a listing. Obtain authoritative records and independent legal advice before making a purchase.

## Stack

- **Frontend:** React 18, TypeScript 5, Vite 5, Three.js 0.187
- **Backend:** FastAPI, Pydantic, Uvicorn, httpx
- **Speech (optional):** Gnani Prisma v3.0 STT and Timbre v2.5 TTS
- **Reasoning:** Qwen3 through Ollama's native chat API, or an explicitly labeled synthetic demo adapter

Gnani publishes Evon model weights, but this project does not configure a hosted Evon API: no supported hosted API contract was found in the official documentation. The repository previously sent requests to an undocumented URL and labeled deterministic responses as Evon. Do not configure that endpoint or label the returned model as Evon. A local Evon deployment is possible separately, but has not been integrated or tested here.

## Requirements

- Python 3.10+
- Node.js 18+

## Install and start

From the repository root:

```bash
cp .env.example .env
python -m pip install -r backend/requirements.txt
cd frontend && npm ci && cd ..
python start.py
```

Or use `./run.sh` on Linux/macOS, or `run.bat` on Windows. The frontend is at `http://localhost:5173`, the API at `http://127.0.0.1:8000`, and OpenAPI docs at `http://127.0.0.1:8000/docs`.

The app needs both processes. Running only `cd frontend && npm run dev` starts the UI but does not start FastAPI; voice and reasoning requests will fail visibly. In Codespaces, `.devcontainer/devcontainer.json` forwards frontend port 5173 and backend port 8000. Vite proxies `/api` to `127.0.0.1:8000`; open the forwarded frontend URL, not the backend port. The API root `/` points users to the frontend, and `/health` is the backend health check (`/api/health` remains available).

Run the services separately when needed:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
cd frontend && npm run dev
```

## Configuration

Copy `.env.example` to `.env`. Provider secrets are read only by the backend.

### Synthetic demo mode (default)

`MOCK_MODE=true` does not call speech or model providers. Typed investigations use the deterministic synthetic-data adapter. Microphone and speech playback requests report that the provider is unavailable; they do not return a made-up transcript or audio.

### Optional Gnani speech services

Get an API key from the [Gnani API dashboard](https://app.gnani.ai/voice), set `GNANI_API_KEY`, and set `MOCK_MODE=false`. The backend uses the documented `X-API-Key-ID` authentication header and endpoints:

- Prisma v3.0: `POST https://api.vachana.ai/stt/v3`, multipart audio and `indic-auto` language detection
- Timbre v2.5: `POST https://api.vachana.ai/api/v1/tts/inference`, binary WAV response

The browser records microphone audio, decodes it to mono PCM WAV, and uploads it to Prisma with automatic language identification. The returned transcript is shown in the conversation and sent to Qwen with the recent turns and extracted buyer facts; Qwen generates one Bhoomi reply, which Timbre returns as WAV. The browser attempts to play the full WAV and offers a manual “Hear Bhoomi” retry when autoplay is blocked. Typed questions use their writing script to choose a supported language. Language-specific voice choices come from Gnani's v2.5 voice catalog. Provider failures are reported; they are not replaced with simulated speech. Browser recordings stop at 25 seconds, below Prisma REST's 30-second limit.
The status endpoint reports `CONFIGURED_UNVERIFIED` until a real transcription or synthesis request succeeds; only then does it report `CONNECTED`. The API key alone does not establish connectivity. Missing credentials are reported as `GNANI_API_KEY` requirements.
Prisma uses `PRISMA_REQUEST_TIMEOUT_SECONDS` (120 seconds by default); its browser request allows 130 seconds so the frontend does not abort before the backend reports an upstream timeout.

### Qwen3 through Ollama

Install and run Ollama separately, fetch a Qwen3 model, then set:

```ini
MOCK_MODE=false
REASONING_PROVIDER=QWEN3_OLLAMA
OLLAMA_API_URL=http://localhost:11434/api/chat
OLLAMA_MODEL=qwen3:0.6b
```

The service checks for the configured model and parses its actual JSON response. Provider errors or malformed responses fail visibly; they do not silently switch to demo reasoning. Configure Gnani credentials too if voice transcription and spoken responses are wanted. Language selection reflects the configured reasoning/STT/TTS capabilities; text-only provider use does not imply speech is available.

## API

Existing API paths are retained. The main experience uses:

- `GET /api/lands`, `GET /api/lands/{land_id}`, `GET /api/lands/stats`
- `POST /api/investigate/collaborate` — the existing investigation response, with optional bounded conversation history; the UI presents the final Bhoomi response
- `POST /api/investigate/report` — generates a PDF from the buyer conversation, supplied document-scan results, and an explicitly selected demonstration parcel
- `GET /api/investigate/models/status` — provider names, mock/live status, and language availability
- `POST /api/ai/transcribe`, `POST /api/ai/speak`
- `POST /api/claims/check`, `POST /api/documents/analyze`
- `POST /api/lands/compare`, `GET /api/lands/{land_id}/report`

The investigation response includes an evidence ledger and distinguishes synthetic listing data from missing or unverified authoritative records. The UI and PDF reports are preliminary awareness tools, not legal advice or government verification.

## Tests and build

```bash
PYTHONPATH=backend python -m pytest backend/tests -q
cd frontend && npm run build
```

The frontend uses the existing locked Three.js dependency; no additional 3D renderer is required.

## Verified provider documentation

- [Gnani speech API authentication and products](https://docs.gnani.ai/api/introduction/introduction)
- [Prisma REST transcription request](https://docs.gnani.ai/api/STT/speech-to-text)
- [Timbre v2.5 REST request and audio response](https://docs.gnani.ai/api/TTS/tts-inference)
- [Timbre v2.5 voice catalog](https://docs.gnani.ai/api/TTS/available-voices)
- [Gnani Evon v3.3 model card](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B)
