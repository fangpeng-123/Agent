---
name: story-prompt-optimizer
description: Use when the user wants to generate, rewrite, test, or optimize prompts, especially children's SEL story prompts. Take a natural-language requirement, decompose it, write or revise the prompt through the prompt_generator role, run the configured prompt_tester script, review the test output through the result_judge role using handwritten Skill rules, iterate up to the configured maximum rounds, and deliver the final prompt with evaluation evidence.
---

# 需求拆解

Read `README.md` first when product scope or implementation boundaries are unclear.

Start from the user's natural-language request. Identify:

- Target task: what the prompt must generate or control.
- Target user: who will use the generated output.
- Output format: files, text structure, JSON, Markdown, role card, story prompt, or other format.
- Required constraints: safety rules, style rules, domain rules, forbidden content, and formatting rules.
- Runtime context: what information should be provided at use time instead of being hardcoded into the prompt.
- Test goal: what output should prove that the prompt works.

For story prompts, explicitly check:

- Story audience and age range.
- Story world,角色体系,SEL能力,交互节点,旁白规则,输出格式.
- Whether角色设定 and上下文输入 are separated.
- Whether the prompt can handle mid-story user changes.

If the requirement is ambiguous enough to affect implementation, ask one focused question before writing. Otherwise make conservative assumptions and record them in the iteration notes.

# 提示词编写

Write the smallest prompt that can satisfy the requirement and pass evaluation.

Prefer this structure when appropriate:

1. Role: model identity and task role.
2. Context: runtime inputs that must be supplied by the caller.
3. Statement: concrete task instructions.
4. Rules: hard constraints and forbidden behaviors.
5. Output: exact output format.
6. Checks: self-check items before final output.

Keep stable identity, domain rules, and output constraints inside the prompt. Keep user-specific runtime values outside the prompt unless the user explicitly asks to hardcode them.

For children's SEL story prompts:

- Keep角色卡 stable.
- Keep上下文 as runtime input.
- Keep SEL goals hidden inside story behavior instead of direct teaching.
- Prefer short, concrete, child-friendly language.
- Avoid emoji, bracketed action notes in dialogue, adult analysis, and abstract preaching.

Save each candidate prompt in an output path that can be referenced by the test step.

# 执行测试

Use `config.json` for model and loop configuration when it exists.

Expected configuration fields:

- `provider.base_url`
- `provider.api_key_env`
- `models.prompt_generator`
- `models.prompt_tester`
- `models.result_judge`
- `loop.max_rounds`
- `loop.pass_score`

Role execution policy:

- `models.prompt_generator` is the role that writes or revises prompts. In the first version this should normally be `codex_builtin_model`.
- `models.prompt_tester` is the external model called by `scripts/eval_prompt.py`. In the first version this is the Aliyun/DashScope model under test.
- `models.result_judge` is the role that reviews test outputs. In the first version this should normally be `codex_builtin_model`.
- Only `models.prompt_tester` requires an external API call.
- The generation and judgment rules must be handwritten in this Skill and its references; do not rely on the model to invent the criteria.

Use `scripts/eval_prompt.py` as the evaluation entrypoint when it exists.

The test step should:

1. Run the prompt with the external `models.prompt_tester` model.
2. Produce a structured test report with the generated sample output.
3. Review the sample output through `models.result_judge` against the handwritten rules in this Skill and `references/story-rubric.md` when the task is a story prompt.
4. Produce a structured judgment result.

The script test report must include:

- Generated sample output.
- Prompt tester model.
- Test task or test case name.
- Raw model response when useful.

The judgment result must include whether the result passed, score, failed items, and fix advice.

Do not hide test failures. If the API key, network, external model service, config file, or script is missing, report the blocker and provide the next concrete fix.

# 测试结果分析

Analyze failures by separating them into these categories:

- Requirement miss: the prompt does not satisfy the user's stated goal.
- Format miss: the output structure is unstable or wrong.
- Rule violation: the output breaks hard constraints.
- Quality miss: the output is technically valid but weak, vague, boring, or off-tone.
- Context leak: runtime context is hardcoded into stable prompt or role card content.
- Model instability: the test model output is noisy even though the prompt is clear.

Prioritize hard failures first:

1. Safety or forbidden content.
2. Output format failure.
3. Missing required feature.
4. Runtime context and role boundary confusion.
5. Style or quality issues.

Use the evaluation report as evidence. Do not revise based only on vague preference when a concrete failed item exists.

# 优化建议

Turn each failed item into a small prompt revision.

Prefer targeted edits:

- Add missing constraints.
- Clarify runtime inputs.
- Strengthen output format.
- Add negative examples only when the failure is repeated or likely.
- Split overloaded instructions.
- Remove conflicting instructions.

Avoid broad rewrites unless the prompt structure itself is the cause of repeated failures.

After each revision, record:

- Round number.
- Prompt generator or modifier: `models.prompt_generator`.
- Prompt tester model: external model from `config.json`.
- Result judge: `models.result_judge`.
- Changed prompt path.
- Failed items addressed.
- Revision summary.

Default maximum revision rounds is 5 unless `config.json` sets another value.

# 提交结果或者修复

Stop when one of these conditions is met:

- The evaluation passed and score is at least `loop.pass_score`.
- The maximum revision round count is reached.
- A required dependency blocks testing.
- The user asks to stop.

When the result passes, submit:

- Final prompt path.
- Final evaluation report path.
- Iteration log path.
- Final score.
- Total rounds.
- Short summary of major fixes.

When the result does not pass after the maximum rounds, submit the best current prompt and clearly list:

- Remaining failed items.
- Current score.
- Why the loop stopped.
- What should be changed next.

Recommended output paths:

- `outputs/final_prompt.md`
- `outputs/final_eval_report.json`
- `outputs/iteration_log.json`

Do not claim completion without test evidence unless testing was blocked. If testing was blocked, say exactly what prevented it.
