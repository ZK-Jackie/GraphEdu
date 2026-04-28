"""教育相关实体类
包含所有 edu_ 开头的数据库表对应的实体类
"""

from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CHAR,
    TEXT,
    TIMESTAMP,
    BigInteger,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

JsonLike = dict[str, Any] | list


class EduBase(DeclarativeBase):
    """教育模块 SQLAlchemy 2.0 声明式基类

    所有教育相关的 ORM 模型都应继承此基类

    使用方式:
        class EduModel(EduBase):
            __tablename__ = "edu_table"
            id: Mapped[int] = mapped_column(primary_key=True)
    """


# ============================================================================
# 1. 学生扩展信息表
# ============================================================================
class EduStudent(EduBase):
    """学生扩展信息表。"""

    __tablename__ = "edu_student"

    student_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="学生ID（关联user_id）")
    real_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="真实姓名")
    student_no: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, comment="学号")
    faculty: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="学院")
    major: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="专业")
    grade: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="年级")
    class_name: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="班级")
    gender: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="性别，对照 sys_user_sex（1男 2女 0未知 9其他）"
    )
    age: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="年龄")
    study_style: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="学习风格")
    study_habit: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="学习习惯")
    continue_day: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="连续签到天数")
    vip_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, comment="VIP等级")
    vip_expire_time: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, comment="VIP过期时间")
    total_study_time: Mapped[int | None] = mapped_column(Integer, default=0, comment="总学习时长（分钟）")
    course_count: Mapped[int | None] = mapped_column(Integer, default=0, comment="学习课程数")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="自我介绍")
    status: Mapped[str] = mapped_column(
        CHAR(1), default="0", comment="学生状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index("idx_edu_student_faculty_major", "faculty", "major"),
        Index("idx_edu_student_grade_class_name", "grade", "class_name"),
        Index("idx_edu_student_student_no", "student_no"),
        {"comment": "学生扩展信息表"},
    )


# ============================================================================
# 2. 教师扩展信息表
# ============================================================================
class EduTeacher(EduBase):
    """教师扩展信息表。"""

    __tablename__ = "edu_teacher"

    teacher_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="教师ID（关联user_id）")
    real_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="真实姓名")
    teacher_no: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, comment="工号")
    faculty: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="所属学院")
    title: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="职称: 教授/副教授/讲师/助教")
    research_direction: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="研究方向")
    max_student_count: Mapped[int] = mapped_column(Integer, nullable=False, default=100, comment="最大带教学生数")
    current_student_count: Mapped[int | None] = mapped_column(Integer, default=0, comment="当前学生数")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="个人简介")
    status: Mapped[str] = mapped_column(
        CHAR(1), default="0", comment="教师状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index("idx_edu_teacher_faculty", "faculty"),
        Index("idx_edu_teacher_title", "title"),
        Index("idx_edu_teacher_teacher_no", "teacher_no"),
        {"comment": "教师扩展信息表"},
    )


# ============================================================================
# 3. 课程表
# ============================================================================
class EduCourse(EduBase):
    """课程表。"""

    __tablename__ = "edu_course"

    course_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="课程ID")
    course_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, comment="课程代码")
    course_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="课程名称")
    faculty: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="所属学院")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="课程描述")
    cover_file_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="课程封面文件ID")
    # 课程扩展信息
    category: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="课程分类（如：计算机科学、数学、物理等）"
    )
    difficulty_level: Mapped[str] = mapped_column(CHAR(1), default="1", comment="难度级别（1初级 2中级 3高级）")
    total_hours: Mapped[int] = mapped_column(Integer, default=0, comment="总学时（小时）")
    course_outline: Mapped[str | None] = mapped_column(Text, nullable=True, comment="课程大纲（富文本）")
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True, comment="适用人群（富文本）")
    learning_goals: Mapped[str | None] = mapped_column(Text, nullable=True, comment="学习目标（富文本）")
    tags: Mapped[JsonLike | None] = mapped_column(
        JSONB, nullable=True, comment='课程标签，JSONB数组格式：["Python", "数据结构"]'
    )
    # 课程状态
    status: Mapped[str] = mapped_column(
        CHAR(1), default="0", comment="课程状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    is_public: Mapped[str] = mapped_column(CHAR(1), default="Y", comment="是否公开，对照 sys_data_option（Y是 N否）")
    student_count: Mapped[int] = mapped_column(Integer, default=0, comment="学生人数")
    view_count: Mapped[int] = mapped_column(Integer, default=0, comment="浏览次数")
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index("idx_edu_course_course_code", "course_code"),
        Index("idx_edu_course_status", "status"),
        Index("idx_edu_course_category", "category"),
        Index("idx_edu_course_difficulty_level", "difficulty_level"),
        {"comment": "课程信息表"},
    )


