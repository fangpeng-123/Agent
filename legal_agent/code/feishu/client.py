"""
飞书API客户端
"""

import httpx
import time
from typing import Dict, Any
from ..config import Config


class FeishuClient:
    """飞书客户端"""

    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
        self._tenant_access_token = None
        self._token_expires = 0

    async def get_tenant_access_token(self) -> str:
        """获取token"""
        if self._tenant_access_token and time.time() < self._token_expires:
            return self._tenant_access_token

        url = f"{self.BASE_URL}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.config.feishu_app_id,
            "app_secret": self.config.feishu_app_secret,
        }

        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        result = response.json()
        if result.get("code") != 0:
            raise Exception(f"获取token失败: {result}")

        self._tenant_access_token = result["tenant_access_token"]
        self._token_expires = time.time() + result.get("expire", 7200) - 60
        return self._tenant_access_token

    async def get_headers(self) -> Dict[str, str]:
        token = await self.get_tenant_access_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def send_text_message(self, receive_id: str, text: str) -> Dict:
        """发送文本消息"""
        import json

        url = f"{self.BASE_URL}/im/v1/messages"
        params = {"receive_id_type": "open_id"}
        payload = {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}),
        }

        headers = await self.get_headers()
        response = await self.client.post(
            url, params=params, headers=headers, json=payload
        )
        response.raise_for_status()
        return response.json()

    async def reply_message(self, message_id: str, text: str) -> Dict:
        """回复消息"""
        import json

        url = f"{self.BASE_URL}/im/v1/messages/{message_id}/reply"
        payload = {"msg_type": "text", "content": json.dumps({"text": text})}
        headers = await self.get_headers()
        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    async def verify_subscription(self, challenge: str) -> Dict:
        """验证订阅"""
        return {"challenge": challenge}

    async def close(self):
        await self.client.aclose()
