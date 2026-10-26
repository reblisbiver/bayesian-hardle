"""Explicit non-leaking hypothesis spaces and prior models for ISSUE-006."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.metadata
import math
from typing import Callable, Dict, Optional, Sequence, Tuple

from .belief import BeliefState, PriorModel, UniformPrior
from .game import VocabularyRepository


FrequencyFunction = Callable[[str, str], float]


class FrequencyDependencyError(RuntimeError):
    """Raised when the declared general-language frequency source is unavailable."""


class GeneralEnglishFrequencyPrior:
    """Positive prior from general-English ``wordfreq`` Zipf frequencies.

    The transformation is deliberately simple and reproducible:
    ``raw_weight = max(10 ** zipf_frequency(word, "en"), 1e-12)`` followed by
    normalization over exactly the supplied support.  The source is general
    English usage frequency, not Hardle/Wordle answer membership.
    """

    SOURCE = "wordfreq"
    REQUIRED_VERSION = "3.1.1"
    LANGUAGE = "en"
    POSITIVE_FLOOR = 1e-12

    def __init__(
        self,
        frequency_function: Optional[FrequencyFunction] = None,
        source_version: Optional[str] = None,
    ) -> None:
        self._frequency_function = frequency_function
        self._source_version = source_version

    @property
    def source_version(self) -> str:
        if self._source_version is not None:
            return self._source_version
        try:
            return importlib.metadata.version(self.SOURCE)
        except importlib.metadata.PackageNotFoundError as exc:
            raise FrequencyDependencyError(
                "full-frequency requires wordfreq==3.1.1; install the project "
                "with `python3 -m pip install -e .`"
            ) from exc

    def _function(self) -> FrequencyFunction:
        if self._frequency_function is not None:
            return self._frequency_function
        version = self.source_version
        if version != self.REQUIRED_VERSION:
            raise FrequencyDependencyError(
                f"full-frequency requires wordfreq=={self.REQUIRED_VERSION}; "
                f"found {version}"
            )
        try:
            from wordfreq import zipf_frequency
        except ImportError as exc:
            raise FrequencyDependencyError(
                "full-frequency requires wordfreq==3.1.1; install the project "
                "with `python3 -m pip install -e .`"
            ) from exc
        return zipf_frequency

    @property
    def provenance(self) -> Dict[str, object]:
        return {
            "source": self.SOURCE,
            "version": self.source_version,
            "language": self.LANGUAGE,
            "frequency_metric": "Zipf frequency",
            "transformation": "max(10 ** zipf_frequency(word, 'en'), 1e-12)",
            "positive_floor": self.POSITIVE_FLOOR,
            "answer_membership_used": False,
            "human_like_heuristic": True,
        }

    def initial_belief(self, target_vocabulary: Sequence[str]) -> BeliefState:
        candidates = tuple(target_vocabulary)
        if not candidates:
            raise ValueError("target vocabulary cannot be empty")
        if len(set(candidates)) != len(candidates):
            raise ValueError("target vocabulary must not contain duplicates")
        frequency = self._function()
        weights = []
        for word in candidates:
            zipf = float(frequency(word, self.LANGUAGE))
            if not math.isfinite(zipf):
                raise ValueError(f"frequency for {word!r} must be finite")
            try:
                raw_weight = 10.0 ** zipf
            except OverflowError:
                raise ValueError(f"frequency for {word!r} is too large")
            weights.append(max(raw_weight, self.POSITIVE_FLOOR))
        total = math.fsum(weights)
        if not math.isfinite(total) or total <= 0.0:
            raise ValueError("frequency prior has invalid total mass")
        return BeliefState(
            candidates=candidates,
            probability_mass=tuple(
                (word, weight / total) for word, weight in zip(candidates, weights)
            ),
        )


@dataclass(frozen=True)
class HypothesisMode:
    """Resolved support, prior, and visible provenance for one mode."""

    name: str
    label: str
    support: Tuple[str, ...]
    prior: PriorModel
    answer_list_aware: bool
    provenance: Dict[str, object]


def resolve_hypothesis_mode(
    name: str,
    vocabulary: VocabularyRepository,
    frequency_prior: Optional[GeneralEnglishFrequencyPrior] = None,
) -> HypothesisMode:
    """Resolve one explicit fairness mode without exposing hidden answer labels."""

    legal = tuple(vocabulary.legal_guesses())
    if name == "full-uniform":
        return HypothesisMode(
            name=name,
            label="full-uniform (PRIMARY STRICT FAIRNESS)",
            support=legal,
            prior=UniformPrior(),
            answer_list_aware=False,
            provenance={
                "support": "all legal Hardle words",
                "support_count": len(legal),
                "prior": "uniform",
                "answer_membership_used": False,
            },
        )
    if name == "full-frequency":
        prior = frequency_prior or GeneralEnglishFrequencyPrior()
        return HypothesisMode(
            name=name,
            label="full-frequency (PRIMARY HUMAN-LIKE EXPLORATORY)",
            support=legal,
            prior=prior,
            answer_list_aware=False,
            provenance={
                "support": "all legal Hardle words",
                "support_count": len(legal),
                **prior.provenance,
            },
        )
    if name == "curated-2315":
        curated = tuple(vocabulary.target_vocabulary())
        return HypothesisMode(
            name=name,
            label="curated-2315 (DIAGNOSTIC / ANSWER-LIST-AWARE)",
            support=curated,
            prior=UniformPrior(),
            answer_list_aware=True,
            provenance={
                "support": "curated candidate-answer list",
                "support_count": len(curated),
                "prior": "uniform",
                "answer_membership_used": True,
                "fairness_role": "diagnostic only",
            },
        )
    raise ValueError(
        "unknown hypothesis mode; choose full-uniform, full-frequency, or curated-2315"
    )

