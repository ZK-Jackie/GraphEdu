import base64
import hashlib
import hmac
import json
import logging
from pathlib import Path
import string
import time
from typing import Any

from ..webhook_payload import PayloadGenerator


class FeishuPayloadGenerator(PayloadGenerator):
    """Feishu-specific payload generator with signature support.

    Generates interactive card format payloads with signature verification.
    """

    def __init__(
        self,
        sign_secret: str | None = None,
        template_path: str | None = None,
        template_mapping: dict[str, str] | None = None,
    ):
        """Initialize Feishu payload generator.

        Args:
            sign_secret: Feishu webhook signature secret (optional).
            template_path: Path to the JSON template file (optional).
            template_mapping: Additional template variable mappings (optional).
        """
        self.sign_secret = sign_secret

        # 加载模板文件
        if template_path is None:
            # 默认使用包内的模板
            template_path = Path(__file__).parent / "template.json"
        else:
            template_path = Path(template_path)

        with open(template_path, encoding="utf-8") as f:
            self.template = json.load(f)

    def __call__(self, record: logging.LogRecord) -> dict[str, Any]:
        """生成飞书 webhook payload
        https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot?lang=zh-CN#5a997364

        Args:
            record: Log record to convert.

        Returns:
            Payload dictionary.
        """
        # 准备模板替换值
        template_vars = {
            "log_level": record.levelname,
            "log_time": self._format_time(record.created),
            "log_line": f"{record.pathname}:{record.lineno}",
            "log_message": self._format_short_message(record),
            "stack_info": self._format_stack_trace(record),
            "heading_project_name": "Graphedu",
            "heading_color": self._get_color_by_level(record.levelname),
        }

        # 深度填充模板
        payload = self._deep_format_template(self.template, template_vars)

        # 添加签名
        if self.sign_secret:
            timestamp = str(int(time.time()))  # 单位秒
            sign = self._generate_sign(timestamp, self.sign_secret)
            payload["timestamp"] = timestamp
            payload["sign"] = sign

        return payload

    def _deep_format_template(self, template: Any, template_vars: dict[str, Any]) -> Any:
        """深度填充模板中的占位符

        Args:
            template: 模板对象（可能是 dict, list, 或 str）
            template_vars: 模板变量字典

        Returns:
            填充后的对象
        """
        if isinstance(template, str):
            # 使用 string.Template 替换 ${var} 格式的占位符
            try:
                return string.Template(template).substitute(template_vars)
            except (KeyError, ValueError):
                # 如果占位符不存在或格式错误，使用 safe_substitute 保留原样
                return string.Template(template).safe_substitute(template_vars)
        elif isinstance(template, dict):
            # 递归处理字典
            return {key: self._deep_format_template(value, template_vars) for key, value in template.items()}
        elif isinstance(template, list):
            # 递归处理列表
            return [self._deep_format_template(item, template_vars) for item in template]
        else:
            # 其他类型直接返回
            return template

    def _format_time(self, created: float) -> str:
        """格式化时间戳"""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created))

    def _format_exception(self, exc_info) -> str:
        """格式化异常信息"""
        import traceback

        return "".join(traceback.format_exception(*exc_info))

    def _format_short_message(self, record: logging.LogRecord) -> str:
        """格式化简短的日志消息
        如果消息包含堆栈信息，只显示第一行或简短描述
        否则显示完整消息
        """
        message = record.getMessage()

        # 如果消息包含堆栈追踪信息，提取出末尾1行
        if self._contains_stack_trace(message):
            lines = message.split("\n")
            # 从后往前找到第一行非空消息
            for line in lines[::-1]:
                stripped = line.strip()
                if stripped and not any(
                    indicator in stripped for indicator in ["Traceback", 'File "', "line ", "Error:", "Exception:"]
                ):
                    return stripped

            # 如果没找到合适的摘要，返回提示
            return "<font color='grey'>无</font>"

        # 如果消息不包含堆栈，直接返回
        return message

    def _format_stack_trace(self, record: logging.LogRecord) -> str:
        """格式化堆栈追踪信息
        返回简洁的异常信息、函数位置和关键堆栈帧
        """
        import traceback

        # 优先使用 exc_info（如果通过 logger.exception 或 exc_info=True 记录）
        if record.exc_info:
            # 获取异常类型和消息
            exc_type, exc_value, exc_tb = record.exc_info
            exc_name = exc_type.__name__ if exc_type else "Unknown"
            exc_msg = str(exc_value) if exc_value else ""

            # 提取堆栈信息（限制行数，避免太长）
            tb_list = traceback.extract_tb(exc_tb)
            # 只显示最后几帧（最接近错误发生的位置）
            recent_frames = tb_list[-3:] if len(tb_list) > 3 else tb_list

            # 格式化堆栈帧
            frames_info = []
            for frame in recent_frames:
                frames_info.append(f"  File {frame.filename}, line {frame.lineno}, in {frame.name}\n    {frame.line}")

            # 组合输出
            parts = []

            # 如果有前面的帧被省略，先显示省略提示
            if len(tb_list) > 3:
                parts.append(f"  ... (省略 {len(tb_list) - 3} 个调用帧)")

            # 添加异常类型和消息
            parts.append(f"异常类型: {exc_name}")
            if exc_msg:
                parts.append(f"异常消息: {exc_msg}")

            # 添加堆栈帧
            if frames_info:
                parts.extend(frames_info)

            return "\n".join(parts)

        # 检查 exc_text（某些情况下格式化后的异常信息）
        if record.exc_text:
            return self._format_exc_text(record.exc_text)

        # 如果没有 exc_info，检查消息中是否包含堆栈信息
        message = record.getMessage()
        if self._contains_stack_trace(message):
            # 从消息中提取堆栈信息
            return self._extract_stack_from_message(message)

        return "无异常信息"

    def _format_exc_text(self, exc_text: str) -> str:
        """格式化 exc_text，只显示最后几帧"""
        lines = exc_text.split("\n")

        # 找到所有堆栈帧行（包含 "File " 的行）
        frame_lines = []
        for i, line in enumerate(lines):
            if 'File "' in line or "  File " in line:
                frame_lines.append(i)

        # 如果有堆栈帧，只保留最后3帧
        if len(frame_lines) > 3:
            # 获取最后3帧的起始和结束索引
            last_frames_start = frame_lines[-3]
            omitted_count = len(frame_lines) - 3

            # 构建结果
            result_lines = []
            # 添加省略提示
            result_lines.append(f"  ... (省略 {omitted_count} 个调用帧)")
            # 添加最后3帧的内容
            result_lines.extend(lines[last_frames_start:])
            return "\n".join(result_lines)

        # 如果堆栈帧不多于3个，直接返回原文
        return exc_text

    def _contains_stack_trace(self, message: str) -> bool:
        """检查消息是否包含堆栈追踪信息"""
        if not message:
            return False
        # 常见的堆栈特征
        stack_indicators = ["Traceback (most recent call last)", 'File "', "line ", "in ", "Error:", "Exception:"]
        return any(indicator in message for indicator in stack_indicators)

    def _extract_stack_from_message(self, message: str) -> str:
        """从消息中提取详细信息，只取最后几行信息"""
        # 如果没有完整的 Traceback，直接返回最后几行
        lines = message.split("\n")
        # 从后往前找，取最后5行，除去最后一行
        if len(lines) > 5:
            lines = lines[-5:-1]
        return "\n".join(lines)

    def _get_color_by_level(self, levelname: str) -> str:
        """根据日志级别返回卡片颜色"""
        color_map = {
            "CRITICAL": "red",
            "ERROR": "carmine",
            "WARNING": "yellow",
            "INFO": "blue",
            "DEBUG": "grey",
        }
        return color_map.get(levelname, "grey")

    def _get_header_icon_by_level(self, levelname: str) -> str:
        color_map = {
            "CRITICAL": "spam_outlined",
            "ERROR": "more-close_outlined",
            "WARNING": "warning_outlined",
            "INFO": "info_outlined",
            "DEBUG": "visible_outlined",
        }
        return color_map.get(levelname, "info_outlined")

    def _generate_sign(self, timestamp: str, secret: str) -> str:
        """生成飞书签名，文档：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot#3c6592d6"""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        return base64.b64encode(hmac_code).decode("utf-8")
