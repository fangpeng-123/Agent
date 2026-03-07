# -*- coding: utf-8 -*-
"""Prompt 版本管理"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class PromptVersionManager:
    """Prompt 版本管理器"""

    def __init__(self, version_dir: str = "./data/prompts"):
        self.version_dir = Path(version_dir)
        self.version_dir.mkdir(parents=True, exist_ok=True)
        self.current_version = "1.0.0"
        self.history: Dict[str, list] = {}

    def save_version(
        self, prompt_name: str, content: str, description: str = ""
    ) -> str:
        """保存 Prompt 版本"""
        version_id = f"{prompt_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        version_info = {
            "version": version_id,
            "content": content,
            "description": description,
            "created_at": datetime.now().isoformat(),
        }

        if prompt_name not in self.history:
            self.history[prompt_name] = []
        self.history[prompt_name].append(version_info)

        version_file = self.version_dir / f"{version_id}.json"
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(version_info, f, ensure_ascii=False, indent=2)

        return version_id

    def load_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """加载指定版本"""
        version_file = self.version_dir / f"{version_id}.json"
        if version_file.exists():
            with open(version_file, encoding="utf-8") as f:
                return json.load(f)
        return None

    def list_versions(self, prompt_name: str) -> list:
        """列出所有版本"""
        return self.history.get(prompt_name, [])

    def rollback(self, version_id: str) -> Optional[str]:
        """回滚到指定版本"""
        version_info = self.load_version(version_id)
        if version_info:
            return version_info["content"]
        return None
