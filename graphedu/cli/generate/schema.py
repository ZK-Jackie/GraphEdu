"""生成 Pydantic 模型 JSON Schema 命令模块"""

import logging

import typer

from graphedu.generator.services import SchemaGeneratorService

logger = logging.getLogger(__name__)


def settings_schema_main(
    class_path: str = typer.Argument(None, help="Pydantic 类路径或快捷方式"),
    output: str = typer.Option(None, "--output", "-o", help="输出路径（默认 .generated 目录）"),
    pretty: bool = typer.Option(True, "--pretty/--no-pretty", help="是否格式化 JSON"),
    list: bool = typer.Option(False, "--list", "-l", help="列出快捷方式"),
) -> None:
    """生成 Pydantic 模型的 JSON Schema

    示例:
        uv run -m graphedu generate schema service
        uv run -m graphedu generate schema service --output ./schemas/
        uv run -m graphedu generate schema --list
    """
    service = SchemaGeneratorService()

    if list:
        for shortcut, full_path in service.list_shortcuts().items():
            logger.info(f"  {shortcut} -> {full_path}")
        raise typer.Exit(0)

    if class_path is None:
        logger.error("Error: Class path required (use --list to view shortcuts)")
        raise typer.Exit(1)

    try:
        service.generate_schema(class_path=class_path, output_path=output, pretty=pretty)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    typer.run(settings_schema_main)