# ============================================================================
# 5. 课程与教师关联表
# ============================================================================
class EduCourseTeacher(EduBase):
    """课程与教师关联表。"""

    __tablename__ = "edu_course_teacher"

    course_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="课程ID")
    teacher_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="教师ID")
    role_type: Mapped[str] = mapped_column(
        String(32), default="instructor", comment="教师角色（instructor主讲/assistant助教/consultant顾问）"
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, comment="显示顺序")

    __table_args__ = (
        Index("idx_edu_course_teacher_course_id", "course_id"),
        Index("idx_edu_course_teacher_teacher_id", "teacher_id"),
        Index("idx_edu_course_teacher_role_type", "role_type"),
        {"comment": "课程与教师关联表"},
    )


# ============================================================================
# 7. 学生选课关联表
# ============================================================================
class EduStudentCourse(EduBase):
    """学生选课关联表。"""

    __tablename__ = "edu_student_course"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="学生ID")
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="课程ID")
    enroll_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="选课时间")
    progress: Mapped[int] = mapped_column(Integer, default=0, comment="学习进度（0-100）")
    last_study_time: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, comment="最后学习时间")

    __table_args__ = (
        Index("idx_edu_student_course_student_id_course_id", "student_id", "course_id"),
        {"comment": "学生选课关联表"},
    )


# ============================================================================
# 8. 对话会话表
# ============================================================================
class EduChatSession(EduBase):
    """对话会话表。"""

    __tablename__ = "edu_chat_session"

    session_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="会话ID")
    session_uuid: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, comment="会话UUID")
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="用户ID")
    course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="关联课程ID")
    chapter_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="关联章节ID（可选，用于章节级问答）"
    )
    content_ids: Mapped[JsonLike | None] = mapped_column(
        JSONB, nullable=True, comment="关联的资料ID列表（JSONB数组，用于AI上下文）"
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="会话标题")
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="上下文摘要")
    message_count: Mapped[int] = mapped_column(Integer, default=0, comment="消息数量")
    status: Mapped[str] = mapped_column(
        CHAR(1), default="0", comment="聊天会话状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )
    last_message_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="最后消息时间"
    )

    __table_args__ = (
        Index("idx_edu_chat_session_session_uuid", "session_uuid"),
        Index("idx_edu_chat_session_user_id_create_time", "user_id", "create_time"),
        Index("idx_edu_chat_session_course_id", "course_id"),
        Index("idx_edu_chat_session_chapter_id", "chapter_id"),
        {"comment": "对话会话表"},
    )


