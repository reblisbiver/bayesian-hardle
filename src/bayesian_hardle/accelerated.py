"""Exact NumPy acceleration for fixed-vocabulary Hardle feedback."""

from __future__ import annotations

import math
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, Sequence, Tuple

import numpy as np

from .game import _normalise_word
from .belief import BeliefState, ImpossibleObservationError


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
        storage_path: str | Path | None = None,
        vocabulary_identity: str | None = None,
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
        self._storage_path = Path(storage_path) if storage_path is not None else None
        self._vocabulary_identity = vocabulary_identity or self.identity_for(
            self.legal_guesses, self.candidate_answers, word_length
        )
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
        codes = np.empty((len(legal), len(answers)), dtype=np.uint8)
        cls._build_codes(legal, answers, codes, word_length, guess_chunk_size)
        return cls(legal, answers, codes, word_length)

    @classmethod
    def load_or_build(
        cls,
        legal_guesses: Iterable[str],
        candidate_answers: Iterable[str],
        cache_dir: str | Path,
        word_length: int = 5,
        guess_chunk_size: int = _DEFAULT_GUESS_CHUNK_SIZE,
    ) -> "ExactFeedbackCodeMatrix":
        """Load an exact matrix from a vocabulary-keyed NumPy cache or build it.

        The matrix is written as a read-only ``.npy`` memmap after a complete
        temporary build.  Metadata repeats the vocabulary identity, shape, and
        dtype so a stale or partial cache cannot be mistaken for a valid one.
        """

        legal = tuple(_normalise_word(word, word_length) for word in legal_guesses)
        answers = tuple(_normalise_word(word, word_length) for word in candidate_answers)
        if guess_chunk_size <= 0:
            raise ValueError("guess_chunk_size must be positive")
        if not legal or not answers:
            raise ValueError("legal guesses and candidate answers cannot be empty")
        if len(set(legal)) != len(legal):
            raise ValueError("legal guesses must be unique")
        if len(set(answers)) != len(answers):
            raise ValueError("candidate answers must be unique")

        cache = Path(cache_dir)
        cache.mkdir(parents=True, exist_ok=True)
        identity = cls.identity_for(legal, answers, word_length)
        matrix_path = cache / f"feedback-{identity}.npy"
        metadata_path = cache / f"feedback-{identity}.json"
        metadata = {
            "format": 1,
            "vocabulary_identity": identity,
            "word_length": word_length,
            "shape": [len(legal), len(answers)],
            "dtype": "uint8",
            "feedback_encoding": "exact * (word_length + 1) + misplaced",
        }

        if matrix_path.exists() and metadata_path.exists():
            try:
                saved = json.loads(metadata_path.read_text(encoding="utf-8"))
                codes = np.load(matrix_path, mmap_mode="r")
                if saved == metadata and codes.shape == tuple(metadata["shape"]):
                    return cls(
                        legal,
                        answers,
                        codes,
                        word_length,
                        storage_path=matrix_path,
                        vocabulary_identity=identity,
                    )
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                pass

        temporary_path = cache / (
            f".feedback-{identity}.{os.getpid()}.tmp.npy"
        )
        temporary_metadata = cache / (
            f".feedback-{identity}.{os.getpid()}.tmp.json"
        )
        try:
            codes = np.lib.format.open_memmap(
                temporary_path,
                mode="w+",
                dtype=np.uint8,
                shape=(len(legal), len(answers)),
            )
            cls._build_codes(legal, answers, codes, word_length, guess_chunk_size)
            codes.flush()
            del codes
            temporary_metadata.write_text(
                json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary_path, matrix_path)
            os.replace(temporary_metadata, metadata_path)
        finally:
            for path in (temporary_path, temporary_metadata):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
        codes = np.load(matrix_path, mmap_mode="r")
        return cls(
            legal,
            answers,
            codes,
            word_length,
            storage_path=matrix_path,
            vocabulary_identity=identity,
        )

    @staticmethod
    def identity_for(
        legal_guesses: Sequence[str],
        candidate_answers: Sequence[str],
        word_length: int = 5,
    ) -> str:
        payload = json.dumps(
            {
                "word_length": word_length,
                "legal_guesses": list(legal_guesses),
                "candidate_answers": list(candidate_answers),
            },
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def _build_codes(
        cls,
        legal: Sequence[str],
        answers: Sequence[str],
        codes: np.ndarray,
        word_length: int,
        guess_chunk_size: int,
    ) -> None:
        """Fill a uint8 array with exact duplicate-aware Hardle codes."""

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
    def disk_bytes(self) -> int:
        if self._storage_path is None:
            return 0
        return int(self._storage_path.stat().st_size)

    @property
    def storage_path(self) -> Path:
        if self._storage_path is None:
            raise ValueError("matrix was not loaded from a disk cache")
        return self._storage_path

    @property
    def vocabulary_identity(self) -> str:
        return self._vocabulary_identity

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

    def horizon_two_values(
        self,
        guesses: Sequence[str],
        answer_words: Sequence[str],
        weights: Sequence[float],
        legal_final_answers: Sequence[str],
    ) -> Tuple[Tuple[float, float], ...]:
        """Return exact two-guess values for all supplied first guesses.

        The success probability is the sum, over feedback codes, of the
        largest posterior mass of a legal final answer in that code bucket.
        The expected-guess component is ``2 - P(answer == first_guess)``.
        ``weights`` must already be normalized to the supplied answer words.
        """

        guesses = tuple(guesses)
        answer_words = tuple(answer_words)
        if not guesses or not answer_words:
            raise ValueError("guesses and answer_words cannot be empty")
        if len(answer_words) != len(weights):
            raise ValueError("weights must match answer_words")
        if any(guess not in self._guess_indices for guess in guesses):
            raise ValueError("all guesses must be in the feedback matrix")
        if any(answer not in self._answer_indices for answer in answer_words):
            raise ValueError("all answer_words must be in the feedback matrix")

        values = np.asarray(tuple(float(weight) for weight in weights), dtype=np.float64)
        if np.any(~np.isfinite(values)) or np.any(values < 0):
            raise ValueError("weights must be finite and non-negative")
        legal_final = set(legal_final_answers)
        eligible = np.asarray(
            [weight if word in legal_final else 0.0 for word, weight in zip(answer_words, values)],
            dtype=np.float64,
        )
        guess_indices = np.asarray(
            [self._guess_indices[guess] for guess in guesses], dtype=np.intp
        )
        answer_indices = np.asarray(
            [self._answer_indices[answer] for answer in answer_words], dtype=np.intp
        )
        codes = self._codes[guess_indices][:, answer_indices]
        maxima = np.zeros((len(guesses), self.code_count), dtype=np.float64)
        for row_index, row in enumerate(codes):
            np.maximum.at(maxima[row_index], row, eligible)

        success = maxima.sum(axis=1)
        mass_by_word = dict(zip(answer_words, values.tolist()))
        expected = np.asarray(
            [2.0 - mass_by_word.get(guess, 0.0) for guess in guesses],
            dtype=np.float64,
        )
        return tuple(
            (float(success[index]), float(expected[index]))
            for index in range(len(guesses))
        )

    def _validated_horizon_two_weights(
        self,
        answer_words: Sequence[str],
        weights: Sequence[float],
    ) -> Tuple[Tuple[str, ...], np.ndarray]:
        words = tuple(answer_words)
        if not words:
            raise ValueError("answer_words cannot be empty")
        if len(words) != len(weights):
            raise ValueError("weights must match answer_words")
        if any(answer not in self._answer_indices for answer in words):
            raise ValueError("all answer_words must be in the feedback matrix")
        values = np.asarray(tuple(float(weight) for weight in weights), dtype=np.float64)
        if np.any(~np.isfinite(values)) or np.any(values < 0):
            raise ValueError("weights must be finite and non-negative")
        return words, values

    def horizon_two_capacity_upper_bound(
        self,
        answer_words: Sequence[str],
        weights: Sequence[float],
        legal_final_answers: Sequence[str],
    ) -> float:
        """Return a safe top-mass upper bound for every exact H2 probe.

        A Hardle probe has at most ``code_count`` feedback codes, and a final
        legal answer can collect credit from at most one answer in each code
        bucket.  Therefore the exact H2 success probability, which is the
        sum of the largest eligible mass in every bucket, cannot exceed the
        sum of the largest ``code_count`` legal-answer masses overall.  The
        argument uses only non-negative posterior masses and does not assume
        anything about the probe's partition, so it is an upper bound for
        every legal probe.  The caller is responsible for supplying the same
        normalized weights contract as ``horizon_two_values``.
        """

        words, values = self._validated_horizon_two_weights(answer_words, weights)
        legal_final = set(legal_final_answers)
        eligible = sorted(
            (float(weight) for word, weight in zip(words, values) if word in legal_final),
            reverse=True,
        )
        return float(math.fsum(eligible[: self.code_count]))

    def horizon_two_action_capacity_upper_bound(
        self,
        first_guess: str,
        answer_words: Sequence[str],
        weights: Sequence[float],
        legal_final_answers: Sequence[str],
    ) -> float:
        """Return the safe capacity bound for one specified H2 probe.

        When ``first_guess`` is itself a legal answer in the posterior, its
        exact-win code consumes one of the finite code slots.  Its mass is
        counted exactly and only the largest ``code_count - 1`` remaining
        legal-answer masses are added.  A non-answer probe uses the global
        capacity bound because it has no guaranteed exact-win slot.
        """

        if first_guess not in self._guess_indices:
            raise ValueError("first_guess must be in the feedback matrix")
        words, values = self._validated_horizon_two_weights(answer_words, weights)
        legal_final = set(legal_final_answers)
        eligible = {
            word: float(weight)
            for word, weight in zip(words, values)
            if word in legal_final
        }
        if first_guess not in eligible:
            return float(
                math.fsum(sorted(eligible.values(), reverse=True)[: self.code_count])
            )
        remaining = sorted(
            (
                weight
                for word, weight in eligible.items()
                if word != first_guess
            ),
            reverse=True,
        )
        return float(
            eligible[first_guess]
            + math.fsum(remaining[: max(0, self.code_count - 1)])
        )

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


class MatrixPosteriorUpdater:
    """Exact posterior filtering through a prebuilt feedback-code matrix."""

    def __init__(self, matrix: ExactFeedbackCodeMatrix) -> None:
        self.matrix = matrix

    @staticmethod
    def _mass_table(belief: BeliefState) -> Tuple[Tuple[str, float], ...]:
        if belief.probability_mass:
            total = belief.total_mass
            if total <= 0:
                raise ValueError("belief must have positive total mass")
            return belief.probability_mass
        if not belief.candidates:
            raise ValueError("belief must contain candidates")
        uniform = 1.0 / len(belief.candidates)
        return tuple((word, uniform) for word in belief.candidates)

    def update(
        self,
        belief: BeliefState,
        guess: str,
        feedback: Tuple[int, int],
    ) -> BeliefState:
        observed = tuple(feedback)
        exact, misplaced = self.matrix.decode_code(
            int(observed[0]) * self.matrix._code_base + int(observed[1])
        )
        if (exact, misplaced) != observed:
            raise ValueError("invalid Hardle feedback")
        mass_table = self._mass_table(belief)
        words = tuple(word for word, _ in mass_table)
        indices = self.matrix.answer_indices(words)
        code = exact * self.matrix._code_base + misplaced
        row = self.matrix.row_for(guess)
        retained = [
            (word, mass)
            for word, mass, value in zip(words, (mass for _, mass in mass_table), row[indices])
            if int(value) == code
        ]
        retained_mass = math.fsum(mass for _, mass in retained)
        if retained_mass <= 0:
            raise ImpossibleObservationError(
                "observation has zero posterior mass: " + repr(observed)
            )
        normalized = tuple(
            (target, mass / retained_mass) for target, mass in retained
        )
        return BeliefState(
            candidates=tuple(target for target, _ in normalized),
            observations=belief.observations + ((guess, observed),),
            probability_mass=normalized,
        )


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
