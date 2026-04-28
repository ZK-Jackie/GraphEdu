"""Generator 数据模型模块

本模块包含代码生成器使用的各种数据模型。

模型类型:
    - orm: ORM 实体（GenTable、GenTableColumn）
    - dto: 请求 DTO（数据传输对象）
    - vo: 响应 VO（视图对象）

使用方式:
    from graphedu.common.models.orm.generator import GenTable, GenTableColumn
    from graphedu.common.models.dto.generator import GenTableQueryDTO, GenTableUpdateDTO
    from graphedu.common.models.vo.generator import GenTableDetailVO, GenTableListVO
"""

from graphedu.common.models.dto.toolv2.generator import (
    GenDbTableQueryDTO,
    GenTableColumnUpdateDTO,
    GenTableQueryDTO,
    GenTableUpdateDTO,
)
from graphedu.common.models.orm.generator import GenTable, GenTableColumn
from graphedu.common.models.vo.toolv2.generator import (
    GenTableColumnVO,
    GenTableDetailVO,
    GenTableInfoVO,
    GenTableListVO,
)

__all__ = [
    "GenDbTableQueryDTO",
    "GenTable",
    "GenTableColumn",
    "GenTableColumnUpdateDTO",
    "GenTableColumnVO",
    "GenTableDetailVO",
    "GenTableInfoVO",
    "GenTableListVO",
    "GenTableQueryDTO",
    "GenTableUpdateDTO",
]
