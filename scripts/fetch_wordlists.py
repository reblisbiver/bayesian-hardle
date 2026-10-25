"""Fetch the supervisor-specified ISSUE-004 vocabulary inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "wordlists"
LEGAL_URL = "https://raw.githubusercontent.com/asweigart/wordletools/main/list-of-valid-guess-words.txt"
ANSWER_URL = "https://gist.githubusercontent.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b/raw/wordle-answers-alphabetical.txt"
ADDITIONAL_GUESSES = ("covid", "padel")


def _download(url: str) -> bytes:
    return urlopen(url, timeout=60).read()


def _validate(data: bytes, expected_count: int) -> list[str]:
    words = [line.strip().lower() for line in data.decode("ascii").splitlines() if line.strip()]
    if len(words) != expected_count or len(set(words)) != expected_count:
        raise RuntimeError(f"expected {expected_count} unique words, got {len(words)}")
    if any(len(word) != 5 or not word.isascii() or not word.isalpha() for word in words):
        raise RuntimeError("every word must be five ASCII alphabetic letters")
    return words


def main() -> None:
    legal_bytes = _download(LEGAL_URL)
    answer_bytes = _download(ANSWER_URL)
    legal_words = _validate(legal_bytes, 12972)
    answer_words = _validate(answer_bytes, 2315)
    if not set(answer_words).issubset(set(legal_words) | set(ADDITIONAL_GUESSES)):
        raise RuntimeError("candidate-answer list must be a subset of the legal guess set")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "wordle-legal-guesses.txt").write_bytes(legal_bytes)
    (OUT / "wordle-candidate-answers.txt").write_bytes(answer_bytes)
    provenance = {
        "legal_guess_source": {
            "url": LEGAL_URL,
            "base_count": len(legal_words),
            "sha256": hashlib.sha256(legal_bytes).hexdigest(),
        },
        "hardle_additions": list(ADDITIONAL_GUESSES),
        "legal_guess_count": len(set(legal_words) | set(ADDITIONAL_GUESSES)),
        "candidate_answer_source": {
            "url": ANSWER_URL,
            "count": len(answer_words),
            "sha256": hashlib.sha256(answer_bytes).hexdigest(),
        },
        "scheduled_answer_membership": {
            "used": False,
            "solver_knowledge": False,
        },
    }
    (OUT / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"base_legal": len(legal_words), "legal": len(set(legal_words) | set(ADDITIONAL_GUESSES)), "answers": len(answer_words)}))


if __name__ == "__main__":
    main()
