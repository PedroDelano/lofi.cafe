# Play/Pause Button Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single play/pause toggle to the top-right button cluster that pauses and resumes all three audio layers together (track + rain + keyboard), plus a spacebar shortcut.

**Architecture:** Frontend-only change. Single source of truth is `audio-track.paused`; the button label is driven by `play`/`pause` events on that element so all state changes (click, error, future code paths) keep the UI consistent. Spacebar handler is on `document` with a focus-guard so volume sliders keep their native space/arrow behavior.

**Tech Stack:** Vanilla HTML/CSS/JS. No build step. No frontend test framework — verification is manual in a browser.

**Commit policy for this plan:** A single commit at the very end (Task 4). Do **not** commit between tasks. This matches the existing repo convention and the user's stated preference.

**Spec:** `docs/superpowers/specs/2026-05-04-play-pause-button-design.md`

---

## File Structure

| Path | Change |
|---|---|
| `static/index.html` | Add one `<button>` to `.top-buttons` |
| `static/styles.css` | Add `:disabled` style for top-bar buttons |
| `static/app.js` | Add element ref, helpers, listeners, spacebar handler; tweak now-playing chip prefix |

No new files.

---

## Task 1: HTML & CSS — add the disabled button

**Files:**
- Modify: `static/index.html:14-17` (`.top-buttons` block)
- Modify: `static/styles.css:29-39` (top-button styles block)

- [ ] **Step 1: Add the button to `index.html`**

In `static/index.html`, locate the `.top-buttons` div (currently lines 14-17):

```html
<div class="top-buttons">
  <button id="btn-refresh" type="button">⟳ refresh</button>
  <button id="btn-next-gif" type="button">🖼 next gif</button>
</div>
```

Insert the new button as the **first** child so it appears left of the others:

```html
<div class="top-buttons">
  <button id="btn-play-pause" type="button" disabled>▶ play</button>
  <button id="btn-refresh" type="button">⟳ refresh</button>
  <button id="btn-next-gif" type="button">🖼 next gif</button>
</div>
```

- [ ] **Step 2: Add the disabled style to `styles.css`**

In `static/styles.css`, immediately after the existing `.top-buttons button:hover` rule (currently line 39), append:

```css
.top-buttons button:disabled {
  opacity: 0.4;
  cursor: default;
}
.top-buttons button:disabled:hover {
  background: rgba(255,255,255,0.12);
}
```

The `:disabled:hover` rule overrides the brighter hover from the rule two lines above so a disabled button doesn't visually react to hover.

- [ ] **Step 3: Verify in the browser**

Run the server:

```bash
cd /home/pedro/Documents/personal/lofi.cafe
uv run python main.py
```

Open `http://localhost:8000` and confirm:

1. The `▶ play` button appears to the left of `⟳ refresh` in the top-right.
2. It is visibly faded (opacity ~0.4) and shows a default cursor (no pointer) on hover.
3. Hovering does **not** brighten the background.
4. Clicking it does nothing (disabled).

Stop the server (Ctrl+C). Do **not** commit yet.

---

## Task 2: JS — toggle behavior and chip sync

**Files:**
- Modify: `static/app.js` (multiple locations — see steps)

- [ ] **Step 1: Add the element reference**

In `static/app.js`, the `els` object currently runs lines 14-30. Add `btnPlayPause` to it. The block becomes:

```javascript
const els = {
  backdrop: document.getElementById("backdrop"),
  nowPlaying: document.getElementById("now-playing"),
  trackList: document.getElementById("track-list"),
  btnRefresh: document.getElementById("btn-refresh"),
  btnNextGif: document.getElementById("btn-next-gif"),
  btnPlayPause: document.getElementById("btn-play-pause"),
  audioTrack: document.getElementById("audio-track"),
  audioRain: document.getElementById("audio-rain"),
  audioKeys: document.getElementById("audio-keys"),
  volTrack: document.getElementById("vol-track"),
  volRain: document.getElementById("vol-rain"),
  volKeys: document.getElementById("vol-keys"),
  volTrackVal: document.getElementById("vol-track-val"),
  volRainVal: document.getElementById("vol-rain-val"),
  volKeysVal: document.getElementById("vol-keys-val"),
  toast: document.getElementById("toast"),
};
```

- [ ] **Step 2: Add helpers — chip prefix, button-label sync, toggle**

In `static/app.js`, find `function applyVolumes()` (currently around line 43). Insert these three helpers **immediately above it**:

