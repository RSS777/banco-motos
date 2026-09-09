import json
import os
import time

from google import genai
from google.genai import types

from pipeline.interfaces import ProcessingError
from pipeline.models import ProcessedResult, VideoCandidate

DEFAULT_MODEL = "gemini-flash-lite-latest"

PROMPT = """Você é um analista de conteúdo de vídeos curtos sobre moto elétrica.

Analise o vídeo em anexo (estrutura, ritmo, cortes, gancho inicial, argumento,
enquadramento) e devolva um JSON com:

- "theme": o tema central do vídeo, em poucas palavras.
- "hook": o gancho/abertura que prende atenção nos primeiros segundos.
- "format": o formato/estrutura (ex.: "review rápido com corte a cada 3s",
  "storytime com texto na tela", "comparativo lado a lado").
- "script_pt_br": um roteiro ORIGINAL em português do Brasil, detalhado o
  suficiente para alguém replicar o FORMATO gravando um vídeo do zero.
  Nunca transcreva ou copie falas/texto literal do vídeo original — descreva
  a estrutura e escreva um roteiro novo inspirado nela.

Responda só com o JSON, sem markdown."""

RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "theme": types.Schema(type=types.Type.STRING),
        "hook": types.Schema(type=types.Type.STRING),
        "format": types.Schema(type=types.Type.STRING),
        "script_pt_br": types.Schema(type=types.Type.STRING),
    },
    required=["theme", "hook", "format", "script_pt_br"],
)


class GeminiProcessor:
    """Processor: a single multimodal Gemini call that both analyzes a
    local video file and writes its pt-BR replication script, so a
    candidate is never sent to Gemini twice.

    Requires candidate.local_video_path to be set (by a prior download
    step, e.g. #7's transitory TikTok download) — this processor does not
    fetch video itself.
    """

    def __init__(self, client: genai.Client, model: str = DEFAULT_MODEL):
        self._client = client
        self._model = model

    @classmethod
    def from_env(cls, **kwargs) -> "GeminiProcessor":
        return cls(client=genai.Client(api_key=os.environ["GEMINI_API_KEY"]), **kwargs)

    def process(self, candidate: VideoCandidate) -> ProcessedResult:
        if not candidate.local_video_path:
            raise ProcessingError(
                f"no local video file for candidate {candidate.url}; "
                "a download step must set local_video_path before processing"
            )

        try:
            video_file = self._client.files.upload(file=candidate.local_video_path)
            video_file = self._wait_until_active(video_file)

            response = self._client.models.generate_content(
                model=self._model,
                contents=[video_file, PROMPT],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                ),
            )
            data = json.loads(response.text)
        except Exception as exc:  # noqa: BLE001 - any Gemini/network failure is a processing failure
            raise ProcessingError(f"Gemini processing failed for {candidate.url}: {exc}") from exc

        return ProcessedResult(
            theme=data["theme"],
            hook=data["hook"],
            format=data["format"],
            script_pt_br=data["script_pt_br"],
        )

    def _wait_until_active(self, video_file, timeout_seconds: int = 60):
        start = time.monotonic()
        while video_file.state.name == "PROCESSING":
            if time.monotonic() - start > timeout_seconds:
                raise ProcessingError(f"timed out waiting for Gemini to process {video_file.name}")
            time.sleep(2)
            video_file = self._client.files.get(name=video_file.name)
        if video_file.state.name != "ACTIVE":
            raise ProcessingError(f"Gemini file {video_file.name} ended in state {video_file.state.name}")
        return video_file
