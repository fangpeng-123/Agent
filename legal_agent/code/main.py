"""
FastAPI主入口
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import load_config, HardwareDetector
from .models.schemas import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
    ServiceStatusResponse,
)
from .rag.document_loader import DocumentLoader
from .rag.pipeline import RAGPipelineFactory
from .services.dialog import DialogService
from .services.safety import SafetyService
from .services.llm import LLMService
from .feishu.handler import FeishuHandler


config = load_config()
hardware_detector = HardwareDetector()
dialog_service = DialogService(config)
safety_service = SafetyService(config.safety.sensitive_words)
llm_service = LLMService(config)
rag_pipeline = RAGPipelineFactory(config).create_pipeline("langchain")
feishu_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global feishu_handler
    feishu_handler = FeishuHandler(
        config, rag_pipeline, dialog_service, safety_service, llm_service
    )
    yield
    await llm_service.close()
    if feishu_handler:
        await feishu_handler.close()


app = FastAPI(title="法律知识问答机器人", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    mode = config.get_service_mode()
    return {"message": "法律知识问答机器人", "version": "1.0.0", "service_mode": mode}


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="1.0.0")


@app.get("/api/v1/service/status", response_model=ServiceStatusResponse)
async def service_status():
    status = hardware_detector.check()
    return ServiceStatusResponse(
        mode=config.get_service_mode(),
        has_gpu=status.has_gpu,
        gpu_name=status.gpu_name,
        vram_gb=status.vram_gb,
    )


@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    valid, reason = safety_service.is_valid_question(request.question)
    if not valid:
        raise HTTPException(status_code=400, detail=reason)

    user_id = request.user_id or "anonymous"
    session_id = request.session_id or f"api_{user_id}"

    if not request.session_id:
        session_id = dialog_service.create_session(user_id)

    history_messages = dialog_service.get_history_messages(session_id)
    result = rag_pipeline.query(request.question, history_messages)

    answer = result.answer
    if result.citations:
        citation_text = "\n".join(
            [f"- {c['law']} {c['article']}" for c in result.citations]
        )
        answer = f"{answer}\n\n**法条引用：**\n{citation_text}"

    dialog_service.add_message(session_id, "user", request.question)
    dialog_service.add_message(session_id, "assistant", answer)

    return QueryResponse(
        answer=answer, citations=result.citations, session_id=session_id
    )


@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    body = await request.json()

    if "challenge" in body:
        return await feishu_handler.verify_subscription(body["challenge"])

    if "event" in body:
        await feishu_handler.handle_event(body)

    return {"status": "success"}


@app.get("/api/v1/history/{user_id}")
async def get_user_history(user_id: str):
    sessions = dialog_service.get_user_sessions(user_id)
    return {"sessions": sessions}


@app.delete("/api/v1/history/{session_id}")
async def delete_session(session_id: str):
    success = dialog_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"status": "deleted"}


def main():
    import uvicorn

    uvicorn.run(app, host=config.server.host, port=config.server.port)


if __name__ == "__main__":
    main()
