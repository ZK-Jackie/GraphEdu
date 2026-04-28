import typer

from graphedu.common.config.manager import load_config
from graphedu.common.models.bo.cli import TyperContext

context = TyperContext()


def global_param(
    ctx: typer.Context,
    config: str | None = typer.Option(None, "--config", "-c", help="配置文件路径（默认自动发现）", case_sensitive=True),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="启用详细输出"),
):
    """全局参数

    Args:
        ctx: Typer 上下文对象
        config: 配置文件路径，None 则按优先级自动发现（prod > dev > *.config.yaml > config.yaml）
        verbose: 是否启用详细输出，默认为 False

    See Also:
        https://typer.tiangolo.com/tutorial/commands/callback/?h=call#typer-callback
    """
    # 全局存储
    context["config"] = config
    context["verbose"] = verbose
    # 初始化项目配置和日志
    mode = ctx.invoked_subcommand if ctx.invoked_subcommand else "unknown"
    load_config(config, running_mode=mode, init_logging=True)
