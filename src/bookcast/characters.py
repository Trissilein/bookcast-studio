from __future__ import annotations

from dataclasses import dataclass

from .llm import LlmProvider, parse_json_object


@dataclass(frozen=True)
class CharacterCandidate:
    name: str
    role: str
    evidence: str


def suggest_characters(text: str, provider: LlmProvider, max_chars: int = 12000) -> list[CharacterCandidate]:
    prompt = f"""
Extract recurring speakers or characters from this book excerpt.
Return JSON only:
{{
  "characters": [
    {{"name": "Narrator", "role": "narrator|character|speaker", "evidence": "short reason"}}
  ]
}}

Text:
{text[:max_chars]}
"""
    data = parse_json_object(provider.generate(prompt, mode="json"))
    result: list[CharacterCandidate] = []
    for item in data.get("characters", []):
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        result.append(
            CharacterCandidate(
                name=name,
                role=str(item.get("role", "character")).strip() or "character",
                evidence=str(item.get("evidence", "")).strip(),
            )
        )
    return result

