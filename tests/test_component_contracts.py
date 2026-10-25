from dataclasses import is_dataclass
import inspect
from pathlib import Path
import sys
import unittest
from typing import Protocol, get_type_hints


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

    def test_belief_state_carries_immutable_probability_mass(self):
        belief = BeliefState(
            candidates=("cigar", "rebut"),
            probability_mass=(("cigar", 0.7), ("rebut", 0.3)),
        )

        self.assertEqual(
            belief.probability_mass,
            (("cigar", 0.7), ("rebut", 0.3)),
        )
        self.assertIsInstance(belief.probability_mass, tuple)
        with self.assertRaises(AttributeError):
            belief.probability_mass = (("cigar", 1.0),)

    def test_information_contract_carries_outcome_probability_and_posterior(self):
        from bayesian_hardle import OutcomeBranch, OutcomeDistribution

        posterior = BeliefState(
            candidates=("cigar",),
            probability_mass=(("cigar", 1.0),),
        )
        branch = OutcomeBranch(
            outcome=("opaque-feedback",),
            probability=0.7,
            posterior=posterior,
        )
        distribution = OutcomeDistribution(outcomes=[branch])

        self.assertEqual(distribution.outcomes, (branch,))
        self.assertEqual(distribution.outcomes[0].probability, 0.7)
        self.assertIs(distribution.outcomes[0].posterior, posterior)
        self.assertIsNot(distribution.outcomes, [branch])
        with self.assertRaises(AttributeError):
            distribution.outcomes = ()

        partition_return = get_type_hints(OutcomePartitioner.partition)["return"]
        self.assertIs(partition_return, OutcomeDistribution)
        self.assertEqual(
            tuple(inspect.signature(EntropyCalculator.calculate).parameters),
            ("self", "belief"),
        )
        self.assertEqual(
            tuple(
                inspect.signature(ExpectedEntropyCalculator.calculate).parameters
            ),
            ("self", "distribution"),
        )
        self.assertEqual(
            tuple(
                inspect.signature(InformationGainCalculator.calculate).parameters
            ),
            ("self", "belief", "guess", "outcome_distribution"),
        )

    def test_bayes_optimal_planner_requires_shared_semantics_contracts(self):
        parameters = tuple(
            inspect.signature(BayesOptimalPlanner.select_guess).parameters
        )
        self.assertEqual(
            parameters,
            (
                "self",
                "state",
                "candidate_guesses",
                "feedback_engine",
                "posterior_updater",
            ),
        )

        type_hints = get_type_hints(BayesOptimalPlanner.select_guess)
        self.assertIs(type_hints["feedback_engine"], FeedbackEngine)
        self.assertIs(type_hints["posterior_updater"], PosteriorUpdater)

    def test_scaffold_handoff_keeps_game_belief_and_evaluation_boundaries(self):
        class FakeVocabularyRepository:
            def legal_guesses(self):
                return ("cigar",)

            def target_vocabulary(self):
                return ("cigar",)

        class FakeFeedbackEngine:
            def evaluate(self, guess, target):
                return ("opaque-feedback",)

        class FakePosteriorUpdater:
            def update(self, belief, guess, feedback):
                observation = (guess, tuple(feedback))
                return BeliefState(
                    candidates=belief.candidates,
                    observations=belief.observations + (observation,),
                )

        class FakePolicy:
            def select_guess(self, state, candidate_guesses):
                self.seen_state = state
                return candidate_guesses[0]

        class FakeEpisodeRunner:
            def run(self, config, policy):
                self.seen_config = config
                self.seen_policy = policy
                return MetricsResult(
                    episodes=config.benchmark.episodes,
                    wins=1,
                    guesses=1,
                )

        class RecordingArtifactSink:
            def __init__(self):
                self.artifacts = []

            def write(self, name, artifact):
                self.artifacts.append((name, artifact))

        vocabulary = FakeVocabularyRepository()
        feedback_engine = FakeFeedbackEngine()
        updater = FakePosteriorUpdater()
        policy = FakePolicy()
        runner = FakeEpisodeRunner()
        sink = RecordingArtifactSink()
        belief = BeliefState(candidates=("cigar",))
        state = DecisionState(belief=belief, remaining_guesses=2)
        config = ExperimentConfig(
            game=GameSpec(word_length=5, max_guesses=6),
            benchmark=BenchmarkSpec(name="scaffold", episodes=1),
        )

        self.assertIsInstance(policy, Policy)
        self.assertIsInstance(feedback_engine, FeedbackEngine)
        self.assertIsInstance(updater, PosteriorUpdater)
        self.assertIsInstance(runner, EpisodeRunner)
        self.assertIsInstance(sink, ArtifactSink)

        guess = policy.select_guess(state, vocabulary.legal_guesses())
        feedback = feedback_engine.evaluate(guess, "cigar")
        updated_belief = updater.update(belief, guess, feedback)
        next_state = DecisionState(
            belief=updated_belief,
            remaining_guesses=state.remaining_guesses - 1,
        )
        metrics = runner.run(config, policy)
        sink.write("metrics", metrics)

        self.assertEqual(next_state.remaining_guesses, 1)
        self.assertEqual(next_state.belief.observations, (("cigar", ("opaque-feedback",)),))
        self.assertIs(runner.seen_config, config)
        self.assertIs(runner.seen_policy, policy)
        self.assertEqual(sink.artifacts, [("metrics", metrics)])


if __name__ == "__main__":
    unittest.main()
