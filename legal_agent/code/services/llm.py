"""
LLM服务 - 支持本地模型和阿里云API
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema import HumanMessage, SystemMessage
import httpx
from ..config import Config


class BaseLLMService(ABC):
    """LLM服务基类"""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        pass


class LocalLLMService(BaseLLMService):
    """本地LLM服务"""

    def __init__(self, config: Config):
        self.config = config.llm["local"]
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        """加载模型"""
        if self._model is None:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name, trust_remote_code=True
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                trust_remote_code=True,
                torch_dtype="auto",
                device_map="auto",
            )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """生成文本"""
        self._load_model()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        inputs = self._tokenizer([text], return_tensors="pt").to(self._model.device)

        outputs = self._model.generate(
            **inputs, max_new_tokens=2048, temperature=0.7, do_sample=True
        )

        response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.split("assistant\n")[-1].strip()


class AliLLMService(BaseLLMService):
    """阿里云LLM API服务"""

    API_URL = (
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    )

    def __init__(self, config: Config):
        self.config = config.llm["api"]
        self.api_key = config.dashscope_api_key
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """生成文本"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model,
            "input": {"messages": messages},
            "parameters": {
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = await self.client.post(self.API_URL, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        return result["output"]["text"]

    async def close(self):
        await self.client.aclose()


class LangChainAliLLM(LLM):
    """LangChain兼容的阿里云LLM"""

    API_URL = (
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    )

    def __init__(self, api_key: str, model: str = "qwen-turbo", **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)

    @property
    def _llm_type(self) -> str:
        return "ali_qwen"

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "input": {"messages": messages},
            "parameters": {"max_tokens": 2000, "temperature": 0.7},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = await self.client.post(self.API_URL, headers=headers, json=payload)
        response.raise_for_status()

        return response.json()["output"]["text"]

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        import asyncio

        return asyncio.get_event_loop().run_until_complete(
            self._acall(prompt, stop, run_manager)
        )


class LLMService:
    """LLM服务工厂"""

    def __init__(self, config: Config):
        self.config = config
        self._local_service: Optional[LocalLLMService] = None
        self._api_service: Optional[AliLLMService] = None

    def get_service(self) -> BaseLLMService:
        """获取合适的服务"""
        if self.config.is_local_mode():
            if self._local_service is None:
                self._local_service = LocalLLMService(self.config)
            return self._local_service
        else:
            if self._api_service is None:
                self._api_service = AliLLMService(self.config)
            return self._api_service

    def get_langchain_llm(self) -> LLM:
        """获取LangChain LLM"""
        if self.config.is_local_mode():
            from langchain.llms import HuggingFaceHub

            return HuggingFaceHub(
                repo_id=self.config.llm["local"].model_name, task="text-generation"
            )
        else:
            return LangChainAliLLM(
                api_key=self.config.dashscope_api_key,
                model=self.config.llm["api"].model,
            )

    async def close(self):
        if self._api_service:
            await self._api_service.close()
