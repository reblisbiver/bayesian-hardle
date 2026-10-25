"""Exact game semantics and vocabulary boundaries for Bayesian Hardle."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol, Sequence, Tuple, Union, runtime_checkable


Feedback = Tuple[int, int]


def _normalise_word(word: str, word_length: int = 5) -> str:
    if not isinstance(word, str):
        raise TypeError("words must be strings")
    value = word.strip().lower()
    if len(value) != word_length or not value.isascii() or not value.isalpha():
        raise ValueError(f"word must be {word_length} alphabetic ASCII letters")
    return value


def _normalise_words(words: Iterable[str], word_length: int = 5) -> Tuple[str, ...]:
    result = []
    seen = set()
    for word in words:
        value = _normalise_word(word, word_length)
        if value not in seen:
            result.append(value)
            seen.add(value)
    return tuple(result)


@runtime_checkable
class VocabularyRepository(Protocol):
    """Provides legal guesses separately from candidate answers."""

    def legal_guesses(self) -> Sequence[str]:
        ...

    def target_vocabulary(self) -> Sequence[str]:
        ...


class WordListVocabularyRepository:
    """Immutable in-memory vocabulary loaded from explicit source lists."""

    HARDLE_ADDITIONAL_GUESSES = ("covid", "padel")

    def __init__(
        self,
        legal_words: Iterable[str],
        answer_words: Iterable[str],
        additional_legal_guesses: Iterable[str] = HARDLE_ADDITIONAL_GUESSES,
    ) -> None:
        legal = list(_normalise_words(legal_words))
        answers = _normalise_words(answer_words)
        extras = _normalise_words(additional_legal_guesses)
        legal_set = set(legal)
        for extra in extras:
            if extra not in legal_set:
                legal.append(extra)
                legal_set.add(extra)
        answer_set = set(answers)
        if not answer_set:
            raise ValueError("answer vocabulary cannot be empty")
        if not answer_set.issubset(legal_set):
            missing = sorted(answer_set - legal_set)
            raise ValueError("answer words must be legal guesses: " + ", ".join(missing))
        self._legal_guesses = tuple(sorted(legal))
        self._target_vocabulary = tuple(sorted(answers))

    @classmethod
    def from_files(
        cls,
        legal_path: str | Path,
        answer_path: str | Path,
        additional_legal_guesses: Iterable[str] = HARDLE_ADDITIONAL_GUESSES,
    ) -> "WordListVocabularyRepository":
        def read(path: str | Path) -> Tuple[str, ...]:
            return tuple(Path(path).read_text(encoding="utf-8").splitlines())

        return cls(read(legal_path), read(answer_path), additional_legal_guesses)

    @classmethod
    def from_repository_root(cls, repository_root: str | Path) -> "WordListVocabularyRepository":
        root = Path(repository_root) / "data" / "wordlists"
        return cls.from_files(
            root / "wordle-legal-guesses.txt",
            root / "wordle-candidate-answers.txt",
        )

    def legal_guesses(self) -> Sequence[str]:
        return self._legal_guesses

    def target_vocabulary(self) -> Sequence[str]:
        return self._target_vocabulary


@runtime_checkable
class FeedbackEngine(Protocol):
    """Returns exact-position and present-but-wrong-position counts."""

    def evaluate(self, guess: str, target: str) -> Feedback:
        ...


class HardleFeedbackEngine:
    """Wordle-compatible duplicate-aware feedback engine."""

    def __init__(self, game_spec: Union["GameSpec", int] = 5) -> None:
        if isinstance(game_spec, int):
            if game_spec <= 0:
                raise ValueError("word_length must be positive")
            self.game_spec = GameSpec(word_length=game_spec, max_guesses=10)
        else:
            self.game_spec = game_spec

    def evaluate(self, guess: str, target: str) -> Feedback:
        guess = _normalise_word(guess, self.game_spec.word_length)
        target = _normalise_word(target, self.game_spec.word_length)
        exact = 0
        remaining_target = {}
        remaining_guess = {}
        for guessed, actual in zip(guess, target):
            if guessed == actual:
                exact += 1
            else:
                remaining_target[actual] = remaining_target.get(actual, 0) + 1
                remaining_guess[guessed] = remaining_guess.get(guessed, 0) + 1
        present = sum(
            min(count, remaining_target.get(letter, 0))
            for letter, count in remaining_guess.items()
        )
        return exact, present


@runtime_checkable
class TerminalRules(Protocol):
    """Determines whether a game state is terminal."""

    def is_terminal(
        self,
        guess: str,
        feedback: Feedback,
        guess_number: int,
        game_spec: "GameSpec",
    ) -> bool:
        ...


class HardleTerminalRules:
    """Win on an all-exact feedback or stop at the finite guess limit."""

    def is_win(self, feedback: Feedback, game_spec: "GameSpec") -> bool:
        return feedback == (game_spec.word_length, 0)

    def is_terminal(
        self,
        guess: str,
        feedback: Feedback,
        guess_number: int,
        game_spec: "GameSpec",
    ) -> bool:
        if guess_number <= 0:
            raise ValueError("guess_number must be positive")
        return self.is_win(feedback, game_spec) or guess_number >= game_spec.max_guesses


@dataclass(frozen=True)
class GameSpec:
    """Static game limits."""

    word_length: int
    max_guesses: int

    def __post_init__(self) -> None:
        if self.word_length <= 0:
            raise ValueError("word_length must be positive")
        if self.max_guesses <= 0:
            raise ValueError("max_guesses must be positive")
