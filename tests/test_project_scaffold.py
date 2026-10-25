from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTROL_ROOT = PROJECT_ROOT / "project-control"


class ProjectScaffoldTests(unittest.TestCase):
    def test_required_project_layout_exists(self):
        required_paths = (
            "AGENTS.md",
            "README.md",
            "pyproject.toml",
            ".gitignore",
            "src/bayesian_hardle/__init__.py",
            "tests",
            "experiments",
            "scripts",
            "docs",
            "project-control/README.md",
            "project-control/JOURNAL.md",
            "project-control/PROJECT_STATE.md",
            "project-control/DECISIONS.md",
        )

        for relative_path in required_paths:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((PROJECT_ROOT / relative_path).exists())

    def test_control_plane_declares_formal_record_types(self):
        control_readme = (CONTROL_ROOT / "README.md").read_text()

        for record_type in (
            "[SUPERVISOR TASK]",
            "[EXECUTION REPORT]",
            "[SUPERVISOR REVIEW]",
            "[OWNER DECISION]",
        ):
            with self.subTest(record_type=record_type):
                self.assertIn(record_type, control_readme)

    def test_initial_journal_contains_executor_handoff(self):
        journal = (CONTROL_ROOT / "JOURNAL.md").read_text()

        self.assertIn("[OWNER DECISION]", journal)
        self.assertIn("[EXECUTION REPORT]", journal)
        self.assertIn("IN_PROGRESS", journal)
        self.assertIn("Base SHA:", journal)
        self.assertIn("Result SHA:", journal)
        self.assertIn("Evidence:", journal)


if __name__ == "__main__":
    unittest.main()
