from __future__ import annotations

from dataclasses import dataclass

from .llm import LlmProvider, parse_json_object


PODCAST_MODES = {"educational", "controversial", "interview"}


@dataclass(frozen=True)
class PodcastTurn:
    speaker: str
    text: str


@dataclass(frozen=True)
class PodcastScript:
    title: str
    mode: str
    summary: str
    speakers: list[str]
    turns: list[PodcastTurn]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "mode": self.mode,
            "summary": self.summary,
            "speakers": self.speakers,
            "turns": [{"speaker": turn.speaker, "text": turn.text} for turn in self.turns],
        }


@dataclass(frozen=True)
class InteractivePodcastStep:
    speaker: str
    text: str
    follow_up: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "speaker": self.speaker,
            "text": self.text,
            "follow_up": self.follow_up,
        }


def generate_podcast_script(text: str, provider: LlmProvider, mode: str, max_chars: int = 16000) -> PodcastScript:
    if mode not in PODCAST_MODES:
        raise ValueError(f"Unsupported podcast mode: {mode}")
    speaker_contract = {
        "educational": "host, explainer, skeptic",
        "controversial": "host, position_a, position_b, fact_checker",
        "interview": "host, expert, listener",
    }[mode]
    prompt = f"""
Create a concise podcast script from the source text.
Mode: {mode}
Speakers: {speaker_contract}
Return JSON only:
{{
  "title": "episode title",
  "summary": "one paragraph",
  "speakers": ["host"],
  "turns": [
    {{"speaker": "host", "text": "spoken line"}}
  ]
}}

Rules:
- Keep turns short enough for TTS.
- Do not invent facts beyond the source.
- Make disagreement explicit only in controversial mode.

Source:
{text[:max_chars]}
"""
    data = parse_json_object(provider.generate(prompt, mode="json"))
    turns = [
        PodcastTurn(speaker=str(item.get("speaker", "host")), text=str(item.get("text", "")).strip())
        for item in data.get("turns", [])
        if str(item.get("text", "")).strip()
    ]
    return PodcastScript(
        title=str(data.get("title", "Untitled Podcast")).strip() or "Untitled Podcast",
        mode=mode,
        summary=str(data.get("summary", "")).strip(),
        speakers=[str(speaker) for speaker in data.get("speakers", [])],
        turns=turns,
    )


def generate_interactive_step(
    text: str,
    provider: LlmProvider,
    mode: str,
    history: list[PodcastTurn],
    interruption: str | None = None,
    max_chars: int = 12000,
) -> InteractivePodcastStep:
    if mode not in PODCAST_MODES:
        raise ValueError(f"Unsupported podcast mode: {mode}")
    speaker_contract = {
        "educational": "host, explainer, skeptic",
        "controversial": "host, position_a, position_b, fact_checker",
        "interview": "host, expert, listener",
    }[mode]
    history_block = "\n".join(f"{turn.speaker}: {turn.text}" for turn in history[-8:])
    interruption_block = interruption or ""
    prompt = f"""
You are continuing a live podcast.
Mode: {mode}
Speakers: {speaker_contract}
Current transcript:
{history_block or "(none yet)"}

If the user interrupted with a follow-up, respond directly to it:
{interruption_block or "(no interruption)"}

Return JSON only:
{{
  "speaker": "host",
  "text": "spoken line",
  "follow_up": "short question for the user or empty string"
}}

Rules:
- Keep the segment short and speakable.
- Keep it consistent with the transcript and source text.
- Do not invent facts beyond the source.

Source:
{text[:max_chars]}
"""
    data = parse_json_object(provider.generate(prompt, mode="json"))
    return InteractivePodcastStep(
        speaker=str(data.get("speaker", "host")).strip() or "host",
        text=str(data.get("text", "")).strip(),
        follow_up=str(data.get("follow_up", "")).strip(),
    )
