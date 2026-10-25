"""Bayesian Hardle research package."""

from .belief import BeliefState, LikelihoodModel, PosteriorUpdater, PriorModel
from .decision import (
    BayesOptimalPlanner,
    DecisionState,
    MAPPolicy,
    MaxInformationGainPolicy,
    PlannerCache,
    Policy,
    RandomPolicy,
)
from .evaluation import (
    ArtifactSink,
    BenchmarkSpec,
    EpisodeRunner,
    ExperimentConfig,
    MetricsResult,
)
from .game import FeedbackEngine, GameSpec, TerminalRules, VocabularyRepository
from .information import (
    EntropyCalculator,
    ExpectedEntropyCalculator,
    InformationGainCalculator,
    OutcomePartitioner,
)

__all__ = [
    "ArtifactSink",
    "BayesOptimalPlanner",
    "BeliefState",
    "BenchmarkSpec",
    "DecisionState",
    "EntropyCalculator",
    "EpisodeRunner",
    "ExpectedEntropyCalculator",
    "ExperimentConfig",
    "FeedbackEngine",
    "GameSpec",
    "InformationGainCalculator",
    "LikelihoodModel",
    "MAPPolicy",
    "MaxInformationGainPolicy",
    "MetricsResult",
    "OutcomePartitioner",
    "PlannerCache",
    "Policy",
    "PosteriorUpdater",
    "PriorModel",
    "RandomPolicy",
    "TerminalRules",
    "VocabularyRepository",
    "__version__",
]
__version__ = "0.1.0"
