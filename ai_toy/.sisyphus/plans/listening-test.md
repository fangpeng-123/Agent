# 听力训练逻辑题目测试 - 工作计划

## TL;DR

> **快速摘要**: 创建社会科学题目测试智能体，支持终端文字输入+LLM评估模式

> **交付物**:
> - `tests/Social_Science_qa/data/social_science_questions.json` - 社科题目数据
> - `tests/Social_Science_qa/data/social_science_questions.md` - 社科题目MD源文件
> - `tests/Social_Science_qa/qa_agent.py` - 测试智能体（含终端交互+LLM评估）
> - `tests/Social_Science_qa/test_qa_agent.py` - 测试用例

> **预估工作量**: 短 (Short)
> **并行执行**: 是 - 任务可并行
> **关键路径**: 生成题目 → 创建智能体 → 终端交互 → 测试验证

---

## 需求更新

### 回答模式变更
**原模式**: 听力模式（TTS播题 → ASR识别 → LLM评估）
**新模式**: 终端文字输入模式（显示题目 → 终端输入文字 → LLM评估）

### 交互流程
1. 终端显示题目
2. 用户在终端输入文字回答
3. 大模型评估回答对错
4. 输出评价和反馈

---

## 工作目标

### 核心目标
创建完整的测试智能体，实现社会科学题目的听力训练测试能力。

### 具体交付物
1. 社科题目MD源文件 → JSON数据
2. 测试智能体（含系统提示词 + 模型调用）
3. 测试用例

### 完成定义
- [ ] 目录 `tests/Social_Science_qa/` 创建成功
- [ ] 题目数据包含≥5道社会科学题目
- [ ] 智能体使用 qwen3-235b-a22b 模型
- [ ] 系统提示词和模型配置放在一起
- [ ] 测试可以通过命令行执行

### 必须实现
- 社科题目MD生成 → JSON转换
- 测试智能体（含系统提示词 + 模型调用）
- 测试用例

### 禁止实现（边界）
- 不解耦实现（系统提示词和模型放一起）
- 不修改现有服务代码

---

## 验证策略

### 测试决策
- **基础设施**: 存在 (Python unittest/pytest)
- **自动化测试**: 测试后验证（Tests-after）
- **框架**: pytest

### QA策略
所有测试必须包含agent执行的QA场景：
- **TTS测试**: 验证音频生成成功、文件存在
- **ASR测试**: 验证转写结果正确（mock或实际调用）
- **LLM评估**: 验证评估结果格式正确

---

## 执行策略

### 目录结构
```
tests/Social_Science_qa/
├── __init__.py
├── qa_agent.py              # 测试智能体（含系统提示词+模型）
├── test_qa_agent.py         # 测试用例
└── data/
    ├── social_science_questions.md   # MD源文件
    └── social_science_questions.json # JSON数据
```

### 任务分组

**Wave 1 - 基础结构与数据**:
├── 任务1: 创建目录结构 `tests/Social_Science_qa/`
├── 任务2: 生成社科题目MD文档
└── 任务3: 转换MD为JSON数据

**Wave 2 - 智能体开发**:
├── 任务4: 创建测试智能体（系统提示词+模型）
└── 任务5: 实现题目问答逻辑

**Wave 3 - 测试验证**:
├── 任务6: 编写测试用例
├── 任务7: 执行测试验证
└── 任务8: 添加终端交互模式

### 依赖关系
- 任务1 → 任务2 → 任务3 → 任务4,5,6 → 任务7 → 任务8

---

## 任务详情

### 任务1: 创建目录结构

**工作内容**:
- 创建 `tests/Social_Science_qa/` 目录
- 创建 `tests/Social_Science_qa/data/` 子目录
- 创建 `__init__.py` 文件

**目录结构**:
```
tests/Social_Science_qa/
├── __init__.py
└── data/
    ├── social_science_questions.md
    └── social_science_questions.json
```

**推荐代理**: quick

**QA场景**:
```
场景: 目录创建成功
  工具: Bash
  步骤:
    1. ls -la tests/Social_Science_qa/
    2. ls -la tests/Social_Science_qa/data/
  预期结果: 目录和文件存在
  证据: ls输出
```

---

### 任务2: 生成社科题目MD文档

**工作内容**:
- 在 `tests/Social_Science_qa/data/` 创建 `social_science_questions.md`
- 包含至少5道社会科学领域的逻辑题目

**MD格式**:
```markdown
# 社会科学题目集

## 题目1: 人际关系
- 问题: 怎么样交到好朋友？
- 正确答案: 要真诚、善良、愿意分享
- 解析: 交好朋友需要真心相待

## 题目2: 社会规则
...
```

