# Play/Pause Button — Design

## Goal

Add a single toggle button to lofi.cafe that pauses and resumes all audio (the
selected track plus the rain and keyboard ambience layers) together. Today the
only way to silence the player is to drag every volume slider to zero or close
the tab.

## UI placement

A new button lives in the existing top-right `.top-buttons` cluster, to the
left of `⟳ refresh` and `🖼 next gif`. It uses the same visual style as those
buttons. No layout regions are added.

Label flips with state:

- Default / playing-can-be-paused: `⏸ pause`
- Paused: `▶ play`
- No track selected yet: `▶ play`, **disabled** (greyed out, not clickable)

## Behavior

### What "play" and "pause" act on

Both actions affect all three `<audio>` elements together:

- `#audio-track` (the selected lofi track)
- `#audio-rain`
- `#audio-keys`

There is no per-layer pause. The volume sliders remain the way to silence
individual layers.

### State derivation

The button reflects the play state of `#audio-track`. A single source of
truth: `audio-track.paused`. The button subscribes to `play` and `pause`
events on `#audio-track` and updates its label whenever they fire — so any
state change (user click, end-of-buffer, error) keeps the button consistent.

### Enabling the button

Disabled on page load. Enabled the first time `playTrack()` runs (i.e., the
user picks a track from the sidebar). It stays enabled for the rest of the
session.

### Toggle action

When clicked while enabled:

- If `audio-track.paused` is true → call `.play()` on all three audio elements.
- Otherwise → call `.pause()` on all three audio elements.

`.play()` returns a promise; if it rejects (e.g. the browser blocks resume
without a fresh user gesture, which is unlikely since the user just clicked
the button) the button is left in its prior state and no toast is shown.

### Now-playing chip

The chip already shows `▶ <title>` when a track is playing. When paused, the
prefix becomes `⏸ <title>` so the state is visible in two places. The
`⏳ loading: <title>` state is unchanged — pause is not meaningful while
fetching.

### Spacebar shortcut

Pressing space anywhere on the page toggles play/pause, with one guard:
the handler is a no-op if `document.activeElement` is an `<input>`,
`<button>`, `<textarea>`, or `<select>`. This protects the volume sliders
(focused range inputs use space/arrow keys) and avoids "ghost-clicking" the
refresh or next-gif buttons.

The handler also calls `event.preventDefault()` only when it actually
toggles, so non-form areas don't scroll the page.

## Edge cases

- **Picking a new track while paused.** `playTrack()` already calls
  `.play()` on the track and ambience. The `play` event flips the button
  back to `⏸ pause` automatically — no extra code in `playTrack()`.
- **Track load fails.** The existing `error` handler restores the
  `— select a track —` chip. The button stays in its current state; the
  audio element will be `paused`, so the button shows `▶ play`. Acceptable.
- **User pauses while a track is still loading.** Calling `.pause()` on a
  loading element is safe; it cancels nothing and the buffer continues. When
  the user clicks play again, audio resumes from wherever it has loaded to.
- **Audio element ends naturally.** All three are `loop`, so this should not
  occur. If it ever does, the `pause` event will flip the button correctly.

## Files changed

### `static/index.html`

Add one button inside `.top-buttons`, before the refresh button:

```html
<button id="btn-play-pause" type="button" disabled>▶ play</button>
```

### `static/styles.css`

Add a disabled style for top-bar buttons:

```css
.top-buttons button:disabled {
  opacity: 0.4;
  cursor: default;
}
.top-buttons button:disabled:hover {
  background: rgba(255,255,255,0.12);
}
```

### `static/app.js`

- Add `btnPlayPause: document.getElementById("btn-play-pause")` to `els`.
- Helper `setPlayPauseLabel()` that reads `audio-track.paused` and writes
  the button text.
- Helper `togglePlayPause()` that flips the state across all three audio
  elements.
- In `init()`:
  - Add `play`/`pause` event listeners on `#audio-track` that call
    `setPlayPauseLabel()` and update the now-playing chip prefix.
  - Wire `els.btnPlayPause.addEventListener("click", togglePlayPause)`.
  - Add a `keydown` listener on `document` for the spacebar shortcut, with
    the focus guard described above.
- In `playTrack()`: set `els.btnPlayPause.disabled = false` once.
- In the now-playing chip update points (`onPlaying` callback and the
  paused branch driven by the `pause` event listener), use the appropriate
  prefix (`▶` vs `⏸`) instead of hard-coding `▶`.

Approximate size: ~30 lines added in `app.js`, plus the small HTML and CSS
changes above.

## Out of scope

- Independent pause for individual ambience layers.
- Persisting paused state across reloads.
- Visual play/pause animation, beyond the label flip.
- Media-session API integration (lockscreen / hardware key support).
