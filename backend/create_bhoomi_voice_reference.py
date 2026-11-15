"""Create Bhoomi's local Gnani voice-clone embedding from the Flow introduction.

The audio is uploaded only when --confirm-clean-single-speaker is supplied after
the extracted reference has been listened to and approved by the operator.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import wave

import httpx

from app.config import ROOT_DIR, settings


GNANI_EMBEDDINGS_URL = "https://api.vachana.ai/api/v1/tts/voice-clone/embeddings"
DEFAULT_FLOW_VIDEO = Path(
    r"C:\Users\Gowthami\bhoomivaani\AI_assistant_speaking_to_camera_176b211d.mp4"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract and optionally register Bhoomi's Flow voice reference.")
    parser.add_argument("--video", type=Path, default=Path(settings.bhoomi_intro_video_path or DEFAULT_FLOW_VIDEO))
    parser.add_argument(
        "--confirm-clean-single-speaker",
        action="store_true",
        help="Confirm you listened to the extracted clip and it is clean speech from Bhoomi alone; then send it to Gnani.",
    )
    args = parser.parse_args()
    if not args.video.is_file():
        raise SystemExit("Google Flow video was not found. Set BHOOMI_INTRO_VIDEO_PATH or pass --video.")
    if args.confirm_clean_single_speaker and not settings.gnani_api_key:
        raise SystemExit("GNANI_API_KEY is not configured; no audio was uploaded.")

    reference_dir = Path(tempfile.gettempdir()) / "BhoomiVaani"
    reference_dir.mkdir(parents=True, exist_ok=True)
    reference = reference_dir / "bhoomi-flow-voice-reference.wav"
    try:
        subprocess.run(
            [
                settings.ffmpeg_path, "-nostdin", "-v", "error", "-y", "-i", str(args.video),
                "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(reference),
            ],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit("FFmpeg is required to extract the Flow video's audio. Set FFMPEG_PATH; no files were changed.") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit("FFmpeg could not extract the video's audio track; no files were changed.") from exc

    with wave.open(str(reference), "rb") as wav:
        duration = wav.getnframes() / wav.getframerate()
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or not 5 <= duration <= 30:
            raise SystemExit("Gnani requires 5–30 seconds of audio; the extracted reference did not meet that format/length check.")
    if not args.confirm_clean_single_speaker:
        print(f"Extracted a {duration:.1f}-second mono WAV for review: {reference}")
        print("Listen to it, then rerun with --confirm-clean-single-speaker only if it contains clean speech from Bhoomi alone.")
        return

    try:
        with reference.open("rb") as audio:
            response = httpx.post(
                GNANI_EMBEDDINGS_URL,
                headers={"X-API-Key-ID": settings.gnani_api_key},
                files={"audio_file": ("bhoomi-reference.wav", audio, "audio/wav")},
                timeout=settings.api_timeout_seconds,
            )
    except httpx.HTTPError as exc:
        raise SystemExit("Gnani voice-reference request failed; no embedding was saved.") from exc
    if response.status_code != 200:
        raise SystemExit(f"Gnani voice-reference request failed (HTTP {response.status_code}); no response body or credential was printed.")
    try:
        clone = response.json()["data"]["voice_clone_embedding"]
        if not isinstance(clone.get("embedding"), str) or not clone.get("shape") or not clone.get("dtype"):
            raise ValueError("incomplete embedding")
    except (ValueError, KeyError, TypeError) as exc:
        raise SystemExit("Gnani returned an invalid voice-reference response; no embedding was saved.") from exc

    destination = Path(settings.bhoomi_voice_embedding_path).expanduser().resolve()
    if destination.is_relative_to(ROOT_DIR.resolve()):
        raise SystemExit("BHOOMI_VOICE_EMBEDDING_PATH must point outside the repository to prevent committing voice-reference data.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_destination = destination.with_suffix(destination.suffix + ".tmp")
    temp_destination.write_text(json.dumps(clone), encoding="utf-8")
    if os.name != "nt":
        temp_destination.chmod(0o600)
    temp_destination.replace(destination)
    print("Bhoomi's voice-clone reference was saved outside the repository. Its contents were not displayed.")


if __name__ == "__main__":
    main()
