import tempfile
import unittest
from pathlib import Path

import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_hardle.application import (  # noqa: E402
    BattleSession,
    run_simulation,
)
from bayesian_hardle.fairness import GeneralEnglishFrequencyPrior  # noqa: E402
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402


class ApplicationSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        wordlists = root / "data" / "wordlists"
        wordlists.mkdir(parents=True)
        (wordlists / "wordle-legal-guesses.txt").write_text(
            "aahed\ncigar\nrebut\nsissy\n",
            encoding="utf-8",
        )
        (wordlists / "wordle-candidate-answers.txt").write_text(
            "aahed\ncigar\nrebut\n",
            encoding="utf-8",
        )
        self.root = root

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_known_target_runs_through_shared_application_service(self):
        result = run_simulation(
            "aahed",
            "full-uniform",
            "map",
            repository_root=self.root,
            use_cache=False,
        )

        self.assertTrue(result.solved)
        self.assertEqual(result.target, "aahed")
        self.assertEqual(result.turns[-1].feedback, (5, 0))
        self.assertGreaterEqual(result.turns[-1].cumulative_time_ms, 0.0)

    def test_full_frequency_keeps_positive_support_and_max_ig_uses_same_service(self):
        prior = GeneralEnglishFrequencyPrior(
            frequency_function=lambda word, language: 1.0 if word == "aahed" else 0.0,
            source_version="3.1.1-test-double",
        )
        result = run_simulation(
            "aahed",
            "full-frequency",
            "max-ig",
            repository_root=self.root,
            frequency_prior=prior,
            use_cache=False,
        )

        self.assertTrue(result.solved)
        self.assertEqual(len(result.mode.support), 6)
        self.assertGreater(result.mode.prior.initial_belief(result.mode.support).mass_for("rebut"), 0.0)

    def test_target_validation_rejects_target_outside_selected_support(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            run_simulation(
                "sissy",
                "curated-2315",
                "map",
                repository_root=self.root,
                use_cache=False,
            )

    def test_new_battle_samples_from_selected_support_with_injected_rng(self):
        class RecordingRng:
            def __init__(self):
                self.values = None

            def choice(self, values):
                self.values = tuple(values)
                return values[-1]

        rng = RecordingRng()
        battle = BattleSession(
            mode_name="full-uniform",
            policy_name="map",
            repository_root=self.root,
            use_cache=False,
            rng=rng,
        )

        self.assertEqual(len(rng.values), 6)
        outcome = battle.give_up()
        self.assertEqual(outcome.target, rng.values[-1])

    def test_battle_returns_only_human_feedback_before_finish(self):
        battle = BattleSession(
            mode_name="full-uniform",
            policy_name="map",
            repository_root=self.root,
            target="aahed",
            use_cache=False,
        )
        initial = battle.public_state()
        self.assertIsNone(initial.target)
        self.assertEqual(initial.solver_turns, ())

        result = battle.submit_human_guess("cigar")

        self.assertEqual(result.feedback, HardleFeedbackEngine().evaluate("cigar", "aahed"))
        self.assertFalse(result.finished)
        self.assertIsNone(result.public_state.target)
        self.assertEqual(result.public_state.solver_turns, ())
        self.assertEqual(result.public_state.human_turns[0].guess, "cigar")

    def test_solver_path_is_revealed_only_after_human_finish_even_if_solver_wins_first(self):
        battle = BattleSession(
            mode_name="full-uniform",
            policy_name="map",
            repository_root=self.root,
            target="aahed",
            max_guesses=2,
            use_cache=False,
        )

        first = battle.submit_human_guess("cigar")
        self.assertFalse(first.finished)
        self.assertEqual(first.public_state.solver_turns, ())

        finished = battle.submit_human_guess("aahed")
        self.assertTrue(finished.finished)
        self.assertEqual(finished.public_state.target, "aahed")
        self.assertTrue(finished.public_state.solver_solved)
        self.assertEqual(finished.public_state.solver_turns[-1].feedback, (5, 0))

    def test_give_up_finishes_and_reveals_complete_solver_trajectory(self):
        battle = BattleSession(
            mode_name="full-uniform",
            policy_name="map",
            repository_root=self.root,
            target="aahed",
            max_guesses=2,
            use_cache=False,
        )
        battle.submit_human_guess("cigar")

        outcome = battle.give_up()

        self.assertTrue(outcome.finished)
        self.assertTrue(outcome.gave_up)
        self.assertEqual(outcome.target, "aahed")
        self.assertGreaterEqual(len(outcome.solver_turns), 1)
        self.assertTrue(outcome.solver_turns[-1].status in {"SOLVED", "HORIZON_REACHED"})

    def test_invalid_human_guess_does_not_mutate_battle(self):
        battle = BattleSession(
            mode_name="full-uniform",
            policy_name="map",
            repository_root=self.root,
            target="aahed",
            use_cache=False,
        )

        with self.assertRaisesRegex(ValueError, "legal"):
            battle.submit_human_guess("xxxxx")

        self.assertEqual(battle.public_state().human_turns, ())


if __name__ == "__main__":
    unittest.main()
