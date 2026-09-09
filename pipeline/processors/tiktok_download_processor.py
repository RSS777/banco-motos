import glob
import os
import tempfile
from dataclasses import replace

import yt_dlp

from pipeline.interfaces import Processor, ProcessingError
from pipeline.models import ProcessedResult, VideoCandidate

YTDLP_FORMAT = "best[vcodec!=none]/best"
# "mp4/best" silently produced an audio-only download for a real TikTok
# video: yt-dlp's extractor found exactly one format for it — "audio",
# mp3, no video track at all. That happens when the underlying video is no
# longer really there (deleted/private since collection) and TikTok falls
# back to serving just the reusable "sound"; yt-dlp still succeeds, so
# nothing here raised, and Gemini ended up analyzing background music
# instead of a video — producing a theme with nothing to do with what the
# link actually shows. "best[vcodec!=none]/best" prefers a real video
# format but still resolves instead of hard-erroring when only audio
# exists; AUDIO_ONLY_EXTENSIONS below is what actually catches that case.
AUDIO_ONLY_EXTENSIONS = {".mp3", ".m4a", ".aac", ".wav", ".opus", ".ogg"}


class TikTokDownloadingProcessor:
    """Processor wrapper: for TikTok candidates, downloads the video via
    yt-dlp into a temp directory, delegates to `inner` (the real Gemini
    analysis/scripting), then always deletes the temp directory —
    success or failure — so the video never persists beyond this single
    call. A download failure (including a TikTok block/captcha) becomes
    a ProcessingError, which the orchestrator already treats as "skip
    this item, keep going" without retrying the same round.

    Any other candidate (e.g. YouTube, which Gemini can fetch natively
    by URL — see GeminiProcessor) is passed straight to `inner` unchanged;
    this wrapper only ever downloads for the one platform that needs it,
    so it can wrap `inner` for the whole daily pipeline, not just TikTok.
    """

    def __init__(self, inner: Processor):
        self._inner = inner

    def process(self, candidate: VideoCandidate) -> ProcessedResult:
        if candidate.platform != "tiktok" or candidate.local_video_path:
            return self._inner.process(candidate)

        with tempfile.TemporaryDirectory(prefix="tiktok-dl-") as tmp_dir:
            video_path = self._download(candidate.url, tmp_dir)
            downloaded_candidate = replace(candidate, local_video_path=video_path)
            return self._inner.process(downloaded_candidate)

    def _download(self, url: str, tmp_dir: str) -> str:
        options = {
            "outtmpl": os.path.join(tmp_dir, "%(id)s.%(ext)s"),
            "format": YTDLP_FORMAT,
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
        except Exception as exc:  # noqa: BLE001 - any download failure (incl. block/captcha) is a skip
            raise ProcessingError(f"TikTok download failed for {url}: {exc}") from exc

        downloaded = glob.glob(os.path.join(tmp_dir, "*"))
        if not downloaded:
            raise ProcessingError(f"TikTok download produced no file for {url}")

        video_path = downloaded[0]
        ext = os.path.splitext(video_path)[1].lower()
        if ext in AUDIO_ONLY_EXTENSIONS:
            raise ProcessingError(
                f"TikTok download for {url} produced an audio-only file ({ext}), "
                "not a video — refusing to analyze the wrong media"
            )
        return video_path
