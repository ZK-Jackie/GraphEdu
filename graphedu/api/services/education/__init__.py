"""Education API 路由模块

提供教育模块相关的 API 控制器。
"""

from graphedu.api.services.education.chat import chat_controller
from graphedu.api.services.education.course_exercise import course_exercise_controller
from graphedu.api.services.education.exercise_attempt import exercise_attempt_controller
from graphedu.api.services.education.graphrag_task import graphrag_task_controller
from graphedu.api.services.education.knowledge_graph import knowledge_graph_controller
from graphedu.api.services.education.student import student_controller
from graphedu.api.services.education.teacher import teacher_controller

__all__ = [
    "chat_controller",
    "course_exercise_controller",
    "exercise_attempt_controller",
    "graphrag_task_controller",
    "knowledge_graph_controller",
    "student_controller",
    "teacher_controller",
]
