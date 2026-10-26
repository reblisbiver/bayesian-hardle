"""Exact NumPy acceleration for fixed-vocabulary Hardle feedback."""

from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple

import numpy as np

from .game import _normalise_word
from .belief import BeliefState


class ExactFeedbackCodeMatrix:
    """Read-only exact feedback codes for legal guesses and answer candidates.

    A code is ``exact_count * (word_length + 1) + misplaced_count``.  The
    encoding is deliberately specific to Hardle's two integer feedback values;
    it is not Wordle's positional color-pattern encoding.
    """

    _DEFAULT_GUESS_CHUNK_SIZE = 512

    def __init__(
        self,
        legal_guesses: Sequence[str],
        candidate_answers: Sequence[str],
        codes: np.ndarray,
        word_length: int = 5,
    ) -> None:
        self.legal_guesses = tuple(legal_guesses)
        self.candidate_answers = tuple(candidate_answers)
        self.word_length = word_length
        self._code_base = word_length + 1
        if not self.legal_guesses or not self.candidate_answers:
            raise ValueError("legal guesses and candidate answers cannot be empty")
        if len(set(self.legal_guesses)) != len(self.legal_guesses):
            raise ValueError("legal guesses must be unique")
        if len(set(self.candidate_answers)) != len(self.candidate_answers):
            raise ValueError("candidate answers must be unique")
        expected_shape = (len(self.legal_guesses), len(self.candidate_answers))
        if codes.shape != expected_shape or codes.dtype != np.uint8:
            raise ValueError("codes must be a uint8 matrix matching the vocabularies")
        self._codes = codes
        self._codes.setflags(write=False)
        self._guess_indices = {
            word: index for index, word in enumerate(self.legal_guesses)
        }
        self._answer_indices = {
            word: index for index, word in enumerate(self.candidate_answers)
        }

    @classmethod
    def from_vocabulary(
        cls,
        legal_guesses: Iterable[str],
        candidate_answers: Iterable[str],
        word_length: int = 5,
        guess_chunk_size: int = _DEFAULT_GUESS_CHUNK_SIZE,
    ) -> "ExactFeedbackCodeMatrix":
        """Build the exact matrix with vectorized answer-side operations."""

        legal = tuple(_normalise_word(word, word_length) for word in legal_guesses)
        answers = tuple(_normalise_word(word, word_length) for word in candidate_answers)
        if guess_chunk_size <= 0:
            raise ValueError("guess_chunk_size must be positive")
        if len(set(legal)) != len(legal):
            raise ValueError("legal guesses must be unique")
        if len(set(answers)) != len(answers):
            raise ValueError("candidate answers must be unique")

        guess_codes = cls._encode_words(legal, word_length)
        answer_codes = cls._encode_words(answers, word_length)
        answer_counts = np.zeros((len(answers), 26), dtype=np.uint8)
        for letter in range(26):
            answer_counts[:, letter] = np.count_nonzero(
                answer_codes == letter, axis=1
            ).astype(np.uint8)

        unique_letters = np.zeros(
            (len(legal), word_length), dtype=np.uint8
        )
        unique_counts = np.zeros(
            (len(legal), word_length), dtype=np.uint8
        )
        for index, guess in enumerate(guess_codes):
            letters, counts = np.unique(guess, return_counts=True)
            unique_letters[index, : len(letters)] = letters
            unique_counts[index, : len(counts)] = counts

        codes = np.empty((len(legal), len(answers)), dtype=np.uint8)
        for start in range(0, len(legal), guess_chunk_size):
            stop = min(start + guess_chunk_size, len(legal))
            guess_chunk = guess_codes[start:stop]
            exact = np.count_nonzero(
                answer_codes[:, None, :] == guess_chunk[None, :, :], axis=2
            ).astype(np.uint8)
            target_counts = answer_counts[:, unique_letters[start:stop]]
            overlap = np.minimum(
                target_counts,
                unique_counts[start:stop][None, :, :],
            ).sum(axis=2, dtype=np.uint8)
            misplaced = overlap - exact
            encoded = (
                exact.astype(np.uint16) * cls._code_base(word_length)
                + misplaced.astype(np.uint16)
            ).astype(np.uint8)
            codes[start:stop] = encoded.T
        return cls(legal, answers, codes, word_length)

    @staticmethod
    def _code_base(word_length: int) -> int:
        return word_length + 1

    @staticmethod
    def _encode_words(words: Sequence[str], word_length: int) -> np.ndarray:
        return np.asarray(
            [[ord(letter) - ord("a") for letter in word] for word in words],
            dtype=np.uint8,
        ).reshape(len(words), word_length)

    @property
    def matrix(self) -> np.ndarray:
        """Return the read-only row-major ``uint8`` code matrix."""

        return self._codes

    @property
    def memory_bytes(self) -> int:
        return int(self._codes.nbytes)

    @property
    def code_count(self) -> int:
        return self._code_base * self._code_base

    def guess_index(self, guess: str) -> int:
        return self._guess_indices[guess]

    def answer_index(self, answer: str) -> int:
        return self._answer_indices[answer]

    def answer_indices(self, answers: Sequence[str]) -> np.ndarray:
        return np.asarray(
            [self._answer_indices[answer] for answer in answers],
            dtype=np.intp,
        )

    def contains_answers(self, answers: Sequence[str]) -> bool:
        return all(answer in self._answer_indices for answer in answers)

    def row_for(self, guess: str) -> np.ndarray:
        return self._codes[self.guess_index(guess)]

    def code_for(self, guess: str, answer: str) -> int:
        return int(self._codes[self.guess_index(guess), self.answer_index(answer)])

    def decode_code(self, code: int) -> Tuple[int, int]:
        value = int(code)
        exact, misplaced = divmod(value, self._code_base)
        if (
            exact < 0
            or exact > self.word_length
            or misplaced < 0
            or misplaced > self.word_length - exact
        ):
            raise ValueError("invalid Hardle feedback code")
        return exact, misplaced


