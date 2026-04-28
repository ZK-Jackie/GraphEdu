"""ORM (Object-Relational Mapping) 模块

本模块导出所有 SQLAlchemy ORM 模型，用于数据访问层的数据库操作

导出的模型包括：

**系统相关表 (sys_ 前缀)**:
- SysUser: 用户基础信息表
- SysDept: 部门信息表
- SysUserDept: 用户和部门关联表
- SysRole: 角色信息表
- SysUserRole: 用户和角色关联表
- SysFunction: 功能权限表
- SysRoleFunction: 角色功能关联表
- SysRoleDept: 角色部门关联表（数据权限）
- SysUpload: 文件上传表
- SysDictType: 字典类型表
- SysDictData: 字典数据表
- SysOperLog: 操作日志表
- SysLogininfor: 登录日志表

**教育相关表 (edu_ 前缀)**:
- EduStudent: 学生扩展信息表
- EduTeacher: 教师扩展信息表
- EduCourse: 课程表
- EduCourseTeacher: 课程与教师关联表
- EduStudentCourse: 学生选课关联表
- EduChatSession: 对话会话表
- EduKnowledgeGraph: 知识图谱表
- EduStudentRecord: 用户学习记录表
"""

from .education import (
    EduChatSession,
    EduCourse,
    EduCourseExercise,
    EduCourseTeacher,
    EduKnowledgeGraph,
    EduStudent,
    EduStudentCourse,
    EduTeacher,
)
from .generator import GenTable, GenTableColumn
from .system import (
    SysDept,
    SysDictData,
    SysDictType,
    SysFunction,
    SysLogininfor,
    SysOperLog,
    SysRole,
    SysRoleDept,
    SysRoleFunction,
    SysUpload,
    SysUser,
    SysUserDept,
    SysUserRole,
)

__all__ = [
    # Education
    "EduChatSession",
    "EduCourse",
    "EduCourseExercise",
    "EduCourseTeacher",
    "EduKnowledgeGraph",
    "EduStudent",
    "EduStudentCourse",
    "EduTeacher",
    # Generator
    "GenTable",
    "GenTableColumn",
    # System
    "SysDept",
    "SysDictData",
    "SysDictType",
    "SysFunction",
    "SysLogininfor",
    "SysOperLog",
    "SysRole",
    "SysRoleDept",
    "SysRoleFunction",
    "SysUpload",
    "SysUser",
    "SysUserDept",
    "SysUserRole",
]
