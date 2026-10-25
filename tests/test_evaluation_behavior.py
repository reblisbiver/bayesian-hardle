import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_hardle.belief import ExactPosteriorUpdater, UniformPrior  # noqa: E402
from bayesian_hardle.decision import MAPPolicy  # noqa: E402
from bayesian_hardle.evaluation import (  # noqa: E402
    BenchmarkSpec,
    ExactEpisodeRunner,
    ExperimentConfig,
)
from bayesian_hardle.game import (  # noqa: E402
    GameSpec,
    HardleFeedbackEngine,
    HardleTerminalRules,
    WordListVocabularyRepository,
)


class RecordingPolicy(MAPPolicy):
    def __init__(self):
        self.initial_candidate_sets = []

    def select_guess(self, state, candidate_guesses):
        self.initial_candidate_sets.append(state.belief.candidates)
        return super().select_guess(state, candidate_guesses)


class EvaluationBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.vocabulary = WordListVocabularyRepository(
            legal_words=("cigar", "rebut"),
            answer_words=("cigar", "rebut"),
        )
        self.feedback = HardleFeedbackEngine()
        self.updater = ExactPosteriorUpdater(self.feedback)
        self.runner = ExactEpisodeRunner(
            vocabulary=self.vocabulary,
            feedback_engine=self.feedback,
            prior_model=UniformPrior(),
            posterior_updater=self.updater,
            terminal_rules=HardleTerminalRules(),
            hidden_targets=("rebut", "cigar"),
        )

    def test_hidden_target_pool_does_not_change_solver_initial_belief(self):
        policy = RecordingPolicy()
        self.runner.run(
            ExperimentConfig(
                game=GameSpec(word_length=5, max_guesses=2),
                benchmark=BenchmarkSpec(name="hidden-target-test", episodes=1),
            ),
            policy,
        )
        self.assertEqual(policy.initial_candidate_sets[0], ("cigar", "rebut"))

    def test_runner_reports_solve_rate_and_mean_guesses(self):
        result = self.runner.run(
            ExperimentConfig(
                game=GameSpec(word_length=5, max_guesses=2),
                benchmark=BenchmarkSpec(name="metrics-test", episodes=2),
            ),
            MAPPolicy(),
        )
        self.assertEqual(result.episodes, 2)
        self.assertEqual(result.wins, 2)
        self.assertEqual(result.guesses, 3)
        self.assertEqual(result.per_episode_guesses, (2, 1))
        self.assertAlmostEqual(result.solve_rate, 1.0)
        self.assertAlmostEqual(result.mean_guesses, 1.5)
        self.assertGreaterEqual(result.runtime_seconds, 0.0)


if __name__ == "__main__":
    unittest.main()
