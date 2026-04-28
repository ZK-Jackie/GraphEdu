"""Clean 清理临时文件和缓存命令模块

本模块提供项目临时文件和缓存的清理功能，帮助保持项目目录整洁。

清理功能:
    - Python 缓存文件（__pycache__, .pyc, .pyo）
    - 日志文件（支持保留天数过滤）
    - pytest 缓存和输出
    - 一键清理所有

主要命令:
    pycache    使用 pyclean 清理 Python 字节码缓存
    logs       清理日志文件，支持按天数保留
    pytest     清理 pytest 缓存和测试输出
    all        清理所有临时文件和缓存
    info       显示可清理目录和文件的统计信息

目录结构:
    data/
    ├── logs/              # 日志文件目录
    └── pytest/            # pytest 输出目录
        ├── .pytest_cache/ # pytest 缓存
        ├── htmlcov/       # HTML 覆盖率报告
        └── test-report.html

常用示例:
    # 清理 Python 缓存
    graphedu clean pycache                    # 清理默认目录
    graphedu clean pycache graphedu/services  # 清理指定目录

    # 清理日志文件
    graphedu clean logs                       # 清理所有日志
    graphedu clean logs --keep-days 7         # 保留最近 7 天日志
    graphedu clean logs --dry-run             # 模拟运行

    # 清理 pytest 缓存
    graphedu clean pytest                     # 清理 pytest 缓存
    graphedu clean pytest --all               # 清理所有 pytest 相关文件

    # 一键清理
    graphedu clean all                        # 清理所有
    graphedu clean all --keep-logs-days 30    # 保留 30 天日志

    # 查看信息
    graphedu clean info                       # 显示可清理的目录和大小

依赖工具:
    - pyclean: Python 缓存清理工具（需安装）
      安装方式: pip install pyclean

安全说明:
    - 删除操作不可逆，建议先使用 --dry-run 预览
    - 日志清理会保留指定天数内的文件
    - 会检查文件权限，无权限时给出提示

退出码:
    0    成功
    1    错误或失败
"""

import contextlib
import logging
from pathlib import Path
import shutil
import subprocess
import sys

import typer

clean_app = typer.Typer(help="清理临时文件和缓存")
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = DATA_DIR / "logs"
PYTEST_CACHE_DIR = PROJECT_ROOT / "data" / "pytest" / ".pytest_cache"


def run_pyclean(paths: list[Path]) -> None:
    """运行 pyclean 清理 Python 缓存文件。

    Args:
        paths: 要清理的路径列表

    Raises:
        typer.Exit: pyclean 未安装时退出
    """
    try:
        cmd = [sys.executable, "-m", "pyclean"] + [str(p) for p in paths]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"pyclean 执行失败: {e}")
    except FileNotFoundError:
        logger.error("Error: pyclean not found, please run: pip install pyclean")
        raise typer.Exit(code=1) from None


def remove_directory(path: Path, description: str) -> bool:
    """删除指定目录。

    Args:
        path: 要删除的目录路径
        description: 目录描述（用于日志）

    Returns:
        bool: 是否成功删除
    """
    if not path.exists():
        logger.info(f"{description} 不存在，跳过")
        return False

    try:
        shutil.rmtree(path)
        logger.info(f"已清理 {description}: {path}")
        return True
    except PermissionError:
        logger.error(f"权限不足，无法删除 {description}: {path}")
        return False
    except Exception as e:
        logger.error(f"删除 {description} 失败: {e}")
        return False


def remove_files_by_pattern(directory: Path, pattern: str, description: str) -> int:
    """按照模式删除目录中的文件。

    Args:
        directory: 要清理的目录路径
        pattern: 文件匹配模式（如 *.pyc）
        description: 文件描述（用于日志）

    Returns:
        int: 删除的文件数量
    """
    if not directory.exists():
        logger.info(f"{description} 目录不存在，跳过")
        return 0

    count = 0
    try:
        for file in directory.glob(pattern):
            if file.is_file():
                file.unlink()
                count += 1
        if count > 0:
            logger.info(f"已清理 {count} 个 {description}")
        return count
    except Exception as e:
        logger.error(f"清理 {description} 失败: {e}")
        return 0