```javascript
function nowPlayingPrefix() {
  return els.audioTrack.paused ? "⏸" : "▶";
}

function syncPlayPauseButton() {
  els.btnPlayPause.textContent = els.audioTrack.paused ? "▶ play" : "⏸ pause";
}

function togglePlayPause() {
  if (els.btnPlayPause.disabled) return;
  if (els.audioTrack.paused) {
    els.audioTrack.play().catch(() => {});
    els.audioRain.play().catch(() => {});
    els.audioKeys.play().catch(() => {});
  } else {
    els.audioTrack.pause();
    els.audioRain.pause();
    els.audioKeys.pause();
  }
}
```

- [ ] **Step 3: Update the now-playing chip in `playTrack()` to use the prefix and enable the button**

Find `function playTrack(track)` (currently around line 64). The current `onPlaying` callback hard-codes `▶`:

```javascript
const onPlaying = () => {
  if (loadGeneration === gen) {
    els.nowPlaying.textContent = `▶ ${track.title}`;
  }
  cleanup();
};
```

Change the literal `▶` to the dynamic prefix and enable the button. Also store the active track title on a module-level variable so the `play`/`pause` event listeners (added in Step 4) can re-render the chip without losing the title.

First, add a module-level variable near the other `let` declarations at the top of the file (currently around line 32-35):

```javascript
let tracks = [];
let activeTrackId = null;
let activeTrackTitle = null;
let loadGeneration = 0;
let gifIndex = GIFS.length ? Math.floor(Math.random() * GIFS.length) : -1;
```

Then update `playTrack()`. Set `activeTrackTitle` and use the prefix helper in `onPlaying`:

```javascript
function playTrack(track) {
  activeTrackId = track.id;
  activeTrackTitle = track.title;
  loadGeneration += 1;
  const gen = loadGeneration;

  // Loading state shown until the audio element actually starts playing.
  // The server downloads via yt-dlp on first request, which can take a while.
  els.nowPlaying.textContent = `⏳ loading: ${track.title}`;

  const cleanup = () => {
    els.audioTrack.removeEventListener("playing", onPlaying);
    els.audioTrack.removeEventListener("error", onError);
  };
  const onPlaying = () => {
    if (loadGeneration === gen) {
      els.nowPlaying.textContent = `${nowPlayingPrefix()} ${track.title}`;
      els.btnPlayPause.disabled = false;
    }
    cleanup();
  };
  const onError = () => {
    if (loadGeneration === gen) {
      els.nowPlaying.textContent = "— select a track —";
      showToast("Couldn't fetch this track.");
    }
    cleanup();
  };
  els.audioTrack.addEventListener("playing", onPlaying);
  els.audioTrack.addEventListener("error", onError);

  els.audioTrack.src = `/tracks/${track.id}/audio`;
  els.audioTrack.play().catch(() => {});

  // Start ambience too — browsers require gesture before .play(); the click counts.
  els.audioRain.play().catch(() => {});
  els.audioKeys.play().catch(() => {});
  renderTracks();
}
```

- [ ] **Step 4: Wire listeners in `init()`**

Find `function init()` (currently around line 131). Add the click handler and the two audio-element listeners. The listeners refresh the button label and the chip prefix whenever the track audio plays or pauses (covers click, error-induced pauses, and any future code path):

```javascript
function init() {
  if (gifIndex >= 0) {
    els.backdrop.style.backgroundImage = `url('/static/gifs/${GIFS[gifIndex]}')`;
  }
  applyVolumes();
  els.volTrack.addEventListener("input", applyVolumes);
  els.volRain.addEventListener("input", applyVolumes);
  els.volKeys.addEventListener("input", applyVolumes);
  els.btnRefresh.addEventListener("click", refresh);
  els.btnNextGif.addEventListener("click", nextGif);
  els.btnPlayPause.addEventListener("click", togglePlayPause);
  els.audioTrack.addEventListener("play", () => {
    if (els.btnPlayPause.disabled) return;
    syncPlayPauseButton();
    if (activeTrackTitle && els.nowPlaying.textContent.startsWith("⏸ ")) {
      els.nowPlaying.textContent = `▶ ${activeTrackTitle}`;
    }
  });
  els.audioTrack.addEventListener("pause", () => {
    if (els.btnPlayPause.disabled) return;
    syncPlayPauseButton();
    if (activeTrackTitle && els.nowPlaying.textContent.startsWith("▶ ")) {
      els.nowPlaying.textContent = `⏸ ${activeTrackTitle}`;
    }
  });
  loadTracks();
}
```

