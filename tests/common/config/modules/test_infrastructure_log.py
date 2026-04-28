"""测试日志配置。"""

import pytest

from graphedu.common.config.modules.infrastructure import LogConfig


class TestLogConfig:
    """测试 LogConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = LogConfig()

        assert config.description is None
        # LogConfig 允许额外字段
        assert hasattr(config, "model_dump")

    def test_description_default_none(self):
        """测试 description 默认为 None。"""
        config = LogConfig()

        assert config.description is None

    def test_custom_description(self):
        """测试自定义描述。"""
        config = LogConfig(description="Production logging configuration")

        assert config.description == "Production logging configuration"

    def test_description_empty_string(self):
        """测试空描述。"""
        config = LogConfig(description="")

        assert config.description == ""

    def test_extra_fields_allowed(self):
        """测试允许额外字段（extra='allow'）。"""
        # LogConfig 设置了 extra="allow"，应该允许额外字段
        config_data = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO"
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["console"]
            }
        }

        config = LogConfig(**config_data)

        # 验证额外字段被保留
        assert config.version == 1
        assert config.disable_existing_loggers is False
        assert "formatters" in config.model_dump()
        assert "handlers" in config.model_dump()

    def test_get_dict_config_empty(self):
        """测试获取空配置的字典。"""
        config = LogConfig()

        dict_config = config.get_dict_config()

        # description 应该被排除
        assert "description" not in dict_config

    def test_get_dict_config_with_description(self):
        """测试带 description 的配置获取字典。"""
        config = LogConfig(
            description="Test config",
            version=1,
            disable_existing_loggers=False
        )

        dict_config = config.get_dict_config()

        # description 应该被排除
        assert "description" not in dict_config
        # 其他字段应该保留
        assert dict_config.get("version") == 1
        assert dict_config.get("disable_existing_loggers") is False

    def test_get_dict_config_with_logging_fields(self):
        """测试带日志字段的配置获取字典。"""
        config = LogConfig(
            version=1,
            disable_existing_loggers=False,
            formatters={
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            handlers={
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "default"
                }
            },
            loggers={
                "graphedu": {
                    "level": "DEBUG",
                    "handlers": ["console"]
                }
            }
        )

        dict_config = config.get_dict_config()

        # 验证所有日志配置字段被保留
        assert dict_config["version"] == 1
        assert dict_config["disable_existing_loggers"] is False
        assert "formatters" in dict_config
        assert "handlers" in dict_config
        assert "loggers" in dict_config
        assert "description" not in dict_config

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = LogConfig(
            description="Test",
            version=1
        )

        config_dict = config.model_dump()

        assert config_dict["description"] == "Test"
        assert config_dict["version"] == 1

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = LogConfig(
            description="Test config",
            version=1
        )

        json_str = config.model_dump_json()

        assert "Test config" in json_str

    def test_complex_logging_config(self):
        """测试复杂的日志配置。"""
        config = LogConfig(
            version=1,
            disable_existing_loggers=False,
            formatters={
                "verbose": {
                    "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
                },
                "simple": {
                    "format": "%(levelname)s %(message)s"
                }
            },
            handlers={
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "simple",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "verbose",
                    "filename": "logs/app.log",
                    "maxBytes": 10485760,
                    "backupCount": 5
                }
            },
            loggers={
                "graphedu": {
                    "level": "DEBUG",
                    "handlers": ["console", "file"],
                    "propagate": False
                }
            },
            root={
                "level": "WARNING",
                "handlers": ["console"]
            }
        )

        dict_config = config.get_dict_config()

        # 验证复杂配置结构
        assert "verbose" in dict_config["formatters"]
        assert "simple" in dict_config["formatters"]
        assert "console" in dict_config["handlers"]
        assert "file" in dict_config["handlers"]
        assert "graphedu" in dict_config["loggers"]
        assert dict_config["loggers"]["graphedu"]["level"] == "DEBUG"
        assert "description" not in dict_config

    def test_multiple_handlers(self):
        """测试多个处理器。"""
        config = LogConfig(
            version=1,
            handlers={
                "console": {"class": "logging.StreamHandler"},
                "file": {"class": "logging.FileHandler", "filename": "app.log"},
                "syslog": {"class": "logging.handlers.SysLogHandler"}
            }
        )

        dict_config = config.get_dict_config()

        assert len(dict_config["handlers"]) == 3

    def test_multiple_loggers(self):
        """测试多个日志记录器。"""
        config = LogConfig(
            version=1,
            loggers={
                "graphedu": {"level": "DEBUG"},
                "uvicorn": {"level": "INFO"},
                "sqlalchemy": {"level": "WARNING"}
            }
        )

        dict_config = config.get_dict_config()

        assert len(dict_config["loggers"]) == 3
        assert "graphedu" in dict_config["loggers"]
        assert "uvicorn" in dict_config["loggers"]
        assert "sqlalchemy" in dict_config["loggers"]

    def test_dict_config_for_logging_dictconfig(self):
        """测试生成的字典可用于 logging.config.dictConfig。"""
        config = LogConfig(
            version=1,
            disable_existing_loggers=False,
            formatters={
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            handlers={
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "default"
                }
            },
            root={
                "level": "INFO",
                "handlers": ["console"]
            }
        )

        dict_config = config.get_dict_config()

        # 验证必需的字段存在
        assert "version" in dict_config
        assert "formatters" in dict_config
        assert "handlers" in dict_config
        assert "root" in dict_config

    def test_description_only_documentation(self):
        """测试 description 字段仅用于文档。"""
        config1 = LogConfig(description="Config A", version=1)
        config2 = LogConfig(description="Config B", version=1)

        # description 不影响功能配置
        dict1 = config1.get_dict_config()
        dict2 = config2.get_dict_config()

        assert dict1 == dict2

    def test_exclude_description_in_dump(self):
        """测试 model_dump 不排除 description（由调用方控制）。"""
        config = LogConfig(
            description="Test",
            version=1
        )

        # 默认 model_dump 包含所有字段
        config_dict = config.model_dump()
        assert "description" in config_dict

        # get_dict_config 排除 description
        dict_config = config.get_dict_config()
        assert "description" not in dict_config
