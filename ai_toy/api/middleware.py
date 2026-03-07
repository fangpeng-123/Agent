# -*- coding: utf-8 -*-
"""API 中间件"""

import time

from fastapi import Request, Response


async def request_logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    print(
        f"[API] {request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s"
    )

    return response


async def rate_limit_middleware(request: Request, call_next):
    """速率限制中间件（预留）"""
    return await call_next(request)


def add_middleware(app):
    """添加中间件"""
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware

    app.add_middleware(GZipMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
