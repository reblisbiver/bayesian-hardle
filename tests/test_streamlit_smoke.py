import importlib
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


class StreamlitSmokeTests(unittest.TestCase):
    EXACT_POLICY_LABEL = "精确贝叶斯最优（Exact Bayes-optimal）"
    RUNNABLE_POLICY_LABELS = [
        "随机基线（Random）",
        "最大后验（MAP）",
        "最大信息增益（Max-IG）",
    ]

    def _app(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(PROJECT_ROOT / "src" / "bayesian_hardle" / "streamlit_app.py"))
        app.run(timeout=30)
        return app

    def test_app_module_exposes_main_and_acceptance_modes(self):
        try:
            module = importlib.import_module("bayesian_hardle.streamlit_app")
        except ModuleNotFoundError as exc:
            if exc.name == "streamlit":
                self.skipTest("Streamlit smoke test runs in the uv-managed environment")
            raise

        self.assertTrue(callable(module.main))
        source = Path(module.__file__).read_text(encoding="utf-8")
        self.assertIn("策略比较", source)
        self.assertIn("人类对战求解器", source)

    def test_app_initial_page_renders_both_acceptance_tabs(self):
        try:
            from streamlit.testing.v1 import AppTest
        except ModuleNotFoundError:
            self.skipTest("Streamlit AppTest runs in the uv-managed environment")

        app = self._app()

        self.assertEqual([tab.label for tab in app.tabs], ["策略比较", "人类对战求解器"])
        self.assertEqual([header.value for header in app.header], ["策略比较", "人类对战求解器"])
        self.assertEqual(
            [button.label for button in app.button],
            ["运行策略比较", "开始新对战"],
        )
        self.assertEqual(app.multiselect[0].label, "要运行的策略")
        self.assertEqual(app.multiselect[0].value, ["map", "max-ig"])
        self.assertEqual(app.selectbox[2].label, "求解器策略")

    def test_random_is_selectable_in_both_runnable_policy_controls(self):
        try:
            from streamlit.testing.v1 import AppTest
        except ModuleNotFoundError:
            self.skipTest("Streamlit AppTest runs in the uv-managed environment")

        app = self._app()

        self.assertEqual(app.multiselect[0].options, self.RUNNABLE_POLICY_LABELS)
        self.assertEqual(app.selectbox[2].options, self.RUNNABLE_POLICY_LABELS)

        app.multiselect[0].set_value(["random"])
        app.selectbox[2].set_value("random")
        app.run(timeout=30)

        self.assertEqual(app.multiselect[0].value, ["random"])
        self.assertEqual(app.selectbox[2].value, "random")

    def test_exact_bayes_optimal_is_visible_but_not_runnable_in_full_support_gui(self):
        try:
            from streamlit.testing.v1 import AppTest
        except ModuleNotFoundError:
            self.skipTest("Streamlit AppTest runs in the uv-managed environment")

        app = self._app()
        self.assertNotIn(self.EXACT_POLICY_LABEL, app.multiselect[0].options)
        self.assertNotIn(self.EXACT_POLICY_LABEL, app.selectbox[2].options)

        policy_status = "\n".join(element.value for element in app.info)
        self.assertIn(self.EXACT_POLICY_LABEL, policy_status)
        self.assertIn("12,974", policy_status)
        self.assertIn("较小词表", policy_status)

    def test_comparison_result_table_uses_chinese_columns_and_statuses(self):
        try:
            from streamlit.testing.v1 import AppTest
        except ModuleNotFoundError:
            self.skipTest("Streamlit AppTest runs in the uv-managed environment")

        app = self._app()
        app.text_input[0].set_value("aahed")
        app.multiselect[0].set_value(["random"])
        app.button[0].click()
        app.run(timeout=30)

        self.assertEqual(
            list(app.dataframe[0].value.columns),
            [
                "回合",
                "猜词",
                "反馈（命中、错位）",
                "剩余候选数",
                "熵（比特）",
                "单步决策时间（毫秒）",
                "累计时间（毫秒）",
                "状态",
            ],
        )
        self.assertIn("已达猜测上限", app.dataframe[0].value["状态"].tolist())

    def test_battle_keeps_solver_trajectory_hidden_before_finish(self):
        try:
            from streamlit.testing.v1 import AppTest
        except ModuleNotFoundError:
            self.skipTest("Streamlit AppTest runs in the uv-managed environment")

        app = self._app()
        app.button[1].click()
        app.run(timeout=30)

        self.assertEqual(len(app.dataframe), 0)
        info_text = "\n".join(element.value for element in app.info)
        self.assertIn("隐藏目标已启用", info_text)
        self.assertIn("不会显示求解器猜词和反馈", info_text)
        self.assertEqual([element.label for element in app.form_submit_button], ["提交猜词"])
        self.assertIn("放弃本局", [button.label for button in app.button])

    def test_readme_contains_uv_launch_command(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "uv run --with . streamlit run src/bayesian_hardle/streamlit_app.py",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
