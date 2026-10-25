import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_hardle.game import (  # noqa: E402
    GameSpec,
    HardleFeedbackEngine,
    HardleTerminalRules,
    WordListVocabularyRepository,
)


class GameBehaviorTests(unittest.TestCase):
    def test_feedback_counts_duplicate_letters_with_target_multiplicity(self):
        engine = HardleFeedbackEngine()

        self.assertEqual(engine.evaluate("allee", "eagle"), (1, 3))
        self.assertEqual(engine.evaluate("abbey", "bobby"), (2, 1))
        self.assertEqual(engine.evaluate("cacao", "acorn"), (0, 3))

    def test_feedback_is_all_exact_only_for_the_same_word(self):
        engine = HardleFeedbackEngine()
        self.assertEqual(engine.evaluate("cigar", "cigar"), (5, 0))
        self.assertNotEqual(engine.evaluate("cigar", "rigac"), (5, 0))

    def test_malformed_words_are_rejected(self):
        engine = HardleFeedbackEngine()
        with self.assertRaises(ValueError):
            engine.evaluate("four", "cigar")
        with self.assertRaises(ValueError):
            engine.evaluate("cigar", "CIGAR!")

    def test_terminal_rules_stop_on_win_or_guess_limit(self):
        rules = HardleTerminalRules()
        spec = GameSpec(word_length=5, max_guesses=10)
        self.assertTrue(rules.is_terminal("cigar", (5, 0), 1, spec))
        self.assertFalse(rules.is_terminal("cigar", (4, 0), 9, spec))
        self.assertTrue(rules.is_terminal("cigar", (0, 0), 10, spec))

    def test_legal_guesses_include_exact_hardle_additions_but_answers_do_not(self):
        repository = WordListVocabularyRepository(
            legal_words=("cigar", "rebut", "covid"),
            answer_words=("cigar", "rebut"),
        )
        self.assertEqual(len(repository.legal_guesses()), 4)
        self.assertIn("covid", repository.legal_guesses())
        self.assertIn("padel", repository.legal_guesses())
        self.assertEqual(repository.target_vocabulary(), ("cigar", "rebut"))
        self.assertNotIn("covid", repository.target_vocabulary())

    def test_vendored_supervisor_inputs_have_declared_counts(self):
        repository = WordListVocabularyRepository.from_repository_root(PROJECT_ROOT)
        base_lines = (PROJECT_ROOT / "data/wordlists/wordle-legal-guesses.txt").read_text(
            encoding="utf-8"
        ).splitlines()
        self.assertEqual(len(base_lines), 12972)
        self.assertEqual(len(repository.legal_guesses()), 12974)
        self.assertEqual(len(repository.target_vocabulary()), 2315)
        self.assertEqual(set(("covid", "padel")) - set(repository.legal_guesses()), set())
        self.assertEqual(set(("covid", "padel")) & set(repository.target_vocabulary()), set())


if __name__ == "__main__":
    unittest.main()
