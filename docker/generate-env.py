#!/usr/bin/env python3
"""GraphEdu Docker .env 独立生成脚本

此脚本可完全独立运行，无需安装 graphedu 包，仅需 Python 3.12+ 和 PyYAML。
用于从 YAML 配置文件生成 Docker Compose 所需的 .env 文件。

用法:
    # 默认：自动发现配置文件，输出到 docker/.env
    python3 docker/generate-env.py

    # 指定配置文件和输出路径
    python3 docker/generate-env.py -c prod.config.yaml -o docker/.env

    # 脱敏输出（打印到终端，用于分享）
    python3 docker/generate-env.py --mask

    # 列出模板变量
    python3 docker/generate-env.py --list
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    import yaml
except ImportError:
    print("错误：需要 PyYAML。安装命令：pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# 内置模板
# 注意：更新模板时需同步更新 graphedu/generator/templates/env/.env.template
# ---------------------------------------------------------------------------
BUILTIN_TEMPLATE = """\
# ========================================
# GraphEdu Docker Compose 环境变量
# 此文件由 generate-env.py 独立生成
# 变量语法：path.to.config 或 path.to.config:default_value
# ========================================

# ========================================
# Docker Compose Profiles（控制需要部署的服务）
# ========================================
COMPOSE_PROFILES=${deploy.profiles}

# ========================================
# PostgreSQL 镜像初始化配置
# ========================================
POSTGRES_USER=${datasource.postgresql.dsn.username}
POSTGRES_PASSWORD=${datasource.postgresql.dsn.password}
POSTGRES_DB=${datasource.postgresql.dsn.database}

# ========================================
# 端口配置
# ========================================
FRONTEND_PORT=11334

# ========================================
# Docker 镜像版本
# ========================================
POSTGRES_VERSION=${deploy.images.postgres:18.3.0}
REDIS_VERSION=${deploy.images.redis:8.6.2-alpine}
BACKEND_VERSION=${deploy.images.backend:latest}
FRONTEND_VERSION=${deploy.images.frontend:latest}

