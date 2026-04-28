"""Education 服务模块

提供教育模块相关的业务逻辑服务，包括学生、教师、课程等管理功能。
"""

from graphedu.services.education.student import StudentService
from graphedu.services.education.teacher import TeacherService

__all__ = ["StudentService", "TeacherService"]
