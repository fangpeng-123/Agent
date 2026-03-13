# -*- coding: utf-8 -*-
"""
社会科学问答智能体
包含系统提示词和模型调用（不放在一起）
使用 qwen3-235b-a22b 模型
"""

import json
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 导入LangChain
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from langchain_core.messages import SystemMessage, HumanMessage

# ==================== 配置 ====================

# 模型配置
MODEL_NAME = "qwen3-235b-a22b"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
TEMPERATURE = 0.9

# ==================== 系统提示词 ====================

SYSTEM_PROMPT = """你是儿童教育陪伴助手，负责社会科学题目的训练测试。

你的主要任务是：
1. 显示社会科学题目给用户看
2. 接收用户的文字回答
3. 评估用户的回答是否正确
4. 根据用户的回答给予适当的补充说明

评估标准：
- 回答基本正确：给予鼓励，继续引导用户完善回答
- 回答部分正确：提示需要补充的内容
- 回答错误：温和地给出正确答案，并解释原因

注意：
回答用户问题时使用第一人称语气例如：
- 你说的很好，我认为还可以...
- 你真棒，下次遇到就这样做吧...
- 你需要再学习一下，继续努力！需要做的有这些哦...
- 你说的道理，但也要注意...

请用温暖、鼓励的语气与孩子交流，让学习变得有趣。"""


# ==================== 数据模型 ====================


@dataclass
class Question:
    """题目数据结构"""

    id: str
    topic: str
    question: str
    correct_answer: str
    explanation: str


@dataclass
class EvaluationResult:
    """评估结果"""

    is_correct: bool
    score: str  # 优秀、良好、及格、需要再学习
    feedback: str
    correct_answer: str


# ==================== 智能体类 ====================


class SocialScienceQAAgent:
    """社会科学问答智能体"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化智能体

        Args:
            api_key: API密钥，如果为None则从环境变量读取
        """
        # 加载环境变量
        load_dotenv()

        # API配置
        self.api_key = api_key or os.getenv("API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "未设置API密钥，请设置 API_KEY 或 DASHSCOPE_API_KEY 环境变量"
            )

        # 加载题目
        self.questions: List[Question] = []
        self._load_questions()

        # 创建LLM实例
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            base_url=BASE_URL,
            api_key=SecretStr(self.api_key),
            temperature=TEMPERATURE,
            streaming=True,
            extra_body={"enable_thinking": False},
        )

    def _load_questions(self):
        """从JSON文件加载题目数据"""
        # 获取数据文件路径
        data_dir = Path(__file__).parent / "data"
        questions_file = data_dir / "social_science_questions.json"

        if not questions_file.exists():
            raise FileNotFoundError(f"题目数据文件不存在: {questions_file}")

        # 读取JSON
        with open(questions_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 转换为Question对象
        for q in data.get("questions", []):
            self.questions.append(
                Question(
                    id=q["id"],
                    topic=q["topic"],
                    question=q["question"],
                    correct_answer=q["correct_answer"],
                    explanation=q["explanation"],
                )
            )

        print(f"[INFO] 已加载 {len(self.questions)} 道题目")

    def get_question(self, question_id: str) -> Optional[Question]:
        """根据ID获取题目"""
        for q in self.questions:
            if q.id == question_id:
                return q
        return None

    def get_random_question(self) -> Question:
        """随机获取一道题目"""
        import random

        return random.choice(self.questions)

    def get_all_topics(self) -> List[str]:
        """获取所有主题"""
        topics = set()
        for q in self.questions:
            topics.add(q.topic)
        return sorted(list(topics))

    def get_questions_by_topic(self, topic: str) -> List[Question]:
        """根据主题获取题目"""
        return [q for q in self.questions if q.topic == topic]

    async def evaluate_answer(
        self, question_id: str, user_answer: str
    ) -> EvaluationResult:
        """
        评估用户回答

        Args:
            question_id: 题目ID
            user_answer: 用户的回答

        Returns:
            EvaluationResult: 评估结果
        """
        # 获取题目
        question = self.get_question(question_id)
        if not question:
            raise ValueError(f"未找到题目: {question_id}")

        # 构建评估提示词
        evaluation_prompt = f"""请评估用户对社会科举题目的回答。

题目：{question.question}
正确答案：{question.correct_answer}
用户回答：{user_answer}

请根据以下标准进行评估：
1. 判断用户回答是否正确
2. 给出评分（优秀/良好/及格/需要再学习）
3. 给出具体的反馈意见

请用JSON格式返回结果，格式如下：
{{
    "is_correct": true/false,
    "score": "优秀/良好/及格/需要再学习",
    "feedback": "具体的反馈意见"
}}"""

        # 调用LLM进行评估
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": evaluation_prompt},
            ]
            response = await self.llm.ainvoke(messages)
            content = response.content

            # 尝试解析JSON
            try:
                # 提取JSON部分
                import re

                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(content)

                return EvaluationResult(
                    is_correct=result.get("is_correct", False),
                    score=result.get("score", "需要再学习"),
                    feedback=result.get("feedback", "继续加油！"),
                    correct_answer=question.correct_answer,
                )
            except json.JSONDecodeError:
                # JSON解析失败，使用默认评估
                return EvaluationResult(
                    is_correct=False,
                    score="需要再学习",
                    feedback="评估过程出现问题，请再试一次",
                    correct_answer=question.correct_answer,
                )
        except Exception as e:
            raise RuntimeError(f"LLM调用失败: {e}")

    def format_question_for_tts(self, question: Question) -> str:
        """
        格式化题目为语音播报内容

        Args:
            question: 题目对象

        Returns:
            str: 适合TTS播报的文本
        """
        return f"""请听题目：{question.question}"""