class MatrixInformationGainCalculator:
    """Calculates exact deterministic IG from one feedback-code matrix."""

    SMALL_BELIEF_BATCH_THRESHOLD = 64

    def __init__(self, matrix: ExactFeedbackCodeMatrix) -> None:
        self.matrix = matrix

    @staticmethod
    def _weights(belief: BeliefState) -> Tuple[Tuple[str, float], ...]:
        if belief.probability_mass:
            total = belief.total_mass
            if total <= 0:
                raise ValueError("belief must have positive total mass")
            return tuple((word, mass / total) for word, mass in belief.probability_mass)
        if not belief.candidates:
            raise ValueError("belief must contain candidates")
        mass = 1.0 / len(belief.candidates)
        return tuple((word, mass) for word in belief.candidates)

    def outcome_masses(
        self,
        row: np.ndarray,
        answer_indices: np.ndarray,
        weights: np.ndarray,
    ) -> np.ndarray:
        return np.bincount(
            row[answer_indices],
            weights=weights,
            minlength=self.matrix.code_count,
        )

    def entropies_for_rows(
        self,
        rows: np.ndarray,
        weights: np.ndarray,
    ) -> np.ndarray:
        """Return exact outcome entropies for all rows at once.

        This path is used for small posterior supports.  Each of the finite
        Hardle outcome codes is accumulated as one vectorized weighted mask;
        no branch posterior or per-row Python callback is constructed.
        """

        if rows.ndim != 2 or rows.shape[1] != len(weights) or not len(weights):
            raise ValueError("rows and weights must describe a nonempty belief")
        masses = np.empty(
            (rows.shape[0], self.matrix.code_count), dtype=np.float64
        )
        for code in range(self.matrix.code_count):
            masses[:, code] = np.sum(
                np.where(rows == code, weights[None, :], 0.0), axis=1
            )
        entropies = np.zeros(rows.shape[0], dtype=np.float64)
        for code in range(self.matrix.code_count):
            mass = masses[:, code]
            positive = mass > 0.0
            entropies[positive] -= mass[positive] * np.log2(mass[positive])
        return entropies

    def belief_arrays(self, belief: BeliefState) -> Tuple[np.ndarray, np.ndarray]:
        mass_table = self._weights(belief)
        answers = tuple(word for word, _ in mass_table)
        weights = np.asarray([mass for _, mass in mass_table], dtype=np.float64)
        return self.matrix.answer_indices(answers), weights

    def entropy_for_row(
        self,
        row: np.ndarray,
        answer_indices: np.ndarray,
        weights: np.ndarray,
    ) -> float:
        masses = self.outcome_masses(row, answer_indices, weights)
        positive = masses[masses > 0.0]
        if not len(positive):
            raise ValueError("belief must contain positive probability mass")
        return float(-np.sum(positive * np.log2(positive)))

    def calculate(self, belief: BeliefState, guess: str) -> float:
        answer_indices, weights = self.belief_arrays(belief)
        value = self.entropy_for_row(
            self.matrix.row_for(guess), answer_indices, weights
        )
        if not math.isfinite(value):
            raise ValueError("information gain must be finite")
        return max(0.0, value)
