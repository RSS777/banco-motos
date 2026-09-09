import json

import pytest
from google.genai import errors, types

from pipeline.interfaces import ProcessingError
from pipeline.processors.gemini_processor import GeminiProcessor
from tests.fakes import candidate

FAKE_RESULT = {
    "theme": "tema",
    "hook": "gancho",
    "format": "formato",
    "script_pt_br": "roteiro",
    "is_duplicate": False,
    "duplicate_reason": "",
}


class _FakeResponse:
    def __init__(self, data: dict):
        self.text = json.dumps(data)


class _FakeModels:
    def __init__(self, results=None):
        self.last_contents = None
        self.all_contents = []
        self._results = list(results) if results is not None else [FAKE_RESULT]
        self._call_index = 0

    def generate_content(self, model, contents, config):
        self.last_contents = contents
        self.all_contents.append(contents)
        result = self._results[min(self._call_index, len(self._results) - 1)]
        self._call_index += 1
        if isinstance(result, Exception):
            raise result
        return _FakeResponse(result)


class _FakeUploadedFile:
    state = type("State", (), {"name": "ACTIVE"})()
    name = "files/fake123"


class _FakeFiles:
    def upload(self, file):
        return _FakeUploadedFile()

    def get(self, name):
        return _FakeUploadedFile()


class _FakeClient:
    def __init__(self, results=None):
        self.models = _FakeModels(results=results)
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


def test_recent_themes_are_included_in_the_prompt():
    client = _FakeClient()
    processor = GeminiProcessor(
        client=client, recent_themes=["review de scooter urbana — gancho de preço"]
    )
    yt_candidate = candidate("https://www.youtube.com/watch?v=abc123", platform="youtube")

    processor.process(yt_candidate)

    prompt_text = client.models.last_contents[1]
    assert "review de scooter urbana — gancho de preço" in prompt_text


def test_duplicate_idea_flagged_by_gemini_is_reflected_in_result():
    duplicate_result = dict(FAKE_RESULT, is_duplicate=True, duplicate_reason="mesmo review de X")
    client = _FakeClient(results=[duplicate_result])
    processor = GeminiProcessor(client=client)
    yt_candidate = candidate("https://www.youtube.com/watch?v=abc123", platform="youtube")

    result = processor.process(yt_candidate)

    assert result.is_duplicate is True
    assert result.duplicate_reason == "mesmo review de X"


def test_duplicate_result_does_not_join_recent_themes_but_original_does():
    first = dict(FAKE_RESULT, theme="tema A", hook="gancho A", is_duplicate=False)
    second = dict(FAKE_RESULT, theme="tema B", hook="gancho B", is_duplicate=True)
    client = _FakeClient(results=[first, second])
    processor = GeminiProcessor(client=client)

    processor.process(candidate("https://www.youtube.com/watch?v=a", platform="youtube"))
    processor.process(candidate("https://www.youtube.com/watch?v=b", platform="youtube"))

    assert processor._recent_themes == ["tema A — gancho A"]


def test_transient_server_error_is_retried_and_eventually_succeeds(monkeypatch):
    import pipeline.processors.gemini_processor as module

    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    overload = errors.ServerError(503, {"error": {"message": "overloaded"}})
    client = _FakeClient(results=[overload, FAKE_RESULT])
    processor = GeminiProcessor(client=client)

    result = processor.process(candidate("https://www.youtube.com/watch?v=a", platform="youtube"))

    assert result.script_pt_br == "roteiro"
    assert client.models._call_index == 2  # first attempt failed, second succeeded


def test_server_error_exhausts_retries_and_raises_processing_error(monkeypatch):
    import pipeline.processors.gemini_processor as module

    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    overload = errors.ServerError(503, {"error": {"message": "overloaded"}})
    client = _FakeClient(results=[overload, overload, overload])
    processor = GeminiProcessor(client=client)

    with pytest.raises(ProcessingError):
        processor.process(candidate("https://www.youtube.com/watch?v=a", platform="youtube"))

    assert client.models._call_index == module.MAX_ATTEMPTS


def test_rate_limit_429_is_retried_like_server_error(monkeypatch):
    import pipeline.processors.gemini_processor as module

    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    rate_limited = errors.ClientError(429, {"error": {"message": "rate limited"}})
    client = _FakeClient(results=[rate_limited, FAKE_RESULT])
    processor = GeminiProcessor(client=client)

    result = processor.process(candidate("https://www.youtube.com/watch?v=a", platform="youtube"))

    assert result.script_pt_br == "roteiro"


def test_non_retryable_client_error_fails_immediately_without_retry(monkeypatch):
    import pipeline.processors.gemini_processor as module

    def fail_if_slept(_seconds):
        raise AssertionError("should not retry a non-retryable client error")

    monkeypatch.setattr(module.time, "sleep", fail_if_slept)
    bad_request = errors.ClientError(400, {"error": {"message": "bad request"}})
    client = _FakeClient(results=[bad_request, FAKE_RESULT])
    processor = GeminiProcessor(client=client)

    with pytest.raises(ProcessingError):
        processor.process(candidate("https://www.youtube.com/watch?v=a", platform="youtube"))

    assert client.models._call_index == 1  # never attempted a second call
