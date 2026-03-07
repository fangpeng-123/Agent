# -*- coding: utf-8 -*-
"""
用户画像守护进程

功能：
1. 监控用户对话内容
2. 提取和更新用户画像信息
3. 智能判断（置信度、冲突检测）
4. 将更新后的用户画像保存到文件
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .user_profile_tools import USER_PROFILES, get_user_profile


class ConfidenceEvaluator:
    """评估提取信息的置信度"""

    HIGH_CONFIDENCE_PATTERNS = [
        r"我叫",
        r"我的名字",
        r"叫我",
        r"我喜欢",
        r"我的爱好",
        r"我热衷于",
        r"我的性格",
        r"我是一个",
        r"我是那种",
        r"我喜欢吃",
        r"我爱吃",
        r"我偏好",
        r"我不喜欢",
        r"我讨厌",
        r"我不爱吃",
    ]

    LOW_CONFIDENCE_PATTERNS = [
        r"吗",
        r"呢",
        r"\?$",
        r"是不是",
        r"可能",
        r"大概",
        r"也许",
        r"应该",
    ]

    def evaluate(self, text: str, field: str) -> float:
        """评估文本中提取的某类信息的置信度"""
        text_lower = text.lower()

        if any(p in text_lower for p in self.HIGH_CONFIDENCE_PATTERNS):
            return 0.9

        if any(re.search(p, text) for p in self.LOW_CONFIDENCE_PATTERNS):
            return 0.3

        if field in ["hobbies", "likes", "character"]:
            return 0.6

        return 0.5


class ConflictDetector:
    """检测新旧信息冲突"""

    TIME_KEYWORDS = ["以前", "曾经", "过去", "但是", "不过", "现在", "目前"]
    NEGATION = ["不", "没", "非", "无"]

    def detect(
        self, field: str, old_value: str, new_value: str, context: str = ""
    ) -> str:
        """
        检测冲突并返回处理策略

        返回值:
        - overwrite: 覆盖旧值
        - append: 追加新值
        - merge: 合并新旧值
        - ignore: 忽略新值
        """

        if field == "name":
            return "overwrite"

        if not old_value:
            return "overwrite"

        if field in ["hobbies", "likes"]:
            has_time_contradict = any(kw in context for kw in self.TIME_KEYWORDS)
            has_negation = any(neg in new_value for neg in self.NEGATION)

            if has_negation and not has_time_contradict:
                return "ignore"

            if has_time_contradict:
                return "merge"

        if field == "character":
            return "append"

        return "append"


# 用户画像数据文件路径
USER_PROFILES_FILE = Path(__file__).parent / "user_profiles.json"


def load_user_profiles_from_file() -> Dict[str, Dict]:
    """从文件加载用户画像"""
    try:
        if USER_PROFILES_FILE.exists():
            with open(USER_PROFILES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARN] 加载用户画像文件失败: {e}")
    return {}


def save_user_profiles_to_file(profiles: Dict[str, Dict]) -> bool:
    """保存用户画像到文件"""
    try:
        with open(USER_PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        print(f"[OK] 用户画像已保存到 {USER_PROFILES_FILE}")
        return True
    except Exception as e:
        print(f"[ERROR] 保存用户画像失败: {e}")
        return False


class UserProfileUpdater:
    """用户画像更新器"""

    # 兴趣爱好关键词模式
    HOBBY_PATTERNS = {
        "运动": [
            "喜欢运动",
            "喜欢跑步",
            "喜欢打球",
            "喜欢游泳",
            "喜欢爬山",
            "喜欢骑车",
            "喜欢足球",
            "喜欢篮球",
        ],
        "阅读": [
            "喜欢看书",
            "喜欢读书",
            "喜欢阅读",
            "喜欢故事",
            "喜欢绘本",
            "喜欢漫画",
        ],
        "绘画": ["喜欢画画", "喜欢涂鸦", "喜欢画", "绘画", "美术"],
        "音乐": [
            "喜欢音乐",
            "喜欢唱歌",
            "喜欢弹琴",
            "喜欢跳舞",
            "钢琴",
            "吉他",
            "小提琴",
        ],
        "游戏": ["喜欢游戏", "喜欢玩", "喜欢玩具"],
        "旅游": ["喜欢旅游", "喜欢旅行", "喜欢去玩", "喜欢出门", "喜欢去公园"],
        "动物": ["喜欢动物", "喜欢猫", "喜欢狗", "喜欢小动物", "宠物"],
        "科学": ["喜欢科学", "喜欢探索", "喜欢发明", "喜欢实验", "好奇"],
        "手工": ["喜欢手工", "喜欢做手工", "喜欢折纸", "喜欢拼图"],
    }

    # 性格关键词模式
    CHARACTER_PATTERNS = {
        "开朗": ["开朗", "活泼", "爱笑", "开心", "高兴", "快乐"],
        "内向": ["内向", "害羞", "安静", "文静", "不好意思"],
        "勇敢": ["勇敢", "不怕", "敢于", "胆子大"],
        "善良": ["善良", "好人", "帮助别人", "关心", "体贴"],
        "聪明": ["聪明", "智慧", "机灵", "脑子好", "学得快"],
        "调皮": ["调皮", "淘气", "捣乱", "爱玩"],
    }

    # 喜欢的事物关键词
    LIKES_PATTERNS = {
        "美食": [
            "喜欢吃的",
            "喜欢吃",
            "好吃",
            "美味",
            "美食",
            "零食",
            "糖果",
            "榴莲",
            "蛋糕",
            "冰淇淋",
            "巧克力",
            "披萨",
            "汉堡",
            "炸鸡",
            "火锅",
            "烧烤",
            "寿司",
            "牛排",
            "面条",
            "米饭",
            "包子",
            "水果",
            "苹果",
            "香蕉",
            "橙子",
            "葡萄",
            "西瓜",
            "草莓",
        ],
        "动画片": ["喜欢看动画片", "喜欢看片", "喜欢动画"],
        "玩具": ["喜欢玩具", "玩具", "洋娃娃", "积木", "机器人"],
    }

    def __init__(self):
        self.confidence_evaluator = ConfidenceEvaluator()
        self.conflict_detector = ConflictDetector()
        self.load_profiles()

    def load_profiles(self):
        """加载用户画像"""
        loaded = load_user_profiles_from_file()
        if loaded:
            USER_PROFILES.update(loaded)
            print(f"[OK] 已从文件加载 {len(loaded)} 个用户画像")

    def extract_hobbies(self, text: str) -> List[str]:
        """从文本中提取兴趣爱好（严格模式 + 多层过滤）"""

        # === 第一层：否定词过滤 ===
        negation_patterns = ["不喜欢", "讨厌", "不爱", "不爱好", "没兴趣"]
        if any(neg in text for neg in negation_patterns):
            return []

        # === 第二层：问句过滤 ===
        if text.strip().endswith(("?", "吗", "呢", "？")):
            return []

        # === 第三层：第三方过滤（必须先检查）===
        third_party_patterns = [
            "妈妈",
            "爸爸",
            "朋友",
            "他",
            "她",
            "小明",
            "同学",
            "哥哥",
            "姐姐",
            "弟弟",
            "妹妹",
        ]
        # 检查是否包含第三方词，且后面跟着"喜欢/爱好"等词
        for tp in third_party_patterns:
            if tp in text:
                # 检查是否在同一词组中（如"妈妈喜欢"）
                idx = text.find(tp)
                if idx >= 0:
                    rest = text[idx:]
                    if "喜欢" in rest[:6] or "爱好" in rest[:6]:
                        return []

        # === 第四层：严格匹配爱好表达（必须是句子开头）===
        stripped = text.strip()

        # 只匹配以"我"开头的句子
        if not stripped.startswith("我"):
            return []

        hobby_patterns = [
            (r"^我喜欢(.+)", "我喜欢"),
            (r"^我的爱好是(.+)", "我的爱好是"),
            (r"^我爱(.+)", "我爱"),
            (r"^我热衷于(.+)", "我热衷于"),
        ]

        found_hobbies = []
        for pattern, prefix in hobby_patterns:
            match = re.match(pattern, stripped)
            if match:
                item = match.group(1).strip()
                # 匹配关键词表中的分类
                for hobby, keywords in self.HOBBY_PATTERNS.items():
                    for kw in keywords:
                        if kw in item or item in kw:
                            if hobby not in found_hobbies:
                                found_hobbies.append(hobby)
                break

        return found_hobbies

    def extract_character(self, text: str) -> List[str]:
        """从文本中提取性格特点"""
        found_character = []
        for char, keywords in self.CHARACTER_PATTERNS.items():
            for keyword in keywords:
                if keyword in text:
                    found_character.append(char)
                    break
        return found_character

    def extract_likes(self, text: str) -> List[str]:
        """从文本中提取喜欢的事物（严格模式 + 多层过滤）"""

        # === 第一层：否定词过滤 ===
        negation_patterns = ["不喜欢", "讨厌", "不爱", "不爱吃", "不喜欢吃"]
        if any(neg in text for neg in negation_patterns):
            return []

        # === 第二层：问句过滤 ===
        if text.strip().endswith(("?", "吗", "呢", "？")):
            return []

        # === 第三层：第三方过滤（排除家人/朋友/他人）===
        third_party_patterns = [
            "妈妈喜欢",
            "爸爸喜欢",
            "朋友喜欢",
            "哥哥喜欢",
            "姐姐喜欢",
            "弟弟喜欢",
            "妹妹喜欢",
            "他喜欢",
            "她喜欢",
            "小明喜欢",
            "同学喜欢",
            "老师喜欢",
            "家人喜欢",
            "他/她喜欢",
        ]
        if any(pattern in text for pattern in third_party_patterns):
            return []

        # === 第四层：事实陈述过滤（只是陈述非喜好）===
        factual_patterns = ["吃了", "买了", "去了", "看了", "玩了", "喝了"]
        # 检查是否在句子中间（不是开头）
        for fact in factual_patterns:
            if fact in text and not text.strip().startswith(fact):
                return []

        # === 第五层：严格匹配喜欢表达（必须是句子开头，按优先级）===
        like_patterns = [
            (r"^我喜欢吃(.+)", "我喜欢吃"),
            (r"^我爱吃(.+)", "我爱吃"),
            (r"^我喜欢喝(.+)", "我喜欢喝"),
            (r"^我喜欢(.+)", "我喜欢"),
            (r"^我爱(.+)", "我爱"),
        ]

        found_likes = []
        for pattern, prefix in like_patterns:
            match = re.match(pattern, text.strip())
            if match:
                item = match.group(1).strip()
                # 清理前缀动词
                if item.startswith("吃") or item.startswith("喝"):
                    item = item[1:]
                if item:
                    found_likes.append(item)
                break  # 只取第一个匹配

        return found_likes

    def extract_name(self, text: str) -> Optional[str]:
        """从文本中提取姓名（严格规则）"""
        text = text.strip()

        # 排除问句
        if text.endswith("?") or text.endswith("吗") or text.endswith("呢"):
            return None

        # 严格匹配"我叫..."、"我的名字是..."、"叫我..."等模式
        patterns = [
            r"^我叫(\S{1,4})",
            r"^我的名字是(\S{1,4})",
            r"^叫我(\S{1,4})",
        ]
        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                name = match.group(1)
                # 排除非姓名的词
                if name and name not in [
                    "小朋友",
                    "宝宝",
                    "孩子",
                    "你",
                    "我",
                    "他",
                    "她",
                ]:
                    return name
        return None

    def update_profile(
        self, user_id: str, user_input: str, assistant_response: str = ""
    ) -> bool:
        """更新用户画像（带智能判断）"""
        profile = USER_PROFILES.get(user_id)
        if not profile:
            print(f"[WARN] 用户 {user_id} 不存在，跳过更新")
            return False

        updated = False
        combined_text = f"{user_input} {assistant_response}"

        confidence = self.confidence_evaluator.evaluate(combined_text, "general")
        if confidence < 0.5:
            print(f"[SKIP] 置信度 {confidence:.2f} < 0.5，跳过更新")
            return False

        # 提取并更新姓名
        name = self.extract_name(user_input)
        if name:
            old_name = profile.get("name", "")
            strategy = self.conflict_detector.detect(
                "name", old_name, name, combined_text
            )
            if strategy == "overwrite" and name != old_name:
                profile["name"] = name
                print(f"[UPDATE] 用户 {user_id} 姓名更新为: {name}")
                updated = True

        # 提取并更新兴趣爱好
        hobbies = self.extract_hobbies(combined_text)
        if hobbies:
            current_hobbies = profile.get("hobbies", "")
            hobby_list = [h.strip() for h in current_hobbies.split("、") if h.strip()]

            hobby_confidence = self.confidence_evaluator.evaluate(
                combined_text, "hobbies"
            )
            if hobby_confidence >= 0.5:
                for hobby in hobbies:
                    strategy = self.conflict_detector.detect(
                        "hobbies", ",".join(hobby_list), hobby, combined_text
                    )
                    if strategy == "ignore":
                        print(
                            f"[SKIP] 用户 {user_id} 忽略兴趣爱好: {hobby}（检测到否定或冲突）"
                        )
                        continue
                    if hobby not in hobby_list:
                        hobby_list.append(hobby)
                        print(
                            f"[UPDATE] 用户 {user_id} 添加兴趣爱好: {hobby}（置信度: {hobby_confidence:.2f}）"
                        )
                profile["hobbies"] = "、".join(hobby_list)
                updated = True

        # 提取并更新性格特点
        characters = self.extract_character(combined_text)
        if characters:
            current_character = profile.get("character", "")
            char_confidence = self.confidence_evaluator.evaluate(
                combined_text, "character"
            )

            for char in characters:
                if char not in current_character:
                    if current_character:
                        profile["character"] = f"{current_character}、{char}"
                    else:
                        profile["character"] = char
                    print(
                        f"[UPDATE] 用户 {user_id} 添加性格特点: {char}（置信度: {char_confidence:.2f}）"
                    )
            updated = True

        # 提取并更新喜欢的事物
        likes = self.extract_likes(combined_text)
        if likes:
            current_likes = profile.get("likes", "")
            like_list = [l.strip() for l in current_likes.split("、") if l.strip()]

            likes_confidence = self.confidence_evaluator.evaluate(
                combined_text, "likes"
            )
            if likes_confidence >= 0.5:
                for like in likes:
                    strategy = self.conflict_detector.detect(
                        "likes", ",".join(like_list), like, combined_text
                    )
                    if strategy == "ignore":
                        print(
                            f"[SKIP] 用户 {user_id} 忽略喜欢的事物: {like}（检测到否定或冲突）"
                        )
                        continue
                    if like not in like_list:
                        like_list.append(like)
                        print(
                            f"[UPDATE] 用户 {user_id} 添加喜欢的事物: {like}（置信度: {likes_confidence:.2f}）"
                        )
                profile["likes"] = "、".join(like_list)
                updated = True

        # 如果有更新，保存到文件
        if updated:
            save_user_profiles_to_file(USER_PROFILES)

        return updated


class ProfileDaemon:
    """用户画像守护进程"""

    def __init__(self, check_interval: float = 10.0):
        self.check_interval = check_interval
        self.updater = UserProfileUpdater()
        self.running = False
        self.message_queue = asyncio.Queue()

    async def start(self):
        """启动守护进程"""
        self.running = True
        print("[OK] 用户画像守护进程已启动")
        asyncio.create_task(self._process_messages())

    async def stop(self):
        """停止守护进程"""
        self.running = False
        print("[INFO] 用户画像守护进程正在停止...")

    async def add_message(
        self, user_id: str, user_input: str, assistant_response: str = ""
    ):
        """添加消息到队列"""
        await self.message_queue.put(
            {
                "user_id": user_id,
                "user_input": user_input,
                "assistant_response": assistant_response,
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def _process_messages(self):
        """处理消息队列"""
        while self.running or not self.message_queue.empty():
            try:
                # 等待消息，设置超时避免无限等待
                msg = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                self.updater.update_profile(
                    msg["user_id"], msg["user_input"], msg["assistant_response"]
                )
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[ERROR] 处理消息时出错: {e}")

    def get_updater(self) -> UserProfileUpdater:
        """获取用户画像更新器"""
        return self.updater


# 全局守护进程实例
_daemon: Optional[ProfileDaemon] = None


def get_daemon() -> ProfileDaemon:
    """获取全局守护进程实例"""
    global _daemon
    if _daemon is None:
        _daemon = ProfileDaemon()
    return _daemon


def set_daemon(daemon: ProfileDaemon):
    """设置全局守护进程实例"""
    global _daemon
    _daemon = daemon


if __name__ == "__main__":
    """测试用户画像更新"""
    print("[INFO] 用户画像守护进程测试")
    print("-" * 50)

    updater = UserProfileUpdater()

    # 测试1: 提取兴趣爱好
    test_text1 = "我喜欢跑步和看书"
    hobbies = updater.extract_hobbies(test_text1)
    print(f"[TEST1] 文本: {test_text1}")
    print(f"[TEST1] 提取的兴趣爱好: {hobbies}")

    # 测试2: 提取性格
    test_text2 = "我是一个开朗的小朋友"
    character = updater.extract_character(test_text2)
    print(f"[TEST2] 文本: {test_text2}")
    print(f"[TEST2] 提取的性格: {character}")

    # 测试3: 提取姓名
    test_text3 = "我叫小明"
    name = updater.extract_name(test_text3)
    print(f"[TEST3] 文本: {test_text3}")
    print(f"[TEST3] 提取的姓名: {name}")

    # 测试4: 更新用户画像
    print("\n[TEST4] 更新用户画像测试")
    result = updater.update_profile(
        "user_001", "我叫小明，我喜欢跑步和看书，我是一个开朗的小朋友"
    )
    print(f"[TEST4] 更新结果: {'成功' if result else '无更新'}")

    print("\n[OK] 测试完成")
