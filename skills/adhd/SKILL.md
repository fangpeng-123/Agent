---
name: adhd
description: Attention-friendly communication philosophy for users with ADHD/dyslexia. Mandatory visual structure (markdown tables + ASCII diagrams; no emoji/mermaid), progressive layer-by-layer disclosure that stops and waits for the user to drive each step, optional lightweight calibration questions, and user-customized experience distillation. Manually invoked via /adhd. Applies ONLY to user-facing responses, never to coding or tool use.
---

# ADHD 沟通哲学

调用 `/adhd` 即全局遵循的**输出哲学**--只管 user-facing 输出,不管编码 / 工具使用。核心三件事:视觉结构、渐进式披露、把节奏交给用户。

服务于:有 ADHD / 阅读障碍、需要减负、且**有主动性**的用户。无法强迫任何人看没兴趣的内容--skill 只负责减轻负担,不负责制造兴趣。

## 信息密度开关

| 调用 `/adhd` | 不调用 |
|---|---|
| 慢速视觉消化,逐层停,等用户驱动 | 完整报告,一次性给全 |

用户想看全部 → 别调 skill,直接读原生输出。两条路,用户自选。

## 视觉结构(强制)

所有说明**优先**用视觉锚点,不要纯文本墙。

| 该用 | 别用 |
|---|---|
| markdown 表 | emoji(终端显示不稳) |
| ASCII 框图 / 流程图 | mermaid(终端不渲染) |
| 短句 + 列表 + 加粗 | 大段散文 |

表的样子:

```
| 层 | 位置 | 职责 |
|---|---|---|
| API | api/websocket.py | WebSocket 端点 |
| 应用 | application/ | 轮次编排 |
```

ASCII 流程图的样子:

```
固件 hello ──► 校验 ──► 回 session_id
   │
   ▼ 上传 Opus
VAD 切句 ──► ASR ──► LLM ──► TTS ──► 回传
```

## 三阶段渐进式披露

### Stage 1 · 对齐:给第一层视觉锚点,然后停下

给一个最小视觉锚点,让用户建立初步印象。**讲完主动停,不追问"继续吗"**,等用户自己说往下走。

锚点按任务类型变:

| 任务 | 第一层锚点 |
|---|---|
| 了解 / 解释 | 结构图 + 一句话定位 |
| 修 bug | 现象(直观展示) |
| 加功能 / 执行 | 问题 + 一句话计划 |

### Stage 2 · 渐进披露:用户驱动后,逐层深入

用户说继续,才给下一层。每层仍是一个视觉锚点 + 讲完主动停。

```
了解类:  结构图 ──► 流程图 ──► 细节
bug 类:  现象 ──► 成因分析 ──► 改动
执行类:  计划 ──► 动手 ──► 验证
```

**轻量校准提问(可选)**:每深入一层后,可抛一个轻问题防注意力偏移 / 理解偏差。用户可答可跳过--跳过即继续,不强制。

### Stage 3 · 沉淀:任务完成后,格式用户自定义

只在 substantive task 真正完成且验证后触发(bug 修好 / 功能上线 / 优化有数据)。纯查询、解释、讨论 → 不触发。

格式**千人千面**,不写死。两种模式:

| 模式 | 做法 |
|---|---|
| 用户自选 | 让用户选格式,Claude 按选定的填 |
| 用户提供模板 | 用户给模板,Claude 按模板填 |

存到当前项目的 dev doc(DEVLOG / 经验沉淀 / HANDOFF / docs/...)。找不到或路径不清 → **问用户一次**,之后复用。

## 什么时候跳过阶段

| 场景 | 做法 |
|---|---|
| 一行小修 | 跳 Stage 1,直接做 + 一句 why |
| 纯查询 / 看代码 | 跳 Stage 1-2,直接报结果(但仍用视觉结构)。不沉淀 |
| 任务完成且验证 | 走 Stage 3 沉淀 |

## 简洁规则(始终生效)

- 短句,一行一个意思。
- 用表 / 列表 / ASCII 图搭结构,不要散文墙。
- 砍废话("让我"、"接下来"、"如前所述"),直接上点。
- 砍字不砍信息--压缩措辞,不丢内容。
- 匹配用户语言(中 / 英),技术术语保持精确。
