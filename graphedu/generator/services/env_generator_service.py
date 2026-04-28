"""环境变量生成服务

基于模板从 YAML 配置生成 .env 文件，专供 Docker Compose 使用。

主要功能:
    - 加载 YAML 配置文件
    - 基于模板选择性导出环境变量
    - 支持模板插值语法 ${path.to.config}
    - 支持默认值 ${path:default}
    - 支持 DSN 组件提取 ${datasource.postgresql.dsn.username}
    - 支持敏感字段脱敏

模板语法:
    - ${config.path}：引用配置值
    - ${config.path:default}：带默认值的引用
    - ${datasource.postgresql.dsn.username}：从 DSN 中提取用户名
    - # 开头的行会被保留为注释

使用方式:
    from graphedu.generator.services import EnvGeneratorService

    generator = EnvGeneratorService(config_file="dev.config.yaml")
    generator.load_template()
    generator.generate_env_file(output_path=Path("docker/.env"))
"""

import json
import logging
from pathlib import Path
import re
from typing import Any
from urllib.parse import unquote, urlparse

from pydantic import BaseModel

from graphedu.common import load_config

logger = logging.getLogger(__name__)

# 敏感字段关键词
SENSITIVE_KEYWORDS = [
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "accesskey",
    "private_key",
    "privatekey",
]

# 匹配 ${path.to.config} 或 ${path:default}
VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")

# DSN 可提取的组件后缀
_DSN_COMPONENTS = frozenset({
    "username", "password", "hostname", "port", "database",
    "db",  # Redis 的数据库编号
})


def get_builtin_template_path() -> Path:
    """获取内置模板文件路径"""
    import graphedu

    module_dir = Path(graphedu.__file__).parent
    return module_dir / "generator" / "templates" / "env" / ".env.template"


def _extract_dsn_component(dsn_str: str, component: str) -> str | None:
    """从 DSN 字符串中提取指定组件。

    Args:
        dsn_str: DSN 字符串，如 'postgresql://user:pass@host:5432/dbname'
        component: 要提取的组件名

    Returns:
        提取到的值，无法提取则返回 None
    """
    parsed = urlparse(dsn_str)
    mapping: dict[str, str | None] = {
        "username": parsed.username,
        "password": parsed.password,
        "hostname": parsed.hostname,
        "port": str(parsed.port) if parsed.port else None,
        "database": unquote(parsed.path.lstrip("/")) if parsed.path else None,
        "db": unquote(parsed.path.lstrip("/")) if parsed.path else None,
    }
    value = mapping.get(component)
    if value is not None:
        return value
    return None


