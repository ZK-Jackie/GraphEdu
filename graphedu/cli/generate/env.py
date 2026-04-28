"""Generate Env 环境变量生成命令模块

基于 YAML 配置生成 .env 文件，供 Docker Compose 使用。

常用示例:
    # 使用默认配置生成 docker/.env
    uv run -m graphedu generate env

    # 指定配置文件
    uv run -m graphedu generate env -c prod.config.yaml

    # 使用自定义模板
    uv run -m graphedu generate env --template .env.custom

    # 脱敏生成（用于分享）
    uv run -m graphedu generate env --mask

    # 列出模板变量
    uv run -m graphedu generate env --list
"""

import logging
from pathlib import Path

import typer

from graphedu.generator.services import EnvGeneratorService

logger = logging.getLogger(__name__)


def generate_env(
    config: str | None = typer.Option(None, "--config", "-c", help="配置文件路径（默认自动发现）"),
    template: str = typer.Option(None, "--template", "-t", help="模板文件路径（默认使用内置模板）"),
    output: str = typer.Option("docker/.env", "--output", "-o", help="输出文件路径"),
    mask: bool = typer.Option(False, "--mask", help="脱敏敏感信息"),
    list_vars: bool = typer.Option(False, "--list", "-l", help="列出模板中的所有变量"),
) -> None:
    """基于模板生成 .env 文件"""
    try:
        service = EnvGeneratorService(config_file=config, template_path=template)
        service.load_template()

        if list_vars:
            variables = service.parse_template()
            for var in sorted(variables):
                typer.echo(f"  - ${{{var}}}")
            typer.echo(f"共 {len(variables)} 个变量")
            return

        if mask:
            rendered = service.render_template(mask_sensitive=True)
            typer.echo(rendered)
        else:
            output_path = Path(output)
            env_dict = service.generate_env_file(output_path, mask=False)
            logger.info("环境变量文件已生成: %s (%d 个变量)", output_path, len(env_dict))

    except typer.Exit:
        raise
    except Exception as e:
        logger.error("Error: %s", e)
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    typer.run(generate_env)
