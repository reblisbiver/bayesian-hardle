import random
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_hardle.belief import ExactPosteriorUpdater, UniformPrior  # noqa: E402
from bayesian_hardle.decision import (  # noqa: E402
    DecisionState,
    ExactBayesOptimalPlanner,
    MAPPolicy,
    MaxInformationGainPolicy,
    RandomPolicy,
)
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402


class DecisionBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.feedback = HardleFeedbackEngine()
        self.updater = ExactPosteriorUpdater(self.feedback)
        belief = UniformPrior().initial_belief(("cigar", "rebut", "sissy"))
        self.state = DecisionState(belief=belief, remaining_guesses=3)

    def test_seeded_random_policy_reproduces_legal_guess_sequence(self):
        first = RandomPolicy(rng=random.Random(17))
        second = RandomPolicy(rng=random.Random(17))
        legal = ("adieu", "cigar", "rebut")
        first_sequence = [first.select_guess(self.state, legal) for _ in range(8)]
        second_sequence = [second.select_guess(self.state, legal) for _ in range(8)]
        self.assertEqual(first_sequence, second_sequence)
        self.assertTrue(set(first_sequence).issubset(set(legal)))

    def test_map_policy_uses_posterior_mass_and_keeps_legal_answer_boundary(self):
        belief = self.state.belief
        weighted = belief.__class__(
            candidates=belief.candidates,
            probability_mass=(("cigar", 0.2), ("rebut", 0.7), ("sissy", 0.1)),
        )
        state = DecisionState(weighted, 2)
        self.assertEqual(MAPPolicy().select_guess(state, ("adieu", "cigar", "rebut")), "rebut")
        with self.assertRaises(ValueError):
            MAPPolicy().select_guess(state, ("adieu",))

    def test_max_information_gain_can_select_non_answer_legal_guess(self):
        policy = MaxInformationGainPolicy(self.feedback)
        guess = policy.select_guess(self.state, ("arise", "cigar"))
        self.assertEqual(guess, "arise")
        self.assertNotIn(guess, self.state.belief.candidates)

    def test_exact_planner_solves_hand_checkable_two_answer_tree(self):
        belief = UniformPrior().initial_belief(("cigar", "rebut"))
        state = DecisionState(belief=belief, remaining_guesses=2)
        planner = ExactBayesOptimalPlanner()
        legal = ("cigar", "rebut", "adieu")

        selected = planner.select_guess(state, legal, self.feedback, self.updater)
        probability = planner.success_probability(state, legal, self.feedback, self.updater)

        self.assertEqual(selected, "cigar")
        self.assertAlmostEqual(probability, 1.0)
        self.assertGreater(planner.cache_hits, 0)

    def test_exact_planner_horizon_one_and_terminal_cases(self):
        belief = UniformPrior().initial_belief(("cigar", "rebut"))
        planner = ExactBayesOptimalPlanner()
        legal = ("cigar", "rebut")
        one_step = DecisionState(belief=belief, remaining_guesses=1)
        self.assertEqual(
            planner.success_probability(one_step, legal, self.feedback, self.updater),
            0.5,
        )
        terminal = DecisionState(belief=belief, remaining_guesses=0)
        self.assertEqual(
            planner.success_probability(terminal, legal, self.feedback, self.updater),
            0.0,
        )
        with self.assertRaises(ValueError):
            planner.select_guess(terminal, legal, self.feedback, self.updater)


if __name__ == "__main__":
    unittest.main()
