"""Cron 表达式验证工具

提供 Cron 表达式的验证功能，支持 6 位或 7 位表达式：
- 6 位：秒 分 时 日 月 周
- 7 位：秒 分 时 日 月 周 年
"""

import logging

logger = logging.getLogger(__name__)


class CronUtil:
    """Cron 表达式验证工具类

    提供静态方法用于验证 Cron 表达式的格式是否正确
    """

    # Cron 表达式各字段的有效值范围
    FIELD_RANGES = {
        "second": (0, 59),
        "minute": (0, 59),
        "hour": (0, 23),
        "day": (1, 31),
        "month": (1, 12),
        "day_of_week": (0, 6),  # 0=周日, 6=周六
        "year": (1970, 2099),
    }

    # 字段名称映射
    FIELD_NAMES = ["second", "minute", "hour", "day", "month", "day_of_week", "year"]

    @staticmethod
    def validate_cron_expression(expression: str) -> bool:
        """验证 Cron 表达式格式

        支持 6 位或 7 位 Cron 表达式：
        - 6 位：秒 分 时 日 月 周
        - 7 位：秒 分 时 日 月 周 年

        支持的特殊字符：
        - * : 所有值
        - ? : 不指定值（仅用于日和周）
        - - : 范围（如 1-5）
        - , : 列表（如 1,3,5）
        - / : 步长（如 */5）
        - L : 最后一天（仅用于日和周）
        - W : 工作日（仅用于日）
        - # : 第几周（仅用于周）

        Args:
            expression: Cron 表达式

        Returns:
            是否为有效的 Cron 表达式
        """
        if not expression or not isinstance(expression, str):
            return False

        expression = expression.strip()
        parts = expression.split()

        # 检查位数（6位或7位）
        if len(parts) not in (6, 7):
            logger.warning(f"Cron表达式位数错误: {expression}, 当前位数: {len(parts)}")
            return False

        # 验证每个字段
        for i, part in enumerate(parts):
            field_name = CronUtil.FIELD_NAMES[i]
            if not CronUtil._validate_field(part, field_name, i == 4, i == 5):
                logger.warning(f"Cron表达式字段验证失败: {expression}, 字段: {field_name}, 值: {part}")
                return False

        # 验证日和周不能同时为指定值
        if not CronUtil._validate_day_and_week_combination(parts[3], parts[5]):
            logger.warning(f"Cron表达式日和周不能同时为指定值: {expression}")
            return False

        return True

    @staticmethod
    def _validate_field(value: str, field_name: str, is_month: bool = False, is_day_of_week: bool = False) -> bool:
        """验证单个字段

        Args:
            value: 字段值
            field_name: 字段名称
            is_month: 是否为月份字段
            is_day_of_week: 是否为星期字段

        Returns:
            字段是否有效
        """
        if not value:
            return False

        # 允许的特殊字符
        if value in ("*", "?"):
            return True

        # 处理逗号分隔的列表
        if "," in value:
            return all(
                CronUtil._validate_field(part.strip(), field_name, is_month, is_day_of_week)
                for part in value.split(",")
            )

        # 处理范围（如 1-5）
        if "-" in value:
            parts = value.split("-")
            if len(parts) != 2:
                return False
            start, end = parts
            if not start.isdigit() or not end.isdigit():
                return False
            return CronUtil._validate_field(start, field_name, is_month, is_day_of_week) and CronUtil._validate_field(
                end, field_name, is_month, is_day_of_week
            )

        # 处理步长（如 */5 或 1-10/2）
        if "/" in value:
            base, step = value.split("/", 1)
            if base == "*":
                return step.isdigit() and int(step) > 0
            if not CronUtil._validate_field(base, field_name, is_month, is_day_of_week):
                return False
            return step.isdigit() and int(step) > 0

        # 处理 L（最后一天）
        if value.endswith("L"):
            if is_day_of_week:
                # 星期字段支持 1L-7L 或 MON-SUN + L
                base = value[:-1]
                return base in ("", "1", "2", "3", "4", "5", "6", "7")
            # 日期字段支持 L 或 数字L
            base = value[:-1]
            return base in ("", "W") or (base.isdigit() and 1 <= int(base) <= 31)

        # 处理 W（工作日）
        if value.endswith("W"):
            if is_day_of_week:
                return False
            base = value[:-1]
            return base == "" or (base.isdigit() and 1 <= int(base) <= 31)

        # 处理 #（第几周，仅用于星期字段）
        if "#" in value and is_day_of_week:
            parts = value.split("#")
            if len(parts) != 2:
                return False
            base, week_num = parts
            if not base.isdigit() or not week_num.isdigit():
                return False
            return 0 <= int(base) <= 6 and 1 <= int(week_num) <= 5

        # 处理纯数字
        if value.isdigit():
            num_value = int(value)
            min_val, max_val = CronUtil.FIELD_RANGES[field_name]
            return min_val <= num_value <= max_val

        # 处理月份缩写（JAN-DEC）
        if is_month and value.upper() in (
            "JAN",
            "FEB",
            "MAR",
            "APR",
            "MAY",
            "JUN",
            "JUL",
            "AUG",
            "SEP",
            "OCT",
            "NOV",
            "DEC",
        ):
            return True

        # 处理星期缩写（MON-SUN）
        return bool(is_day_of_week and value.upper() in ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"))

    @staticmethod
    def _validate_day_and_week_combination(day_value: str, week_value: str) -> bool:
        """验证日和周字段的组合

        日和周不能同时为指定值（不能同时使用数字），只能其中一个为 ? 或 *

        Args:
            day_value: 日字段值
            week_value: 周字段值

        Returns:
            组合是否有效
        """
        # 如果其中一个为 ? 或 *，则有效
        if day_value in ("?", "*") or week_value in ("?", "*"):
            return True

        # 检查是否包含数字（不包含 L、W 等特殊字符）
        day_has_number = any(c.isdigit() for c in day_value if c not in ("L", "W"))
        week_has_number = any(c.isdigit() for c in week_value if c not in ("L", "#"))

        # 不能同时为数字
        return not (day_has_number and week_has_number)

    @staticmethod
    def get_next_run_time(expression: str) -> str | None:
        """获取下次执行时间（简化版）

        Args:
            expression: Cron 表达式

        Returns:
            下次执行时间描述（简化版）
        """
        if not CronUtil.validate_cron_expression(expression):
            return None

        # 这里简化处理，实际应该使用 croniter 或类似库计算
        return "Cron表达式有效（下次执行时间待计算）"
