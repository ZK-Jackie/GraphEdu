"""File and directory utility functions.

This module provides utilities for file and directory operations,
including path handling, file classification, YAML reading, etc.
"""

import hashlib
import logging
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Literal

from .strings import is_match

logger = logging.getLogger(__name__)

OS_WIN = "windows"
OS_LINUX = "linux"
OS_DARWIN = "darwin"
T_OS = Literal["windows", "linux", "darwin", "unknown"]
_file_cache: dict[str, Any] = {}


def get_os_type() -> T_OS:
    """Get the operating system type.

    Returns:
        One of "windows", "linux", "darwin", or "unknown".
    """
    logger.info("sys_platform: %s", sys.platform)
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform.startswith("darwin"):
        return "darwin"
    return "unknown"


def ensure_path(path: Path, folder=False, renew=False) -> Path:
    """Ensure that a path exists, creating directories if necessary.

    Args:
        path: Path to ensure.
        folder: Whether the path is a folder. If True, creates the folder.
            If False, ensures the parent directory of the file exists.
        renew: Whether to delete existing files/folders before creating.

    Returns:
        The Path object.
    """
    if folder:
        # 如果是文件夹，需要创建文件夹
        if renew and path.exists():  # 如果文件夹存在，先删除文件夹
            shutil.rmtree(path)
            logger.debug("Delete folder: %s", path)
        path.mkdir(parents=True, exist_ok=True)
        logger.debug("Create folder: %s", path)
    else:
        # 如果是文件，创建文件所在的上一级文件夹
        if renew and path.exists():  # 如果文件存在，先删除文件
            path.unlink()
            logger.debug("Delete file: %s", path)
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Create file folder: %s", path.parent)
    return path


def ensure_str_path(path: str, folder=False, renew=False) -> Path:
    """Handle path differences between Windows and Linux environments.

    Linux is often the production environment while Windows is typically
    the test/development environment. This function handles path conversion:

    - On Windows: Converts paths starting with / to relative paths
    - On Linux: Returns absolute paths without conversion

    Args:
        path: Path string.
        folder: Whether the path is a folder.
        renew: Whether to delete existing files/folders.

    Returns:
        The absolute Path object.
    """
    # 1 处理路径/位置差异
    # 1.1 如果是 windows 系统，需要将路径转换为相对路径
    if get_os_type() == OS_WIN:  # noqa: SIM102
        # 如果是 / 开头的路径，需要转换为相对路径
        if path.startswith("/"):
            path = "." + path
    # 1.2 linux 系统无需额外操作
    # 2 确定路径目录存在
    abs_path = Path(path).resolve()
    if folder:
        # 2.1 如果是文件夹，需要创建文件夹
        # 如果文件夹存在，先删除文件夹
        if renew and abs_path.exists():
            shutil.rmtree(abs_path)
            logger.debug("Delete folder: %s", abs_path)
        abs_path.mkdir(parents=True, exist_ok=True)
        logger.debug("Create folder: %s", abs_path)
    else:
        # 2.2 如果是文件，创建文件所在的上一级文件夹
        # 如果文件存在，先删除文件
        if renew and abs_path.exists():
            abs_path.unlink()
            logger.debug("Delete file: %s", abs_path)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Create file folder: %s", abs_path.parent)
    # 3 返回绝对路径
    return abs_path


def is_file_exists(file_path: str) -> bool:
    """Check if a file exists.

    Args:
        file_path: Path to the file.

    Returns:
        True if the file exists, False otherwise.
    """
    if not file_path:
        return False
    return Path(file_path).exists()


def get_file_md5(file_path: str) -> str:
    """Calculate MD5 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        MD5 hash as a hexadecimal string.
    """
    with open(file_path, "rb") as f:
        md5_hash = hashlib.md5()
        while chunk := f.read(8192):
            md5_hash.update(chunk)
    ret_md5 = md5_hash.hexdigest()
    logger.debug("File: %s, MD5: %s", file_path, ret_md5)
    return ret_md5


