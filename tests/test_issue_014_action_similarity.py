import unittest
import random

from bayesian_hardle.accelerated import ExactFeedbackCodeMatrix

from experiments.issue_014_h2_action_similarity import (
    action_value_from_partition,
    canonical_partition_signature,
    collapsed_h2_values,
    dominance_from_refinement,
    optimal_similarity_bounds,
    posterior_distance,
    safe_action_equivalence_key,
    similarity_action_bounds,
)


class Issue014ActionSimilarityTests(unittest.TestCase):
    def test_partition_signature_ignores_feedback_code_renaming(self):
        first = canonical_partition_signature((4, 4, 9, 2, 9, 2))
        relabeled = canonical_partition_signature((17, 17, 3, 8, 3, 8))
        different = canonical_partition_signature((4, 4, 9, 2, 4, 2))

        self.assertEqual(first, relabeled)
        self.assertNotEqual(first, different)

    def test_same_future_partition_needs_equal_immediate_mass(self):
        signature = ((0,), (1, 2))
        words = ("alpha", "bravo", "charlie")
        weights = (0.6, 0.25, 0.15)
        legal_final = words

        candidate_value = action_value_from_partition(
            signature, words, weights, legal_final, "alpha"
        )
        probe_value = action_value_from_partition(
            signature, words, weights, legal_final, "probe"
        )

        self.assertAlmostEqual(candidate_value[0], probe_value[0])
        self.assertAlmostEqual(candidate_value[1], 1.4)
        self.assertAlmostEqual(probe_value[1], 2.0)
        self.assertNotEqual(
            safe_action_equivalence_key(signature, "alpha", words, weights),
            safe_action_equivalence_key(signature, "probe", words, weights),
        )

    def test_partition_value_matches_exact_matrix_h2_value(self):
        legal = ("allee", "eagle", "llama", "belle", "civic", "arise")
        words = ("allee", "eagle", "llama", "belle", "civic")
        weights = (0.07, 0.19, 0.23, 0.31, 0.20)
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, words)
        exact = matrix.horizon_two_values(legal, words, weights, legal)

        for guess, expected in zip(legal, exact):
            signature = canonical_partition_signature(
                matrix.row_for(guess)[matrix.answer_indices(words)]
            )
            actual = action_value_from_partition(
                signature, words, weights, legal, guess
            )
            self.assertAlmostEqual(actual[0], expected[0], delta=1e-12)
            self.assertAlmostEqual(actual[1], expected[1], delta=1e-12)

    def test_collapsed_h2_values_match_every_exact_action_value(self):
        legal = ("allee", "eagle", "llama", "belle", "civic", "arise")
        words = ("allee", "eagle", "llama", "belle", "civic")
        weights = (0.07, 0.19, 0.23, 0.31, 0.20)
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, words)
        expected = matrix.horizon_two_values(legal, words, weights, legal)
        actual = collapsed_h2_values(matrix, legal, words, weights, legal)

        self.assertEqual(len(actual), len(expected))
        for actual_value, expected_value in zip(actual, expected):
            self.assertAlmostEqual(actual_value[0], expected_value[0], delta=1e-12)
            self.assertAlmostEqual(actual_value[1], expected_value[1], delta=1e-12)

    def test_partition_refinement_dominance_accounts_for_immediate_mass(self):
        coarser = ((0, 1), (2,))
        finer = ((0,), (1,), (2,))

        self.assertTrue(
            dominance_from_refinement(
                finer, coarser, immediate_mass_a=0.4, immediate_mass_b=0.2
            )
        )
        self.assertFalse(
            dominance_from_refinement(
                finer, coarser, immediate_mass_a=0.1, immediate_mass_b=0.2
            )
        )

    def test_partition_refinement_rule_survives_adversarial_small_partitions(self):
        def partitions(items):
            if not items:
                yield ()
                return
            first = items[0]
            for rest in partitions(items[1:]):
                for index in range(len(rest)):
                    yield rest[:index] + ((first,) + rest[index],) + rest[index + 1 :]
                yield rest + ((first,),)

        all_partitions = tuple(partitions(tuple(range(4))))
        rng = random.Random(20261026)
        words = tuple(f"w{index}" for index in range(4))
        legal = words
        for _ in range(32):
            raw = [rng.randint(1, 29) for _ in words]
            total = float(sum(raw))
            weights = tuple(value / total for value in raw)
            for finer in all_partitions:
                for coarser in all_partitions:
                    if not dominance_from_refinement(
                        finer,
                        coarser,
                        weights[0],
                        weights[1],
                    ):
                        continue
                    finer_value = action_value_from_partition(
                        finer, words, weights, legal, "w0"
                    )
                    coarser_value = action_value_from_partition(
                        coarser, words, weights, legal, "w1"
                    )
                    self.assertGreaterEqual(
                        finer_value[0] + 1e-12, coarser_value[0]
                    )
                    if abs(finer_value[0] - coarser_value[0]) <= 1e-12:
                        self.assertLessEqual(
                            finer_value[1], coarser_value[1] + 1e-12
                        )

    def test_similarity_action_bounds_contain_exact_neighbor_value(self):
        value = (0.7, 1.35)
        distance = 0.2
        lower, upper = similarity_action_bounds(value, distance)

        self.assertAlmostEqual(lower[0], 0.5)
        self.assertAlmostEqual(lower[1], 1.15)
        self.assertAlmostEqual(upper[0], 0.9)
        self.assertAlmostEqual(upper[1], 1.55)

    def test_similarity_optimal_bounds_use_near_optimal_action_set(self):
        solved = {
            "a": (0.80, 1.40),
            "b": (0.75, 1.10),
            "c": (0.10, 1.01),
        }
        bounds = optimal_similarity_bounds(solved, distance=0.04)

        self.assertAlmostEqual(bounds["success_lower"], 0.76)
        self.assertAlmostEqual(bounds["success_upper"], 0.84)
        self.assertEqual(bounds["candidate_actions"], ("a", "b"))
        self.assertAlmostEqual(bounds["expected_lower"], 1.06)
        self.assertAlmostEqual(bounds["expected_upper"], 1.44)

    def test_similarity_optimal_bounds_contain_exact_matrix_neighbor(self):
        legal = ("allee", "eagle", "llama", "belle", "civic", "arise")
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, legal[:-1])
        first_words = ("allee", "eagle", "llama")
        second_words = ("allee", "eagle", "belle")
        first_weights = (0.2, 0.3, 0.5)
        second_weights = (0.2, 0.3, 0.5)
        first_values = dict(
            zip(
                legal,
                matrix.horizon_two_values(
                    legal, first_words, first_weights, legal
                ),
            )
        )
        second_values = dict(
            zip(
                legal,
                matrix.horizon_two_values(
                    legal, second_words, second_weights, legal
                ),
            )
        )
        distance = posterior_distance(
            dict(zip(first_words, first_weights)),
            dict(zip(second_words, second_weights)),
        )["total_variation"]
        bounds = optimal_similarity_bounds(first_values, distance)
        second_best = max(
            second_values.values(), key=lambda value: (value[0], -value[1])
        )

        self.assertLessEqual(
            bounds["success_lower"] - 1e-12,
            second_best[0],
        )
        self.assertGreaterEqual(
            bounds["success_upper"] + 1e-12,
            second_best[0],
        )
        self.assertLessEqual(
            bounds["expected_lower"] - 1e-12,
            second_best[1],
        )
        self.assertGreaterEqual(
            bounds["expected_upper"] + 1e-12,
            second_best[1],
        )

    def test_posterior_distance_reports_added_and_removed_mass(self):
        distance = posterior_distance(
            {"a": 0.6, "b": 0.4},
            {"a": 0.5, "c": 0.5},
        )

        self.assertAlmostEqual(distance["total_variation"], 0.5)
        self.assertAlmostEqual(distance["removed_mass"], 0.5)
        self.assertAlmostEqual(distance["added_mass"], 0.5)
        self.assertEqual(distance["removed_count"], 1)
        self.assertEqual(distance["added_count"], 1)


if __name__ == "__main__":
    unittest.main()
