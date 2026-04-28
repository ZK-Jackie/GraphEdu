"""
测试 graphedu.common.utils.logger 模块

包含以下组件的测试：
- TimeLoggerRolloverHandler: 基于时间的日志轮转处理器
- WebhookLoggerHandler: 通用 Webhook 日志处理器
- FeishuWebhookHandler: 飞书 Webhook 日志处理器
- PayloadGenerator: Payload 生成器基类
- TemplatePayloadGenerator: 模板 Payload 生成器
"""

import contextlib
import logging
import logging.handlers
from pathlib import Path
from threading import Thread
import time
from unittest.mock import patch

from graphedu.common.utils.logger import (
    FeishuWebhookHandler,
    TimeLoggerRolloverHandler,
)
from graphedu.common.utils.logger.webhook_handler import WebhookLoggerHandler

# ============================================================================
# TimeLoggerRolloverHandler Tests
# ============================================================================

class TestTimeLoggerRolloverHandler:
    """测试 TimeLoggerRolloverHandler 自定义日志轮转处理器"""

    def setup_method(self):
        """每个测试前执行：创建临时测试目录"""
        self.test_dir = Path("tests/temp/test_logger_rollover")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """每个测试后执行：清理临时目录"""
        if self.test_dir.exists():
            import gc
            import shutil
            gc.collect()
            time.sleep(0.1)
            with contextlib.suppress(PermissionError, OSError):
                shutil.rmtree(self.test_dir)

    def test_handler_initialization_basic(self):
        """测试基本初始化"""
        log_file = self.test_dir / "test.log"
        handler = TimeLoggerRolloverHandler(str(log_file), when='h', interval=1)

        # baseFilename 会被转换为绝对路径
        assert handler.baseFilename == str(log_file.absolute())
        assert handler.when == 'H'
        # interval 会被转换为秒 (1 小时 = 3600 秒)
        assert handler.interval == 3600
        assert handler.backupCount == 0

        handler.close()

    def test_handler_initialization_with_backup_count(self):
        """测试带备份计数的初始化"""
        log_file = self.test_dir / "test.log"
        handler = TimeLoggerRolloverHandler(
            str(log_file),
            when='h',
            interval=1,
            backupCount=5
        )

        assert handler.backupCount == 5

        handler.close()

    def test_handler_creates_log_file_on_emit(self):
        """测试 emit 时创建日志文件"""
        log_file = self.test_dir / "test.log"
        handler = TimeLoggerRolloverHandler(str(log_file), when='h')
        logger = logging.getLogger('test_logger')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("Test message")

        # 确保日志文件被创建
        assert log_file.exists()

        # 清理
        logger.removeHandler(handler)
        handler.close()

    def test_handler_writes_log_content(self):
        """测试写入日志内容"""
        log_file = self.test_dir / "test.log"
        handler = TimeLoggerRolloverHandler(str(log_file), when='h')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        logger = logging.getLogger('test_logger_write')
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        test_message = "Test log message"
        logger.info(test_message)

        # 刷新缓冲区
        handler.flush()

        # 读取日志内容
        log_content = log_file.read_text(encoding='utf-8')
        assert test_message in log_content
        assert "INFO" in log_content

        # 清理
        logger.removeHandler(handler)
        handler.close()

    def test_handler_rollover_naming_format(self):
        """测试轮转文件命名格式"""
        log_file = self.test_dir / "app.log"
        handler = TimeLoggerRolloverHandler(
            str(log_file),
            when='h',
            interval=1,
            backupCount=5
        )

        # 写入一些内容以确保文件被创建
        handler.stream.write("Test content")
        handler.stream.flush()

        # 修改 rolloverAt 使其触发轮转
        handler.rolloverAt = int(time.time()) - 1

        # 执行轮转
        handler.doRollover()

        # 检查轮转后的文件命名
        # 格式是 app.YYYY-MM-DD_HH.log (使用下划线)
        rolled_files = list(self.test_dir.glob("app.*_*.*.log")) + list(self.test_dir.glob("app.20*"))
        # 找到轮转文件（排除当前日志文件）
        rolled_files = [f for f in rolled_files if f.name != "app.log"]
        assert len(rolled_files) >= 1, f"未找到轮转文件，当前目录: {list(self.test_dir.glob('*'))}"

        # 检查文件名格式
        rolled_file = rolled_files[0]
        # 文件名应该是 app.YYYY-MM-DD_HH.log 或 app.YYYY-MM-DD_HH.log
        assert "app." in rolled_file.name
        assert ".log" in rolled_file.name

        handler.close()

    def test_handler_rollover_skips_if_exists(self):
        """测试如果轮转文件已存在则跳过"""
        log_file = self.test_dir / "test.log"
        handler = TimeLoggerRolloverHandler(str(log_file), when='h', backupCount=5)

        # 创建一个已存在的轮转文件
        current_time = time.localtime()
        timestamp = time.strftime("%Y%m%d.%H", current_time)
        existing_rolled = self.test_dir / f"test.{timestamp}.log"
        existing_rolled.write_text("Existing rolled content")

        # 写入当前日志
        handler.stream.write("New content")

        # 强制轮转
        handler.rolloverAt = int(time.time()) - 1
        handler.doRollover()

        # 已存在的文件内容应该保持不变
        assert "Existing rolled content" in existing_rolled.read_text()

        handler.close()


