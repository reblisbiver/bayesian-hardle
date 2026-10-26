import os
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_hardle.cli import run_simulation  # noqa: E402
from bayesian_hardle.fairness import GeneralEnglishFrequencyPrior  # noqa: E402


class CliAcceptanceTests(unittest.TestCase):
    def _run(self, *arguments, input_text=None):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        environment["PYTHONPYCACHEPREFIX"] = "/tmp/bayesian-hardle-issue006-pycache"
        return subprocess.run(
            [sys.executable, "-m", "bayesian_hardle.cli", *arguments],
            cwd=PROJECT_ROOT,
            env=environment,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_help_lists_simulate_live_and_compare(self):
        result = self._run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("simulate", result.stdout)
        self.assertIn("live", result.stdout)
        self.assertIn("compare", result.stdout)

    def test_full_uniform_simulation_solves_legal_word_outside_curated_list(self):
        result = self._run(
            "simulate",
            "--target",
            "aahed",
            "--mode",
            "full-uniform",
            "--policy",
            "map",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mode=full-uniform (PRIMARY STRICT FAIRNESS)", result.stdout)
        self.assertIn("support=", result.stdout)
        self.assertIn("status=SOLVED", result.stdout)
        self.assertIn("RESULT solved=True", result.stdout)

    def test_live_rejects_malformed_feedback_without_corrupting_state(self):
        result = self._run(
            "live",
            "--mode",
            "full-uniform",
            "--policy",
            "map",
            input_text="not feedback\n5 0\n",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("REJECTED feedback", result.stdout)
        self.assertIn("status=SOLVED", result.stdout)

    def test_full_frequency_simulation_solves_same_outside_target(self):
        result = run_simulation(
            "aahed",
            "full-frequency",
            "map",
            max_guesses=20,
            frequency_prior=GeneralEnglishFrequencyPrior(
                frequency_function=lambda word, language: 1.0,
                source_version="3.1.1-test-double",
            ),
        )
        self.assertTrue(result.solved)
        self.assertIn("aahed", result.turns[-1].guess)
        self.assertEqual(len(result.mode.support), 12974)


if __name__ == "__main__":
    unittest.main()
