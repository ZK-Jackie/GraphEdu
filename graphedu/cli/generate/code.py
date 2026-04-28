"""Generate Code 代码生成命令模块

本模块提供从数据库表结构生成代码的功能。

生成内容:
    - ORM 实体（SQLAlchemy）- 数据库实体类
    - DTO 模型（Data Transfer Object）- API 数据传输对象
    - VO 模型（View Object）- API 响应模型
    - Mapper 层 - 数据访问层（Repository 模式）
    - Service 层 - 业务逻辑层
    - API 接口 - FastAPI 路由控制器

代码架构:
    生成的代码遵循项目分层架构:

    graphedu/
    ├── api/services/{domain}/     # API 控制器层
    │   └── {module}.py            # FastAPI 路由
    ├── services/{domain}/         # 业务逻辑层
    │   └── {module}.py            # Service 类
    ├── mapper/                    # 数据访问层
    │   └── {module}.py            # Mapper 类
    └── common/models/             # 数据模型
        ├── orm/{domain}.py        → 手动合并 ORM 实体
        ├── dto/{module}.py        # DTO 模型
        └── vo/{module}.py         # VO 模型

主要命令:
    model      生成 ORM 模型（从数据库表结构）
    crud       生成完整 CRUD 代码（包含所有层）
    list       列出所有可用的代码生成模板

常用示例:
    # 生成 ORM 模型（输出到当前目录）
    uv run -m graphedu generate code model edu_course
    uv run -m graphedu generate code model edu_course -m course

    # 生成完整 CRUD 代码
    uv run -m graphedu generate code crud course
    uv run -m graphedu generate code crud student --table edu_student
    uv run -m graphedu generate code crud teacher --no-api

    # 列出模板
    uv run -m graphedu generate code list

生成规则:
    1. 模块名: 通常使用单数形式（如 course, student）
    2. 表名: 默认添加前缀（如 edu_course, sys_user）
    3. ORM 实体使用完整表名驼峰（如 EduCourse），生成后需手动合并到对应领域文件
    4. DTO 模型包含:
       - {Module}QueryDTO (查询参数)
       - {Module}CreateDTO (创建请求)
       - {Module}UpdateDTO (更新请求)
    5. VO 模型包含:
       - {Module}ListVO (列表项)
       - {Module}DetailVO (详情)
    6. Mapper 提供 CRUD 基础方法
    7. Service 提供业务逻辑封装
    8. API 提供 RESTful 接口

退出码:
    0    成功
    1    错误或失败
"""

import logging
from pathlib import Path

import typer

code_app = typer.Typer(help="从数据库表结构生成代码")
logger = logging.getLogger(__name__)


@code_app.command("model")
def generate_model_cmd(
    table_name: str = typer.Argument(..., help="数据库表名（如 edu_course, sys_user）"),
    module_name: str = typer.Option(None, "--module", "-m", help="模块名（默认从表名中提取）"),
    output_dir: str = typer.Option(".", "--output", "-o", help="输出根目录（默认为当前目录）"),
    overwrite: bool = typer.Option(False, "--overwrite", help="是否覆盖已存在的文件"),
    config: str = typer.Option("dev.config.yaml", "--config", "-c", help="配置文件路径"),
):
    """生成 ORM 实体模型（从数据库表结构）

    示例:

        # 生成 edu_course 表的 ORM 实体
        uv run -m graphedu generate code model edu_course

        # 指定模块名（影响输出文件的 businessName）
        uv run -m graphedu generate code model edu_course -m course

        # 指定输出目录（默认为项目根目录 .）
        uv run -m graphedu generate code model edu_course -o graphedu
    """
    from graphedu.generator.services.cli_generator import generate_model

    logger.info(f"Generating ORM model from table [{table_name}]...")
    if module_name is None:
        from graphedu.generator.core.gen_util import GenUtils

        module_name = GenUtils.get_module_from_table(table_name)

    try:
        generated = generate_model(
            table_name=table_name,
            module_name=module_name,
            output_root=output_dir,
            overwrite=overwrite,
            config_file=config,
        )

        if generated:
            logger.info("Code generation completed successfully")
            logger.info(f"Total {len(generated)} files generated:")
            for f in generated:
                logger.info(f"  {f}")
            logger.info(
                "Note: ORM files should be manually merged to the corresponding domain file "
                "(e.g., graphedu/common/models/orm/education.py)"
            )
        else:
            logger.warning("No files generated (files may already exist, use --overwrite to force)")

    except Exception as e:
        logger.debug("Model generation error", exc_info=True)
        logger.error(f"Error: {e}")
        raise typer.Exit(code=1) from None