Two guards keep these listeners well-behaved:

- **`disabled` short-circuit:** before the button is enabled (during the very first track load), `play`/`pause` events from the audio element fire while the user has no way to interact with the toggle. Bailing means the button text stays as the initial `▶ play` until `onPlaying` enables it for real.
- **Chip prefix check:** events fired during a track switch (setting `src` triggers a `pause` if currently playing; the subsequent `play()` call triggers a `play`) would otherwise clobber the `⏳ loading: …` state. By only rewriting the chip when it currently starts with `▶ ` or `⏸ `, we leave loading and the initial `— select a track —` state alone.

- [ ] **Step 5: Verify in the browser**

Run the server:

```bash
cd /home/pedro/Documents/personal/lofi.cafe
uv run python main.py
```

Open `http://localhost:8000` and confirm:

1. On load, the `▶ play` button is faded (disabled).
2. Click a track in the sidebar. While loading, the chip shows `⏳ loading: <title>` and the button is still disabled.
3. Once audio starts, the chip flips to `▶ <title>`, the button becomes solid (enabled) and reads `⏸ pause`.
4. Click `⏸ pause`. All three audio layers stop. The button now reads `▶ play`. The chip reads `⏸ <title>`.
5. Click `▶ play`. Track + rain + keyboard all resume. The button reads `⏸ pause` again. The chip reads `▶ <title>`.
6. While paused, click a different track in the sidebar. It should load, then play, and the button should flip back to `⏸ pause` automatically.
7. While **playing**, click a different track in the sidebar. The chip should briefly show `⏳ loading: <new title>` (NOT a flicker through `⏸ <old title>` or `▶ <old title>`). When playback starts, the chip should read `▶ <new title>` and the button `⏸ pause`.
8. Volume sliders still work normally and don't affect the button.

Stop the server. Do **not** commit yet.

---

## Task 3: JS — spacebar shortcut

**Files:**
- Modify: `static/app.js` — `init()` (the function that grew in Task 2)

- [ ] **Step 1: Add the keydown handler**

Inside `init()`, after the `els.audioTrack.addEventListener("pause", ...)` block from Task 2 and before the `loadTracks()` call, insert the spacebar handler:

```javascript
  document.addEventListener("keydown", (event) => {
    if (event.code !== "Space") return;
    const tag = document.activeElement && document.activeElement.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || tag === "BUTTON") {
      return;
    }
    if (els.btnPlayPause.disabled) return;
    event.preventDefault();
    togglePlayPause();
  });
```

The guard order matters: bail before `preventDefault()` if the event belongs to a focused control or the button is disabled, so we never swallow space in those cases.

- [ ] **Step 2: Verify in the browser**

Run the server, open the page, and confirm:

1. Before picking a track: pressing space does nothing visible (button disabled, no error in console).
2. After picking a track and it starts playing: pressing space (with nothing focused — click on the dark backdrop area first) toggles pause/play. Button label and chip prefix flip every time.
3. Click a volume slider so it has focus. Press space. The slider's native behavior should still apply (no page toggle) — the audio should not pause, because the handler bailed.
4. Move focus away from the slider (click the backdrop). Space toggles again.
5. Press space repeatedly with no focused control. The page does **not** scroll (because `preventDefault()` ran on the toggle path).

Stop the server. Do **not** commit yet.

---

## Task 4: Final commit

**Files:**
- All changes from Tasks 1-3

- [ ] **Step 1: Review the diff**

```bash
cd /home/pedro/Documents/personal/lofi.cafe
git status
git diff
```

Expected files modified: `static/index.html`, `static/styles.css`, `static/app.js`. New file: `docs/superpowers/specs/2026-05-04-play-pause-button-design.md` and `docs/superpowers/plans/2026-05-04-play-pause-button.md`. No other files should appear.

- [ ] **Step 2: Stage and commit**

```bash
cd /home/pedro/Documents/personal/lofi.cafe
git add static/index.html static/styles.css static/app.js \
  docs/superpowers/specs/2026-05-04-play-pause-button-design.md \
  docs/superpowers/plans/2026-05-04-play-pause-button.md
git commit -m "Add play/pause button with spacebar shortcut"
```

Do **not** add a `Co-Authored-By` trailer — the user has explicitly opted out of AI-attribution trailers.

- [ ] **Step 3: Verify the commit**

```bash
git log -1 --stat
```

Expected: one commit titled `Add play/pause button with spacebar shortcut`, touching the five files listed above. No co-author trailer.