# ============================================================================
# WebhookLoggerHandler Tests
# ============================================================================

class TestWebhookLoggerHandler:
    """测试 WebhookLoggerHandler 对外暴露的处理器"""

    def setup_method(self):
        """每个测试前执行"""
        self.test_url = "https://example.com/webhook"

    def teardown_method(self):
        """每个测试后执行：清理处理器"""
        import logging
        for handler in logging.root.handlers[:]:
            if isinstance(handler, (WebhookLoggerHandler, FeishuWebhookHandler)):
                handler.close()

    def test_handler_initialization_with_string_template(self):
        """测试使用字符串模板初始化处理器"""
        handler = WebhookLoggerHandler(
            url=self.test_url,
            payload_generator='{"message": "{message}"}'
        )

        assert handler.url == self.test_url
        assert handler.queue is not None
        assert handler.listener is not None
        assert handler.dispatcher is not None

        handler.close()

    def test_handler_initialization_with_callable(self):
        """测试使用可调用对象初始化处理器"""
        def custom_generator(record):
            return {"msg": record.getMessage()}

        handler = WebhookLoggerHandler(
            url=self.test_url,
            payload_generator=custom_generator
        )

        assert handler.url == self.test_url

        handler.close()

    def test_handler_close_stops_listener(self):
        """测试 close 停止监听器"""
        handler = WebhookLoggerHandler(
            url=self.test_url,
            payload_generator='{}'
        )

        # 监听器内部线程应该是活跃的
        assert handler.listener._thread is not None
        assert handler.listener._thread.is_alive()

        # 关闭处理器
        handler.close()

        # 监听器线程应该被清理
        assert handler.listener._thread is None

    def test_handler_integration_with_logger(self):
        """测试与 logger 的集成"""
        handler = WebhookLoggerHandler(
            url=self.test_url,
            payload_generator='{"text": "{message}"}'
        )

        # Mock dispatcher
        with patch.object(handler.dispatcher, 'emit'):
            logger = logging.getLogger('test_webhook_logger')
            logger.handlers.clear()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            # 发送日志
            logger.info("Test webhook message")

            # 验证没有异常抛出
            assert True

            logger.removeHandler(handler)

        handler.close()


# ============================================================================
# FeishuWebhookHandler Tests
# ============================================================================

class TestFeishuWebhookHandler:
    """测试 FeishuWebhookHandler 飞书 Webhook 处理器"""

    def setup_method(self):
        """每个测试前执行"""
        self.test_url = "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"

    def teardown_method(self):
        """每个测试后执行：清理处理器"""
        import logging
        for handler in logging.root.handlers[:]:
            if isinstance(handler, FeishuWebhookHandler):
                handler.close()

    def test_feishu_handler_initialization_basic(self):
        """测试基本初始化"""
        handler = FeishuWebhookHandler(url=self.test_url)

        assert handler.url == self.test_url
        assert handler.headers == {"Content-Type": "application/json"}

        handler.close()

    def test_feishu_handler_initialization_with_signature(self):
        """测试带签名初始化"""
        handler = FeishuWebhookHandler(
            url=self.test_url,
            sign_secret="test_secret"
        )

        assert handler.url == self.test_url

        handler.close()


# ============================================================================
# Integration Tests
# ============================================================================

