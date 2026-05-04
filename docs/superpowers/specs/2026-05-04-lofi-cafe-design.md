# lofi.cafe — design

A self-hosted, single-user lofi player. Streams audio from `@thebootlegboy2`'s
latest YouTube uploads, layers configurable rain and keyboard ambience on top,
and rotates through bundled lofi-aesthetic GIFs as a backdrop.

## Goals

- Run locally, for a single user, on `localhost:8000`.
- Stay small and simple: one Python module for the backend, vanilla
  HTML/CSS/JS for the frontend, no build step, no Node.
- Use `uv` for dependency and execution management.

## Non-goals

- Multi-user / authenticated / public deployment.
- Persistent state across restarts (cache, refresh state, etc.).
- Generating new GIFs or music (the GIF set ships with the repo).
- Multi-channel curation. Channel is hardcoded.

## High-level architecture

```
┌─────────────────────────────────────────┐
│  Browser (localhost:8000)               │
│    index.html / app.js / styles.css     │
│    3× <audio>  (track, rain, keyboard)  │
│    3× volume sliders                    │
│    Track list, refresh button, gif btn  │
│    Bundled GIF as full-bleed backdrop   │
└────────────────┬────────────────────────┘
                 │ HTTP
┌────────────────┴────────────────────────┐
│  FastAPI app (main.py + helpers)        │
│    GET  /              → index.html     │
│    GET  /tracks        → JSON list      │
│    POST /refresh       → re-fetch list  │
│    GET  /tracks/{id}/audio → audio file │
│    /static/*           → assets + gifs  │
│                                         │
│  yt-dlp (Python lib) → tempfile cache   │
│  TemporaryDirectory: deleted on exit    │
└─────────────────────────────────────────┘
```

## Project layout

```
lofi.cafe/
├── pyproject.toml          # uv-managed, pinned deps
├── main.py                 # FastAPI app + uvicorn entry point
├── youtube.py              # yt-dlp wrapper
├── cache.py                # tempfile-backed audio cache
├── static/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── gifs/               # bundled lofi GIFs (5–10 files)
│   └── ambient/
│       ├── rain.mp3
│       └── keyboard.mp3
├── tests/
│   ├── test_youtube.py
│   ├── test_cache.py
│   └── test_api.py
└── README.md
```

## Components

### `youtube.py`

- `list_channel_tracks() -> list[Track]` — fetches metadata (no audio
  download) for the latest 20 uploads from `@thebootlegboy2` via the
  `yt_dlp.YoutubeDL` Python API. Returns dataclass `Track(id, title,
  duration, thumbnail_url)`.
- `download_audio(video_id: str, dest: Path) -> None` — downloads
  bestaudio for one video to `dest` (an `.m4a` file).
- The channel handle `@thebootlegboy2` is a module-level constant.

### `cache.py`

- Wraps a `tempfile.TemporaryDirectory` created at FastAPI startup.
- `get_or_download(video_id: str) -> Path` — returns the cached file
  path; on miss, calls `youtube.download_audio` to populate it.
- Cleanup happens automatically when the process exits
  (`TemporaryDirectory` registers a finalizer).
- No size cap in v1.

### `main.py`

- FastAPI app, route handlers, and `uvicorn.run` at the bottom.
- Holds the in-memory track list. `/refresh` re-runs the youtube fetch and
  replaces the list.
- Audio is served via `FileResponse`, which supports range requests so
  HTML5 `<audio>` can scrub.

### Frontend (`static/`)

Single page:

- Full-bleed GIF backdrop (`background-image` on `<body>` or a fixed div).
- Top bar: "Now playing" pill on the left, "Refresh" and "Next GIF"
  buttons on the right.
- Right sidebar: scrollable list of tracks; clicking sets the active
  track.
- Bottom bar: three volume sliders (track / rain / keyboard) over a
  translucent panel.
- Three `<audio>` elements:
  - `#track` → `src` set to `/tracks/{id}/audio`, `loop=true`.
  - `#rain` → `src` = bundled `rain.mp3`, `loop=true`.
  - `#keys` → `src` = bundled `keyboard.mp3`, `loop=true`.