# ============================================================================
# 9. 知识图谱表
# ============================================================================
class EduKnowledgeGraph(EduBase):
    """知识图谱表。"""

    __tablename__ = "edu_knowledge_graph"

    graph_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="图谱ID")
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="课程ID")
    graph_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="图谱名称")
    graph_database: Mapped[str] = mapped_column(String(64), nullable=False, comment="AGE 图名称")
    version: Mapped[str] = mapped_column(String(16), default="1.0.0", comment="图谱版本号")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="图谱描述")
    total_nodes: Mapped[int | None] = mapped_column(Integer, default=0, comment="总节点数")
    total_relationships: Mapped[int | None] = mapped_column(Integer, default=0, comment="总关系数")
    node_type_stats: Mapped[JsonLike | None] = mapped_column(JSONB, nullable=True, comment="节点类型统计（JSONB格式）")
    relationship_type_stats: Mapped[JsonLike | None] = mapped_column(
        JSONB, nullable=True, comment="关系类型统计（JSONB格式）"
    )
    average_degree: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0, comment="平均度数")
    connectivity_score: Mapped[float | None] = mapped_column(Numeric(5, 4), default=0, comment="连通性评分")
    build_method: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="构建方法，对照 kg_build_method（nlp llm llm_assisted 等）"
    )
    build_info: Mapped[JsonLike | None] = mapped_column(
        JSONB, nullable=True, comment="构建信息（JSONB格式，包含构建参数、模型信息等）"
    )
    last_extended: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, comment="最后扩展时间")
    status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="知识图谱状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    is_draft: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="N", comment="是否草稿（Y待审核/N已确认）")
    task_status: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        default=None,
        comment="异步生成任务状态（pending/processing/success/failed），仅自动生成时有值",
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index("idx_knowledge_graph_course_id", "course_id"),
        Index("idx_knowledge_graph_graph_database", "graph_database"),
        Index("idx_knowledge_graph_build_method", "build_method"),
        Index("idx_knowledge_graph_status", "status"),
        {"comment": "知识图谱表"},
    )


# ============================================================================
# 10. 知识点-章节关联表
# ============================================================================
class EduKnowledgeNodeChapter(EduBase):
    """知识点-章节关联表。

    记录知识图谱中的知识点节点与章节的多对多关系。
    `node_uuid` 指向知识图谱中的知识点节点业务 UUID。
    """

    __tablename__ = "edu_knowledge_node_chapter"

    node_chapter_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="关系ID")
    chapter_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="章节ID")
    node_uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, comment="知识点业务UUID")
    relevance_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0, comment="知识点与章节的相关性评分")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="关系描述")
    is_primary: Mapped[str] = mapped_column(CHAR(1), default="N", comment="是否主要关联（Y是 N否）")
    status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="关系状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index("idx_knowledge_node_chapter_chapter_id", "chapter_id"),
        Index("idx_knowledge_node_chapter_node_uuid", "node_uuid"),
        {"comment": "知识点-章节关联表"},
    )


# ============================================================================
# 学生学习事件表（唯一的真相来源，所有统计由此表聚合计算）
# ============================================================================
class EduStudentLearningEvent(EduBase):
    """学生学习事件明细表（唯一的真相来源）。"""

    __tablename__ = "edu_student_learning_event"

    event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="事件ID")
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="学生ID")
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="课程ID")
    session_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="会话ID")
    chapter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="关联章节ID")
    node_uuid: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, comment="知识点业务UUID")
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="事件类型")
    event_source: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="事件来源（chat/ui/tool/system）"
    )
    message_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="关联的聊天消息ID（用于回溯对话上下文）"
    )
    event_content: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="事件文本内容（question类型存用户原始问题）"
    )
    event_payload: Mapped[JsonLike | None] = mapped_column(JSONB, nullable=True, comment="事件扩展数据")

    # 事件持续时长（秒），用于记录查阅时长等
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="事件持续时长（秒）")
    effective_duration_seconds: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="有效持续时长（秒），排除空闲"
    )
    is_review: Mapped[bool | None] = mapped_column(nullable=True, default=False, comment="是否为复习")

    event_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="事件发生时间")
    status: Mapped[str] = mapped_column(CHAR(1), default="0", comment="状态（0正常 1停用 2已删除）")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index(
            "idx_edu_student_learning_event_student_course_time",
            "student_id",
            "course_id",
            "event_time",
        ),
        Index("idx_edu_student_learning_event_node_type", "node_uuid", "event_type", "event_time"),
        Index("idx_edu_student_learning_event_session_time", "session_id", "event_time"),
        Index("idx_edu_student_learning_event_course_type_time", "course_id", "event_type", "event_time"),
        Index(
            "idx_edu_student_learning_event_event_payload_gin",
            "event_payload",
            postgresql_using="gin",
        ),
        # 新增：日期索引，方便日级统计
        Index("idx_edu_student_learning_event_date", "student_id", "course_id", text("DATE(event_time)")),
        {"comment": "学生学习事件明细表（唯一的真相来源）"},
    )


