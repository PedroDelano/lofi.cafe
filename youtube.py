from dataclasses import dataclass
from pathlib import Path

import yt_dlp

CHANNEL_HANDLE = "@thebootlegboy2"
CHANNEL_URL = f"https://www.youtube.com/{CHANNEL_HANDLE}/videos"
MAX_TRACKS = 20


@dataclass(frozen=True)
class Track:
    id: str
    title: str
    duration: int
    thumbnail_url: str


def list_channel_tracks() -> list[Track]:
    opts = {
        "extract_flat": True,
        "playlistend": MAX_TRACKS,
        "quiet": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(CHANNEL_URL, download=False)

    tracks: list[Track] = []
    for entry in info.get("entries", []):
        thumbnails = entry.get("thumbnails") or []
        thumbnail_url = thumbnails[0]["url"] if thumbnails else ""
        tracks.append(
            Track(
                id=entry["id"],
                title=entry.get("title", ""),
                duration=int(entry.get("duration") or 0),
                thumbnail_url=thumbnail_url,
            )
        )
    return tracks


def download_audio(video_id: str, dest_dir: Path) -> Path:
    url = f"https://www.youtube.com/watch?v={video_id}"
    opts = {
        "format": "bestaudio",
        "outtmpl": str(dest_dir / f"{video_id}.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info))
