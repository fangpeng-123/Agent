"""
飞书消息处理器
"""

from typing import Dict, Any
from ..config import Config
from ..feishu.client import FeishuClient
from ..services.dialog import DialogService
from ..services.safety import SafetyService
from ..services.llm import LLMService
from ..rag.pipeline import RAGPipelineFactory


class FeishuHandler:
    """飞书消息处理器"""

    def __init__(
        self,
        config: Config,
        rag_pipeline,
        dialog_service: DialogService,
        safety_service: SafetyService,
        llm_service: LLMService,
    ):
        self.config = config
        self.rag_pipeline = rag_pipeline
        self.dialog_service = dialog_service
        self.safety_service = safety_service
        self.llm_service = llm_service
        self.feishu_client = FeishuClient(config)

    async def handle_event(self, event: Dict[str, Any]) -> Dict:
        """处理消息事件"""
        message = event.get("event", {})
        message_id = message.get("message_id")
        sender_id = message.get("sender", {}).get("open_id")
        text = message.get("text", "")

        user_id = sender_id
        session_id = f"feishu_{user_id}"

        safety_result = self.safety_service.check_input(text)
        if not safety_result.passed:
            await self.feishu_client.send_text_message(
                sender_id, "抱歉，您的问题包含敏感内容。"
            )
            return {"status": "blocked"}

        try:
            history_messages = self.dialog_service.get_history_messages(session_id)
            result = self.rag_pipeline.query(text, history_messages)

            answer = result.answer
            if result.citations:
                citation_text = "\n".join(
                    [f"- {c['law']} {c['article']}" for c in result.citations]
                )
                answer = f"{answer}\n\n**法条引用：**\n{citation_text}"

            await self.feishu_client.send_text_message(sender_id, answer)

            self.dialog_service.add_message(session_id, "user", text)
            self.dialog_service.add_message(session_id, "assistant", answer)

            return {"status": "success"}

        except Exception as e:
            await self.feishu_client.send_text_message(
                sender_id, "处理问题时出错，请稍后再试。"
            )
            return {"status": "error", "message": str(e)}

    async def verify_subscription(self, challenge: str) -> Dict:
        return await self.feishu_client.verify_subscription(challenge)

    async def close(self):
        await self.feishu_client.close()
