"""API 服务路由模块.

提供所有 API 控制器的注册和路由管理功能。
"""

from fastapi import FastAPI

from graphedu.api.services.common.captcha import captcha_controller
from graphedu.api.services.common.upload_proxy import upload_proxy_controller
from graphedu.api.services.education.chapter import chapter_controller
from graphedu.api.services.education.chapter_resource import chapter_resource_controller
from graphedu.api.services.education.chat import chat_controller
from graphedu.api.services.education.course import course_controller
from graphedu.api.services.education.course_exercise import course_exercise_controller
from graphedu.api.services.education.dashboard import dashboard_controller
from graphedu.api.services.education.exercise_attempt import exercise_attempt_controller
from graphedu.api.services.education.graphrag_task import graphrag_task_controller
from graphedu.api.services.education.knowledge_graph import knowledge_graph_controller
from graphedu.api.services.education.learning_event import learning_event_controller
from graphedu.api.services.education.learning_path import learning_path_controller
from graphedu.api.services.education.resource_progress import resource_progress_controller
from graphedu.api.services.education.student import student_controller
from graphedu.api.services.education.student_course import student_course_controller
from graphedu.api.services.education.teach_analytics import teach_analytics_controller
from graphedu.api.services.education.teacher import teacher_controller
from graphedu.api.services.generator import gen_controller
from graphedu.api.services.health import health_controller
from graphedu.api.services.system.admin_dashboard import admin_dashboard_controller
from graphedu.api.services.system.async_task import async_task_controller
from graphedu.api.services.system.auth import login_controller
from graphedu.api.services.system.dept import dept_controller
from graphedu.api.services.system.dict import dict_controller
from graphedu.api.services.system.function import function_controller
from graphedu.api.services.system.job import job_controller, job_webhook_controller
from graphedu.api.services.system.log import log_controller
from graphedu.api.services.system.role import role_controller
from graphedu.api.services.system.upload import upload_controller
from graphedu.api.services.system.user import user_controller

__all__ = ["add_routers", "controller_list"]

controller_list = [
    {"router": health_controller, "tags": ["健康检查"]},
    {"router": captcha_controller, "tags": ["通用模块-验证码"]},
    {"router": upload_controller, "tags": ["系统管理-文件上传"]},
    {"router": upload_proxy_controller, "tags": ["系统管理-文件代理"]},
    {"router": login_controller, "tags": ["系统管理-登录认证"]},
    {"router": admin_dashboard_controller, "tags": ["系统管理-管理员仪表盘"]},
    {"router": user_controller, "tags": ["系统管理-用户管理"]},
    {"router": role_controller, "tags": ["系统管理-角色管理"]},
    {"router": function_controller, "tags": ["系统管理-功能管理"]},
    {"router": dept_controller, "tags": ["系统管理-部门管理"]},
    {"router": dict_controller, "tags": ["系统管理-字典管理"]},
    {"router": log_controller, "tags": ["系统管理-日志管理"]},
    {"router": job_controller, "tags": ["系统管理-定时任务"]},
    {"router": job_webhook_controller, "tags": ["定时任务-Webhook触发"]},
    {"router": async_task_controller, "tags": ["系统管理-异步任务"]},
    {"router": student_controller, "tags": ["教育管理-学生管理"]},
    {"router": teacher_controller, "tags": ["教育管理-教师管理"]},
    {"router": course_controller, "tags": ["教育管理-课程管理"]},
    {"router": course_exercise_controller, "tags": ["教育管理-课程练习管理"]},
    {"router": exercise_attempt_controller, "tags": ["教育管理-习题作答记录"]},
    {"router": student_course_controller, "tags": ["教育管理-学生选课"]},
    {"router": chat_controller, "tags": ["教育管理-聊天会话"]},
    {"router": chapter_controller, "tags": ["教育管理-章节管理"]},
    {"router": chapter_resource_controller, "tags": ["教育管理-章节资料管理"]},
    {"router": resource_progress_controller, "tags": ["教育管理-资料阅读进度"]},
    {"router": graphrag_task_controller, "tags": ["教育管理-GraphRAG任务管理"]},
    {"router": knowledge_graph_controller, "tags": ["教育管理-知识图谱管理"]},
    {"router": teach_analytics_controller, "tags": ["教育管理-教师工作台分析"]},
    {"router": dashboard_controller, "tags": ["教育管理-首页仪表盘"]},
    {"router": learning_event_controller, "tags": ["教育管理-学习事件上报"]},
    {"router": learning_path_controller, "tags": ["教育管理-学习路径管理"]},
    {"router": gen_controller, "tags": ["系统管理-代码生成"]},
]


def add_routers(app: FastAPI) -> None:
    """Register all API routers to the FastAPI application.

    Args:
        app: The FastAPI application instance
    """
    for controller in controller_list:
        app.include_router(controller["router"], tags=controller["tags"])
