import os
from dataclasses import dataclass
from pathlib import Path

import yt_dlp

CHANNEL_HANDLE = "@thebootlegboy2"
CHANNEL_URL = f"https://www.youtube.com/{CHANNEL_HANDLE}/videos"
MAX_TRACKS = 20


def _auth_opts() -> dict:
    """yt-dlp options that authenticate requests to YouTube.

    YouTube gates the player endpoint behind a "confirm you're not a bot"
    check for unauthenticated requests from datacenter IPs. Point
    ``YTDLP_COOKIES_FILE`` at a Netscape-format cookies.txt exported from a
    logged-in session to pass it. Absent/missing file → no auth (local dev).
    """
    path = os.environ.get("YTDLP_COOKIES_FILE", "")
    if path and Path(path).is_file():
        return {"cookiefile": path}
    return {}


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
        **_auth_opts(),
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
        **_auth_opts(),
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info))
