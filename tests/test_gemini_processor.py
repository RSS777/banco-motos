import json

import pytest
from google.genai import types

from pipeline.interfaces import ProcessingError
from pipeline.processors.gemini_processor import GeminiProcessor
from tests.fakes import candidate

FAKE_RESULT = {
    "theme": "tema",
    "hook": "gancho",
    "format": "formato",
    "script_pt_br": "roteiro",
}


class _FakeResponse:
    def __init__(self, data: dict):
        self.text = json.dumps(data)


class _FakeModels:
    def __init__(self):
        self.last_contents = None

    def generate_content(self, model, contents, config):
        self.last_contents = contents
        return _FakeResponse(FAKE_RESULT)


class _FakeUploadedFile:
    state = type("State", (), {"name": "ACTIVE"})()
    name = "files/fake123"


class _FakeFiles:
    def upload(self, file):
        return _FakeUploadedFile()

    def get(self, name):
        return _FakeUploadedFile()


class _FakeClient:
    def __init__(self):
        self.models = _FakeModels()
        self.files = _FakeFiles()


def test_youtube_candidate_without_local_file_uses_native_url_no_upload():
    client = _FakeClient()
    processor = GeminiProcessor(client=client)
    yt_candidate = candidate("https://www.youtube.com/watch?v=abc123", platform="youtube")

    result = processor.process(yt_candidate)

    assert result.script_pt_br == "roteiro"
    video_part = client.models.last_contents[0]
    assert isinstance(video_part, types.Part)
    assert video_part.file_data.file_uri == "https://www.youtube.com/watch?v=abc123"


def test_candidate_with_local_video_path_uploads_instead_of_using_url():
    client = _FakeClient()
    processor = GeminiProcessor(client=client)
    tiktok_candidate = candidate(
        "https://www.tiktok.com/@x/video/1",
        platform="tiktok",
        local_video_path="/tmp/some-video.mp4",
    )

    result = processor.process(tiktok_candidate)

    assert result.script_pt_br == "roteiro"
    video_part = client.models.last_contents[0]
    assert isinstance(video_part, _FakeUploadedFile)


def test_non_youtube_candidate_without_local_file_raises_processing_error():
    client = _FakeClient()
    processor = GeminiProcessor(client=client)
    tiktok_candidate_missing_download = candidate(
        "https://www.tiktok.com/@x/video/1", platform="tiktok"
    )

    with pytest.raises(ProcessingError):
        processor.process(tiktok_candidate_missing_download)

    # Never even attempted a Gemini call.
    assert client.models.last_contents is None