# ========================================
# Docker 构建参数（镜像源加速）
# ========================================
APT_MIRROR=${deploy.build.apt_mirror:mirrors.aliyun.com}
NPM_REGISTRY=${deploy.build.npm_registry:}
UV_INDEX_URL=${deploy.build.uv_index:https://mirrors.aliyun.com/pypi/simple}
GITHUB_PROXY=${deploy.build.github_proxy:https://gh-proxy.org}
"""

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
# 匹配 ${path.to.config} 或 ${path:default}
VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")

# DSN 可提取的组件后缀
DSN_COMPONENTS = frozenset({"username", "password", "hostname", "port", "database", "db"})

# 敏感字段关键词
SENSITIVE_KEYWORDS = [
    "password", "secret", "token", "api_key", "apikey",
    "access_key", "accesskey", "private_key", "privatekey",
]


# ---------------------------------------------------------------------------
# 核心函数
# ---------------------------------------------------------------------------
def extract_dsn_component(dsn_str: str, component: str) -> str | None:
    """从 DSN 字符串中提取指定组件"""
    parsed = urlparse(dsn_str)
    mapping: dict[str, str | None] = {
        "username": parsed.username,
        "password": parsed.password,
        "hostname": parsed.hostname,
        "port": str(parsed.port) if parsed.port else None,
        "database": unquote(parsed.path.lstrip("/")) if parsed.path else None,
        "db": unquote(parsed.path.lstrip("/")) if parsed.path else None,
    }
    return mapping.get(component)


def get_nested_value(data: dict, path: str):
    """从嵌套字典中获取值，支持 DSN 组件提取"""
    parts = path.split(".")
    current = data

    for i, part in enumerate(parts):
        # DSN 组件提取：路径末尾是 .dsn.<component>
        if (
            isinstance(current, str)
            and i == len(parts) - 1
            and part in DSN_COMPONENTS
            and i > 0
            and parts[i - 1] == "dsn"
        ):
            return extract_dsn_component(current, part)

        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


def value_to_string(value) -> str:
    """将任意 Python 值转为 .env 兼容字符串"""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        if all(isinstance(v, str) for v in value):
            return ",".join(value)
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)


def is_sensitive(path: str) -> bool:
    """判断路径叶子字段是否为敏感字段"""
    leaf = path.rsplit(".", 1)[-1].lower()
    return any(kw in leaf for kw in SENSITIVE_KEYWORDS)


def mask_value(value: str) -> str:
    """对敏感值做脱敏处理"""
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


# ---------------------------------------------------------------------------
# 配置发现
# ---------------------------------------------------------------------------
def discover_config(project_dir: Path) -> Path | None:
    """在项目根目录自动发现配置文件"""
    for name in ("prod.config.yaml", "dev.config.yaml"):
        p = project_dir / name
        if p.exists():
            return p
    for p in project_dir.glob("*.config.yaml"):
        return p
    return None


def load_config(config_path: Path) -> dict:
    """加载 YAML 配置文件"""
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not config:
        print("错误：配置文件为空", file=sys.stderr)
        sys.exit(1)
    return config


# ---------------------------------------------------------------------------
# 模板渲染
# ---------------------------------------------------------------------------
def render_template(template: str, config: dict, *, mask: bool = False) -> str:
    """渲染模板，替换所有 ${path} 和 ${path:default} 变量"""

    def replace_var(match: re.Match[str]) -> str:
        path = match.group(1)
        default = match.group(2)

        value = get_nested_value(config, path)
        if value is None:
            return default if default is not None else ""

        str_value = value_to_string(value)
        if mask and is_sensitive(path):
            str_value = mask_value(str_value)
        return str_value

    return VAR_PATTERN.sub(replace_var, template)


def parse_template_variables(template: str) -> list[str]:
    """提取模板中所有变量路径（去重保序）"""
    seen: set[str] = set()
    variables: list[str] = []
    for m in VAR_PATTERN.finditer(template):
        path = m.group(1)
        if path not in seen:
            seen.add(path)
            variables.append(path)
    return variables


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def resolve_project_dir() -> Path:
    """根据脚本位置推断项目根目录"""
    script_dir = Path(__file__).resolve().parent
    # 脚本在 docker/ 子目录中，上一级就是项目根
    return script_dir.parent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GraphEdu Docker .env 独立生成脚本（无需 graphedu 包）",
    )
    parser.add_argument("-c", "--config", help="配置文件路径（默认自动发现）")
    parser.add_argument("-t", "--template", help="模板文件路径（默认使用内置模板）")
    parser.add_argument("-o", "--output", default="docker/.env", help="输出文件路径（默认: docker/.env）")
    parser.add_argument("--mask", action="store_true", help="脱敏敏感信息并输出到终端")
    parser.add_argument("-l", "--list", action="store_true", help="列出模板中的所有变量")
    args = parser.parse_args()

    project_dir = resolve_project_dir()
    script_dir = Path(__file__).resolve().parent

    # --- 加载模板 ---
    if args.template:
        template = Path(args.template).read_text(encoding="utf-8")
    else:
        # 优先读取仓库中的模板文件（开发时自动同步）
        repo_template = project_dir / "graphedu" / "generator" / "templates" / "env" / ".env.template"
        if repo_template.exists():
            template = repo_template.read_text(encoding="utf-8")
        else:
            template = BUILTIN_TEMPLATE

    # --- 列出变量 ---
    if args.list:
        variables = parse_template_variables(template)
        for var in sorted(variables):
            print(f"  - ${{{var}}}")
        print(f"共 {len(variables)} 个变量")
        return

    # --- 发现配置文件 ---
    if args.config:
        config_path = Path(args.config).resolve()
    else:
        config_path = discover_config(project_dir)
        if not config_path:
            print("错误：未找到配置文件，请使用 -c 指定", file=sys.stderr)
            sys.exit(1)
        config_path = config_path.resolve()

    config = load_config(config_path)
    print(f"配置文件: {config_path}")

    # --- 渲染 ---
    rendered = render_template(template, config, mask=args.mask)

    if args.mask:
        print(rendered)
    else:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = project_dir / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"已生成: {output_path}")


if __name__ == "__main__":
    main()
