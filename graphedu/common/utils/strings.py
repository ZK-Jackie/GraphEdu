"""String manipulation and time formatting utility functions.

This module provides utilities for:
- Time/timestamp formatting and conversion
- Duration formatting with internationalization support
- String utilities like camel/snake case conversion
- URL and path validation
- SQLAlchemy result serialization
"""

from datetime import datetime, timedelta
from enum import Enum
import os
import re
import time
from typing import Any, Literal

from pydantic import HttpUrl
from sqlalchemy import Row
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm.collections import InstrumentedList

from ..exceptions import ImportException, TypeConversionException, ValueException

# ============================================================================
# Time formatting enums and constants
# ============================================================================


class TimePrecision(Enum):
    """Time precision levels for formatting."""

    AUTO = "auto"  # Automatically select appropriate precision
    SECOND = "second"  # Second-level precision
    MINUTE = "minute"  # Minute-level precision
    HOUR = "hour"  # Hour-level precision
    DAY = "day"  # Day-level precision


class Language(Enum):
    """Supported languages for internationalization."""

    ZH_CN = "zh_CN"  # Simplified Chinese
    EN_US = "en_US"  # American English
    JA_JP = "ja_JP"  # Japanese
    KO_KR = "ko_KR"  # Korean


# Multilingual time unit mappings
_TIME_UNITS_I18N = {
    Language.ZH_CN: {
        "year": "年",
        "month": "个月",
        "week": "周",
        "day": "天",
        "hour": "小时",
        "minute": "分钟",
        "second": "秒",
        "and": "和",
        "separator": "",
        "ago": "前",
        "later": "后",
        "just_now": "刚刚",
        "format_full": "{value}{unit}",
        "format_short": "{value}{unit}",
    },
    Language.EN_US: {
        "year": "year",
        "years": "years",
        "month": "month",
        "months": "months",
        "week": "week",
        "weeks": "weeks",
        "day": "day",
        "days": "days",
        "hour": "hour",
        "hours": "hours",
        "minute": "minute",
        "minutes": "minutes",
        "second": "second",
        "seconds": "seconds",
        "and": "and",
        "separator": " ",
        "ago": "ago",
        "later": "later",
        "just_now": "just now",
    },
    Language.JA_JP: {
        "year": "年",
        "month": "ヶ月",
        "week": "週間",
        "day": "日",
        "hour": "時間",
        "minute": "分",
        "second": "秒",
        "and": "と",
        "separator": "",
        "ago": "前",
        "later": "後",
        "just_now": "たった今",
    },
    Language.KO_KR: {
        "year": "년",
        "month": "개월",
        "week": "주",
        "day": "일",
        "hour": "시간",
        "minute": "분",
        "second": "초",
        "and": "와",
        "separator": "",
        "ago": "전",
        "later": "후",
        "just_now": "방금",
    },
}


# https://blog.csdn.net/pengjunlee/article/details/102719877
def get_timestamp_s() -> str:
    """Get current timestamp in seconds.

    Returns:
        Current timestamp as string (seconds since epoch).
    """
    return str(int(time.time()))


def get_timestamp_ms() -> str:
    """Get current timestamp in milliseconds.

    Returns:
        Current timestamp as string (milliseconds since epoch).
    """
    return str(round(time.time() * 1000))


def get_timestamp_us() -> str:
    """Get current timestamp in microseconds.

    Returns:
        Current timestamp as string (microseconds since epoch).
    """
    return str(round(time.time() * 1000000))


def get_datetime(format_str: str = "%Y-%m-%d") -> str:
    """Get current datetime formatted as string.

    Args:
        format_str: Datetime format string (default: "%Y-%m-%d").

    Returns:
        Formatted datetime string.
    """
    return time.strftime(format_str, time.localtime())


