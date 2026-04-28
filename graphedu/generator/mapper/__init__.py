"""Generator 数据访问层模块

本模块包含代码生成器的数据访问逻辑（仓储模式）。

Mapper 类:
    - GenTableMapper: 业务表数据访问
    - GenTableColumnMapper: 业务表字段数据访问

使用方式:
    from graphedu.generator.mapper import GenTableMapper, GenTableColumnMapper
"""

from graphedu.mapper.tool.gen_table import GenTableColumnMapper, GenTableMapper

__all__ = [
    "GenTableColumnMapper",
    "GenTableMapper",
]
