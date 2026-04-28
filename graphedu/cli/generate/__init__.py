"""Generate 子命令模块"""

from typer import Typer

from graphedu.cli.generate.code import code_app
from graphedu.cli.generate.env import generate_env
from graphedu.cli.generate.schema import settings_schema_main

generate_app = Typer(help="代码生成工具（code/env/schema）")
generate_app.add_typer(code_app, name="code")
generate_app.command(name="env")(generate_env)
generate_app.command(name="schema")(settings_schema_main)

__all__ = ["generate_app"]
