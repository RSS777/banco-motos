import os

import pytest

from pipeline.interfaces import ProcessingError
from pipeline.models import ProcessedResult
from pipeline.processors.tiktok_download_processor import TikTokDownloadingProcessor
from tests.fakes import candidate


class _FakeYoutubeDLWritesFile:
    """Stands in for yt_dlp.YoutubeDL: writes a dummy file into the
    outtmpl's directory, like a real download would.
    """

    def __init__(self, options):
        self._dir = os.path.dirname(options["outtmpl"])

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def download(self, urls):
        with open(os.path.join(self._dir, "video.mp4"), "wb") as f:
            f.write(b"fake video bytes")


class _FakeYoutubeDLAlwaysFails:
    def __init__(self, options):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def download(self, urls):
        raise RuntimeError("captcha bloqueado")


class _RecordingInnerProcessor:
    def __init__(self):
        self.seen_paths: list[str] = []

    def process(self, candidate) -> ProcessedResult:
        assert candidate.local_video_path is not None
        assert os.path.exists(candidate.local_video_path)
        self.seen_paths.append(candidate.local_video_path)
        return ProcessedResult(theme="t", hook="h", format="f", script_pt_br="s")


def test_downloads_delegates_to_inner_and_cleans_up_afterwards(monkeypatch):
    import pipeline.processors.tiktok_download_processor as module

    monkeypatch.setattr(module.yt_dlp, "YoutubeDL", _FakeYoutubeDLWritesFile)
    inner = _RecordingInnerProcessor()
    processor = TikTokDownloadingProcessor(inner=inner)

    result = processor.process(candidate("https://www.tiktok.com/@x/video/1", platform="tiktok"))

    assert result.script_pt_br == "s"
    assert len(inner.seen_paths) == 1
    # The temp dir (and the file in it) must be gone once processing returns.
    assert not os.path.exists(inner.seen_paths[0])


def test_download_failure_raises_processing_error_and_leaves_no_file(monkeypatch, tmp_path):
    import pipeline.processors.tiktok_download_processor as module

    monkeypatch.setattr(module.yt_dlp, "YoutubeDL", _FakeYoutubeDLAlwaysFails)
    inner = _RecordingInnerProcessor()
    processor = TikTokDownloadingProcessor(inner=inner)

    with pytest.raises(ProcessingError):
        processor.process(candidate("https://www.tiktok.com/@x/video/2", platform="tiktok"))

    assert inner.seen_paths == []  # inner processor never even called
