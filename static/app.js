"use strict";

// Hardcoded list of bundled GIF filenames. Update when files in
// static/gifs/ change.
const GIFS = [
  "anime-window.gif",
  "cloudscape.gif",
  "flower-zen.gif",
  "pink-drive.gif",
  "vaporwave-bw.gif",
  "wave-chill.gif",
];

const els = {
  backdrop: document.getElementById("backdrop"),
  nowPlaying: document.getElementById("now-playing"),
  trackList: document.getElementById("track-list"),
  btnRefresh: document.getElementById("btn-refresh"),
  btnNextGif: document.getElementById("btn-next-gif"),
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

let tracks = [];
let activeTrackId = null;
let loadGeneration = 0;
let gifIndex = GIFS.length ? Math.floor(Math.random() * GIFS.length) : -1;

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.remove("hidden");
  setTimeout(() => els.toast.classList.add("hidden"), 3000);
}

function applyVolumes() {
  els.audioTrack.volume = els.volTrack.value / 100;
  els.audioRain.volume = els.volRain.value / 100;
  els.audioKeys.volume = els.volKeys.value / 100;
  els.volTrackVal.textContent = `${els.volTrack.value}%`;
  els.volRainVal.textContent = `${els.volRain.value}%`;
  els.volKeysVal.textContent = `${els.volKeys.value}%`;
}

function renderTracks() {
  els.trackList.innerHTML = "";
  for (const t of tracks) {
    const li = document.createElement("li");
    li.textContent = t.title;
    li.dataset.id = t.id;
    if (t.id === activeTrackId) li.classList.add("active");
    li.addEventListener("click", () => playTrack(t));
    els.trackList.appendChild(li);
  }
}

function playTrack(track) {
  activeTrackId = track.id;
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
      els.nowPlaying.textContent = `▶ ${track.title}`;
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

async function loadTracks() {
  const response = await fetch("/tracks");
  if (!response.ok) {
    showToast("Couldn't load tracks.");
    return;
  }
  tracks = await response.json();
  renderTracks();
}

async function refresh() {
  const response = await fetch("/refresh", { method: "POST" });
  if (!response.ok) {
    showToast("Couldn't reach YouTube — try refresh again.");
    return;
  }
  tracks = await response.json();
  renderTracks();
}

function nextGif() {
  if (!GIFS.length) {
    showToast("No GIFs bundled. Drop files in static/gifs/ and edit GIFS in app.js.");
    return;
  }
  gifIndex = (gifIndex + 1) % GIFS.length;
  els.backdrop.style.backgroundImage = `url('/static/gifs/${GIFS[gifIndex]}')`;
}

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
  loadTracks();
}

init();
