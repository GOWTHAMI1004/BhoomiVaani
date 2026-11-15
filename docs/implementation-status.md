# BhoomiVaani implementation checklist

This checklist reflects the repository inspected on 15 November 2026. “Verified” means the stated check was actually run; configuration alone does not count as a successful integration.

## Existing foundations

- [x] FastAPI backend and Vite/React frontend are present.
- [x] Bhoomi avatar image and MP4 assets are present.
- [x] Gnani Prisma, Gemini `generateContent`, and Gnani Timbre backend adapters are implemented.
- [x] Live Prisma transcription succeeded with generated speech audio (23 transcript characters; detected `hi-IN`).
- [x] Live Gemini reasoning request succeeded (138-character response).
- [x] Live Timbre synthesis succeeded (WAV returned; 2.49-second duration).
- [x] Listing search, details, comparison, provider-status, submissions, and stats routes exist. User submissions are stored in a local JSON file; bundled example listings are synthetic.
- [x] Investigation conversation and downloadable PDF report routes exist.
- [x] PDF text extraction and rule-based document scanning routes exist.
- [x] `.env` is ignored by Git; `.env.example` contains placeholders.
- [x] Frontend production build succeeded.
- [x] Backend suite passed: 85 tests. Tests were run with provider credentials blanked in the test process and an isolated temporary directory; live credentials were not changed.

## Remaining product work

- [ ] Add database-backed users, conversations, investigations, documents, findings, saved properties, and comparisons. There is no database configuration or ORM/schema in the repository; current investigation conversations live in frontend state and listing submissions use a JSON file.
- [ ] Add authenticated user and administrator authorization, user management, and protected admin routes. No authentication or admin backend exists.
- [ ] Add durable investigation save/reopen and server-side document storage/cleanup.
- [ ] Extend document processing to OCR scanned PDFs/images, document-type classification, structured field extraction, page citations, and supported/contradicted/not-verified evidence comparisons. Current scans are rule-based and do not authenticate title.
- [ ] Connect an external live listing provider. Only local user submissions and clearly labeled synthetic demo records are available; no external listing adapter is installed.
- [ ] Add the interactive map, verified geocoding, map-linked listing selection, and reliable nearby-facility data. No map component/provider is currently installed.
- [ ] Add saved-property shortlists and a comparison dashboard with data-source reliability and evidence status. A comparison API and UI exist, but durable saved properties and full comparison evidence are not implemented.
- [ ] Complete price intelligence with sourced guideline values and genuine comparable transactions/listings. Existing calculations or synthetic examples must not be represented as verified market data.
- [ ] Exercise the complete voice-to-investigation-to-report flow in a browser, including microphone permissions, playback, and responsive layout.
- [ ] Restore live synchronized-video playback only after a reachable MuseTalk adapter returns and a generated MP4 has been played and checked against its WAV. The frontend currently labels live lip-sync unverified and keeps generated audio available independently.
- [ ] Prepare deployment configuration and verify a deployed URL; none is currently available.

## Avatar adapter findings

The backend keeps the adapter key server-side and now sends the MuseTalk-compatible `X-API-Key` header with multipart `video_file` and `audio_file`. It accepts only a completed `video/mp4` response. On 15 November 2026, the configured adapter's `/health` check failed because its Cloudflare tunnel hostname did not resolve. The legacy Colab endpoint named in the original project brief returned HTTP 404 at `/health`. No generated synchronized video was obtained or played, so live synchronization is not verified.

## Current API surface

- `GET /health`, `GET /api/health`
- `GET /api/lands`, `GET /api/lands/{land_id}`, `GET /api/lands/stats`, `POST /api/lands/compare`
- `GET /api/lands/providers/status`, `GET /api/lands/source-status`, `GET /api/lands/provider-search`, `POST /api/lands/submissions`
- `POST /api/ai/chat`, `POST /api/ai/transcribe`, `POST /api/ai/speak`
- `GET /api/ai/avatar/status`, `GET /api/ai/avatar/intro`, `POST /api/ai/avatar/lipsync`
- `POST /api/investigate/collaborate`, `POST /api/investigate/report`, `GET /api/investigate/models/status`
- `POST /api/documents/analyze`, `GET /api/documents/samples`, `GET /api/documents/samples/{sample_id}`
- `POST /api/claims/check`, `GET /api/lands/{land_id}/report`

## Configuration

Backend environment variable names are documented in `.env.example`. Live speech uses `GNANI_API_KEY`; Gemini uses `REASONING_PROVIDER=GEMINI`, `REASONING_API_KEY`, `REASONING_API_BASE_URL`, and `REASONING_MODEL`; lip-sync uses `LIPSYNC_API_URL` and `LIPSYNC_API_KEY`. Keep values in the ignored `.env` file or deployment secret store. The external listing, records, geocoding, and nearby-places providers are not implemented merely by setting their configuration names.
