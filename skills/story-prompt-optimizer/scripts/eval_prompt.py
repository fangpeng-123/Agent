"""Run a prompt through the configured external test model.

This script only tests prompt behavior by generating a sample output. It does
not judge quality or revise prompts; the story-prompt-optimizer Skill performs
that review with its handwritten rubric.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REQUIRED_CONFIG_FIELDS = (
    ("provider", "base_url"),
    ("provider", "api_key_env"),
    ("models", "prompt_generator"),
    ("models", "prompt_tester"),
    ("models", "result_judge"),
    ("loop", "max_rounds"),
    ("loop", "pass_score"),
)


class EvalPromptError(RuntimeError):
    """Raised when prompt evaluation cannot continue."""


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise EvalPromptError(f"File not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvalPromptError(f"Invalid JSON in {path}: {exc}") from exc


def load_config(path: Path) -> dict[str, Any]:
    config = load_json(path)
    missing: list[str] = []

    for section, key in REQUIRED_CONFIG_FIELDS:
        value = config.get(section, {}).get(key)
        if value in (None, "", []):
            missing.append(f"{section}.{key}")

    if missing:
        raise EvalPromptError("Missing required config fields: " + ", ".join(missing))

    api_key_env = config["provider"]["api_key_env"]
    if isinstance(api_key_env, str):
        config["provider"]["api_key_env"] = [api_key_env]
    elif not isinstance(api_key_env, list):
        raise EvalPromptError("provider.api_key_env must be a string or list of strings")

    return config


def read_text_file(path: Path, label: str) -> str:
    if not path.exists():
        raise EvalPromptError(f"{label} file not found: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise EvalPromptError(f"{label} file is empty: {path}")
    return text


def resolve_api_key(config: dict[str, Any]) -> tuple[str, str]:
    for env_name in config["provider"]["api_key_env"]:
        value = os.getenv(env_name)
        if value:
            return value, env_name
    names = ", ".join(config["provider"]["api_key_env"])
    raise EvalPromptError(f"API key not found. Set one of: {names}")


def build_messages(prompt: str, test_task: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": test_task},
    ]


def call_prompt_tester(
    *,
    config: dict[str, Any],
    prompt: str,
    test_task: str,
    timeout: int,
    temperature: float,
) -> tuple[str, dict[str, Any], str]:
    api_key, api_key_env = resolve_api_key(config)
    base_url = str(config["provider"]["base_url"]).rstrip("/")
    url = f"{base_url}/chat/completions"
    model = config["models"]["prompt_tester"]
    payload = {
        "model": model,
        "messages": build_messages(prompt, test_task),
        "temperature": temperature,
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise EvalPromptError(f"Prompt tester HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise EvalPromptError(f"Prompt tester request failed: {exc.reason}") from exc

    try:
        raw_response = json.loads(raw_body)
        generated_output = raw_response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise EvalPromptError("Prompt tester returned an unexpected response shape") from exc

    return generated_output, raw_response, api_key_env


def build_report(
    *,
    config: dict[str, Any],
    prompt_path: Path,
    test_task: str,
    generated_output: str,
    raw_response: dict[str, Any],
    dry_run: bool,
    api_key_env: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "created_at_unix": int(time.time()),
        "dry_run": dry_run,
        "prompt_path": str(prompt_path),
        "test_task": test_task,
        "models": {
            "prompt_generator": config["models"]["prompt_generator"],
            "prompt_tester": config["models"]["prompt_tester"],
            "result_judge": config["models"]["result_judge"],
        },
        "provider": {
            "base_url": config["provider"]["base_url"],
            "api_key_env": api_key_env,
        },
        "loop": {
            "max_rounds": config["loop"]["max_rounds"],
            "pass_score": config["loop"]["pass_score"],
        },
        "generated_output": generated_output,
        "raw_response": raw_response,
    }


def write_report(report: dict[str, Any], output_path: Path | None) -> None:
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if output_path is None:
        print(text)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text + "\n", encoding="utf-8")


def run(
    *,
    config_path: Path,
    prompt_path: Path,
    test_task: str,
    output_path: Path | None,
    dry_run: bool,
    timeout: int = 60,
    temperature: float = 0.7,
) -> dict[str, Any]:
    config = load_config(config_path)
    prompt = read_text_file(prompt_path, "Prompt")

    if not test_task.strip():
        raise EvalPromptError("Test task is empty")

    if dry_run:
        generated_output = (
            "DRY RUN: no external model was called.\n\n"
            f"Prompt length: {len(prompt)} characters.\n"
            f"Test task: {test_task}"
        )
        raw_response = {
            "dry_run": True,
            "message": "External prompt_tester call skipped.",
        }
        api_key_env = None
    else:
        generated_output, raw_response, api_key_env = call_prompt_tester(
            config=config,
            prompt=prompt,
            test_task=test_task,
            timeout=timeout,
            temperature=temperature,
        )

    report = build_report(
        config=config,
        prompt_path=prompt_path,
        test_task=test_task,
        generated_output=generated_output,
        raw_response=raw_response,
        dry_run=dry_run,
        api_key_env=api_key_env,
    )
    write_report(report, output_path)
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a sample output with the configured prompt_tester model."
    )
    parser.add_argument("--prompt", required=True, type=Path, help="Prompt file to test.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "config.json",
        help="Path to config.json.",
    )
    parser.add_argument("--task", help="Test task text.")
    parser.add_argument("--task-file", type=Path, help="File containing the test task.")
    parser.add_argument("--output", type=Path, help="Where to write the JSON report.")
    parser.add_argument("--dry-run", action="store_true", help="Skip external API call.")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--temperature", type=float, default=0.7, help="Sampling temperature."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.task_file:
            test_task = read_text_file(args.task_file, "Task")
        elif args.task:
            test_task = args.task
        else:
            raise EvalPromptError("Provide --task or --task-file")

        run(
            config_path=args.config,
            prompt_path=args.prompt,
            test_task=test_task,
            output_path=args.output,
            dry_run=args.dry_run,
            timeout=args.timeout,
            temperature=args.temperature,
        )
    except EvalPromptError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
