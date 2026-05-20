# Story Prompt Optimizer 

## 1. 背景

`story-prompt-optimizer` 是一个用于提示词生成与优化的 Skill。

它的目标不是让用户手动描述完整提示词结构，而是让用户只提出任务需求，由 Skill 自动完成需求拆解、提示词生成、模型测试、结果评审、问题返工和最终交付。

第一阶段聚焦儿童 SEL 故事提示词，但设计上允许后续扩展到其他提示词优化任务。

## 2. 目标

用户使用该 Skill 时，只需要提供自然语言需求，例如：

```text
帮我生成一个用于儿童情绪故事的提示词，要求支持角色卡、上下文输入和互动节点。
```

Skill 需要完成：

1. 拆解任务目标、输出格式、质量要求和约束条件。
2. 由 Codex 内置模型生成或修改目标提示词。
3. 调用测试脚本，让指定测试模型使用该提示词生成样例输出。
4. 由 Codex 内置模型按内置评审规则检查样例输出是否满足要求。
5. 如果不满足要求，根据失败项返工提示词。
6. 最多返工 5 轮。
7. 输出最终提示词、测试结果、评审结论和迭代记录。

## 3. 非目标

第一版不做以下内容：

- 不做长期运行的 Agent。
- 不做任务队列、后台服务或自动调度。
- 不做多用户管理。
- 不做提示词版本管理系统。
- 不做 Web UI。
- 不自动提交到业务系统。
- 不支持所有类型提示词的深度优化，优先服务故事提示词。

## 4. 最小可用系统

第一版采用带工具的 Skill 形态：

```text
story-prompt-optimizer/
├── SKILL.md
├── README.md
├── config.json
├── references/
│   └── story-rubric.md
└── scripts/
    └── eval_prompt.py
```

各部分职责：

- `SKILL.md`：定义工作流、返工规则、交付格式和使用方式。
- `config.json`：配置流程角色、阿里云测试模型、API、最大返工轮次和通过分数。
- `references/story-rubric.md`：定义故事提示词评审规则。
- `scripts/eval_prompt.py`：调用阿里云测试模型，生成待评审样例输出。
- `README.md`：记录当前产品需求和实现边界。

## 5. 核心流程

```text
用户提出需求
↓
Skill 拆解任务
↓
Codex 生成初版提示词
↓
调用测试脚本
↓
阿里云测试模型根据提示词生成样例输出
↓
Codex 根据规则检查样例输出
↓
如果通过：提交最终结果
↓
如果不通过：Codex 根据失败项修复提示词
↓
最多重复 5 轮
↓
提交最终提示词和迭代记录
```

## 6. 模型配置

第一版需要提供独立配置文件，支持声明三个流程模型角色，并支持切换阿里云测试模型。

提示词生成、提示词返工和结果审核由 Codex 内置模型完成。

但 `prompt_generator` 和 `result_judge` 仍然需要保留在配置与迭代记录中，用于明确流程角色和结果归因。

测试脚本调用的 `prompt_tester` 才使用阿里云接口。

生成规则、审核规则和返工规则必须手写在 Skill 文档中，主要位置是：

- `SKILL.md`
- `references/story-rubric.md`
- 具体任务需要时补充的任务级规则

推荐配置文件：

```text
config.json
```

建议结构：

```json
{
  "provider": {
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key_env": ["DASHSCOPE_API_KEY", "API_KEY"]
  },
  "models": {
    "prompt_generator": "codex_builtin_model",
    "result_judge": "codex_builtin_model",
    "prompt_tester": "qwen3-235b-a22b"
  },
  "loop": {
    "max_rounds": 5,
    "pass_score": 85
  }
}
```

模型角色：

- `prompt_generator`：提示词生成或修改角色，第一版执行方为 Codex 内置模型。
- `prompt_tester`：测试脚本实际调用的阿里云模型，用待测提示词生成样例输出。
- `result_judge`：结果审核角色，第一版执行方为 Codex 内置模型，审核规则来自 Skill 文档与 rubric。

API Key 读取顺序：

1. `DASHSCOPE_API_KEY`
2. `API_KEY`

## 7. 测试脚本要求

测试脚本第一版建议命名为：

```text
scripts/eval_prompt.py
```

脚本职责：

1. 读取配置文件。
2. 读取待测提示词。
3. 读取或接收测试任务。
4. 调用 `prompt_tester` 模型生成样例输出。
5. 输出 JSON 格式测试报告。

脚本不负责自动修改提示词。