- Sliders set each element's `volume` independently.
- "Next GIF" picks a different filename from a hardcoded JS array and
  swaps the backdrop.

No frontend framework, no build step.

## API

| Method | Path | Body / Returns | Behavior |
|---|---|---|---|
| `GET`  | `/`                       | `text/html`                                   | Serves `static/index.html` |
| `GET`  | `/tracks`                 | `[{id, title, duration, thumbnail_url}, ...]` | Returns the in-memory list (populated at startup) |
| `POST` | `/refresh`                | same shape as `/tracks`                       | Re-fetches metadata, replaces in-memory list |
| `GET`  | `/tracks/{video_id}/audio`| `audio/mp4` or `audio/mpeg`                   | Streams cached audio; downloads on first request |
| `GET`  | `/static/*`               | static asset                                  | Bundled GIFs, ambient loops, JS, CSS |

## Data flow

**Startup**

1. Create `TemporaryDirectory` for audio cache.
2. Call `list_channel_tracks()`; store in memory.
3. Start uvicorn on `:8000`.

**Play a track**

1. User clicks track in sidebar.
2. JS sets `#track.src = "/tracks/{id}/audio"`, calls `.play()`. Same for
   `#rain` and `#keys` (already pointing at bundled loops).
3. Server cache miss → `yt-dlp` downloads bestaudio to
   `{tempdir}/{video_id}.m4a`, then returns it via `FileResponse`. Cache
   hit → returns existing file.
4. On `ended` event, JS sets `currentTime = 0` and calls `.play()` again
   (loop current track forever).

**Refresh**

1. JS `POST /refresh`.
2. Server re-runs `list_channel_tracks()`, replaces in-memory list.
3. Returns new list; UI re-renders sidebar. Audio cache untouched.

**Next GIF**

Client-side only. JS keeps an integer index into a hardcoded array of
GIF filenames; clicking advances the index (wrapping at the end) and
swaps `background-image`. Initial index is randomised on page load.

**Concurrency**

Localhost single-user — no locking around the cache. Two simultaneous
downloads of the same uncached track is a non-issue; not handled.

## Bundled assets

- `static/gifs/` — 5–10 lofi GIFs sourced by the user (royalty-free or
  fair-use). Filenames hardcoded in `app.js`. Repo does not commit
  copyrighted media; the README documents where to drop files.
- `static/ambient/rain.mp3`, `static/ambient/keyboard.mp3` — looping
  ambience, sourced from freesound.org or similar (CC0 / CC-BY). README
  documents source links.

## Error handling

Errors are handled at boundaries only; internal code trusts itself.

- `yt-dlp` metadata fetch failure → API returns `503` with JSON error.
  Frontend shows a toast ("Couldn't reach YouTube — try refresh again").
  No retries.
- Audio download failure → API returns `503`. Frontend toasts and the
  user picks another track or refreshes.
- Channel handle invalid at startup → app exits with a clear log line.
  Acceptable: single-user app, user fixes it.
- Tempdir creation failure → log + exit.

## Testing

- `tests/test_youtube.py` — mock `yt_dlp.YoutubeDL`; assert
  `list_channel_tracks()` returns correctly shaped `Track` objects from
  canned metadata. Tests do not hit YouTube.
- `tests/test_cache.py` — real `TemporaryDirectory`, monkeypatch
  `download_audio`. Assert miss triggers download once, hit returns the
  same path without re-downloading.
- `tests/test_api.py` — FastAPI `TestClient`; mock youtube/cache modules.
  Verify route shapes, status codes, and that `/refresh` mutates the
  in-memory list.
- No frontend tests; eyeball in browser.
- Run with `uv run pytest`. Test deps: `pytest`, `httpx`.

## Dependencies

`pyproject.toml`:

- Runtime: `fastapi`, `uvicorn`, `yt-dlp`.
- Dev: `pytest`, `httpx`.

Managed via `uv`. Run with `uv run main.py`.