**推荐代理**: quick

**QA场景**:
```
场景: MD文档创建成功
  工具: Bash
  步骤:
    1. 检查 tests/Social_Science_qa/data/social_science_questions.md 存在
    2. 验证包含至少5道题目
  预期结果: 文件存在，题目数量≥5
  证据: 文件内容
```

---

### 任务3: 转换MD为JSON数据

**工作内容**:
- 将MD文档转换为JSON格式
- 保存到 `social_science_questions.json`

**JSON格式**:
```json
{
  "version": "1.0",
  "category": "social_science",
  "questions": [
    {
      "id": "ss_001",
      "question": "怎么样交到好朋友？",
      "correct_answer": "要真诚、善良、愿意分享",
      "explanation": "交好朋友需要真心相待，互相帮助"
    }
  ]
}
```

**推荐代理**: quick

**QA场景**:
```
场景: JSON文件创建成功
  工具: Bash
  步骤:
    1. 检查 tests/Social_Science_qa/data/social_science_questions.json 存在
    2. 验证是有效JSON
    3. 验证包含至少5道题目
  预期结果: 文件存在，JSON有效，题目≥5
  证据: 文件内容
```

---

### 任务4: 创建测试智能体（系统提示词+模型）

**工作内容**:
- 创建 `qa_agent.py`
- 包含系统提示词和模型配置（不放在一起）
- 使用 `qwen3-235b-a22b` 模型

**文件结构**:
```python
# -*- coding: utf-8 -*-
"""社会科学问答智能体"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# 模型配置
MODEL_NAME = "qwen3-235b-a22b"

# 系统提示词
SYSTEM_PROMPT = """你是儿童教育陪伴助手，负责社会科学题目的听力训练。

你将：
1. 播报题目（如果需要TTS）
2. 评估用户的回答
3. 给出适当的评价和反馈

评分标准：
- 正确且完整：优秀
- 基本正确：良好
- 部分正确：及格
- 完全错误：需要再学习"""


@dataclass
class Question:
    id: str
    question: str
    correct_answer: str
    explanation: str = ""


class SocialScienceQAAgent:
    """社会科学问答智能体"""
    
    def __init__(self):
        self.questions: List[Question] = []
        self._load_questions()
    
    def _load_questions(self):
        """加载题目数据"""
        pass
    
    def evaluate_answer(self, question_id: str, user_answer: str) -> Dict:
        """评估用户回答"""
        pass


# 便捷函数
def create_agent() -> SocialScienceQAAgent:
    """创建智能体实例"""
    return SocialScienceQAAgent()
```

**推荐代理**: quick

**QA场景**:
```
场景: 智能体文件创建成功
  工具: Bash
  步骤:
    1. 检查 tests/Social_Science_qa/qa_agent.py 存在
    2. 验证语法正确 python -m py_compile
  预期结果: 文件存在，语法正确
  证据: py_compile输出
```

---

### 任务5: 实现题目问答逻辑

**工作内容**:
- 实现题目加载逻辑
- 实现LLM评估功能
- 实现回答反馈

**实现要点**:
1. 从JSON加载题目
2. 调用LLM评估用户回答
3. 返回评估结果和反馈

**LLM评估提示词**:
```
请评估用户对社会科举题目的回答。

题目：{question}
正确答案：{correct_answer}
用户回答：{user_answer}

请判断对错，并给出评价。
```

**推荐代理**: quick

**QA场景**:
```
场景: 智能体功能完整
  工具: Bash
  步骤:
    1. 导入智能体
    2. 创建实例
    3. 加载题目
  预期结果: 功能正常
  证据: Python导入测试
```

---

### 任务6: 编写测试用例

**工作内容**:
- 创建 `test_qa_agent.py`
- 包含完整的测试用例

**测试用例**:
```python
# -*- coding: utf-8 -*-
"""社会科学问答智能体测试"""

import unittest
import json
from pathlib import Path

from qa_agent import SocialScienceQAAgent, Question


class TestSocialScienceQAAgent(unittest.TestCase):
    """测试社会科学问答智能体"""
    
    @classmethod
    def setUpClass(cls):
        cls.agent = SocialScienceQAAgent()
    
    def test_load_questions(self):
        """测试题目加载"""
        self.assertGreater(len(self.agent.questions), 0)
    
    def test_evaluate_correct_answer(self):
        """测试正确答案评估"""
        result = self.agent.evaluate_answer("ss_001", "要真诚、善良、愿意分享")
        self.assertIn("evaluation", result)
    
    def test_evaluate_wrong_answer(self):
        """测试错误答案评估"""
        result = self.agent.evaluate_answer("ss_001", "打架")
        self.assertIn("evaluation", result)


if __name__ == "__main__":
    unittest.main()
```

