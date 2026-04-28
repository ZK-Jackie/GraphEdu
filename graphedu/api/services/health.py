"""健康检查 API 控制器

提供系统健康检查端点，用于 Docker 健康检查和负载均衡器探测。
"""

from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

health_controller = APIRouter(prefix="/health", tags=["健康检查"])


@health_controller.get("", response_class=HTMLResponse)
async def health_check() -> str:
    """健康检查端点

    返回简单的健康状态 HTML 页面，用于 Docker 健康检查和负载均衡器探测。

    Returns:
        HTML 健康状态页面
    """
    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GraphEdu 健康检查</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                    Oxygen, Ubuntu, Cantarell, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                text-align: center;
                padding: 40px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            }}
            .status {{
                font-size: 72px;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
            }}
            .timestamp {{
                color: #666;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="status">✅</div>
            <h1>系统运行正常</h1>
            <p class="timestamp">{datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
        </div>
    </body>
    </html>
    """


@health_controller.get("/detail")
async def health_check_detail() -> dict:
    """详细健康检查端点

    返回详细的系统健康状态，包括各组件的连接状态。

    Returns:
        包含详细健康状态的字典
    """
    # TODO: 添加数据库连接检查、Redis 连接检查等
    return {
        "status": "healthy",
        "components": {
            "api": "ok",
            # "database": "ok",  # 待实现
            # "redis": "ok",  # 待实现
        },
    }
