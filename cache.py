import tempfile
from pathlib import Path

import youtube


class AudioCache:
    def __init__(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory(prefix="lofi-cafe-")
        self.root = Path(self._tempdir.name)
        self._paths: dict[str, Path] = {}

    def get_or_download(self, video_id: str) -> Path:
        cached = self._paths.get(video_id)
        if cached is not None and cached.exists():
            return cached
        path = youtube.download_audio(video_id, self.root)
        self._paths[video_id] = path
        return path

    def close(self) -> None:
        self._tempdir.cleanup()