脚本不负责评审提示词质量。

提示词审核和修复由 `result_judge` 角色根据测试报告与评审规则执行；第一版中该角色由 Codex 内置模型承担。

## 8. 评审规则

评审规则应封装在 Skill 内部，优先放入：

```text
references/story-rubric.md
```

第一版至少检查：

- 是否符合用户需求。
- 是否有清晰角色设定。
- 是否明确上下文来源。
- 是否避免把上下文写死进角色卡。
- 是否明确输出格式。
- 是否包含交互节点。
- 是否适合 3-6 岁儿童。
- 是否避免教育腔。
- 是否避免动作括号、emoji、复杂长句等禁止项。
- 是否能处理用户中途修改故事方向。
- 是否能保持角色、旁白、故事结构边界清晰。

`result_judge` 审核时必须输出结构化结果。

审核规则不是模型自由发挥，必须来自 Skill 内手写规则，包括 `SKILL.md` 的流程要求和 `references/story-rubric.md` 的质量标准。

建议 JSON 格式：

```json
{
  "passed": false,
  "score": 78,
  "failed_items": [
    "缺少用户中途修改故事方向的处理规则",
    "角色卡中混入上下文内容"
  ],
  "fix_advice": [
    "新增运行时上下文输入规则",
    "将角色身份设定与上下文来源拆开"
  ]
}
```

## 9. 迭代记录

每轮返工必须记录：

- 轮次。
- 提示词生成或修改角色：`prompt_generator`。
- 提示词测试模型：阿里云 `prompt_tester`。
- 结果审核角色：`result_judge`。
- 本轮提示词文件路径。
- 本轮测试输出摘要。
- 分数。
- 是否通过。
- 失败项。
- 修复动作摘要。

建议结构：

```json
{
  "round": 1,
  "prompt_generator": "codex_builtin_model",
  "prompt_tester_model": "qwen3-235b-a22b",
  "result_judge": "codex_builtin_model",
  "prompt_path": "outputs/round-1/prompt.md",
  "passed": false,
  "score": 72,
  "failed_items": [
    "输出格式不稳定"
  ],
  "revision_summary": "补充固定输出格式和禁止项检查"
}
```

## 10. 输出产物

最终交付至少包含：

```text
outputs/
├── final_prompt.md
├── final_eval_report.json
└── iteration_log.json
```

可选输出：

```text
outputs/
└── samples/
    ├── round-1-output.md
    └── round-2-output.md
```

最终回答用户时，需要简要说明：

- 最终提示词路径。
- 是否通过评审。
- 最终分数。
- 总迭代轮次。
- 主要修复了哪些问题。

## 11. 返工规则

默认最大返工轮次为 5。

停止条件：

1. 评审通过且分数达到 `pass_score`。
2. 已达到最大返工轮次。
3. 测试脚本因缺少 API Key、网络或阿里云测试模型服务异常无法继续。
4. 用户明确要求停止。

达到最大轮次但仍未通过时，仍需交付当前最佳版本，并明确列出残余问题。

## 12. 错误处理

脚本需要明确处理：

- 缺少配置文件。
- 配置字段缺失。
- API Key 未设置。
- 阿里云测试模型调用失败。
- 测试脚本未返回合法 JSON。
- 输入提示词文件不存在。
- 输出目录不可写。

错误信息需要清楚说明问题和修复方式。

## 13. 验收标准

第一版完成后，应满足：

1. 用户只提供需求，Skill 能说明并执行完整优化流程。
2. 支持通过 `config.json` 声明 `prompt_generator`、`prompt_tester`、`result_judge` 三个流程角色。
3. 支持通过 `config.json` 切换阿里云 `prompt_tester` 测试模型。
4. 每轮迭代记录提示词由哪个 `prompt_generator` 生成或修改、测试使用哪个 `prompt_tester`、审核使用哪个 `result_judge`。
5. 最大返工轮次默认为 5。
6. 测试脚本能输出结构化测试报告。
7. 达标时输出最终提示词。
8. 不达标时能根据失败项返工。
9. 达到最大轮次仍能交付当前最佳结果和残余问题。

## 14. 后续扩展

后续可以考虑：

- 支持多测试用例批量评测。
- 支持不同任务类型的 rubric。
- 支持自动生成测试用例。
- 支持多个模型横向对比。
- 支持提示词版本 diff。
- 支持自动生成 Markdown 总结报告。
- 支持把优化循环固化进 `optimize_loop.py`。
