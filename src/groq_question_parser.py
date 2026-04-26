from __future__ import annotations

import json
import os
from typing import Any

import requests


GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"
_ENV_LOADED = False

VALID_TOPICS = {
    "wealth",
    "marriage",
    "children",
    "illness",
    "career",
    "property",
    "siblings",
    "longevity",
    "father",
    "travel",
    "legal",
    "loss",
}

HOUSE_TOPIC = {
    1: "wealth",
    2: "wealth",
    3: "siblings",
    4: "property",
    5: "children",
    6: "illness",
    7: "marriage",
    8: "longevity",
    9: "travel",
    10: "career",
    11: "wealth",
    12: "loss",
}

_RELATION_BASE_HOUSES = {
    "child": 5,
    "children": 5,
    "son": 5,
    "daughter": 5,
    "mother": 4,
    "father": 9,
    "brother": 3,
    "sister": 3,
    "sibling": 3,
    "wife": 7,
    "husband": 7,
    "spouse": 7,
    "partner": 7,
    "friend": 11,
}

_MATTER_HOUSES = {
    "job": 10,
    "career": 10,
    "profession": 10,
    "work": 10,
    "marriage": 7,
    "married": 7,
    "marry": 7,
    "wedding": 7,
    "wife": 7,
    "husband": 7,
    "spouse": 7,
    "health": 6,
    "illness": 6,
    "sick": 6,
    "property": 4,
    "house": 4,
    "land": 4,
    "money": 2,
    "wealth": 2,
    "valuables": 2,
    "valuable": 2,
    "item": 2,
    "article": 2,
    "lost": 2,
    "stolen": 2,
    "longevity": 8,
    "death": 8,
    "life": 8,
}

_MATTER_LABELS = {
    "job": "career",
    "work": "career",
    "profession": "career",
    "married": "marriage",
    "marry": "marriage",
    "wedding": "marriage",
    "sick": "illness",
    "lost": "lost property",
    "stolen": "lost property",
    "item": "lost property",
    "article": "lost property",
}


def _ordinal(number: int) -> str:
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _load_local_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True

    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except OSError:
        return


def get_groq_api_key() -> str | None:
    _load_local_env()
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key

    try:
        import streamlit as st

        return st.secrets.get("GROQ_API_KEY")
    except Exception:
        return None


def groq_is_configured() -> bool:
    return bool(get_groq_api_key())


def _extract_json(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _sanitize_result(raw: dict[str, Any], original_question: str) -> dict[str, Any] | None:
    try:
        query_house = int(raw.get("query_house"))
    except (TypeError, ValueError):
        return None

    if query_house < 1 or query_house > 12:
        return None

    query_topic = str(raw.get("query_topic") or HOUSE_TOPIC.get(query_house, "wealth")).lower().strip()
    if query_topic not in VALID_TOPICS:
        query_topic = HOUSE_TOPIC.get(query_house, "wealth")

    confidence = str(raw.get("confidence") or "medium").lower().strip()
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"

    needs_clarification = bool(raw.get("needs_clarification", False))
    reasoning = str(raw.get("reasoning") or "Groq identified the relevant Prasna house from the question.").strip()
    rephrased = str(raw.get("rephrased") or original_question).strip()
    if len(rephrased) > 60:
        rephrased = rephrased[:57] + "..."

    return {
        "house": query_house,
        "topic": query_topic,
        "query_topic": query_topic,
        "query_house": query_house,
        "confidence": confidence,
        "rephrased": rephrased,
        "reasoning": reasoning,
        "needs_clarification": needs_clarification,
        "parser": "groq",
        "derived_house_used": bool(raw.get("derived_house_used", False)),
        "base_house": raw.get("base_house"),
        "derived_from": raw.get("derived_from"),
    }


def _apply_common_derived_house_correction(parsed: dict[str, Any], original_question: str) -> dict[str, Any]:
    text = original_question.lower()
    relation_house: int | None = None
    matter_house: int | None = None
    relation_word: str | None = None
    matter_word: str | None = None

    for word, house in _RELATION_BASE_HOUSES.items():
        if word in text:
            relation_house = house
            relation_word = word
            break

    for word, house in _MATTER_HOUSES.items():
        if word == relation_word:
            continue
        if word in text:
            matter_house = house
            matter_word = word
            break

    if relation_house is None or matter_house is None:
        return parsed

    derived_house = ((relation_house - 1) + (matter_house - 1)) % 12 + 1
    if derived_house == parsed.get("query_house") and parsed.get("derived_house_used"):
        return parsed

    parsed = dict(parsed)
    parsed["query_house"] = derived_house
    parsed["house"] = derived_house
    parsed["query_topic"] = HOUSE_TOPIC.get(matter_house, parsed.get("query_topic", "wealth"))
    parsed["topic"] = parsed["query_topic"]
    parsed["derived_house_used"] = True
    parsed["base_house"] = relation_house
    matter_label = _MATTER_LABELS.get(matter_word or "", matter_word)
    parsed["derived_from"] = f"{_ordinal(matter_house)} from {_ordinal(relation_house)} = House {derived_house}."
    parsed["reasoning"] = (
        f"The question concerns {relation_word}'s {matter_label}; using derived houses, "
        f"this becomes House {derived_house}."
    )
    return parsed


def parse_question_with_groq(user_question: str, api_key: str | None = None) -> dict[str, Any] | None:
    key = api_key or get_groq_api_key()
    if not key:
        return None

    system_prompt = """
You classify a single Prasna Tantra horary question.
Return JSON only. No markdown.

Use these houses:
1 self/body, 2 wealth/valuables, 3 siblings/messages, 4 property/home/mother,
5 children/pregnancy/education, 6 illness/enemies/conflict, 7 marriage/partner/legal,
8 longevity/danger/hidden/lost, 9 travel/father/fortune/pilgrimage,
10 career/status/authority, 11 gains/friends/desires, 12 loss/expense/foreign/isolation.

Use derived houses when the question is about another person's matter.
The query_house must be the final derived house, not the natural topic house.
Examples: brother's wife = 7th from 3rd = 9th; child's profession = 10th from 5th = 2nd;
mother's longevity = 8th from 4th = 11th; spouse's money = 2nd from 7th = 8th;
child's marriage = 7th from 5th = 11th; father's health = 6th from 9th = 2nd;
friend's lost article = 2nd from 11th = 12th.

If the question is vague, casual, or not a real single matter, set needs_clarification true.
Do not invent a prediction. Only classify the question.

JSON schema:
{
  "query_house": 1-12,
  "query_topic": "wealth|marriage|children|illness|career|property|siblings|longevity|father|travel|legal|loss",
  "confidence": "high|medium|low",
  "needs_clarification": true|false,
  "rephrased": "short user question",
  "reasoning": "brief house-selection reason",
  "derived_house_used": true|false,
  "base_house": 1-12 or null,
  "derived_from": "brief derived-house explanation or null"
}
""".strip()

    payload = {
        "model": os.environ.get("GROQ_MODEL", DEFAULT_MODEL),
        "temperature": 0,
        "max_tokens": 350,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ],
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=12)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return None

    parsed = _extract_json(content)
    if not parsed:
        return None
    sanitized = _sanitize_result(parsed, user_question)
    if sanitized is None:
        return None
    return _apply_common_derived_house_correction(sanitized, user_question)
