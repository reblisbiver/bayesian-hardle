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
    ExactBayesOptimalReferencePlanner,
    MAPPolicy,
    MaxInformationGainPolicy,
    RandomPolicy,
)
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402
from bayesian_hardle.accelerated import ExactFeedbackCodeMatrix  # noqa: E402


class ConstantInformationGainCalculator:
    """Controlled calculator for exercising policy tie resolution."""

    def calculate(self, belief, guess, outcome_distribution):
        del belief, guess, outcome_distribution
        return 1.0


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

    def test_max_information_gain_can_select_non_answer_with_strictly_higher_gain(self):
        policy = MaxInformationGainPolicy(self.feedback)
        belief = UniformPrior().initial_belief(
            ("awake", "cigar", "humph", "rebut", "sissy")
        )
        state = DecisionState(belief, 3)
        guess = policy.select_guess(state, ("arise", "cigar"))
        self.assertEqual(guess, "arise")
        self.assertNotIn(guess, state.belief.candidates)

    def test_max_information_gain_singleton_posterior_guesses_remaining_answer(self):
        initial = UniformPrior().initial_belief(("cigar", "rebut"))
        singleton = self.updater.update(
            initial, "cigar", self.feedback.evaluate("cigar", "cigar")
        )
        state = DecisionState(singleton, 2)
        policy = MaxInformationGainPolicy(self.feedback)

        self.assertEqual(policy.select_guess(state, ("adieu", "cigar")), "cigar")

    def test_max_information_gain_candidate_wins_controlled_equal_gain_tie(self):
        weighted = self.state.belief.__class__(
            candidates=self.state.belief.candidates,
            probability_mass=(
                ("cigar", 0.8),
                ("rebut", 0.1),
                ("sissy", 0.1),
            ),
        )
        state = DecisionState(weighted, 2)
        policy = MaxInformationGainPolicy(
            self.feedback,
            information_gain_calculator=ConstantInformationGainCalculator(),
        )

        self.assertEqual(policy.select_guess(state, ("adieu", "cigar")), "cigar")

    def test_max_information_gain_non_answer_tie_keeps_stable_legal_order(self):
        policy = MaxInformationGainPolicy(
            self.feedback,
            information_gain_calculator=ConstantInformationGainCalculator(),
        )

        self.assertEqual(policy.select_guess(self.state, ("arise", "adieu")), "arise")

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

    def test_exact_planner_equal_success_prefers_lower_expected_guesses(self):
        belief = UniformPrior().initial_belief(("cigar",))
        state = DecisionState(belief=belief, remaining_guesses=2)
        planner = ExactBayesOptimalPlanner()

        self.assertAlmostEqual(
            planner.success_probability(
                state, ("adieu", "cigar"), self.feedback, self.updater
            ),
            1.0,
        )
        self.assertEqual(
            planner.select_guess(
                state, ("adieu", "cigar"), self.feedback, self.updater
            ),
            "cigar",
        )

    def test_exact_planner_singleton_posterior_guesses_answer_immediately(self):
        belief = UniformPrior().initial_belief(("cigar",))
        state = DecisionState(belief=belief, remaining_guesses=1)
        planner = ExactBayesOptimalPlanner()

        self.assertEqual(
            planner.select_guess(
                state, ("adieu", "cigar"), self.feedback, self.updater
            ),
            "cigar",
        )

    def test_closed_forms_have_their_proved_lexicographic_values(self):
        singleton = DecisionState(
            UniformPrior().initial_belief(("cigar",)),
            remaining_guesses=3,
        )
        planner = ExactBayesOptimalPlanner(optimization_layers=("closed_forms",))
        self.assertEqual(
            planner.select_guess(
                singleton,
                ("adieu", "cigar"),
                self.feedback,
                self.updater,
            ),
            "cigar",
        )
        self.assertEqual(
            planner._guess_value(
                singleton,
                "cigar",
                ("adieu", "cigar"),
                self.feedback,
                self.updater,
            ),
            (1.0, 1.0),
        )

        last_horizon_belief = singleton.belief.__class__(
            candidates=("cigar", "rebut"),
            probability_mass=(("cigar", 0.2), ("rebut", 0.8)),
        )
        last_horizon = DecisionState(last_horizon_belief, remaining_guesses=1)
        self.assertEqual(
            planner.select_guess(
                last_horizon,
                ("adieu", "cigar", "rebut"),
                self.feedback,
                self.updater,
            ),
            "rebut",
        )
        self.assertEqual(
            planner._guess_value(
                last_horizon,
                "rebut",
                ("adieu", "cigar", "rebut"),
                self.feedback,
                self.updater,
            ),
            (0.8, 1.0),
        )

        two_candidates = DecisionState(last_horizon_belief, remaining_guesses=2)
        self.assertEqual(
            planner.select_guess(
                two_candidates,
                ("adieu", "cigar", "rebut"),
                self.feedback,
                self.updater,
            ),
            "rebut",
        )
        self.assertEqual(
            planner._guess_value(
                two_candidates,
                "rebut",
                ("adieu", "cigar", "rebut"),
                self.feedback,
                self.updater,
            ),
            (1.0, 1.2),
        )

    def test_canonical_key_normalizes_mass_and_ignores_history(self):
        first = self.state.belief.__class__(
            candidates=("cigar", "rebut", "sissy"),
            observations=(("adieu", (0, 0)),),
            probability_mass=(("cigar", 2.0), ("rebut", 3.0), ("sissy", 5.0)),
        )
        second = self.state.belief.__class__(
            candidates=("sissy", "cigar", "rebut"),
            observations=(("arise", (1, 0)),),
            probability_mass=(("sissy", 0.5), ("cigar", 0.2), ("rebut", 0.3)),
        )
        first_key = ExactBayesOptimalPlanner._canonical_key(
            DecisionState(first, 2), ("rebut", "adieu", "cigar")
        )
        second_key = ExactBayesOptimalPlanner._canonical_key(
            DecisionState(second, 2), ("cigar", "rebut", "adieu")
        )
        self.assertEqual(first_key, second_key)

    def test_reference_and_optimized_planners_match_on_deterministic_random_states(self):
        rng = random.Random(20261025)
        support = ("awake", "cigar", "humph", "rebut", "sissy")
        legal = (
            "adieu",
            "arise",
            "awake",
            "cigar",
            "covid",
            "humph",
            "padel",
            "rebut",
            "sissy",
            "stare",
        )
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, support)
        for _ in range(24):
            selected = tuple(sorted(rng.sample(support, rng.randint(1, len(support)))))
            raw = [rng.randint(1, 9) for _ in selected]
            total = float(sum(raw))
            belief = self.state.belief.__class__(
                candidates=selected,
                probability_mass=tuple(
                    (word, value / total) for word, value in zip(selected, raw)
                ),
            )
            state = DecisionState(belief, rng.randint(1, 3))
            reference = ExactBayesOptimalReferencePlanner()
            optimized = ExactBayesOptimalPlanner(feedback_matrix=matrix)
            reference_guess = reference.select_guess(
                state, legal, self.feedback, self.updater
            )
            optimized_guess = optimized.select_guess(
                state, legal, self.feedback, self.updater
            )
            reference_value = reference._guess_value(
                state, reference_guess, legal, self.feedback, self.updater
            )
            optimized_value = optimized._guess_value(
                state, optimized_guess, legal, self.feedback, self.updater
            )
            self.assertEqual(optimized_guess, reference_guess)
            self.assertIsNotNone(reference_value)
            self.assertIsNotNone(optimized_value)
            self.assertAlmostEqual(optimized_value[0], reference_value[0])
            self.assertAlmostEqual(optimized_value[1], reference_value[1])

    def test_branch_and_bound_prunes_only_noncompetitive_actions(self):
        support = ("awake", "cigar", "humph", "rebut", "sissy")
        legal = (
            "adieu",
            "arise",
            "awake",
            "cigar",
            "covid",
            "humph",
            "padel",
            "rebut",
            "sissy",
            "stare",
        )
        belief = UniformPrior().initial_belief(support)
        state = DecisionState(belief, 3)
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, support)
        reference = ExactBayesOptimalReferencePlanner()
        optimized = ExactBayesOptimalPlanner(feedback_matrix=matrix)
        reference_guess = reference.select_guess(
            state, legal, self.feedback, self.updater
        )
        optimized_guess = optimized.select_guess(
            state, legal, self.feedback, self.updater
        )
        self.assertEqual(optimized_guess, reference_guess)
        reference_value = reference._guess_value(
            state, reference_guess, legal, self.feedback, self.updater
        )
        optimized_value = optimized._guess_value(
            state, optimized_guess, legal, self.feedback, self.updater
        )
        self.assertEqual(optimized_value, reference_value)
        self.assertGreater(optimized.stats["actions_pruned"], 0)
        self.assertLess(
            optimized.stats["actions_completed"],
            optimized.stats["actions_evaluated"],
        )

    def test_horizon_two_scalar_formula_counts_only_legal_final_answers(self):
        weighted = self.state.belief.__class__(
            candidates=("cigar", "rebut", "sissy"),
            probability_mass=(
                ("cigar", 0.6),
                ("rebut", 0.3),
                ("sissy", 0.1),
            ),
        )
        state = DecisionState(weighted, remaining_guesses=2)
        planner = ExactBayesOptimalPlanner(
            optimization_layers=("horizon_two_closed_form",)
        )
        legal = ("adieu", "cigar", "rebut")

        # Guessing cigar wins on the 0.6 branch, can recover rebut on the
        # (0, 1) branch, and cannot give final-guess credit to sissy because
        # sissy is not legal in this state.
        cigar_value = planner._guess_value(
            state, "cigar", legal, self.feedback, self.updater
        )
        self.assertIsNotNone(cigar_value)
        self.assertAlmostEqual(cigar_value[0], 0.9)
        self.assertAlmostEqual(cigar_value[1], 1.4)
        # A non-answer probe cannot win immediately; its final guess can only
        # recover the largest legal candidate mass in each feedback branch.
        probe_value = planner._guess_value(
            state, "adieu", legal, self.feedback, self.updater
        )
        self.assertIsNotNone(probe_value)
        self.assertAlmostEqual(probe_value[0], 0.6)
        self.assertAlmostEqual(probe_value[1], 2.0)

    def test_horizon_two_scalar_formula_matches_reference_on_random_weighted_states(self):
        rng = random.Random(20261026)
        support = ("awake", "cigar", "humph", "rebut", "sissy")
        legal = (
            "adieu",
            "arise",
            "awake",
            "cigar",
            "covid",
            "humph",
            "padel",
            "rebut",
            "sissy",
            "stare",
        )
        for _ in range(32):
            selected = tuple(sorted(rng.sample(support, rng.randint(1, len(support)))))
            raw = [rng.randint(1, 19) for _ in selected]
            total = float(sum(raw))
            belief = self.state.belief.__class__(
                candidates=selected,
                probability_mass=tuple(
                    (word, value / total) for word, value in zip(selected, raw)
                ),
            )
            state = DecisionState(belief, remaining_guesses=2)
            reference = ExactBayesOptimalReferencePlanner()
            scalar = ExactBayesOptimalPlanner(
                optimization_layers=("horizon_two_closed_form",)
            )
            for guess in legal:
                reference_value = reference._guess_value(
                    state, guess, legal, self.feedback, self.updater
                )
                scalar_value = scalar._guess_value(
                    state, guess, legal, self.feedback, self.updater
                )
                self.assertIsNotNone(reference_value)
                self.assertIsNotNone(scalar_value)
                self.assertAlmostEqual(scalar_value[0], reference_value[0])
                self.assertAlmostEqual(scalar_value[1], reference_value[1])
            self.assertEqual(
                scalar.select_guess(state, legal, self.feedback, self.updater),
                reference.select_guess(state, legal, self.feedback, self.updater),
            )

    def test_horizon_two_matrix_batch_matches_scalar_and_reference_with_duplicates(self):
        support = ("awake", "cigar", "humph", "rebut", "sissy")
        legal = (
            "adieu",
            "arise",
            "awake",
            "cigar",
            "covid",
            "humph",
            "padel",
            "rebut",
            "sissy",
            "stare",
        )
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, support)
        rng = random.Random(20261027)
        for _ in range(24):
            selected = tuple(sorted(rng.sample(support, rng.randint(2, len(support)))))
            raw = [rng.randint(1, 19) for _ in selected]
            total = float(sum(raw))
            belief = self.state.belief.__class__(
                candidates=selected,
                probability_mass=tuple(
                    (word, value / total) for word, value in zip(selected, raw)
                ),
            )
            state = DecisionState(belief, remaining_guesses=2)
            reference = ExactBayesOptimalReferencePlanner()
            scalar = ExactBayesOptimalPlanner(
                optimization_layers=("horizon_two_closed_form",)
            )
            batch = ExactBayesOptimalPlanner(
                feedback_matrix=matrix,
                optimization_layers=(
                    "matrix_transitions",
                    "canonical_memoization",
                    "horizon_two_closed_form",
                    "horizon_two_batch",
                ),
            )
            for guess in legal:
                scalar_value = scalar._guess_value(
                    state, guess, legal, self.feedback, self.updater
                )
                batch_value = batch._guess_value(
                    state, guess, legal, self.feedback, self.updater
                )
                reference_value = reference._guess_value(
                    state, guess, legal, self.feedback, self.updater
                )
                self.assertAlmostEqual(batch_value[0], scalar_value[0])
                self.assertAlmostEqual(batch_value[1], scalar_value[1])
                self.assertAlmostEqual(batch_value[0], reference_value[0])
                self.assertAlmostEqual(batch_value[1], reference_value[1])
            self.assertEqual(
                batch.select_guess(state, legal, self.feedback, self.updater),
                reference.select_guess(state, legal, self.feedback, self.updater),
            )
        self.assertGreater(batch.stats["horizon_two_batch_calls"], 0)

    def test_matrix_eligibility_is_checked_once_per_transition(self):
        support = ("awake", "cigar", "humph", "rebut", "sissy")
        legal = (
            "adieu",
            "arise",
            "awake",
            "cigar",
            "covid",
            "humph",
            "padel",
            "rebut",
            "sissy",
            "stare",
        )
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, support)
        planner = ExactBayesOptimalPlanner(
            feedback_matrix=matrix,
            optimization_layers=(
                "closed_forms",
                "matrix_transitions",
                "canonical_memoization",
                "action_ordering",
                "branch_ordering",
                "branch_and_bound",
            ),
        )
        planner.select_guess(self.state, legal, self.feedback, self.updater)

        self.assertGreater(planner.stats["matrix_transition_calls"], 0)
        self.assertEqual(
            planner.stats["matrix_eligibility_checks"],
            planner.stats["matrix_transition_calls"],
        )
        instrumentation = planner.instrumentation()
        self.assertGreater(instrumentation["branch_count_histogram"].get("1", 0), 0)
        self.assertGreater(instrumentation["branch_size_histogram"].get("1", 0), 0)
        self.assertGreater(instrumentation["state_support_histogram"].get("5", 0), 0)
        self.assertGreater(instrumentation["action_sort_calls"], 0)
        self.assertGreater(instrumentation["branch_grouping_calls"], 0)


if __name__ == "__main__":
    unittest.main()