# ============================================================================
# 学生知识点掌握度评估记录表（成长轨迹）
# ============================================================================
class EduStudentMastery(EduBase):
    """学生知识点掌握度评估记录表（成长轨迹，每次AI评估生成一条记录）。"""

    __tablename__ = "edu_student_mastery"

    mastery_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="评估记录ID")
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="学生ID")
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="课程ID")
    node_uuid: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, comment="知识点业务UUID")
    session_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="触发评估的会话ID")
    mastery_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True, comment="掌握度评分（0-100）")
    mastery_level: Mapped[str | None] = mapped_column(
        String(16), nullable=True, comment="掌握等级（unknown/low/medium/high）"
    )
    trigger_type: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="触发类型（quiz_complete/periodic/manual/system）"
    )
    reason: Mapped[str | None] = mapped_column(TEXT, nullable=True, comment="AI 评估理由")
    assessed_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="评估时间")
    status: Mapped[str] = mapped_column(CHAR(1), default="0", comment="状态（0正常 1停用 2已删除）")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index("idx_edu_student_mastery_student_course_node", "student_id", "course_id", "node_uuid"),
        Index("idx_edu_student_mastery_student_course_time", "student_id", "course_id", assessed_at),
        Index("idx_edu_student_mastery_level", "mastery_level"),
        {"comment": "学生知识点掌握度评估记录表（成长轨迹）"},
    )


class EduKnowledgePointEmbedding(EduBase):
    """知识点向量嵌入表（pgvector）。"""

    __tablename__ = "edu_knowledge_point_embedding"

    node_uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, comment="知识点业务UUID（对应AGE n.uuid）"
    )
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="课程ID")
    title: Mapped[str] = mapped_column(Text, nullable=False, comment="知识点标题")
    embedding: Mapped[list[int | float]] = mapped_column(
        Vector(1024), nullable=False, comment="知识点向量嵌入（1024维）"
    )


# ============================================================================
# 课程章节表
# ============================================================================
class EduChapter(EduBase):
    """课程章节表。"""

    __tablename__ = "edu_chapter"

    chapter_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="章节ID")
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="课程ID")
    parent_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment="父章节ID（0表示根节点）")
    chapter_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="章节名称")
    chapter_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="章节序号（用于排序）")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="章节描述")
    embedding: Mapped[list[int | float]] = mapped_column(Vector(1024), nullable=True, comment="章节向量嵌入（1024维）")
    status: Mapped[str] = mapped_column(
        CHAR(1), default="0", comment="章节状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index("idx_edu_chapter_course_id", "course_id"),
        Index("idx_edu_chapter_parent_id", "parent_id"),
        Index("idx_edu_chapter_status", "status"),
        {"comment": "课程章节表"},
    )


# ============================================================================
# 章节学习资料表
# ============================================================================
class EduChapterResource(EduBase):
    """章节学习资料表

    数据库表名为 edu_resource，Python 层使用 resource_* 命名规范以保持一致性。
    """

    __tablename__ = "edu_resource"

    resource_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="资料ID")
    chapter_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="所属章节ID")
    resource_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="资料名称")
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="资料类型（video/document/text）")
    file_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="文件ID（引用sys_upload.file_id）")
    resource_url: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="外部链接URL")
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True, comment="描述")
    resource_data: Mapped[JsonLike | None] = mapped_column(JSONB, nullable=True, comment="扩展数据（JSONB格式）")
    # 解析相关字段
    text_file_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="纯文本文件ID（引用sys_upload.file_id，PDF解析后的文本内容）"
    )
    parse_status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="解析状态（0待处理 1处理中 2处理成功 3处理失败）"
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="显示顺序")
    is_visible: Mapped[str] = mapped_column(CHAR(1), default="Y", comment="是否可见（Y/N）")
    status: Mapped[str] = mapped_column(CHAR(1), default="0", comment="状态（0正常 1停用 2已删除）")
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index("idx_edu_chapter_content_chapter_id", "chapter_id"),
        Index("idx_edu_chapter_content_content_type", "resource_type"),
        Index("idx_edu_chapter_content_display_order", "chapter_id", "display_order"),
        {"comment": "章节学习资料表"},
    )


