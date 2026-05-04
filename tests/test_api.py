from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _fake_track(id_="abc123", title="midnight tape"):
    from youtube import Track

    return Track(id=id_, title=title, duration=1800, thumbnail_url="http://t/x.jpg")


def test_app_boots_and_populates_tracks():
    fake_cache = MagicMock()
    with (
        patch("main.list_channel_tracks", return_value=[_fake_track()]) as fetch,
        patch("main.AudioCache", return_value=fake_cache),
    ):
        from main import app

        with TestClient(app) as client:
            assert fetch.called
            response = client.get("/tracks")
            assert response.status_code == 200
            payload = response.json()
            assert len(payload) == 1
            assert payload[0]["id"] == "abc123"


def test_refresh_replaces_track_list():
    fake_cache = MagicMock()
    initial = [_fake_track("a", "first")]
    refreshed = [_fake_track("b", "second"), _fake_track("c", "third")]

    fetch = MagicMock(side_effect=[initial, refreshed])

    with (
        patch("main.list_channel_tracks", fetch),
        patch("main.AudioCache", return_value=fake_cache),
    ):
        from main import app

        with TestClient(app) as client:
            assert client.get("/tracks").json()[0]["id"] == "a"

            response = client.post("/refresh")
            assert response.status_code == 200
            payload = response.json()
            assert [p["id"] for p in payload] == ["b", "c"]

            # Subsequent /tracks reflects the refresh.
            assert [p["id"] for p in client.get("/tracks").json()] == ["b", "c"]


def test_refresh_returns_503_on_fetch_failure():
    fake_cache = MagicMock()
    fetch = MagicMock(side_effect=[[], RuntimeError("network down")])

    with (
        patch("main.list_channel_tracks", fetch),
        patch("main.AudioCache", return_value=fake_cache),
    ):
        from main import app

        with TestClient(app) as client:
            response = client.post("/refresh")
            assert response.status_code == 503


def test_audio_endpoint_streams_cached_file(tmp_path):
    fake_audio = tmp_path / "abc123.m4a"
    fake_audio.write_bytes(b"audio bytes")

    fake_cache = MagicMock()
    fake_cache.get_or_download.return_value = fake_audio

    with (
        patch("main.list_channel_tracks", return_value=[_fake_track()]),
        patch("main.AudioCache", return_value=fake_cache),
    ):
        from main import app

        with TestClient(app) as client:
            response = client.get("/tracks/abc123/audio")
            assert response.status_code == 200
            assert response.content == b"audio bytes"
            fake_cache.get_or_download.assert_called_once_with("abc123")


def test_audio_endpoint_returns_503_on_download_failure(tmp_path):
    fake_cache = MagicMock()
    fake_cache.get_or_download.side_effect = RuntimeError("yt-dlp failed")

    with (
        patch("main.list_channel_tracks", return_value=[_fake_track()]),
        patch("main.AudioCache", return_value=fake_cache),
    ):
        from main import app

        with TestClient(app) as client:
            response = client.get("/tracks/abc123/audio")
            assert response.status_code == 503


def test_root_serves_index_html():
    fake_cache = MagicMock()
    with (
        patch("main.list_channel_tracks", return_value=[]),
        patch("main.AudioCache", return_value=fake_cache),
    ):
        from main import app

        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            assert "<html" in response.text.lower()


def test_static_mount_serves_files():
    fake_cache = MagicMock()
    with (
        patch("main.list_channel_tracks", return_value=[]),
        patch("main.AudioCache", return_value=fake_cache),
    ):
        from main import app

        with TestClient(app) as client:
            response = client.get("/static/index.html")
            assert response.status_code == 200
