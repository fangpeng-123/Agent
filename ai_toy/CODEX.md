# Codex 项目阅读

## 阅读目标
本文件记录本次对 `ai_toy` 项目的整体认知，包括：
- 项目框架
- 完整交互流程
- 关键模块职责（ReQuery、FunctionCall、TTS、MessageList、主模型系统提示词）
- 字段级输入输出表（阶段化）

## 一、项目整体框架认知
项目当前主链路采用“解耦架构”：
1. ReQuery（意图理解与参数提取）
2. 工具智能体并行判断 + 按需工具执行
3. Message List 结构化构建
4. 主模型生成回答（支持流式）
5. TTS 语音合成与播放
6. 对话历史更新

入口脚本在 `decoupled_agent.py`，核心在 `src/core/agent.py`。

## 二、核心模块认知

### 1) ReQuery 模块（`src/core/requery.py`）
- 职责：把用户原始输入重写为清晰意图，并提取工具参数。
- 模型：`qwen3-30b-a3b-instruct-2507`
- Prompt 注入信息：
  - 用户画像（来自 `get_user_profile("user_001")`）
  - 默认城市（从画像文本中解析，缺省“合肥”）
  - 可用工具列表（`ALL_TOOLS`）
- 输出：严格 JSON
  - `rewritten_query`
  - `params`
- 容错：JSON 解析失败时回退到 `rewritten_query=原始输入, params={}`。

### 2) FunctionCall 模块（`Function_Call/`）
统一导出层：`Function_Call/__init__.py`
- `ALL_TOOLS`：所有工具 schema（供 ReQuery 参考）
- `ALL_FUNCTIONS`：所有可执行函数
- `ALL_AGENTS`：所有工具智能体

工具族：
- 天气：`Function_Call/Weather/weather_tools.py`
- 地图：`Function_Call/Map/map_tools.py`
- 日期时间：`Function_Call/DateTime/datetime_tools.py`
- 用户画像：`Function_Call/UserProfile/user_profile_tools.py`

工具智能体决策：
- `weather_agents.py` / `map_agents.py` / `datetime_agents.py`
- 每个智能体先返回 `use_tool/reason/result`，再决定是否真正执行函数。
- 并行调度在 `src/core/tool_agent_executor.py`（`asyncio.gather`）。

### 3) MessageList 模块（`src/core/builder.py`）
新架构核心：`build_structured_messages(...)`
消息顺序：
1. system（系统提示词）
2. user（用户画像）
3. user（逐工具决策与结果）
4. user（原始输入 + 重写意图）
5. user（最近历史）
6. user（回答请求）

旧架构兼容：`build_main_model_messages(...)`（结构较简化）。

### 4) 主模型系统提示词
配置入口：`config.yaml` -> `model.system_prompt_type`
当前值：`child_education`

解析逻辑：`src/utils/config.py::get_system_prompt()`
- `child_education` / `child_companion` -> `CHILD_EDUCATION_PROMPT`
- `base` -> `MAIN_MODEL_SYSTEM_PROMPT`

儿童教育提示词文件：
- `src/prompts/system_prompts/child_companion.py`
- 覆盖年龄分段、安全约束、回复长度限制、语言风格等。

### 5) TTS 模块
当前 Agent 接入：`QwenTTSService`（`src/services/tts_service.py`）
- `is_available()` 检查 SDK + API key
- `synthesize(text)` 合成音频

主流程中的流式 TTS 并行任务：`src/core/agent.py::TTSTask`
- 文本队列 + 音频队列双队列
- 按标点切分文本触发合成
- 播放器异步消费音频

项目还实现了更完整的 `StreamTTSService` / `StreamTTS`（推荐方向），但当前 `DecoupledAgent` 默认主链路仍主要走 `QwenTTSService + TTSTask`。

## 三、完整交互流程（端到端）
1. 用户输入到 `DecoupledAgent.process(user_input, stream=True)`。
2. Stage 1：ReQuery 产出 `rewritten_query + params`。
3. Stage 2：并行运行所有工具智能体，得到每个工具的 `use_tool/reason/result`。
4. Stage 3：构建结构化 Message List（系统提示词 + 画像 + 工具结果 + 历史 + 任务指令）。
5. Stage 4：主模型流式生成文本回复。
6. Stage 5：TTS 并行合成并播放音频。
7. Stage 6：写入 `conversation_history`（超长截断）。

## 四、字段表（阶段化 I/O）

| 阶段 | 输入字段 | 输出字段 | 关键字段说明 |
|---|---|---|---|
| 入口调用 | `user_input: str`, `stream: bool` | `AgentResponse` | 入口在 `DecoupledAgent.process` |
| ReQuery | `user_input`, `available_tools(ALL_TOOLS)`, `user_profile` | `ReQueryResult{rewritten_query, params}` | `params` 包含 location/query/address/origin/destination/days/hours/query_type 等 |
| 工具智能体并行判断 | `rewritten_query`, `requery_params` | `tool_results: List[Dict]` | 每项结构：`tool`, `use_tool`, `reason`, `result` |
| MessageList 构建 | `rewritten_query`, `tool_results`, `conversation_history` | `messages: List[Dict]` | 新架构统一给主模型多条 `role=user/system` 的上下文 |
| 主模型生成 | `messages`, `stream` | `content: str` | 流式模式下逐 chunk 拼接 `content` |
| TTS 合成 | `content`（或流式分段文本） | `tts_result` / 音频播放副作用 | `TTSTask` 统计首音延迟、音频大小 |
| 历史更新 | `user_input`, `content` | `conversation_history` | 追加 user/assistant 两条，超过阈值截断 |
| 最终返回 | `content`, metrics, history, tts | `AgentResponse` | 当前新架构默认 `intent=TOOL_CALL` |

## 五、关键数据结构表

| 结构名 | 所在模块 | 主要字段 |
|---|---|---|
| `ReQueryResult` | `src/core/requery.py` | `rewritten_query: str`, `params: Dict[str, Any]` |
| `ToolCall` | `src/utils`（执行器返回） | `tool_name`, `arguments`, `result`, `start_time`, `end_time` |
| `AgentResponse` | `src/utils` | `content`, `intent`, `tool_calls`, `metrics`, `message_history`, `tts_result` |
| `TTSConfig` | `src/services/tts_service.py` | `api_key`, `model`, `voice`, `sample_rate`, `speed` |
| `TTSResult` | `src/services/tts_service.py` | `audio_data`, `duration_ms`, `success`, `error_message`, `session_id` |

## 六、当前实现特征与注意点
1. 新架构不依赖主模型原生 function-calling，而是“ReQuery + 工具智能体决策 + 代码执行”。
2. Message List 中会注入完整用户画像 JSON，有利于个性化回复。
3. 系统提示词由配置动态切换，当前是儿童教育模式。
4. 工具智能体是全量并行评估，最终可同时启用多个工具。
5. TTS 已有两套能力：兼容版服务 + 流式服务，当前主流程偏向兼容版接入方式。

## 七、结论
项目已形成较完整的“意图理解 -> 工具执行 -> 结构化上下文 -> 主模型回答 -> 语音输出”闭环。整体架构清晰，模块边界明确，适合继续在以下方向演进：
- 工具智能体决策质量与成本优化
- MessageList 压缩与上下文长度治理
- StreamTTSService 在主流程中的统一接入
- ReQuery 结构化输出的约束与评估
