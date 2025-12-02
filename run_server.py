#!/usr/bin/env python3
"""
启动 Chatflow Tailor 后端服务
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  Chatflow Tailor API Server")
    print("  http://localhost:8000")
    print("=" * 60)
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=True)
