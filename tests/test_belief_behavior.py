import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_hardle.belief import (  # noqa: E402
    ExactPosteriorUpdater,
    ImpossibleObservationError,
    UniformPrior,
)
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402


class BeliefBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.feedback = HardleFeedbackEngine()
        self.prior = UniformPrior()
        self.updater = ExactPosteriorUpdater(self.feedback)

    def test_uniform_prior_is_normalized_and_preserves_candidate_order(self):
        belief = self.prior.initial_belief(("cigar", "rebut", "sissy"))
        self.assertEqual(belief.candidates, ("cigar", "rebut", "sissy"))
        self.assertEqual(belief.probability_mass, (
            ("cigar", 1 / 3),
            ("rebut", 1 / 3),
            ("sissy", 1 / 3),
        ))
        self.assertAlmostEqual(belief.total_mass, 1.0)

    def test_exact_update_filters_and_renormalizes(self):
        belief = self.prior.initial_belief(("cigar", "rebut", "sissy"))
        feedback = self.feedback.evaluate("cigar", "rebut")
        posterior = self.updater.update(belief, "cigar", feedback)

        expected = tuple(
            word for word in belief.candidates
            if self.feedback.evaluate("cigar", word) == feedback
        )
        self.assertEqual(posterior.candidates, expected)
        self.assertAlmostEqual(posterior.total_mass, 1.0)
        self.assertEqual(posterior.observations[-1], ("cigar", feedback))

    def test_impossible_observation_is_explicitly_rejected(self):
        belief = self.prior.initial_belief(("cigar", "rebut"))
        with self.assertRaises(ImpossibleObservationError):
            self.updater.update(belief, "cigar", (5, 5))

    def test_update_can_start_from_candidate_only_scaffold_state(self):
        posterior = self.updater.update(
            self.prior.initial_belief(("cigar", "rebut")),
            "cigar",
            (5, 0),
        )
        self.assertEqual(posterior.candidates, ("cigar",))
        self.assertEqual(posterior.probability_mass, (("cigar", 1.0),))


if __name__ == "__main__":
    unittest.main()