class EnvGeneratorService:
    """环境变量生成服务

    职责：
    1. 加载 YAML 配置
    2. 读取模板文件
    3. 解析模板变量（${path.to.config}）
    4. 从配置中获取值（支持 DSN 组件提取）
    5. 生成最终的 .env 文件
    """

    def __init__(
        self,
        config_file: str | None = None,
        template_path: str | None = None,
        sensitive_fields: list[str] | None = None,
    ):
        self.config_file = config_file
        self.template_path = template_path
        self.sensitive_fields = sensitive_fields or SENSITIVE_KEYWORDS
        self.template: str | None = None
        self.config: BaseModel | None = load_config(config_file)

    # ------------------------------------------------------------------
    # 模板加载
    # ------------------------------------------------------------------

    def load_template(self) -> str:
        """加载模板文件。

        优先使用构造时传入的 template_path，否则使用内置模板。

        Returns:
            模板内容

        Raises:
            FileNotFoundError: 模板文件不存在
        """
        path = Path(self.template_path) if self.template_path else get_builtin_template_path()

        if not path.exists():
            raise FileNotFoundError(f"模板文件不存在: {path}")

        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.template = content
        logger.info("成功加载模板: %s", path)
        return content

    # ------------------------------------------------------------------
    # 模板解析
    # ------------------------------------------------------------------

    def parse_template(self, template: str | None = None) -> list[str]:
        """解析模板，提取所有变量引用路径。

        Args:
            template: 模板内容，为 None 则使用已加载的模板

        Returns:
            变量路径列表
        """
        content = template or self.template
        if content is None:
            raise ValueError("模板未加载")
        variables: list[str] = []
        for match in VAR_PATTERN.finditer(content):
            path = match.group(1)
            if path not in variables:
                variables.append(path)
        return variables

    # ------------------------------------------------------------------
    # 配置值获取
    # ------------------------------------------------------------------

    def get_config_value(self, path: str) -> Any:
        """从配置中获取指定路径的值。

        支持两种模式：
        - 普通路径：`datasource.postgresql.echo` → 遍历嵌套 dict
        - DSN 组件提取：`datasource.postgresql.dsn.username` → 先取 DSN 字符串，再解析

        使用 model_dump(mode='json') 确保所有 Pydantic 特殊类型（PostgresDsn、
        RedisDsn、AnyHttpUrl 等）被序列化为纯字符串。

        Args:
            path: 点号分隔的配置路径

        Returns:
            配置值；路径不存在或组件无法提取时返回 None
        """
        if self.config is None:
            return None

        # 使用 mode='json' 确保 URL 类型被序列化为字符串
        current: Any = self.config.model_dump(mode="json")

        parts = path.split(".")

        for i, part in enumerate(parts):
            # 检查是否是 DSN 组件提取模式：当前值是字符串且下一个 part 是已知组件名
            if (
                isinstance(current, str)
                and i == len(parts) - 1
                and part in _DSN_COMPONENTS
                and i > 0
                and parts[i - 1] == "dsn"
            ):
                return _extract_dsn_component(current, part)

            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        # 到达末尾，但如果最后一个 part 本身是 DSN 组件关键字，需要额外处理
        # 这种情况不会发生（上面的循环已经处理），但保留安全检查
        return current

    # ------------------------------------------------------------------
    # 值转换 & 脱敏
    # ------------------------------------------------------------------

    @staticmethod
    def _value_to_string(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, list):
            # 纯字符串列表用逗号分隔（如 profiles），否则用 JSON
            if all(isinstance(v, str) for v in value):
                return ",".join(value)
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        if value is None:
            return ""
        return str(value)

    def _is_sensitive_field(self, path: str) -> bool:
        # 只检查路径的叶子字段名，避免 security.token.expire 被 token 误判
        leaf = path.rsplit(".", 1)[-1].lower()
        return any(kw in leaf for kw in self.sensitive_fields)

    @staticmethod
    def _mask_value(value: str) -> str:
        if len(value) <= 8:
            return "*" * len(value)
        return value[:4] + "*" * (len(value) - 8) + value[-4:]

    # ------------------------------------------------------------------
    # 模板渲染
    # ------------------------------------------------------------------

    def render_template(self, mask_sensitive: bool = False) -> str:
        """渲染模板，替换所有变量引用。

        Args:
            mask_sensitive: 是否脱敏敏感信息

        Returns:
            渲染后的内容

        Raises:
            ValueError: 模板或配置未加载
        """
        if self.template is None or self.config is None:
            raise ValueError("模板和配置必须先加载")

        def replace_var(match: re.Match[str]) -> str:
            path = match.group(1)
            default = match.group(2)

            value = self.get_config_value(path)

            if value is None:
                return default if default is not None else ""

            str_value = self._value_to_string(value)

            if mask_sensitive and self._is_sensitive_field(path):
                str_value = self._mask_value(str_value)

            return str_value

        return VAR_PATTERN.sub(replace_var, self.template)

    # ------------------------------------------------------------------
    # 文件生成
    # ------------------------------------------------------------------

    def generate_env_file(self, output_path: Path, mask: bool = False) -> dict[str, str]:
        """生成 .env 文件。

        Args:
            output_path: 输出文件路径
            mask: 是否脱敏敏感信息

        Returns:
            生成的环境变量字典
        """
        if self.template is None:
            self.load_template()

        rendered = self.render_template(mask_sensitive=mask)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)

        logger.info("成功生成 .env 文件: %s", output_path)

        env_dict: dict[str, str] = {}
        for line in rendered.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_dict[key.strip()] = value.strip()

        return env_dict
