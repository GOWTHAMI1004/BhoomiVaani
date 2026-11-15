"""Local storage for Gnani speaker embeddings (never log or return embedding values)."""

import json
import os
from pathlib import Path
from typing import Any

from app.config import ROOT_DIR, settings


class VoiceReferenceService:
    @property
    def path(self) -> Path:
        return Path(settings.bhoomi_voice_embedding_path).expanduser()

    def load_embedding(self) -> dict[str, Any] | None:
        if self.path.resolve().is_relative_to(ROOT_DIR.resolve()):
            return None
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(value, dict):
            return None
        embedding = value.get("embedding")
        shape = value.get("shape")
        dtype = value.get("dtype")
        if not isinstance(embedding, str) or not embedding.strip():
            return None
        if not isinstance(shape, list) or not shape or not all(isinstance(item, int) for item in shape):
            return None
        if not isinstance(dtype, str) or not dtype.strip():
            return None
        return {"embedding": embedding, "shape": shape, "dtype": dtype}

    def is_configured(self) -> bool:
        return self.load_embedding() is not None


voice_reference_service = VoiceReferenceService()