@code_app.command("crud")
def generate_crud_cmd(
    module_name: str = typer.Argument(..., help="模块名称（如: course, student）"),
    table_name: str = typer.Option(None, "--table", "-t", help="数据库表名（默认为 edu_{module_name}）"),
    output_dir: str = typer.Option(".", "--output", "-o", help="输出根目录（默认为当前目录）"),
    with_api: bool = typer.Option(True, "--api/--no-api", help="是否生成 API Controller 层"),
    with_service: bool = typer.Option(True, "--service/--no-service", help="是否生成 Service 层"),
    with_mapper: bool = typer.Option(True, "--mapper/--no-mapper", help="是否生成 Mapper 层"),
    overwrite: bool = typer.Option(False, "--overwrite", help="是否覆盖已存在的文件"),
    config: str = typer.Option("dev.config.yaml", "--config", "-c", help="配置文件路径"),
):
    """生成完整的 CRUD 代码

    会根据数据库表结构自动生成 DTO、VO、Mapper、Service、API 各层代码。

    示例:

        # 生成 course 模块（表名默认为 edu_course）
        uv run -m graphedu generate code crud course

        # 指定表名
        uv run -m graphedu generate code crud student --table edu_student

        # 只生成 Mapper + Service，不生成 API
        uv run -m graphedu generate code crud teacher --no-api

        # 生成到指定目录并覆盖
        uv run -m graphedu generate code crud course -o . --overwrite
    """
    from graphedu.generator.services.cli_generator import generate_crud

    resolved_table = table_name or f"edu_{module_name}"

    components = []
    if with_mapper:
        components.append("Mapper")
    if with_service:
        components.append("Service")
    if with_api:
        components.append("API")
    components += ["DTO", "VO"]

    logger.info(
        f"Generating CRUD module [{module_name}] (table: {resolved_table}, components: {', '.join(components)})..."
    )

    try:
        generated = generate_crud(
            module_name=module_name,
            table_name=resolved_table,
            output_root=output_dir,
            overwrite=overwrite,
            with_api=with_api,
            with_service=with_service,
            with_mapper=with_mapper,
            config_file=config,
        )

        if generated:
            logger.info("Code generation completed successfully")
            logger.info(f"Total {len(generated)} files generated:")
            for f in generated:
                logger.info(f"  {f}")

            domain = _guess_domain(resolved_table)
            logger.info("Suggested next steps:")
            logger.info(f"  1. Register route in graphedu/api/service.py: {module_name}_controller")
            logger.info(f"  2. Confirm ORM entity is defined in graphedu/common/models/orm/{domain}.py")
            logger.info("  3. Add permission menu SQL in scripts (sys_function table)")
        else:
            logger.warning("No files generated (files may already exist, use --overwrite to force)")

    except Exception as e:
        logger.debug("CRUD generation error", exc_info=True)
        logger.error(f"Error: {e}")
        raise typer.Exit(code=1) from None


@code_app.command("list")
def list_templates():
    """List all available code generation templates

    Displays template names and their corresponding generation content and output path rules.
    """
    template_info: list[tuple[str, str]] = [
        ("python/orm.py.jinja2", "ORM entity (SQLAlchemy)           -> common/models/orm/{businessName}.py"),
        ("python/dto.py.jinja2", "DTO data transfer object          -> common/models/dto/{businessName}.py"),
        ("python/vo.py.jinja2", "VO view object                    -> common/models/vo/{businessName}.py"),
        ("python/mapper.py.jinja2", "Mapper data access layer          -> mapper/{businessName}.py"),
        ("python/service.py.jinja2", "Service business logic layer      -> services/{module}/{businessName}.py"),
        ("python/api.py.jinja2", "API controller                    -> api/services/{module}/{businessName}.py"),
        ("python/mapper-tree.py.jinja2", "Mapper (tree structure)           -> mapper/{businessName}.py"),
        ("python/service-tree.py.jinja2", "Service (tree structure)          -> services/{module}/{businessName}.py"),
        ("python/api-tree.py.jinja2", "API (tree structure)              -> api/services/{module}/{businessName}.py"),
        ("typescript/api.ts.jinja2", "TypeScript API interface          -> src/api/{module}/{businessName}.ts"),
        ("typescript/types.ts.jinja2", "TypeScript type declaration       -> src/types/api/{businessName}.ts"),
        ("locales/zh.json.jinja2", "Chinese i18n language pack        -> src/locales/{module}.{businessName}.zh.json"),
        ("locales/en.json.jinja2", "English i18n language pack        -> src/locales/{module}.{businessName}.en.json"),
        ("sql/sql.jinja2", "Menu SQL data                     -> sql/{businessName}_menu.sql"),
        (
            "vue/antd/index.vue.jinja2",
            "Vue page (Ant Design Vue)         -> src/views/{module}/{businessName}/index.vue",
        ),
        (
            "vue/antd/index-tree.vue.jinja2",
            "Vue page (tree structure)         -> src/views/{module}/{businessName}/index.vue",
        ),
    ]

    _tpl_root = Path(__file__).parent.parent.parent / "generator" / "templates"
    lines = ["Available code generation templates:"]
    for tpl, desc in template_info:
        exists = (_tpl_root / tpl).exists()
        status = "[OK]" if exists else "[TODO]"
        lines.append(f"  {status}  {tpl:<46}  {desc}")

    lines.extend(
        [
            "",
            "Quick generation commands:",
            "  uv run -m graphedu generate code model <table_name>   # Generate ORM model",
            "  uv run -m graphedu generate code crud  <module_name>  # Generate full CRUD",
        ]
    )

    logger.info("\n".join(lines))


def _get_domain_name(table_name: str) -> str:
    """从表名获取领域名称（用于 ORM 文件名）"""
    from graphedu.generator.core.gen_util import GenUtils

    return GenUtils.get_domain_from_table(table_name)


def _guess_domain(table_name: str) -> str:
    """根据表名推断领域名"""
    return _get_domain_name(table_name)


if __name__ == "__main__":
    typer.run(code_app)
