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
from .services.dialog import DialogService
from .services.safety import SafetyService
from .services.llm import LLMService
from .wechat.handler import WeChatHandler


config = load_config()
hardware_detector = HardwareDetector()
dialog_service = DialogService(config)
safety_service = SafetyService(config.safety.sensitive_words)
llm_service = LLMService(config)
wechat_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global wechat_handler
    wechat_handler = WeChatHandler(
        config, dialog_service, safety_service, llm_service
    )
    yield
    await llm_service.close()
    if wechat_handler:
        await wechat_handler.close()


app = FastAPI(title="健康管理助手", version="1.0.0", lifespan=lifespan)

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
    return {"message": "健康管理助手", "version": "1.0.0", "service_mode": mode}


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
    result = await wechat_handler.process_query(request.question, user_id, history_messages)

    dialog_service.add_message(session_id, "user", request.question)
    dialog_service.add_message(session_id, "assistant", result.answer)

    return QueryResponse(
        answer=result.answer,
        session_id=session_id,
        review_level=result.review_level
    )


@app.post("/wechat/webhook")
async def wechat_webhook(request: Request):
    body = await request.body()

    if "echostr" in request.query_params:
        return await wechat_handler.verify_url(request.query_params)

    if body:
        await wechat_handler.handle_callback(body)

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