# ============================================================================
# 课程评价表
# ============================================================================
class EduCourseReview(EduBase):
    """课程评价表。"""

    __tablename__ = "edu_course_review"

    review_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="评价ID")
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="课程ID")
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="学生ID")
    rating: Mapped[int] = mapped_column(Integer, nullable=False, comment="整体评分（1-5星）")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="评价内容")
    dimension_scores: Mapped[JsonLike | None] = mapped_column(JSONB, nullable=True, comment="分项评分（JSONB格式）")
    like_count: Mapped[int] = mapped_column(Integer, default=0, comment="点赞数")
    status: Mapped[str] = mapped_column(CHAR(1), default="0", comment="状态（0正常 1停用 2已删除）")
    is_visible: Mapped[str] = mapped_column(CHAR(1), default="Y", comment="是否可见（Y/N）")
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index("idx_edu_course_review_course_id", "course_id"),
        Index("idx_edu_course_review_student_id", "student_id"),
        Index("idx_edu_course_review_rating", "rating"),
        Index("idx_edu_course_review_create_time", "create_time"),
        {"comment": "课程评价表"},
    )


# ============================================================================
# 课程练习表
# ============================================================================
class EduCourseExercise(EduBase):
    """课程练习表。"""

    __tablename__ = "edu_course_exercise"

    exercise_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="练习ID")
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="课程ID")
    chapter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="章节ID（可选）")
    exercise: Mapped[JsonLike | None] = mapped_column(
        JSONB, nullable=True, comment="练习内容（JSONB格式，包含题目、选项、答案等信息）"
    )
    source: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="练习来源（如：教师上传、系统生成等）"
    )
    status: Mapped[str] = mapped_column(
        CHAR(1), default="0", comment="练习状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index("idx_edu_course_exercise_course_id", "course_id"),
        Index("idx_edu_course_exercise_chapter_id", "chapter_id"),
        Index("idx_edu_course_exercise_status", "status"),
        {"comment": "课程练习表"},
    )


# ============================================================================
# 习题作答记录表
# ============================================================================
class EduExerciseAttempt(EduBase):
    """习题作答记录表。"""

    __tablename__ = "edu_exercise_attempt"

    attempt_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="作答记录ID")
    exercise_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="关联习题ID（FK → edu_course_exercise）"
    )
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="学生ID")
    student_answer: Mapped[JsonLike | None] = mapped_column(
        JSONB, nullable=True, comment="学生答案（JSONB，支持多选等复杂答案）"
    )
    is_correct: Mapped[bool | None] = mapped_column(nullable=True, comment="是否正确（bool，简答题可为 null 待批改）")
    time_spent: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="用时（秒）")
    attempt_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="作答时间")

    __table_args__ = (
        Index("idx_edu_exercise_attempt_exercise_id", "exercise_id"),
        Index("idx_edu_exercise_attempt_student_id", "student_id"),
        Index("idx_edu_exercise_attempt_attempt_time", "attempt_time"),
        {"comment": "习题作答记录表"},
    )