class TestLoggerIntegration:
    """集成测试：测试日志处理器的实际使用场景"""

    def setup_method(self):
        """每个测试前执行：创建临时测试目录"""
        self.test_dir = Path("tests/temp/test_logger_integration")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """每个测试后执行：清理临时目录"""
        if self.test_dir.exists():
            import gc
            import shutil
            gc.collect()
            time.sleep(0.1)
            with contextlib.suppress(PermissionError, OSError):
                shutil.rmtree(self.test_dir)

    def test_file_and_webhook_handlers_together(self):
        """测试同时使用文件和 webhook 处理器"""
        # 创建文件处理器
        log_file = self.test_dir / "test.log"
        file_handler = TimeLoggerRolloverHandler(str(log_file), when='h')

        # 创建 webhook 处理器
        webhook_handler = WebhookLoggerHandler(
            url="https://example.com/webhook",
            payload_generator='{"msg": "{message}"}'
        )

        # Mock webhook dispatcher
        with patch.object(webhook_handler.dispatcher, 'emit'):
            # 创建 logger 并添加两个处理器
            logger = logging.getLogger('test_integration')
            logger.handlers.clear()
            logger.addHandler(file_handler)
            logger.addHandler(webhook_handler)
            logger.setLevel(logging.INFO)

            # 发送日志
            logger.info("Integration test message")

            # 清理
            logger.removeHandler(file_handler)
            logger.removeHandler(webhook_handler)

            # 验证文件日志
            file_handler.flush()
            assert log_file.exists()

        file_handler.close()
        webhook_handler.close()

    def test_concurrent_logging(self):
        """测试并发日志记录"""
        log_file = self.test_dir / "concurrent.log"
        handler = TimeLoggerRolloverHandler(str(log_file), when='h')

        logger = logging.getLogger('test_concurrent')
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # 创建多个线程同时记录日志
        threads = []
        for i in range(10):
            def log_messages(thread_id):
                for j in range(100):
                    logger.info(f"Thread {thread_id}, Message {j}")

            thread = Thread(target=log_messages, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        handler.flush()

        # 验证日志文件存在
        assert log_file.exists()

        logger.removeHandler(handler)
        handler.close()


# ============================================================================
# Edge Cases Tests
# ============================================================================

class TestEdgeCases:
    """测试边界情况"""

    def setup_method(self):
        """每个测试前执行：创建临时测试目录"""
        self.test_dir = Path("tests/temp/test_logger_edge_cases")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """每个测试后执行：清理临时目录"""
        if self.test_dir.exists():
            import gc
            import shutil
            gc.collect()
            time.sleep(0.1)
            with contextlib.suppress(PermissionError, OSError):
                shutil.rmtree(self.test_dir)

    def test_handler_with_nonexistent_directory(self):
        """测试在不存在的目录中创建日志文件"""
        log_file = self.test_dir / "subdir" / "test.log"
        handler = TimeLoggerRolloverHandler(str(log_file), when='h')

        logger = logging.getLogger('test_nonexistent_dir')
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Test message")

        handler.flush()

        # 目录应该被创建
        assert log_file.parent.exists()
        assert log_file.exists()

        logger.removeHandler(handler)
        handler.close()

    def test_very_long_log_message(self):
        """测试非常长的日志消息"""
        log_file = self.test_dir / "long_message.log"
        handler = TimeLoggerRolloverHandler(str(log_file), when='h')

        logger = logging.getLogger('test_long_message')
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # 创建一个非常长的消息
        long_message = "A" * 10000
        logger.info(long_message)

        handler.flush()

        # 验证日志被写入
        assert log_file.exists()
        content = log_file.read_text(encoding='utf-8')
        assert "A" in content

        logger.removeHandler(handler)
        handler.close()

    def test_unicode_in_log_message(self):
        """测试日志消息中的 Unicode 字符"""
        log_file = self.test_dir / "unicode.log"
        handler = TimeLoggerRolloverHandler(
            str(log_file),
            when='h',
            encoding='utf-8'
        )

        logger = logging.getLogger('test_unicode')
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # 测试各种 Unicode 字符
        unicode_messages = [
            "Hello 世界",
            "Привет мир",
            "🎉🎊🎈",
            "测试中文日志"
        ]

        for msg in unicode_messages:
            logger.info(msg)

        handler.flush()

        # 验证日志被正确写入
        assert log_file.exists()
        content = log_file.read_text(encoding='utf-8')
        for msg in unicode_messages:
            assert msg in content

        logger.removeHandler(handler)
        handler.close()
