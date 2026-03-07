import hashlib
import xml.etree.ElementTree as ET
from typing import Optional
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import struct

from ..config import Config
from ..models.schemas import WeChatMessage, QueryResponse, ReviewLevel
from ..services.dialog import DialogService
from ..services.safety import SafetyService
from ..services.llm import LLMService


@dataclass
class QueryResult:
    answer: str
    review_level: ReviewLevel


class WeChatHandler:
    def __init__(
        self,
        config: Config,
        dialog_service: DialogService,
        safety_service: SafetyService,
        llm_service: LLMService
    ):
        self.config = config
        self.dialog_service = dialog_service
        self.safety_service = safety_service
        self.llm_service = llm_service
        self.wechat_config = config.wechat_work

    async def verify_url(self, params: dict) -> str:
        token = self.wechat_config.token
        signature = params.get("msg_signature", "")
        timestamp = params.get("timestamp", "")
        nonce = params.get("nonce", "")
        echostr = params.get("echostr", "")

        if self._verify_signature(token, timestamp, nonce, echostr, signature):
            return echostr
        return ""

    def _verify_signature(self, token: str, timestamp: str, nonce: str, echostr: str, signature: str) -> bool:
        tmp_list = [token, timestamp, nonce, echostr]
        tmp_list.sort()
        tmp_str = "".join(tmp_list)
        sha1 = hashlib.sha1()
        sha1.update(tmp_str.encode("utf-8"))
        hashcode = sha1.hexdigest()
        return hashcode == signature

    def _decrypt_message(self, encrypted_msg: str, msg_signature: str, timestamp: str, nonce: str) -> str:
        token = self.wechat_config.token
        encoding_aes_key = self.wechat_config.encoding_aes_key + "="
        aes_key = base64.b64decode(encoding_aes_key)

        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.CBC(aes_key[:16]),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()

        encrypted_data = base64.b64decode(encrypted_msg)
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

        pad = decrypted_data[-1]
        content = decrypted_data[:-pad].decode("utf-8")

        msg_len = struct.unpack("I", content[16:20])[0]
        msg_content = content[20:20 + msg_len]

        received_signature = content[:16]
        tmp_list = [token, timestamp, nonce, msg_content]
        tmp_list.sort()
        tmp_str = "".join(tmp_list)
        sha1 = hashlib.sha1()
        sha1.update(tmp_str.encode("utf-8"))
        expected_signature = sha1.digest()

        if received_signature != expected_signature:
            raise ValueError("签名验证失败")

        return msg_content

    def _encrypt_message(self, message: str, timestamp: str, nonce: str) -> str:
        token = self.wechat_config.token
        encoding_aes_key = self.wechat_config.encoding_aes_key + "="
        aes_key = base64.b64decode(encoding_aes_key)

        tmp_list = [token, timestamp, nonce, message]
        tmp_list.sort()
        tmp_str = "".join(tmp_list)
        sha1 = hashlib.sha1()
        sha1.update(tmp_str.encode("utf-8"))
        signature = sha1.digest()

        msg_len = len(message)
        msg_content = struct.pack("I", msg_len) + message.encode("utf-8")

        pad = 32 - (len(signature) + len(msg_content)) % 32
        msg_content += bytes([pad]) * pad

        plaintext = signature + msg_content

        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.CBC(aes_key[:16]),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(plaintext) + encryptor.finalize()

        return base64.b64encode(encrypted_data).decode("utf-8")

    async def handle_callback(self, body: bytes):
        try:
            xml_str = body.decode("utf-8")
            root = ET.fromstring(xml_str)

            encrypted_msg = root.find("Encrypt").text
            msg_signature = root.find("MsgSignature").text
            timestamp = root.find("TimeStamp").text
            nonce = root.find("Nonce").text

            decrypted_msg = self._decrypt_message(encrypted_msg, msg_signature, timestamp, nonce)
            msg_root = ET.fromstring(decrypted_msg)

            msg_type = msg_root.find("MsgType").text
            from_user = msg_root.find("FromUserName").text
            to_user = msg_root.find("ToUserName").text
            create_time = msg_root.find("CreateTime").text

            message = WeChatMessage(
                to_user_name=to_user,
                from_user_name=from_user,
                create_time=int(create_time),
                msg_type=msg_type
            )

            if msg_type == "text":
                content = msg_root.find("Content").text
                message.content = content
                await self._handle_text_message(message)
            elif msg_type == "image":
                media_id = msg_root.find("MediaId").text
                message.media_id = media_id
                await self._handle_image_message(message)
            elif msg_type == "file":
                media_id = msg_root.find("MediaId").text
                message.media_id = media_id
                await self._handle_file_message(message)

        except Exception as e:
            print(f"处理企微消息失败: {e}")

    async def _handle_text_message(self, message: WeChatMessage):
        user_id = message.from_user_name
        question = message.content

        valid, reason = self.safety_service.is_valid_question(question)
        if not valid:
            await self._send_message(user_id, f"抱歉，您的问题包含敏感内容，无法回答。原因：{reason}")
            return

        session_id = self.dialog_service.get_or_create_session(user_id)
        history_messages = self.dialog_service.get_history_messages(session_id)

        result = await self.process_query(question, user_id, history_messages)

        self.dialog_service.add_message(session_id, "user", question)
        self.dialog_service.add_message(session_id, "assistant", result.answer)

        if result.review_level == ReviewLevel.L0:
            await self._send_message(user_id, result.answer)
        else:
            await self._send_to_review(user_id, question, result.answer, result.review_level)

    async def _handle_image_message(self, message: WeChatMessage):
        await self._send_message(message.from_user_name, "图片功能正在开发中，敬请期待")

    async def _handle_file_message(self, message: WeChatMessage):
        await self._send_message(message.from_user_name, "文件功能正在开发中，敬请期待")

    async def process_query(self, question: str, user_id: str, history_messages: list) -> QueryResult:
        review_level = self._classify_question(question)

        if review_level == ReviewLevel.L0:
            answer = await self.llm_service.generate_response(question, history_messages)
        else:
            answer = await self.llm_service.generate_response(question, history_messages)

        return QueryResult(answer=answer, review_level=review_level)

    def _classify_question(self, question: str) -> ReviewLevel:
        l0_keywords = ["什么是", "定义", "解释", "什么是", "是什么"]
        l1_keywords = ["饮食", "运动", "锻炼", "减肥", "增肌"]
        l2_keywords = ["医院", "科室", "医生", "挂号", "看病"]
        l3_keywords = ["诊断", "治疗", "用药", "吃药", "手术"]

        question_lower = question.lower()

        for keyword in l3_keywords:
            if keyword in question_lower:
                return ReviewLevel.L3

        for keyword in l2_keywords:
            if keyword in question_lower:
                return ReviewLevel.L2

        for keyword in l1_keywords:
            if keyword in question_lower:
                return ReviewLevel.L1

        return ReviewLevel.L0

    async def _send_message(self, user_id: str, message: str):
        pass

    async def _send_to_review(self, user_id: str, question: str, ai_response: str, review_level: ReviewLevel):
        pass

    async def close(self):
        pass