async def async_get_file_md5(file_path: str) -> str:
    """Calculate MD5 hash of a file asynchronously.

    Args:
        file_path: Path to the file.

    Returns:
        MD5 hash as a hexadecimal string.

    Raises:
        ImportError: If aiofiles is not installed.
    """
    try:
        import aiofiles
    except ImportError:
        raise ImportError("Please install aiofiles: pip install aiofiles") from None
    async with aiofiles.open(file_path, "rb") as f:
        md5_hash = hashlib.md5()
        while chunk := await f.read(8192):
            md5_hash.update(chunk)
    ret_md5 = md5_hash.hexdigest()
    logger.debug("File: %s, MD5: %s", file_path, ret_md5)
    return ret_md5


def save_file(file: bytes, path: str):
    """保存文件到指定路径，注意 path 应当明确指定文件名
    Args:
        file: 文件字节内容
        path: 保存路径
    Returns: None
    """
    # 确保文件夹存在
    abs_file_path = ensure_str_path(path, folder=False)
    # 保存文件
    with open(str(abs_file_path), "wb") as f:
        f.write(file)
    logger.debug("Save file: %s", abs_file_path)


def filenames_classify(filenames: list) -> dict[str, list[str]]:
    """Classify filenames by their file extensions.

    Args:
        filenames: List of filenames.

    Returns:
        Dictionary mapping file extensions to lists of filenames.
    """
    suffix_dict = {}
    for filename in filenames:
        # 获取文件后缀并按后缀分类
        suffix = filename.split(".")[-1].lower()
        if suffix in suffix_dict:
            suffix_dict[suffix].append(filename)
        else:
            suffix_dict[suffix] = [filename]
    return suffix_dict


def filenames_classify_in_folder(folder_path: str, not_found_err=False) -> dict[str, list[str]]:
    """Traverse a directory and classify files by extension.

    Args:
        folder_path: Path to the directory.
        not_found_err: Whether to raise an exception if directory doesn't exist.

    Returns:
        Dictionary mapping file extensions to lists of filenames.

    Raises:
        FileNotFoundError: If directory doesn't exist and not_found_err is True.
    """
    suffix_dict = {}
    # 1 获取工作文件夹路径
    dir_path = str(Path(folder_path).resolve())
    # 1.1 如果目录不存在，抛出异常
    if not os.path.exists(dir_path):
        if not_found_err:
            raise FileNotFoundError(f"Directory `{dir_path}` does not exist.")
        return suffix_dict
    # 2 检测文件类型
    for _root, _dirs, filenames in os.walk(dir_path):
        # 3 遍历文件夹下所有文件
        for filename in filenames:
            # 4 获取文件后缀并按后缀分类
            suffix = filename.split(".")[-1].lower()
            if suffix in suffix_dict:
                suffix_dict[suffix].append(filename)
            else:
                suffix_dict[suffix] = [filename]
    return suffix_dict


def is_dir(path) -> bool:
    """检查是否是目录
    Args:
        path: 文件路径
    Returns: 是否是目录
    """
    return os.path.isdir(path)


def is_file(path) -> bool:
    """检查是否是文件
    Args:
        path: 文件路径
    Returns: 是否是文件
    """
    return os.path.isfile(path)


def list_files(directory, file_list, file_type: tuple = None, pattern: str = None) -> None:
    """遍历指定目录下的所有文件和子目录，将文件路径添加到列表中
    Args:
        directory:  目录路径
        file_list:  文件路径列表，用于存储文件路径，由用户传入，最终返回
        file_type:  允许的文件类型
        pattern:    文件名匹配模式，需要正则表达式
    Returns: None
    """
    # 遍历指定目录下的所有文件和子目录
    for item in os.listdir(directory):
        # 拼接完整的文件或目录路径
        path = os.path.join(directory, item)
        # 如果是目录，递归调用list_files函数
        if is_dir(path):
            list_files(path, file_list, file_type, pattern)
        # 如果是文件，将路径添加到列表中
        else:
            if is_match(item, pattern) and (not file_type or item.endswith(file_type)):
                file_list.append(path)
            else:
                continue
    return


def read_yaml(file_path: str, cache: bool = True, not_found_err: bool = True) -> dict:
    """Read a YAML file.

    Args:
        file_path: Path to the YAML file.
        cache: Whether to cache file contents (default: True).
        not_found_err: Whether to raise an exception if file doesn't exist (default: True).

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        FileNotFoundError: If file doesn't exist and not_found_err is True.
    """
    import yaml

    if is_file_exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    elif not_found_err:
        raise FileNotFoundError(f"File `{file_path}` does not exist.")
    else:
        return {}