@clean_app.command("pycache")
def clean_pycache(
    paths: list[str] = typer.Argument(None, help="要清理的路径（默认为 graphedu 和 tests 目录）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细输出"),
):
    """清理 Python 缓存文件（使用 pyclean）"""
    if paths:
        clean_paths = [Path(p) for p in paths]
    else:
        clean_paths = [PROJECT_ROOT / "graphedu", PROJECT_ROOT / "tests"]

    logger.info(f"清理 Python 缓存: {', '.join(str(p) for p in clean_paths)}")
    run_pyclean(clean_paths)
    logger.info("Python 缓存清理完成")


@clean_app.command("logs")
def clean_logs(
    keep_days: int = typer.Option(0, "--keep-days", "-k", help="保留最近 N 天的日志（0 表示全部清理）"),
    dry_run: bool = typer.Option(False, "--dry-run", help="模拟运行，不实际删除"),
):
    """清理日志文件"""
    logger.info(f"清理日志文件 (保留天数:{keep_days}, 模拟:{dry_run})")

    if not LOGS_DIR.exists():
        logger.info("日志目录不存在")
        return

    import time

    current_time = time.time()
    count = 0
    total_size = 0

    for log_file in LOGS_DIR.rglob("*.log"):
        if keep_days > 0:
            file_age_days = (current_time - log_file.stat().st_mtime) / 86400
            if file_age_days <= keep_days:
                continue

        file_size = log_file.stat().st_size
        total_size += file_size

        if dry_run:
            logger.info(f"将删除: {log_file.relative_to(PROJECT_ROOT)}")
        else:
            log_file.unlink()
        count += 1

    if dry_run:
        logger.info(f"模拟结果: 将删除 {count} 个日志文件，总计 {total_size} bytes")
    else:
        logger.info(f"已清理 {count} 个日志文件，释放 {total_size} bytes")


@clean_app.command("pytest")
def clean_pytest(
    all_: bool = typer.Option(False, "--all", "-a", help="清理所有 pytest 相关缓存"),
):
    """清理 pytest 缓存"""
    logger.info("清理 pytest 缓存")

    removed = False
    if remove_directory(PYTEST_CACHE_DIR, "pytest 缓存目录"):
        removed = True

    if all_:
        tests_pycache = PROJECT_ROOT / "tests" / "__pycache__"
        if remove_directory(tests_pycache, "tests __pycache__"):
            removed = True

        tests_dir = PROJECT_ROOT / "tests"
        if tests_dir.exists():
            count = remove_files_by_pattern(tests_dir, "**/*.pyc", "tests .pyc 文件")
            if count > 0:
                removed = True

        pytest_output_dir = PROJECT_ROOT / "data" / "pytest"
        if pytest_output_dir.exists():
            for item in pytest_output_dir.iterdir():
                if item.name != ".pytest_cache":  # noqa: SIM102
                    if remove_directory(item, f"pytest 输出 ({item.name})"):
                        removed = True

    if removed:
        logger.info("pytest 缓存清理完成")
    else:
        logger.info("没有需要清理的 pytest 缓存")


@clean_app.command("all")
def clean_all(
    keep_logs_days: int = typer.Option(0, "--keep-logs-days", "-k", help="保留最近 N 天的日志"),
    dry_run: bool = typer.Option(False, "--dry-run", help="模拟运行"),
):
    """清理所有临时文件和缓存"""
    logger.info("清理所有临时文件和缓存")

    with contextlib.suppress(SystemExit):
        clean_pycache()

    clean_logs(keep_days=keep_logs_days, dry_run=dry_run)
    clean_pytest(all_=True)

    if dry_run:
        logger.info("--dry-run 模式，未实际删除文件")
    else:
        logger.info("所有清理完成")


@clean_app.command("info")
def clean_info():
    """显示可清理的目录和文件信息"""
    logger.info("可清理的目录和文件信息")

    def get_dir_size(path: Path) -> int:
        if not path.exists():
            return 0
        total = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
        except PermissionError:
            pass
        return total

    def format_size(size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    for base_dir in [PROJECT_ROOT / "graphedu", PROJECT_ROOT / "tests"]:
        if base_dir.exists():
            pycache_dirs = list(base_dir.rglob("__pycache__"))
            pyc_count = len(list(base_dir.rglob("*.pyc")))
            logger.info(f"  {base_dir.relative_to(PROJECT_ROOT)}: __pycache__={len(pycache_dirs)}, .pyc={pyc_count}")

    if LOGS_DIR.exists():
        log_files = list(LOGS_DIR.rglob("*.log"))
        logs_size = get_dir_size(LOGS_DIR)
        logger.info(f"日志: {len(log_files)} 个文件, {format_size(logs_size)}")
