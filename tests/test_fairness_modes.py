import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_hardle.fairness import (  # noqa: E402
    GeneralEnglishFrequencyPrior,
    resolve_hypothesis_mode,
)
from bayesian_hardle.game import WordListVocabularyRepository  # noqa: E402


class FairnessModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vocabulary = WordListVocabularyRepository.from_repository_root(PROJECT_ROOT)

    def test_full_uniform_uses_all_legal_words_and_primary_label(self):
        mode = resolve_hypothesis_mode("full-uniform", self.vocabulary)

        self.assertEqual(mode.support, tuple(self.vocabulary.legal_guesses()))
        self.assertEqual(mode.prior.initial_belief(mode.support).total_mass, 1.0)
        self.assertEqual(mode.label, "full-uniform (PRIMARY STRICT FAIRNESS)")
        self.assertFalse(mode.answer_list_aware)

    def test_frequency_prior_is_positive_normalized_and_uses_injected_general_frequency(self):
        def fake_zipf(word, language):
            self.assertEqual(language, "en")
            return 8.0 if word == "cigar" else 1.0

        prior = GeneralEnglishFrequencyPrior(
            frequency_function=fake_zipf,
            source_version="3.1.1-test-double",
        )
        mode = resolve_hypothesis_mode(
            "full-frequency", self.vocabulary, frequency_prior=prior
        )
        belief = mode.prior.initial_belief(mode.support)
        masses = dict(belief.probability_mass)

        self.assertEqual(len(mode.support), 12974)
        self.assertEqual(belief.total_mass, 1.0)
        self.assertTrue(all(value > 0.0 for value in masses.values()))
        self.assertGreater(masses["cigar"], masses["civic"])
        self.assertEqual(mode.provenance["source"], "wordfreq")
        self.assertEqual(mode.provenance["version"], "3.1.1-test-double")

    def test_curated_mode_is_explicitly_answer_list_aware_and_isolated(self):
        mode = resolve_hypothesis_mode("curated-2315", self.vocabulary)

        self.assertEqual(mode.support, tuple(self.vocabulary.target_vocabulary()))
        self.assertEqual(len(mode.support), 2315)
        self.assertTrue(mode.answer_list_aware)
        self.assertEqual(
            mode.label,
            "curated-2315 (DIAGNOSTIC / ANSWER-LIST-AWARE)",
        )

    def test_legal_word_outside_curated_support_remains_in_fair_modes(self):
        legal = set(self.vocabulary.legal_guesses())
        curated = set(self.vocabulary.target_vocabulary())
        outside = sorted(legal - curated)[0]

        for name in ("full-uniform", "full-frequency"):
            prior = (
                GeneralEnglishFrequencyPrior(
                    frequency_function=lambda word, language: 1.0,
                    source_version="3.1.1-test-double",
                )
                if name == "full-frequency"
                else None
            )
            mode = resolve_hypothesis_mode(name, self.vocabulary, prior)
            belief = mode.prior.initial_belief(mode.support)
            self.assertIn(outside, belief.candidates)
            self.assertGreater(belief.mass_for(outside), 0.0)

    def test_fair_modes_do_not_read_curated_answer_membership(self):
        class LegalOnlyRepository:
            def legal_guesses(self):
                return ("aahed", "cigar")

            def target_vocabulary(self):
                raise AssertionError("fair mode must not read curated answers")

        repository = LegalOnlyRepository()
        resolve_hypothesis_mode("full-uniform", repository)
        resolve_hypothesis_mode(
            "full-frequency",
            repository,
            GeneralEnglishFrequencyPrior(
                frequency_function=lambda word, language: 1.0,
                source_version="3.1.1-test-double",
            ),
        )


if __name__ == "__main__":
    unittest.main()
