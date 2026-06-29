from __future__ import annotations

from bookcast.characters import suggest_characters
from bookcast.llm import LlmProvider
from bookcast.podcast import generate_podcast_script, podcast_script_from_dict


def test_suggest_characters_from_llm_json() -> None:
    provider = _FakeProvider(
        '{"characters":[{"name":"Ada","role":"character","evidence":"dialogue"},{"name":"Narrator","role":"narrator","evidence":"summary"}]}'
    )

    characters = suggest_characters("Ada said hello.", provider)

    assert [character.name for character in characters] == ["Ada", "Narrator"]
    assert characters[0].role == "character"


def test_generate_podcast_script_from_llm_json() -> None:
    provider = _FakeProvider(
        '{"title":"Episode","summary":"Short summary","speakers":["host","explainer"],'
        '"citations":["source-backed point"],'
        '"turns":[{"speaker":"host","text":"Welcome."},{"speaker":"explainer","text":"Here is the idea."}]}'
    )

    script = generate_podcast_script(
        "Source text",
        provider,
        mode="educational",
        focus="practical use",
        style="calm expert",
    )

    assert script.title == "Episode"
    assert script.mode == "educational"
    assert script.speakers == ["host", "explainer"]
    assert script.citations == ["source-backed point"]
    assert script.turns[1].text == "Here is the idea."
    assert "Focus: practical use" in provider.prompts[0]
    assert "Style: calm expert" in provider.prompts[0]


def test_podcast_script_from_dict_normalizes_saved_json() -> None:
    script = podcast_script_from_dict(
        {
            "title": "Saved",
            "mode": "invalid",
            "summary": "Summary",
            "speakers": [],
            "citations": "not a list",
            "turns": [{"speaker": "host", "text": "Welcome."}],
        },
        fallback_mode="interview",
    )

    assert script.title == "Saved"
    assert script.mode == "interview"
    assert script.speakers == ["host"]
    assert script.citations == []
    assert script.turns[0].text == "Welcome."


class _FakeProvider(LlmProvider):
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    def health(self) -> bool:
        return True

    def generate(self, prompt: str, mode: str = "json") -> str:
        assert mode == "json"
        assert prompt
        self.prompts.append(prompt)
        return self.response
