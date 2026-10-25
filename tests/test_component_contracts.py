from dataclasses import is_dataclass
from pathlib import Path
import sys
import unittest
from typing import Protocol


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_hardle import (  # noqa: E402
    ArtifactSink,
    BayesOptimalPlanner,
    BeliefState,
    BenchmarkSpec,
    DecisionState,
    EntropyCalculator,
    EpisodeRunner,
    ExpectedEntropyCalculator,
    ExperimentConfig,
    FeedbackEngine,
    GameSpec,
    InformationGainCalculator,
    LikelihoodModel,
    MAPPolicy,
    MaxInformationGainPolicy,
    MetricsResult,
    OutcomePartitioner,
    PlannerCache,
    Policy,
    PosteriorUpdater,
    PriorModel,
    RandomPolicy,
    TerminalRules,
    VocabularyRepository,
)


class ComponentContractTests(unittest.TestCase):
    def test_public_component_contracts_import_and_have_minimal_shapes(self):
        protocols = (
            VocabularyRepository,
            FeedbackEngine,
            TerminalRules,
            PriorModel,
            LikelihoodModel,
            PosteriorUpdater,
            OutcomePartitioner,
            EntropyCalculator,
            ExpectedEntropyCalculator,
            InformationGainCalculator,
            Policy,
            BayesOptimalPlanner,
            PlannerCache,
            EpisodeRunner,
            ArtifactSink,
        )
        for contract in protocols:
            with self.subTest(contract=contract.__name__):
                self.assertTrue(issubclass(contract, Protocol))

        value_objects = (
            BeliefState,
            GameSpec,
            DecisionState,
            BenchmarkSpec,
            MetricsResult,
            ExperimentConfig,
        )
        for value_object in value_objects:
            with self.subTest(value_object=value_object.__name__):
                self.assertTrue(is_dataclass(value_object))

        placeholders = (RandomPolicy, MAPPolicy, MaxInformationGainPolicy)
        for placeholder in placeholders:
            with self.subTest(placeholder=placeholder.__name__):
                self.assertTrue(callable(getattr(placeholder, "select_guess")))

    def test_value_objects_store_scaffold_state_and_validate_horizon(self):
        game = GameSpec(word_length=5, max_guesses=6)
        belief = BeliefState(candidates=("cigar",))
        decision = DecisionState(belief=belief, remaining_guesses=2)
        benchmark = BenchmarkSpec(name="smoke", episodes=1)
        metrics = MetricsResult(episodes=1, wins=1, guesses=1)
        config = ExperimentConfig(game=game, benchmark=benchmark)

        self.assertEqual(game.max_guesses, 6)
        self.assertEqual(decision.belief, belief)
        self.assertEqual(metrics.wins, 1)
        self.assertEqual(config.benchmark, benchmark)
        with self.assertRaises(ValueError):
            DecisionState(belief=belief, remaining_guesses=-1)


if __name__ == "__main__":
    unittest.main()