# ==================== 便捷函数 ====================


def create_agent(api_key: Optional[str] = None) -> SocialScienceQAAgent:
    """
    创建智能体实例

    Args:
        api_key: API密钥

    Returns:
        SocialScienceQAAgent: 智能体实例
    """
    return SocialScienceQAAgent(api_key=api_key)


# ==================== 交互模式 ====================


async def interactive_mode(agent: SocialScienceQAAgent):
    """
    交互式问答模式

    Args:
        agent: 智能体实例
    """
    print("\n" + "=" * 60)
    print("欢迎使用社会科学问答训练系统")
    print("=" * 60)
    print(f"\n已加载 {len(agent.questions)} 道题目")
    print("输入 'q' 或 'quit' 退出程序")
    print("输入 'n' 跳过本题")
    print("输入 's' 查看所有主题")
    print("输入 't <主题>' 按主题选题")
    print("-" * 60)

    # 初始化第一道题
    question = agent.get_random_question()

    while True:
        try:
            # 显示题目
            print(f"\n【主题】{question.topic}")
            print(f"【题目】{question.question}")

            # 获取用户输入
            user_answer = input("\n请输入你的回答: ").strip()

            if user_answer.lower() in ["q", "quit", "退出"]:
                print("\n再见！感谢使用！")
                break

            if user_answer.lower() in ["n", "next", "跳过"]:
                print("好的，跳过本题")
                question = agent.get_random_question()
                continue

            if user_answer.lower() in ["s", "topics", "主题"]:
                topics = agent.get_all_topics()
                print(f"\n可用主题: {topics}")
                continue

            if user_answer.lower().startswith("t "):
                # 按主题选题
                topic = user_answer[2:].strip()
                questions = agent.get_questions_by_topic(topic)
                if questions:
                    question = questions[0]
                    print(f"已切换到主题: {topic}")
                else:
                    print(f"未找到主题: {topic}")
                continue

            if not user_answer:
                print("请输入回答后再提交！")
                continue

            # 评估回答
            print("\n正在评估...", end="", flush=True)
            result = await agent.evaluate_answer(question.id, user_answer)

            # 显示结果
            print("\n" + "-" * 40)
            print(f"【评估】{result.score}")
            print(f"【反馈】{result.feedback}")
            print("-" * 40)

            # 如果回答达到良好标准，自动跳转到下一题
            if result.score in ["优秀", "良好"]:
                print("回答得很好！自动进入下一题...")
                question = agent.get_random_question()
                continue

        except KeyboardInterrupt:
            print("\n\n程序已退出")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")


# ==================== 主程序入口 ====================


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="社会科学问答训练系统")
    parser.add_argument(
        "--mode",
        choices=["test", "interactive"],
        default="interactive",
        help="运行模式: test=测试, interactive=交互问答",
    )
    args = parser.parse_args()

    try:
        # 创建智能体
        agent = create_agent()

        if args.mode == "interactive":
            # 启动交互模式
            # 获取第一道题
            question = agent.get_random_question()

            # 运行交互模式
            asyncio.run(interactive_mode(agent))
        else:
            # 测试模式
            print("=" * 60)
            print("社会科学问答智能体测试模式")
            print("=" * 60)

            # 显示加载的题目
            print(f"\n已加载 {len(agent.questions)} 道题目：")
            topics = agent.get_all_topics()
            print(f"主题: {topics}")

            # 测试获取随机题目
            q = agent.get_random_question()
            print(f"\n随机题目: {q.question}")
            print(f"正确答案: {q.correct_answer}")

            # 测试评估功能
            print("\n" + "-" * 40)
            print("测试评估功能...")

            # 模拟正确答案
            result = asyncio.run(agent.evaluate_answer(q.id, q.correct_answer))
            print(f"回答: {q.correct_answer}")
            print(f"评估结果: {result.score}")
            print(f"反馈: {result.feedback}")

            print("\n[OK] 测试完成！")

    except Exception as e:
        print(f"[ERROR] {e}")
