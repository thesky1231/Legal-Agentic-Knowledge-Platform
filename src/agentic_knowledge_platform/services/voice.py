from __future__ import annotations

import hashlib

from agentic_knowledge_platform.types import ModelRequest, VoiceJob


class StubSpeechSynthesizer:
    def synthesize(self, script: str, voice: str) -> dict[str, int | str]:
        digest = hashlib.sha1(f"{voice}|{script}".encode("utf-8")).hexdigest()[:10]
        return {
            "audio_url": f"https://demo.local/audio/{digest}.wav",
            "duration_ms": max(1800, len(script) * 35),
        }


class StubAvatarRenderer:
    def enqueue(self, script: str, voice: str) -> dict[str, str]:
        digest = hashlib.sha1(f"{voice}|avatar|{script}".encode("utf-8")).hexdigest()[:10]
        return {"avatar_job_id": f"a2f-{digest}", "status": "queued"}


class VoicePipeline:
    def __init__(self, model_router, synthesizer: StubSpeechSynthesizer, avatar_renderer: StubAvatarRenderer) -> None:
        self.model_router = model_router
        self.synthesizer = synthesizer
        self.avatar_renderer = avatar_renderer

    def narrate(self, text: str, voice: str = "mentor") -> VoiceJob:
        speech_source = text.split("\n引用：", maxsplit=1)[0].strip()
        script_response = self.model_router.generate(
            ModelRequest(
                task="speech_script",
                prompt="将回答转换为适合 60 到 90 秒的讲解脚本",
                context_blocks=[speech_source],
            )
        )
        synth = self.synthesizer.synthesize(script_response.output, voice)
        avatar = self.avatar_renderer.enqueue(script_response.output, voice)
        digest = hashlib.sha1(f"{voice}|job|{text}".encode("utf-8")).hexdigest()[:10]
        return VoiceJob(
            job_id=f"voice-{digest}",
            voice=voice,
            text=text,
            script=script_response.output,
            audio_url=str(synth["audio_url"]),
            avatar_job_id=avatar["avatar_job_id"],
            avatar_status=avatar["status"],
            estimated_latency_ms=int(synth["duration_ms"]) + 800,
        )