def timestamp_to_datetime(timestamp: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Convert timestamp to datetime string.

    Args:
        timestamp: Timestamp string (seconds, milliseconds, or microseconds).
        format_str: Datetime format string.

    Returns:
        Formatted datetime string.

    Raises:
        ValueError: If timestamp length is invalid.
    """
    # 检查 timestamp 的类型（秒级、毫秒级、微秒级）
    if len(timestamp) == 10:
        return time.strftime(format_str, time.localtime(int(timestamp)))
    if len(timestamp) == 13:
        return time.strftime(format_str, time.localtime(int(timestamp) // 1000))
    if len(timestamp) == 16:
        return time.strftime(format_str, time.localtime(int(timestamp) // 1000000))
    raise ValueException(
        f"Invalid timestamp: {timestamp}",
        value=timestamp,
        constraint="Length must be 10 (seconds), 13 (milliseconds), or 16 (microseconds)",
    )


def extract_contents(input_str: str, start_tag: str, end_tag: str) -> tuple[str | None, str | None]:
    """从字符串中提取指定标签之间的内容和标签后的内容

    Args:
        input_str: 输入字符串
        start_tag: 起始标签
        end_tag: 结束标签

    Returns:
        tuple[str | None, str | None]: 包含两个元素的元组
            - 第一个元素：起始标签和结束标签之间的内容，如果找不到则返回 None
            - 第二个元素：结束标签之后到字符串末尾的内容，如果找不到则返回 None
    """
    start_index = input_str.find(start_tag)
    end_index = input_str.find(end_tag)

    if start_index == -1 or end_index == -1 or start_index > end_index:
        return None, None  # 找不到或者标签顺序错误

    # 提取<think>与</think>之间的内容
    content_between = input_str[start_index + len(start_tag) : end_index]
    # 提取</think>到字符串末尾的内容
    content_after = input_str[end_index + len(end_tag) :]

    return content_between, content_after


def check_path_or_url(input_str: str) -> Literal["path", "url"]:
    """Check if input string is a path or URL.

    Args:
        input_str: Input string to check.

    Returns:
        'path' if it's a file path, 'url' if it's a URL.

    Raises:
        ValueError: If string is neither a valid URL nor existing file path.
    """
    if input_str.startswith("http://") or input_str.startswith("https://"):
        return "url"
    if os.path.exists(input_str):
        return "path"
    raise ValueException(
        f"Invalid path or url: {input_str}",
        value=input_str,
        field="input_str",
        constraint="Must be a valid URL or existing file path",
    )


def get_short_uuid(length: int = 8, alphabet: str = "abcdefghijklmnopqrstuvwxyz1234567890") -> str:
    """生成指定长度的短 UUID

    Args:
        length: UUID 长度，默认为 8
        alphabet: 字符集，默认为小写字母和数字

    Returns:
        str: 指定长度的短 UUID 字符串

    Raises:
        ImportException: 当未安装 shortuuid 包时
    """
    try:
        import shortuuid
    except ImportError:
        raise ImportException(
            "Please install shortuuid: pip install shortuuid", module_path="shortuuid", reason="Module not found"
        ) from None
    return shortuuid.ShortUUID(alphabet=alphabet).random(length)


def get_letter_start_uuid(length: int = 8, alphabet: str = "abcdefghijklmnopqrstuvwxyz1234567890") -> str:
    """生成以字母开头的短 UUID

    Args:
        length: UUID 总长度，默认为 8
        alphabet: 除首字母外的字符集，默认为小写字母和数字

    Returns:
        str: 以字母开头、指定长度的短 UUID 字符串

    Raises:
        ImportException: 当未安装 shortuuid 包时
    """
    try:
        import shortuuid
    except ImportError:
        raise ImportException(
            "Please install shortuuid: pip install shortuuid", module_path="shortuuid", reason="Module not found"
        ) from None
    letters = "abcdefghijklmnopqrstuvwxyz"
    return shortuuid.ShortUUID(alphabet=letters).random(1) + shortuuid.ShortUUID(alphabet=alphabet).random(length - 1)


def get_url_params(url: str) -> dict:
    """从 URL 中提取查询参数

    Args:
        url: URL 字符串

    Returns:
        dict: 包含所有查询参数的字典，键为参数名，值为参数值

    Examples:
        >>> get_url_params("https://example.com?key1=value1&key2=value2")
        {'key1': 'value1', 'key2': 'value2'}
    """
    if "?" in url:
        params = url.split("?")[1].split("&")
    elif "&" in url:
        params = url.split("&")
    else:
        return {}
    ret = {}
    for param in params:
        key, value = param.split("=")
        ret[key] = value
    return ret


def is_http_url(path: str) -> bool:
    """检查字符串是否为有效的 HTTP/HTTPS URL

    Args:
        path: 待检查的字符串

    Returns:
        bool: 如果是有效的 HTTP/HTTPS URL 则返回 True，否则返回 False
    """
    try:
        HttpUrl(path)
        return True
    except Exception:
        return False


def is_file_path(path: str) -> bool:
    r"""检查字符串是否为有效的文件路径

    支持 Windows 路径（如 C:\path）和 Unix 路径（如 /path）。

    Args:
        path: 待检查的字符串

    Returns:
        bool: 如果是有效的文件路径格式则返回 True，否则返回 False
    """
    file_pattern = re.compile(r"^[a-zA-Z]:\\|^/")
    return bool(file_pattern.match(path))


def is_match(string: str, pattern: str = None) -> bool:
    """检查字符串是否匹配指定的正则表达式模式

    Args:
        string: 待检查的字符串
        pattern: 正则表达式模式，如果为 None 则返回 True

    Returns:
        bool: 如果字符串匹配模式则返回 True，否则返回 False
    """
    if not pattern:
        return True
    return bool(re.match(pattern, string))


def str_to_bool(value: str) -> bool:
    """Convert string to boolean value.

    Args:
        value: Input string to convert.

    Returns:
        Boolean value.

    Raises:
        TypeConversionException: If string cannot be converted to boolean.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.lower()
        if value in ["true", "1", "yes", "y"]:
            return True
        if value in ["false", "0", "no", "n"]:
            return False
    raise TypeConversionException(
        f"Invalid boolean string: {value}",
        value=value,
        target_type=bool,
        reason="Must be one of: true, false, 1, 0, yes, no, y, n (case-insensitive)",
    )


# ============================================================================
# Time formatting utility functions
# ============================================================================


def format_duration(
    duration: int | float | timedelta,
    language: Language | str = Language.ZH_CN,
    precision: TimePrecision = TimePrecision.AUTO,
    max_units: int = 2,
    show_seconds_threshold: int = 60,
) -> str:
    """将时间间隔格式化为人类可读的字符串

    Args:
        duration: 时间间隔，可以是：
            - int/float: 秒数
            - timedelta: datetime.timedelta 对象
        language: 语言（默认中文）
        precision: 时间精度
        max_units: 最多显示几个时间单位（默认2个，如"2天3小时"）
        show_seconds_threshold: 少于多少秒时显示秒（默认60秒）

    Returns:
        格式化后的时间字符串，如 "2天3小时", "2 hours and 30 minutes"

    Examples:
        >>> format_duration(3661)  # 1小时1分1秒
        '1小时1分钟'
        >>> format_duration(3661, language=Language.EN_US)
        '1 hour 1 minute'
        >>> format_duration(timedelta(days=2, hours=3))
        '2天3小时'
    """
    # 转换为语言枚举
    if isinstance(language, str):
        try:
            language = Language(language)
        except ValueError:
            language = Language.ZH_CN

    # 转换为秒数
    total_seconds = int(duration.total_seconds()) if isinstance(duration, timedelta) else int(duration)

    # 处理负数
    if total_seconds < 0:
        total_seconds = abs(total_seconds)

    # 处理0秒
    if total_seconds == 0:
        units = _TIME_UNITS_I18N[language]
        return units.get("just_now", "0" + units["second"])

    # 定义时间单位（秒）
    time_units = [
        ("year", 31536000),  # 365天
        ("month", 2592000),  # 30天
        ("week", 604800),  # 7天
        ("day", 86400),
        ("hour", 3600),
        ("minute", 60),
        ("second", 1),
    ]

    # 根据精度过滤单位
    if precision != TimePrecision.AUTO:
        # time_units索引: 0:year, 1:month, 2:week, 3:day, 4:hour, 5:minute, 6:second
        # 使用slice(0, min_index)来限制最大精度（如HOUR时只显示到小时，不显示分钟和秒）
        precision_max_index = {
            TimePrecision.SECOND: 7,  # 显示所有单位（包括秒）
            TimePrecision.MINUTE: 6,  # 显示到分钟（不包括秒）
            TimePrecision.HOUR: 5,  # 显示到小时（不包括分钟和秒）
            TimePrecision.DAY: 4,  # 显示到天（不包括小时及以下）
        }
        max_index = precision_max_index.get(precision, 7)
        time_units = time_units[:max_index]

    # 计算各单位的值
    parts = []
    remaining = total_seconds

    for unit_name, unit_seconds in time_units:
        if remaining >= unit_seconds:
            value = remaining // unit_seconds
            remaining = remaining % unit_seconds

            # 根据语言选择单复数形式
            unit_key = (unit_name + "s" if value > 1 else unit_name) if language == Language.EN_US else unit_name

            unit_text = _TIME_UNITS_I18N[language][unit_key]
            parts.append((value, unit_text))

            if len(parts) >= max_units:
                break

    # 如果没有单位（小于精度），显示最小单位
    if not parts:
        min_unit = time_units[-1][0]
        if language == Language.EN_US:
            min_unit = min_unit + "s" if total_seconds > 1 else min_unit
        unit_text = _TIME_UNITS_I18N[language][min_unit]
        return f"{total_seconds}{unit_text}"

    # 格式化输出
    units = _TIME_UNITS_I18N[language]
    separator = units.get("separator", "")
    and_word = units.get("and", "")

    if language == Language.EN_US:
        # 英文格式：数字和单位之间需要空格
        if len(parts) > 1:
            # 多个单位：最后一个单位用 "and" 连接
            *first_parts, last_part = parts
            formatted_parts = [f"{value}{separator}{unit}" for value, unit in first_parts]
            formatted_parts.append(f"{last_part[0]}{separator}{last_part[1]}")
            result = f" {and_word} ".join(formatted_parts)
        else:
            # 单个单位：也要添加空格
            result = "".join([f"{value}{separator}{unit}" for value, unit in parts])
    else:
        # 其他语言直接连接
        result = "".join([f"{value}{unit}" for value, unit in parts])

    return result


def format_duration_short(duration: int | float | timedelta, language: Language | str = Language.ZH_CN) -> str:
    """将时间间隔格式化为简短形式

    Args:
        duration: 时间间隔（秒数或timedelta）
        language: 语言

    Returns:
        简短格式字符串，如 "2天", "1小时", "30分钟"

    Examples:
        >>> format_duration_short(3661)
        '1小时'
        >>> format_duration_short(3661, Language.EN_US)
        '1 hour'
    """
    return format_duration(duration, language, max_units=1)


def format_duration_detailed(duration: int | float | timedelta, language: Language | str = Language.ZH_CN) -> str:
    """将时间间隔格式化为详细形式

    Args:
        duration: 时间间隔（秒数或timedelta）
        language: 语言

    Returns:
        详细格式字符串，如 "2天3小时15分钟30秒"

    Examples:
        >>> format_duration_detailed(3661)
        '1小时1分钟1秒'
    """
    return format_duration(duration, language, max_units=10)


def format_retry_after(wait_seconds: int, language: Language | str = Language.ZH_CN) -> str:
    """格式化重试等待时间（用于错误提示）

    Args:
        wait_seconds: 需要等待的秒数
        language: 语言

    Returns:
        格式化后的等待时间提示

    Examples:
        >>> format_retry_after(150)
        '请2分钟后再试'
        >>> format_retry_after(150, Language.EN_US)
        'Please try again after 2 minutes'
    """
    duration_str = format_duration(wait_seconds, language, max_units=1)

    if language == Language.EN_US:
        return f"Please try again after {duration_str}"
    if language == Language.JA_JP:
        return f"{duration_str}後にもう一度お試しください"
    if language == Language.KO_KR:
        return f"{duration_str}후 다시 시도해 주세요"
    # ZH_CN
    return f"请{duration_str}后再试"


def format_time_ago(
    timestamp: datetime | int | float, language: Language | str = Language.ZH_CN, now: datetime | None = None
) -> str:
    """格式化时间为"多久之前"的形式

    Args:
        timestamp: 时间（datetime对象或时间戳）
        language: 语言
        now: 当前时间（用于测试，默认为实际当前时间）

    Returns:
        格式化后的相对时间字符串

    Examples:
        >>> format_time_ago(datetime.now() - timedelta(hours=2))
        '2小时前'
        >>> format_time_ago(datetime.now() - timedelta(hours=2), Language.EN_US)
        '2 hours ago'
    """
    if now is None:
        now = datetime.now()

    # 转换为 datetime
    dt = datetime.fromtimestamp(timestamp) if isinstance(timestamp, (int, float)) else timestamp

    # 计算时间差
    delta = now - dt
    total_seconds = int(abs(delta.total_seconds()))

    # 小于60秒显示"刚刚"
    if total_seconds < 60:
        units = _TIME_UNITS_I18N[language]
        return units.get("just_now", "刚刚")

    duration_str = format_duration(total_seconds, language, max_units=1)
    units = _TIME_UNITS_I18N[language]

    # 添加时间方向（前/后）
    suffix = units.get("ago", "前") if delta.total_seconds() >= 0 else units.get("later", "后")

    separator = units.get("separator", "")
    if language == Language.EN_US:
        return f"{duration_str}{separator}{suffix}"
    return f"{duration_str}{suffix}"


def format_wait_time(wait_seconds: int | float, language: Language | str = Language.ZH_CN) -> str:
    """格式化等待时间（用于限流等场景）

    Args:
        wait_seconds: 需要等待的秒数
        language: 语言

    Returns:
        格式化后的等待时间

    Examples:
        >>> format_wait_time(150)
        '需等待2分钟'
        >>> format_wait_time(150, Language.EN_US)
        'Please wait 2 minutes'
    """
    duration_str = format_duration(wait_seconds, language, max_units=1)

    if language == Language.EN_US:
        return f"Please wait {duration_str}"
    if language == Language.JA_JP:
        return f"{duration_str}お待ちください"
    if language == Language.KO_KR:
        return f"{duration_str}기다려주세요"
    # ZH_CN
    return f"需等待{duration_str}"


def format_timeout(timeout_seconds: int | float, language: Language | str = Language.ZH_CN) -> str:
    """格式化超时时间

    Args:
        timeout_seconds: 超时秒数
        language: 语言

    Returns:
        格式化后的超时时间

    Examples:
        >>> format_timeout(30)
        '超时时间：30秒'
        >>> format_timeout(30, Language.EN_US)
        'Timeout: 30 seconds'
    """
    duration_str = format_duration_short(timeout_seconds, language)

    if language == Language.EN_US:
        return f"Timeout: {duration_str}"
    if language == Language.JA_JP:
        return f"タイムアウト：{duration_str}"
    if language == Language.KO_KR:
        return f"시간 초과：{duration_str}"
    # ZH_CN
    return f"超时时间：{duration_str}"


def pascal_to_snake(pascal_str: str) -> str:
    """将 PascalCase 命名转换为下划线命名

    Args:
        pascal_str: PascalCase 命名的字符串

    Returns:
        str: 下划线命名的字符串

    Examples:
        >>> pascal_to_snake("PascalCase")
        'pascal_case'
    """
    words = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", pascal_str)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", words).lower()


