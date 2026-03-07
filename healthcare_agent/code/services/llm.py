from typing import List, Optional
from dashscope import Generation
from dashscope import get_api_key
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun

from ..config import Config


class DashScopeLLM(LLM):
    model: str = "qwen-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7

    @property
    def _llm_type(self) -> str:
        return "dashscope"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> str:
        response = Generation.call(
            model=self.model,
            prompt=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            api_key=get_api_key()
        )

        if response.status_code == 200:
            return response.output.text
        else:
            raise Exception(f"API调用失败: {response.message}")


class LLMService:
    def __init__(self, config: Config):
        self.config = config
        self.mode = config.get_service_mode()
        self._llm = None

    def get_llm(self):
        if self._llm is None:
            if self.mode == "local":
                self._llm = self._create_local_llm()
            else:
                self._llm = self._create_api_llm()
        return self._llm

    def _create_local_llm(self):
        local_config = self.config.llm.local
        model_name = local_config.get("model_name", "Qwen/Qwen2.5-7B-Instruct")
        device = local_config.get("device", "cpu")

        try:
            from langchain_community.llms import HuggingFacePipeline
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map=device,
                trust_remote_code=True
            )

            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=2000,
                temperature=0.7
            )

            return HuggingFacePipeline(pipeline=pipe)
        except Exception as e:
            print(f"加载本地模型失败，切换到API模式: {e}")
            return self._create_api_llm()

    def _create_api_llm(self):
        api_config = self.config.llm.api
        provider = api_config.get("provider", "ali")

        if provider == "ali":
            model = api_config.get("model", "qwen-turbo")
            max_tokens = api_config.get("max_tokens", 2000)
            temperature = api_config.get("temperature", 0.7)

            return DashScopeLLM(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")

    async def generate_response(self, question: str, history: Optional[List] = None) -> str:
        llm = self.get_llm()

        prompt = self._build_prompt(question, history)
        response = llm(prompt)

        return response

    def _build_prompt(self, question: str, history: Optional[List] = None) -> str:
        prompt = "你是一个专业的健康管理助手，为用户提供健康咨询和建议。请基于医学知识回答用户的问题，回答要专业、准确、易懂。\n\n"

        if history:
            prompt += "对话历史:\n"
            for msg in history[-5:]:
                role = "用户" if msg["role"] == "user" else "助手"
                prompt += f"{role}: {msg['content']}\n"
            prompt += "\n"

        prompt += f"用户问题: {question}\n\n请回答:"

        return prompt

    async def close(self):
        pass
