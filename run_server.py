#!/usr/bin/env python3
"""
启动 Chatflow Tailor 后端服务
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    is_dev = os.environ.get("RAILWAY_ENVIRONMENT") is None

    print("=" * 60)
    print("  Chatflow Tailor API Server")
    print(f"  http://localhost:{port}")
    print("=" * 60)

    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=port,
        reload=is_dev  # 开发环境启用热重载
    )
