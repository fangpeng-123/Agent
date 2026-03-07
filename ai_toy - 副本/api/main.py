# -*- coding: utf-8 -*-
"""FastAPI 主入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.middleware import add_middleware, request_logging_middleware
from api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    print("[INFO] 服务启动")
    yield
    print("[INFO] 服务关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="AI Agent API",
        description="解耦智能体 API 服务",
        version="1.0.0",
        lifespan=lifespan,
    )

    add_middleware(app)

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
