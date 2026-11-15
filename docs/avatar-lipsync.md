# Bhoomi's Flow avatar and live lip-sync

`BHOOMI_INTRO_VIDEO_PATH` points to the original Google Flow MP4. FastAPI serves it read-only at `/api/ai/avatar/intro`; the frontend plays it once as the introduction (muted autoplay with browser controls). It is not used as a response clip.

## Live lip-sync adapter

MuseTalk 1.5 is the selected lip-sync engine candidate. The project does not include its weights, FFmpeg, CUDA environment, or an HTTP server, so configure a separately deployed MuseTalk-compatible GPU adapter with `LIPSYNC_API_URL`. Optional `LIPSYNC_API_KEY` is sent as a Bearer token. The adapter must implement this BhoomiVaani contract:

- `POST` to the exact URL in `LIPSYNC_API_URL`.
- Multipart fields `video_file` (the original Flow MP4) and `audio_file` (the generated Timbre WAV).
- Return the completed synchronized video as `video/mp4`, including the supplied speech audio track.
- Preserve the source identity and return only after the video is ready to play.

The frontend only replaces the introduction frame with a returned clip after Timbre has generated audio. When the endpoint is not configured or fails, Bhoomi's original character stays visible and her generated audio remains playable, but live mouth synchronization is reported unavailable.

MuseTalk's upstream README recommends 25 fps input (the supplied clip is 24 fps). It reports 30+ fps on an NVIDIA Tesla V100, while its Gradio demonstration reports that an 8-second clip may take about five minutes on an RTX 3050 Ti Laptop GPU with 4 GB VRAM in fp16. It documents Python 3.10, CUDA 11.7, FFmpeg, and additional model weights/dependencies. That means the upstream demo minimum is not evidence of low-latency production performance. Its code and model are described as MIT/commercially usable; licenses for bundled third-party weights/models remain separate. See the [MuseTalk upstream repository](https://github.com/TMElyralab/MuseTalk).

## Voice reference

Gnani documents a two-step voice clone flow: upload 5–30 seconds of clean reference audio to `/api/v1/tts/voice-clone/embeddings`, then send the resulting speaker embedding with text to its voice-cloned Timbre inference endpoint. The MP4's AAC stereo 48 kHz audio track is 7.9 seconds long, so its duration is within that documented range. This environment has no FFmpeg/ffprobe and no `GNANI_API_KEY`; the audio could not be extracted, auditioned for clean single-speaker quality, or sent to Gnani. Do not mark the reference as approved or claim the clone is active until those checks pass. Gnani's [voice-clone embedding docs](https://docs.gnani.ai/api/VC/voice-clone-embeddings) specify that the reference must be clean audio for 5–30 seconds; their [voice-cloned TTS docs](https://docs.gnani.ai/api/VC/vc-inference) document the embedding-based synthesis request.
