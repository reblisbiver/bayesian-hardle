import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_hardle.belief import ExactPosteriorUpdater, UniformPrior  # noqa: E402
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402
from bayesian_hardle.information import (  # noqa: E402
    ExactInformationGainCalculator,
    ExactOutcomePartitioner,
    ExpectedPosteriorEntropyCalculator,
    ShannonEntropyCalculator,
)


class InformationBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.feedback = HardleFeedbackEngine()
        self.prior = UniformPrior()
        self.updater = ExactPosteriorUpdater(self.feedback)
        self.partitioner = ExactOutcomePartitioner(self.updater)
        self.entropy = ShannonEntropyCalculator()
        self.expected_entropy = ExpectedPosteriorEntropyCalculator(self.entropy)
        self.gain = ExactInformationGainCalculator(self.entropy, self.expected_entropy)

    def test_partition_posteriors_and_probabilities_are_exact(self):
        belief = self.prior.initial_belief(("cigar", "rebut", "sissy"))
        distribution = self.partitioner.partition(belief, "cigar", self.feedback)

        self.assertGreaterEqual(len(distribution.outcomes), 2)
        self.assertAlmostEqual(distribution.total_probability, 1.0)
        for branch in distribution.outcomes:
            self.assertAlmostEqual(branch.posterior.total_mass, 1.0)
            expected = tuple(
                word for word in belief.candidates
                if self.feedback.evaluate("cigar", word) == branch.outcome
            )
            self.assertEqual(branch.posterior.candidates, expected)

    def test_entropy_expected_entropy_and_information_gain_identity(self):
        belief = self.prior.initial_belief(("cigar", "rebut"))
        distribution = self.partitioner.partition(belief, "cigar", self.feedback)

        self.assertAlmostEqual(self.entropy.calculate(belief), 1.0)
        self.assertAlmostEqual(
            self.gain.calculate(belief, "cigar", distribution),
            1.0,
        )
        self.assertAlmostEqual(
            self.expected_entropy.calculate(distribution),
            0.0,
        )

    def test_indistinguishing_guess_has_zero_information_gain(self):
        belief = self.prior.initial_belief(("cigar", "rebut"))
        distribution = self.partitioner.partition(belief, "adieu", self.feedback)
        self.assertEqual(len(distribution.outcomes), 1)
        self.assertAlmostEqual(self.gain.calculate(belief, "adieu", distribution), 0.0)


if __name__ == "__main__":
    unittest.main()