**推荐代理**: quick

**QA场景**:
```
场景: 测试文件创建成功
  工具: Bash
  步骤:
    1. 检查 tests/Social_Science_qa/test_qa_agent.py 存在
    2. 验证语法正确
  预期结果: 文件存在，语法正确
  证据: py_compile输出
```

---

### 任务7: 执行测试验证

**工作内容**:
- 运行所有测试
- 验证功能正常

**测试命令**:
```bash
cd tests/Social_Science_qa
python -m pytest test_qa_agent.py -v
```

**推荐代理**: quick

**QA场景**:
```
场景: 测试执行成功
  工具: Bash
  步骤:
    1. cd tests/Social_Science_qa
    2. python -m pytest test_qa_agent.py -v
  预期结果: 所有测试通过
  证据: pytest输出
```

---

### 任务8: 添加终端交互模式

**工作内容**:
- 修改 `qa_agent.py`
- 添加终端交互主循环
- 支持用户在终端输入文字回答
- 大模型实时评估并反馈

**交互流程**:
```
1. 显示题目（随机或指定）
2. 用户在终端输入回答
3. 大模型评估回答
4. 显示评估结果和反馈
5. 继续下一题或退出
```

**实现代码**:
```python
async def interactive_mode(agent: SocialScienceQAAgent):
    """交互式问答模式"""
    print("\n" + "=" * 60)
    print("欢迎使用社会科学问答训练系统")
    print("=" * 60)
    
    while True:
        # 获取随机题目
        question = agent.get_random_question()
        
        # 显示题目
        print(f"\n【主题】{question.topic}")
        print(f"【题目】{question.question}")
        
        # 获取用户输入
        user_answer = input("\n请输入你的回答（输入'q'退出）: ").strip()
        
        if user_answer.lower() in ['q', 'quit', '退出']:
            print("\n再见！")
            break
        
        if not user_answer:
            print("请输入回答后再提交！")
            continue
        
        # 评估回答
        print("\n正在评估...")
        result = await agent.evaluate_answer(question.id, user_answer)
        
        # 显示结果
        print("\n" + "-" * 40)
        print(f"【评估】{result.score}")
        print(f"【反馈】{result.feedback}")
        print("-" * 40)
```

**更新主程序入口**:
```python
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="社会科学问答训练")
    parser.add_argument("--mode", choices=["test", "interactive"], default="interactive",
                        help="运行模式: test=测试, interactive=交互问答")
    args = parser.parse_args()
    
    if args.mode == "interactive":
        # 启动交互模式
        agent = create_agent()
        asyncio.run(interactive_mode(agent))
    else:
        # 原有的测试代码
        ...
```

**使用方式**:
```bash
# 启动交互模式（默认）
python tests/Social_Science_qa/qa_agent.py

# 启动测试模式
python tests/Social_Science_qa/qa_agent.py --mode test
```

**推荐代理**: quick

**QA场景**:
```
场景: 终端交互功能正常
  工具: Bash
  步骤:
    1. python tests/Social_Science_qa/qa_agent.py
    2. 输入回答测试
    3. 验证评估结果输出
  预期结果: 交互正常，评估结果正确显示
  证据: 终端输出
```

---

## 最终验证

### 验证命令
```bash
# 检查目录结构
ls -la tests/Social_Science_qa/
ls -la tests/Social_Science_qa/data/

# 运行测试
cd tests/Social_Science_qa
python -m pytest test_qa_agent.py -v
```

### 完成标准
- [ ] 目录 `tests/Social_Science_qa/` 创建成功
- [ ] MD源文件和JSON数据文件都存在
- [ ] 智能体使用 `qwen3-235b-a22b` 模型
- [ ] 系统提示词和模型配置放在一起
- [ ] 测试可以正常执行

---

## 备注

### 假设
- `qwen3-235b-a22b` 模型可用
- API密钥已配置

### 目录结构（最终）
```
tests/Social_Science_qa/
├── __init__.py
├── qa_agent.py              # 测试智能体（含系统提示词+模型）
├── test_qa_agent.py         # 测试用例
└── data/
    ├── social_science_questions.md   # MD源文件
    └── social_science_questions.json # JSON数据
```
