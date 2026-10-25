"""Contracts for the shared game model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


class VocabularyRepository(Protocol):
    """Provides the legal-guess and target vocabularies."""

    def legal_guesses(self) -> Sequence[str]:
        ...

    def target_vocabulary(self) -> Sequence[str]:
        ...


class FeedbackEngine(Protocol):
    """Defines the feedback boundary without defining feedback semantics."""

    def evaluate(self, guess: str, target: str) -> Sequence[str]:
        ...


class TerminalRules(Protocol):
    """Determines whether a game state is terminal."""

    def is_terminal(
        self,
        guess: str,
        feedback: Sequence[str],
        guess_number: int,
        game_spec: "GameSpec",
    ) -> bool:
        ...


@dataclass(frozen=True)
class GameSpec:
    """Static game limits needed by components without encoding game rules."""

    word_length: int
    max_guesses: int

    def __post_init__(self) -> None:
        if self.word_length <= 0:
            raise ValueError("word_length must be positive")
        if self.max_guesses <= 0:
            raise ValueError("max_guesses must be positive")
