import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_prompt


TEST_ROOT = Path(__file__).resolve().parents[1] / ".test-work"
TEST_ROOT.mkdir(parents=True, exist_ok=True)


class EvalPromptTests(unittest.TestCase):
    def test_load_config_requires_three_model_roles(self):
        config_path = TEST_ROOT / "config-valid.json"
        config_path.write_text(
            json.dumps(
                {
                    "provider": {
                        "base_url": "https://example.test/v1",
                        "api_key_env": ["DASHSCOPE_API_KEY", "API_KEY"],
                    },
                    "models": {
                        "prompt_generator": "codex_builtin_model",
                        "prompt_tester": "qwen3-235b-a22b",
                        "result_judge": "codex_builtin_model",
                    },
                    "loop": {"max_rounds": 5, "pass_score": 85},
                }
            ),
            encoding="utf-8",
        )

        config = eval_prompt.load_config(config_path)

        self.assertEqual(config["models"]["prompt_generator"], "codex_builtin_model")
        self.assertEqual(config["models"]["prompt_tester"], "qwen3-235b-a22b")
        self.assertEqual(config["models"]["result_judge"], "codex_builtin_model")

    def test_build_report_records_roles_and_generated_output(self):
        config = {
            "provider": {
                "base_url": "https://example.test/v1",
                "api_key_env": ["DASHSCOPE_API_KEY", "API_KEY"],
            },
            "models": {
                "prompt_generator": "codex_builtin_model",
                "prompt_tester": "qwen3-235b-a22b",
                "result_judge": "codex_builtin_model",
            },
            "loop": {"max_rounds": 5, "pass_score": 85},
        }

        report = eval_prompt.build_report(
            config=config,
            prompt_path=Path("prompt.md"),
            test_task="生成一个两角色故事",
            generated_output="旁白：\n故事开始了。",
            raw_response={"id": "test-response"},
            dry_run=False,
        )

        self.assertEqual(report["models"]["prompt_generator"], "codex_builtin_model")
        self.assertEqual(report["models"]["prompt_tester"], "qwen3-235b-a22b")
        self.assertEqual(report["models"]["result_judge"], "codex_builtin_model")
        self.assertEqual(report["generated_output"], "旁白：\n故事开始了。")
        self.assertEqual(report["test_task"], "生成一个两角色故事")

    def test_run_dry_run_writes_report_without_api_key(self):
        config_path = TEST_ROOT / "config-dry-run.json"
        prompt_path = TEST_ROOT / "prompt.md"
        output_path = TEST_ROOT / "report.json"

        config_path.write_text(
            json.dumps(
                {
                    "provider": {
                        "base_url": "https://example.test/v1",
                        "api_key_env": ["MISSING_API_KEY"],
                    },
                    "models": {
                        "prompt_generator": "codex_builtin_model",
                        "prompt_tester": "qwen3-235b-a22b",
                        "result_judge": "codex_builtin_model",
                    },
                    "loop": {"max_rounds": 5, "pass_score": 85},
                }
            ),
            encoding="utf-8",
        )
        prompt_path.write_text("你是故事生成器。", encoding="utf-8")

        report = eval_prompt.run(
            config_path=config_path,
            prompt_path=prompt_path,
            test_task="生成一个短故事",
            output_path=output_path,
            dry_run=True,
        )

        saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertTrue(report["dry_run"])
        self.assertEqual(saved["models"]["prompt_tester"], "qwen3-235b-a22b")
        self.assertIn("DRY RUN", saved["generated_output"])


if __name__ == "__main__":
    unittest.main()
