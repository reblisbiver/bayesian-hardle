import sys
import unittest
import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_hardle.accelerated import ExactFeedbackCodeMatrix  # noqa: E402
from bayesian_hardle.game import (  # noqa: E402
    HardleFeedbackEngine,
    WordListVocabularyRepository,
)
from bayesian_hardle.belief import (  # noqa: E402
    BeliefState,
    ExactPosteriorUpdater,
    UniformPrior,
)
from bayesian_hardle.information import (  # noqa: E402
    ExactInformationGainCalculator,
    ExactOutcomePartitioner,
)
from bayesian_hardle.decision import DecisionState, MaxInformationGainPolicy  # noqa: E402
from bayesian_hardle.accelerated import MatrixInformationGainCalculator  # noqa: E402


class AcceleratedMaxIGTests(unittest.TestCase):
    def test_matrix_preserves_duplicate_aware_feedback_and_round_trips_codes(self):
        legal = ("allee", "eagle", "llama", "belle", "civic")
        answers = ("allee", "eagle", "llama", "belle", "civic")
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, answers)
        scalar = HardleFeedbackEngine()

        for guess in legal:
            for answer in answers:
                expected = scalar.evaluate(guess, answer)
                code = matrix.code_for(guess, answer)
                self.assertEqual(matrix.decode_code(code), expected)
                self.assertEqual(
                    matrix.row_for(guess)[matrix.answer_index(answer)], code
                )

    def test_full_vocabulary_matrix_matches_10000_deterministic_pairs(self):
        vocabulary = WordListVocabularyRepository.from_repository_root(PROJECT_ROOT)
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(
            vocabulary.legal_guesses(), vocabulary.target_vocabulary()
        )
        scalar = HardleFeedbackEngine()
        rng = random.Random(20261025)

        for _ in range(10000):
            guess = rng.choice(vocabulary.legal_guesses())
            answer = rng.choice(vocabulary.target_vocabulary())
            self.assertEqual(
                matrix.decode_code(matrix.code_for(guess, answer)),
                scalar.evaluate(guess, answer),
            )
        self.assertEqual(matrix.matrix.dtype.name, "uint8")
        self.assertFalse(matrix.matrix.flags.writeable)

    def test_weighted_matrix_entropy_matches_reference_on_random_beliefs(self):
        vocabulary = WordListVocabularyRepository.from_repository_root(PROJECT_ROOT)
        legal = tuple(vocabulary.legal_guesses()[:80])
        answers = tuple(vocabulary.target_vocabulary()[:60])
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, answers)
        scalar = HardleFeedbackEngine()
        partitioner = ExactOutcomePartitioner()
        reference = ExactInformationGainCalculator()
        accelerated = MatrixInformationGainCalculator(matrix)
        rng = random.Random(20261026)

        uniform = UniformPrior().initial_belief(answers)
        beliefs = [uniform]
        for _ in range(5):
            subset = tuple(rng.sample(answers, 3 + (_ % 5)))
            raw = [rng.random() + 0.01 for _ in subset]
            beliefs.append(
                BeliefState(
                    candidates=subset,
                    probability_mass=tuple(zip(subset, raw)),
                )
            )

        for belief in beliefs:
            for guess in legal[:12]:
                distribution = partitioner.partition(belief, guess, scalar)
                expected = reference.calculate(belief, guess, distribution)
                actual = accelerated.calculate(belief, guess)
                self.assertAlmostEqual(actual, expected, delta=1e-12)

    def test_fast_and_reference_policies_choose_identical_actions_and_cache(self):
        scalar = HardleFeedbackEngine()
        answers = ("awake", "cigar", "humph", "rebut", "sissy")
        belief = UniformPrior().initial_belief(answers)
        state = DecisionState(belief, 3)
        legal = ("arise", "cigar", "rebut", "sissy")

        fast = MaxInformationGainPolicy(scalar)
        reference = MaxInformationGainPolicy(scalar, use_acceleration=False)
        expected = reference.select_guess(state, legal)
        self.assertEqual(fast.select_guess(state, legal), expected)
        evaluated = fast.evaluated_guesses
        self.assertEqual(fast.select_guess(state, legal), expected)
        self.assertEqual(fast.evaluated_guesses, evaluated)
        self.assertEqual(fast.decision_cache_hits, 1)

    def test_fast_and_reference_select_same_guess_on_random_weighted_subsets(self):
        vocabulary = WordListVocabularyRepository.from_repository_root(PROJECT_ROOT)
        legal = tuple(vocabulary.legal_guesses()[:32])
        answer_pool = tuple(vocabulary.target_vocabulary()[:48])
        scalar = HardleFeedbackEngine()
        rng = random.Random(20261027)

        for _ in range(6):
            answers = tuple(rng.sample(answer_pool, 4 + rng.randrange(8)))
            raw = [rng.random() + 0.01 for _ in answers]
            belief = BeliefState(
                candidates=answers,
                probability_mass=tuple(zip(answers, raw)),
            )
            state = DecisionState(belief, 2)
            fast = MaxInformationGainPolicy(scalar)
            reference = MaxInformationGainPolicy(scalar, use_acceleration=False)
            self.assertEqual(
                fast.select_guess(state, legal),
                reference.select_guess(state, legal),
            )

    def test_fast_policy_does_not_change_canonical_candidate_filtering(self):
        scalar = HardleFeedbackEngine()
        updater = ExactPosteriorUpdater(scalar)
        answers = ("allee", "eagle", "llama", "belle", "civic")
        initial = UniformPrior().initial_belief(answers)
        state = DecisionState(initial, 3)
        policy = MaxInformationGainPolicy(scalar)
        guess = policy.select_guess(state, ("allee", "eagle", "llama", "belle", "civic"))
        feedback = scalar.evaluate(guess, "llama")
        actual = updater.update(initial, guess, feedback)
        retained = tuple(
            word for word in answers if scalar.evaluate(guess, word) == feedback
        )
        expected = BeliefState(
            candidates=retained,
            observations=((guess, feedback),),
            probability_mass=tuple(
                (word, 1.0 / len(retained)) for word in retained
            ),
        )
        self.assertEqual(actual.candidates, expected.candidates)
        self.assertEqual(actual.probability_mass, expected.probability_mass)

    def test_fast_policy_preserves_candidate_and_stable_order_ties(self):
        scalar = HardleFeedbackEngine()
        belief = UniformPrior().initial_belief(("cigar",))
        state = DecisionState(belief, 2)
        policy = MaxInformationGainPolicy(scalar)

        self.assertEqual(policy.select_guess(state, ("adieu", "cigar")), "cigar")
        policy = MaxInformationGainPolicy(scalar)
        self.assertEqual(policy.select_guess(state, ("arise", "adieu")), "arise")

    def test_batched_small_belief_scores_match_row_scores(self):
        legal = ("allee", "eagle", "llama", "belle", "civic", "arise")
        answers = ("allee", "eagle", "llama", "belle", "civic")
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, answers)
        belief = BeliefState(
            candidates=("allee", "llama", "civic"),
            probability_mass=(("allee", 0.2), ("llama", 0.3), ("civic", 0.5)),
        )
        scorer = MatrixInformationGainCalculator(matrix)
        answer_indices, weights = scorer.belief_arrays(belief)
        batch = scorer.entropies_for_rows(
            matrix.matrix[:, answer_indices], weights
        )

        for index, guess in enumerate(legal):
            self.assertAlmostEqual(
                float(batch[index]),
                scorer.entropy_for_row(matrix.row_for(guess), answer_indices, weights),
                delta=1e-12,
            )

    def test_batched_entropy_matches_reference_on_repeated_letter_belief(self):
        legal = ("allee", "eagle", "llama", "belle", "civic", "arise")
        answers = ("allee", "llama", "belle", "civic")
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, answers)
        scalar = HardleFeedbackEngine()
        belief = BeliefState(
            candidates=answers,
            probability_mass=(
                ("allee", 0.1),
                ("llama", 0.2),
                ("belle", 0.3),
                ("civic", 0.4),
            ),
        )
        reference = ExactInformationGainCalculator()
        partitioner = ExactOutcomePartitioner()
        accelerated = MatrixInformationGainCalculator(matrix)
        answer_indices, weights = accelerated.belief_arrays(belief)
        batch = accelerated.entropies_for_rows(
            matrix.matrix[:, answer_indices], weights
        )

        for index, guess in enumerate(legal):
            distribution = partitioner.partition(belief, guess, scalar)
            expected = reference.calculate(belief, guess, distribution)
            self.assertAlmostEqual(float(batch[index]), expected, delta=1e-12)


if __name__ == "__main__":
    unittest.main()