# ============================================================================
# GraphRAG 任务表
# ============================================================================
class EduGraphRAGTask(EduBase):
    """GraphRAG 任务表。"""

    __tablename__ = "edu_graphrag_task"

    task_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="关联课程ID")
    resource_ids: Mapped[list[int]] = mapped_column(JSONB, nullable=False, comment="处理的文档ID列表（JSONB数组）")
    task_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="任务状态（pending待处理/processing处理中/success成功/failed失败）",
    )
    task_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="任务类型（如：graphrag_build构建、graphrag_update更新等）"
    )
    task_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="任务最后信息（如果任务失败，记录错误详情）"
    )
    entity_types: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True, comment="涉及的实体类型列表（JSONB数组，对照知识图谱中的实体类型）"
    )
    prompt_template: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="使用的提示词模板（从 default/en default/zh edu/en edu/zh中选择）",
    )
    custom_prompt_template: Mapped[JsonLike | None] = mapped_column(
        JSONB, nullable=True, comment="自定义提示词模板（JSONB格式，允许用户覆盖默认模板中的某些部分）"
    )
    stats: Mapped[JsonLike | None] = mapped_column(
        JSONB, nullable=True, comment="任务统计信息（JSONB格式，包含处理的文档数量、提取的实体数量、构建的关系数量等）"
    )
    start_time: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, comment="任务开始时间")
    end_time: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, comment="任务结束时间")
    enabled: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="N", comment="是否启用，对照 sys_data_option（Y是 N否）"
    )
    status: Mapped[str] = mapped_column(
        CHAR(1), default="0", comment="任务记录状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        Index("idx_edu_graphrag_task_course_id", "course_id"),
        Index("idx_edu_graphrag_task_task_status", "task_status"),
        Index("idx_edu_graphrag_task_task_type", "task_type"),
        Index("idx_edu_graphrag_task_create_time", "create_time"),
        {"comment": "GraphRAG 任务表"},
    )


# ============================================================================
# 学生资料阅读进度表
# ============================================================================
class EduStudentResourceProgress(EduBase):
    """学生资料阅读进度表。"""

    __tablename__ = "edu_student_resource_progress"

    progress_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="进度记录ID")
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="学生ID")
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="课程ID")
    chapter_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="章节ID")
    resource_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="资料ID（关联edu_resource.resource_id）"
    )
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="资料类型（video/document/text）")

    # 进度数据
    completion_rate: Mapped[int] = mapped_column(Integer, default=0, comment="完成度（0-100）")
    is_completed: Mapped[str] = mapped_column(CHAR(1), default="N", comment="是否完成（Y/N）")
    view_count: Mapped[int] = mapped_column(Integer, default=0, comment="阅读次数")
    total_duration: Mapped[int] = mapped_column(Integer, default=0, comment="累计阅读时长（秒）")
    effective_duration: Mapped[int] = mapped_column(Integer, default=0, comment="有效阅读时长（秒），排除空闲时间")
    review_duration: Mapped[int] = mapped_column(
        Integer, default=0, comment="复习时长（秒），资源完成后再次阅读的有效时长"
    )
    first_read_duration: Mapped[int] = mapped_column(
        Integer, default=0, comment="首次阅读时长（秒），资源完成前的有效累计时长"
    )

    # 位置快照（用于断点续学）
    last_position: Mapped[JsonLike | None] = mapped_column(
        JSONB, nullable=True, comment="最后阅读位置（JSONB格式，如 {page:12}、{video_second:145.5}）"
    )

    # 时间
    first_view_time: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, comment="首次阅读时间")
    last_view_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="最后阅读时间"
    )
    complete_time: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, comment="完成时间")

    status: Mapped[str] = mapped_column(CHAR(1), default="0", comment="状态（0正常 1停用 2已删除）")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )

    __table_args__ = (
        UniqueConstraint("student_id", "resource_id", name="uk_edu_srp_student_resource"),
        Index("idx_edu_srp_student_course", "student_id", "course_id"),
        Index("idx_edu_srp_chapter", "chapter_id"),
        Index("idx_edu_srp_resource_type", "resource_type"),
        Index("idx_edu_srp_is_completed", "is_completed"),
        Index("idx_edu_srp_student_chapter", "student_id", "chapter_id"),
        {"comment": "学生资料阅读进度表"},
    )


# ============================================================================
# 习题-知识点关联表
# ============================================================================
class EduExerciseKnowledgePoint(EduBase):
    """习题-知识点关联表。"""

    __tablename__ = "edu_exercise_knowledge_point"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    exercise_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="习题ID（关联 edu_course_exercise）")
    node_uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, comment="知识点业务UUID")
    relevance_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0, comment="关联相关性评分")
    source: Mapped[str] = mapped_column(String(16), default="auto", comment="关联来源（auto自动/manual手动）")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")

    __table_args__ = (
        Index("idx_ekp_exercise", "exercise_id"),
        Index("idx_ekp_node", "node_uuid"),
        {"comment": "习题-知识点关联表"},
    )
