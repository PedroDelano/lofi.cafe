import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from cache import AudioCache
from youtube import Track, list_channel_tracks

log = logging.getLogger("lofi-cafe")

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cache = AudioCache()
    try:
        app.state.tracks = list_channel_tracks()
    except Exception:
        log.exception("startup track fetch failed; starting with empty list")
        app.state.tracks = []
    try:
        yield
    finally:
        app.state.cache.close()


app = FastAPI(lifespan=lifespan)


def _track_to_json(t: Track) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "duration": t.duration,
        "thumbnail_url": t.thumbnail_url,
    }


@app.get("/tracks")
def get_tracks():
    return [_track_to_json(t) for t in app.state.tracks]


@app.post("/refresh")
def refresh_tracks():
    try:
        app.state.tracks = list_channel_tracks()
    except Exception as exc:
        log.exception("refresh failed")
        raise HTTPException(status_code=503, detail="Couldn't reach YouTube") from exc
    return [_track_to_json(t) for t in app.state.tracks]


@app.get("/tracks/{video_id}/audio")
def get_audio(video_id: str):
    try:
        path = app.state.cache.get_or_download(video_id)
    except Exception as exc:
        log.exception("audio download failed for %s", video_id)
        raise HTTPException(status_code=503, detail="Couldn't fetch this track") from exc
    return FileResponse(path)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