def camel_to_snake(camel_str: str) -> str:
    """将驼峰命名转换为下划线命名

    Args:
        camel_str: 驼峰命名的字符串

    Returns:
        str: 下划线命名的字符串

    Examples:
        >>> camel_to_snake("camelCase")
        'camel_case'
        >>> camel_to_snake("CamelCase")
        'camel_case'
    """
    words = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", words).lower()


def snake_to_camel(snake_str: str) -> str:
    """将下划线命名转换为驼峰命名

    Args:
        snake_str: 下划线命名的字符串

    Returns:
        str: 驼峰命名的字符串（首字母小写）

    Examples:
        >>> snake_to_camel("snake_case")
        'snakeCase'
    """
    words = snake_str.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


class SqlalchemyUtil:
    """SQLAlchemy utility class.

    Provides utilities for converting SQLAlchemy models to dictionaries,
    with support for case transformation (snake_case/camelCase).
    """

    @staticmethod
    def base_to_dict(obj: Any, transform_case: Literal["no_case", "snake_to_camel", "camel_to_snake"] = "no_case"):
        """Convert SQLAlchemy model object to dictionary.

        Args:
            obj: SQLAlchemy model object or dictionary.
            transform_case: Case transformation to apply:
                - 'no_case': No transformation
                - 'snake_to_camel': Convert snake_case to camelCase
                - 'camel_to_snake': Convert camelCase to snake_case
                Default is 'no_case'.

        Returns:
            Dictionary representation of the model.
        """
        base_dict = {}
        # 使用 isinstance(obj, DeclarativeBase) 检查（支持 SQLAlchemy 2.0）
        # 如果是旧版本，会回退到 hasattr(obj, "__table__") 检查
        is_orm_instance = isinstance(obj, DeclarativeBase) or hasattr(obj, "__table__")
        if is_orm_instance:
            base_dict = obj.__dict__.copy()
            base_dict.pop("_sa_instance_state", None)
            for name, value in base_dict.items():
                if isinstance(value, InstrumentedList):
                    base_dict[name] = SqlalchemyUtil.serialize_result(value, "snake_to_camel")
        elif isinstance(obj, dict):
            base_dict = obj.copy()
        if transform_case == "snake_to_camel":
            return {snake_to_camel(k): v for k, v in base_dict.items()}
        if transform_case == "camel_to_snake":
            return {camel_to_snake(k): v for k, v in base_dict.items()}

        return base_dict

    @staticmethod
    def serialize_result(
        result: Any, transform_case: Literal["no_case", "snake_to_camel", "camel_to_snake"] = "no_case"
    ):
        """Serialize SQLAlchemy query result.

        Args:
            result: SQLAlchemy query result (can be model, dict, list, or Row).
            transform_case: Case transformation to apply:
                - 'no_case': No transformation
                - 'snake_to_camel': Convert snake_case to camelCase
                - 'camel_to_snake': Convert camelCase to snake_case
                Default is 'no_case'.

        Returns:
            Serialized result.
        """
        # 检查是否为 ORM 实例或字典（兼容 SQLAlchemy 2.0 DeclarativeBase 和旧版本）
        is_orm_instance = isinstance(result, DeclarativeBase) or hasattr(result, "__table__")
        if is_orm_instance or isinstance(result, dict):
            return SqlalchemyUtil.base_to_dict(result, transform_case)
        if isinstance(result, list):
            return [SqlalchemyUtil.serialize_result(row, transform_case) for row in result]
        if isinstance(result, Row):
            # 检查 Row 中的每个元素是否为 ORM 实例
            all_orm = all(isinstance(row, DeclarativeBase) or hasattr(row, "__table__") for row in result)
            any_orm = any(isinstance(row, DeclarativeBase) or hasattr(row, "__table__") for row in result)
            if all_orm:
                return [SqlalchemyUtil.base_to_dict(row, transform_case) for row in result]
            if any_orm:
                return [SqlalchemyUtil.serialize_result(row, transform_case) for row in result]
            result_dict = result._asdict()
            if transform_case == "snake_to_camel":
                return {snake_to_camel(k): v for k, v in result_dict.items()}
            if transform_case == "camel_to_snake":
                return {camel_to_snake(k): v for k, v in result_dict.items()}
            return result_dict
        return result
