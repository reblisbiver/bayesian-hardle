import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_hardle.accelerated import ExactFeedbackCodeMatrix  # noqa: E402
from bayesian_hardle.belief import BeliefState, ExactPosteriorUpdater, UniformPrior  # noqa: E402
from bayesian_hardle.decision import (  # noqa: E402
    DecisionState,
    ExactBayesOptimalPlanner,
    ExactBayesOptimalReferencePlanner,
    POLICY_TIE_TOLERANCE,
)
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402


class UniformH3CapacityTests(unittest.TestCase):
    def setUp(self):
        self.feedback = HardleFeedbackEngine()
        self.updater = ExactPosteriorUpdater(self.feedback)
        self.answers = tuple(
            line.strip()
            for line in (
                PROJECT_ROOT / "data" / "wordlists" / "wordle-candidate-answers.txt"
            ).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )

    def _optimized_layers(self):
        return tuple(
            layer
            for layer in ExactBayesOptimalPlanner.ALL_OPTIMIZATION_LAYERS
            if layer != "horizon_two_child_batch"
        )

    def _paired_planners(self, support, legal):
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, support)
        reference = ExactBayesOptimalReferencePlanner()
        optimized = ExactBayesOptimalPlanner(
            feedback_matrix=matrix,
            optimization_layers=self._optimized_layers(),
        )
        state = DecisionState(UniformPrior().initial_belief(support), 3)
        return reference, optimized, state

    def test_integer_capacity_units_cover_small_large_and_win_branches(self):
        small = tuple(
            (f"a{i:04d}", 1.0, ((f"a{i:04d}", 1.0),)) for i in range(3)
        )
        large_members = tuple((f"b{i:04d}", 1.0, ) for i in range(40))
        branches = (
            ((5, 0), 1.0, (("win", 1.0),)),
            ((1, 1), 1.0, tuple((word, 1.0) for word, _ in large_members)),
            ((0, 1), 1.0, tuple((word, 1.0) for word, _, _ in small)),
        )

        self.assertEqual(
            ExactBayesOptimalPlanner._uniform_h3_capacity_units(branches, 5),
            (1, 36, 3),
        )

    def test_actual_uniform_children_never_exceed_branch_capacity_with_duplicates(self):
        repeated = ("abbey", "array", "civic", "eerie", "sassy", "sissy")
        sampled = tuple(
            word
            for word in self.answers
            if word not in repeated
        )[:44]
        support = tuple(sorted(repeated + sampled))
        legal = tuple(sorted(set(support) | {"adieu", "arise", "cigar", "covid", "padel"}))
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, support)
        state = DecisionState(UniformPrior().initial_belief(support), 3)
        mass_table = ExactBayesOptimalPlanner._mass_table(state.belief)
        planner = ExactBayesOptimalPlanner(feedback_matrix=matrix)
        root_size = len(support)

        for root_guess in ("abbey", "cigar"):
            branches = planner._transition_branches(
                state,
                root_guess,
                mass_table,
                self.feedback,
                use_matrix=True,
            )
            units = planner._uniform_h3_capacity_units(branches, 5)
            self.assertEqual(
                any(outcome == (5, 0) for outcome, _, _ in branches),
                root_guess in support,
            )
            for unit, (outcome, _, members) in zip(units, branches):
                child_size = len(members)
                if outcome == (5, 0):
                    self.assertEqual(unit, 1)
                    self.assertEqual(child_size, 1)
                    continue
                child_words = tuple(word for word, _ in members)
                child_weights = tuple(1.0 / child_size for _ in child_words)
                values = matrix.horizon_two_values(
                    legal,
                    child_words,
                    child_weights,
                    legal,
                )
                best_child_success = max(value[0] for value in values)
                actual_root_contribution = child_size / root_size * best_child_success
                capacity = unit / root_size
                self.assertLessEqual(actual_root_contribution, capacity + 1e-12)

    def test_optimized_planner_matches_reference_on_small_support_with_win(self):
        support = ("abbey", "array", "civic", "eerie", "sassy", "sissy")
        legal = tuple(sorted(set(support) | {"adieu", "arise", "cigar", "rebut"}))
        reference, optimized, state = self._paired_planners(support, legal)

        expected_guess = reference.select_guess(
            state, legal, self.feedback, self.updater
        )
        expected_value = reference._guess_value(
            state, expected_guess, legal, self.feedback, self.updater
        )
        selected = optimized.select_guess(state, legal, self.feedback, self.updater)
        value = optimized._guess_value(
            state, selected, legal, self.feedback, self.updater
        )

        self.assertEqual(selected, expected_guess)
        self.assertIsNotNone(value)
        self.assertIsNotNone(expected_value)
        self.assertAlmostEqual(value[0], expected_value[0], places=12)
        self.assertAlmostEqual(value[1], expected_value[1], places=12)
        self.assertGreater(
            optimized.stats["uniform_h3_capacity_initializations"], 0
        )

    def test_optimized_planner_matches_reference_on_large_support_probe_without_win(self):
        repeated = ("abbey", "array", "civic", "eerie", "sassy", "sissy")
        support = tuple(sorted(repeated + self.answers[20:51]))
        legal = tuple(sorted(set(support) | {"adieu"}))
        reference, optimized, state = self._paired_planners(support, legal)

        expected_guess = reference.select_guess(
            state, legal, self.feedback, self.updater
        )
        expected_value = reference._guess_value(
            state, expected_guess, legal, self.feedback, self.updater
        )
        selected = optimized.select_guess(state, legal, self.feedback, self.updater)
        value = optimized._guess_value(
            state, selected, legal, self.feedback, self.updater
        )

        self.assertEqual(selected, expected_guess)
        self.assertIsNotNone(value)
        self.assertIsNotNone(expected_value)
        self.assertAlmostEqual(value[0], expected_value[0], places=12)
        self.assertAlmostEqual(value[1], expected_value[1], places=12)
        self.assertGreater(optimized.stats["uniform_h3_capacity_initializations"], 0)

    def test_capacity_bound_can_prune_before_any_child_h2_work(self):
        support = tuple(self.answers[:100])
        legal = ("adieu", "arise", "cigar", "covid", "padel")
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, support)
        state = DecisionState(UniformPrior().initial_belief(support), 3)
        planner = ExactBayesOptimalPlanner(
            feedback_matrix=matrix,
            optimization_layers=self._optimized_layers(),
            root_audit=True,
        )

        value = planner._guess_value(
            state,
            "cigar",
            legal,
            self.feedback,
            self.updater,
            incumbent=(0.95, 1.0),
        )

        self.assertIsNone(value)
        self.assertEqual(planner.stats["horizon_two_child_exact_solves"], 0)
        self.assertEqual(
            planner.stats["uniform_h3_capacity_pruned_before_first_child"], 1
        )

    def test_nonuniform_and_non_h3_states_use_fallback_semantics(self):
        support = ("abbey", "array", "civic", "eerie", "sassy")
        legal = tuple(sorted(set(support) | {"adieu", "arise", "cigar"}))
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, support)
        weighted = BeliefState(
            candidates=support,
            probability_mass=tuple(
                (word, float(index + 1)) for index, word in enumerate(support)
            ),
        )
        weighted_state = DecisionState(weighted, 3)
        planner = ExactBayesOptimalPlanner(
            feedback_matrix=matrix,
            optimization_layers=self._optimized_layers(),
        )
        planner.select_guess(weighted_state, legal, self.feedback, self.updater)
        self.assertEqual(planner.stats["uniform_h3_capacity_initializations"], 0)

        uniform_state = DecisionState(UniformPrior().initial_belief(support), 2)
        planner.select_guess(uniform_state, legal, self.feedback, self.updater)
        self.assertEqual(planner.stats["uniform_h3_capacity_initializations"], 0)

    def test_tie_tolerance_keeps_exact_equality_and_only_prunes_strict_losses(self):
        incumbent = (0.5, 1.5)
        self.assertFalse(
            ExactBayesOptimalPlanner._cannot_beat_incumbent(
                incumbent[0], incumbent[1], incumbent
            )
        )
        self.assertFalse(
            ExactBayesOptimalPlanner._cannot_beat_incumbent(
                incumbent[0] - POLICY_TIE_TOLERANCE / 2,
                incumbent[1],
                incumbent,
            )
        )
        self.assertTrue(
            ExactBayesOptimalPlanner._cannot_beat_incumbent(
                incumbent[0],
                incumbent[1] + 2 * POLICY_TIE_TOLERANCE,
                incumbent,
            )
        )
        self.assertTrue(
            ExactBayesOptimalPlanner._cannot_beat_incumbent(
                incumbent[0] - 2 * POLICY_TIE_TOLERANCE,
                incumbent[1],
                incumbent,
            )
        )


if __name__ == "__main__":
    unittest.main()
