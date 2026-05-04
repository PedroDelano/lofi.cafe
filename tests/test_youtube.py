from pathlib import Path
from unittest.mock import MagicMock, patch

import youtube


def test_list_channel_tracks_returns_tracks_from_yt_dlp_entries():
    fake_info = {
        "entries": [
            {
                "id": "abc123",
                "title": "midnight tape",
                "duration": 1800,
                "thumbnails": [{"url": "https://i.ytimg.com/vi/abc123/hq.jpg"}],
            },
            {
                "id": "def456",
                "title": "5am study",
                "duration": 2100,
                "thumbnails": [{"url": "https://i.ytimg.com/vi/def456/hq.jpg"}],
            },
        ]
    }

    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value.extract_info.return_value = fake_info

    with patch("youtube.yt_dlp.YoutubeDL", return_value=fake_ydl) as ctor:
        tracks = youtube.list_channel_tracks()

    assert len(tracks) == 2
    assert tracks[0].id == "abc123"
    assert tracks[0].title == "midnight tape"
    assert tracks[0].duration == 1800
    assert tracks[0].thumbnail_url == "https://i.ytimg.com/vi/abc123/hq.jpg"
    # Confirm we asked yt-dlp to extract flat metadata only.
    opts = ctor.call_args.args[0]
    assert opts.get("extract_flat") is True
    assert opts.get("playlistend") == 20


def test_list_channel_tracks_handles_missing_thumbnails():
    fake_info = {
        "entries": [{"id": "x", "title": "t", "duration": 60}],
    }
    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value.extract_info.return_value = fake_info

    with patch("youtube.yt_dlp.YoutubeDL", return_value=fake_ydl):
        tracks = youtube.list_channel_tracks()

    assert tracks[0].thumbnail_url == ""


def test_download_audio_writes_file_and_returns_path(tmp_path: Path):
    video_id = "abc123"
    expected_file = tmp_path / f"{video_id}.m4a"

    fake_ydl_inst = MagicMock()

    def _fake_extract_info(_url, download):
        assert download is True
        expected_file.write_bytes(b"fake audio")
        return {"id": video_id, "ext": "m4a"}

    fake_ydl_inst.extract_info.side_effect = _fake_extract_info
    fake_ydl_inst.prepare_filename.return_value = str(expected_file)

    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value = fake_ydl_inst

    with patch("youtube.yt_dlp.YoutubeDL", return_value=fake_ydl) as ctor:
        result = youtube.download_audio(video_id, tmp_path)

    assert result == expected_file
    assert result.exists()
    assert result.read_bytes() == b"fake audio"
    # download() should NOT have been called separately — extract_info(download=True) handles both.
    fake_ydl_inst.download.assert_not_called()

    opts = ctor.call_args.args[0]
    assert opts["format"].startswith("bestaudio")
    assert str(tmp_path) in opts["outtmpl"]
