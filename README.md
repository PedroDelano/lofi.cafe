# lofi.cafe

Self-hosted single-user lofi player. Streams audio from
[`@thebootlegboy2`](https://www.youtube.com/@thebootlegboy2)'s latest
YouTube uploads, layers rain and keyboard ambience on top, and rotates
through bundled lofi GIFs as a backdrop.

## Setup

1. Install [`uv`](https://docs.astral.sh/uv/).
2. Sync deps:

   ```bash
   uv sync
   ```

3. Drop ambient loops into `static/ambient/`:

   - `rain.mp3` — e.g. https://freesound.org search for "rain loop CC0".
   - `keyboard.mp3` — e.g. https://freesound.org search for "mechanical
     keyboard typing CC0".

4. Drop a few `.gif` files into `static/gifs/` (lofi-aesthetic loops).
   Then add their filenames to the `GIFS` array near the top of
   `static/app.js`:

   ```javascript
   const GIFS = [
     "rainy-window.gif",
     "girl-studying.gif",
   ];
   ```

5. Run:

   ```bash
   uv run main.py
   ```

6. Open <http://localhost:8000>.

## How it works

- On startup the server fetches metadata for the latest 20 uploads from
  the channel via `yt-dlp`.
- Click a track in the sidebar — the server downloads its audio into a
  temp directory (auto-deleted on shutdown) and streams it to the
  browser.
- Three independent volume sliders control the track, rain, and
  keyboard layers.
- "⟳ refresh" re-fetches the channel listing.
- "🖼 next gif" cycles to the next bundled GIF.

## Tests

```bash
uv run pytest
```

Tests do not hit YouTube.
