import importlib
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


class StreamlitSmokeTests(unittest.TestCase):
    def test_app_module_exposes_main_and_acceptance_modes(self):
        try:
            module = importlib.import_module("bayesian_hardle.streamlit_app")
        except ModuleNotFoundError as exc:
            if exc.name == "streamlit":
                self.skipTest("Streamlit smoke test runs in the uv-managed environment")
            raise

        self.assertTrue(callable(module.main))
        source = Path(module.__file__).read_text(encoding="utf-8")
        self.assertIn("Strategy comparison", source)
        self.assertIn("Human vs Solver", source)

    def test_app_initial_page_renders_both_acceptance_tabs(self):
        try:
            from streamlit.testing.v1 import AppTest
        except ModuleNotFoundError:
            self.skipTest("Streamlit AppTest runs in the uv-managed environment")

        app = AppTest.from_file(str(PROJECT_ROOT / "src" / "bayesian_hardle" / "streamlit_app.py"))
        app.run(timeout=30)

        self.assertEqual([tab.label for tab in app.tabs], ["Strategy comparison", "Human vs Solver"])
        self.assertEqual(
            [button.label for button in app.button],
            ["Run comparison", "Start New Battle"],
        )

    def test_readme_contains_uv_launch_command(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "uv run --with . streamlit run src/bayesian_hardle/streamlit_app.py",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
