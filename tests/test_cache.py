from pathlib import Path
from unittest.mock import patch

from cache import AudioCache


def test_get_or_download_misses_then_downloads(tmp_path):
    calls = []

    def fake_download(video_id, dest_dir):
        calls.append(video_id)
        out = Path(dest_dir) / f"{video_id}.m4a"
        out.write_bytes(b"x")
        return out

    cache = AudioCache()
    try:
        with patch("cache.youtube.download_audio", side_effect=fake_download):
            path1 = cache.get_or_download("abc")
            path2 = cache.get_or_download("abc")
            path3 = cache.get_or_download("def")

        assert path1.exists()
        assert path1 == path2
        assert path3.name.startswith("def")
        # only two downloads happened — second call for "abc" was a hit
        assert calls == ["abc", "def"]
    finally:
        cache.close()


def test_close_removes_tempdir():
    cache = AudioCache()
    root = cache.root
    assert root.exists()
    cache.close()
    assert not root.exists()
