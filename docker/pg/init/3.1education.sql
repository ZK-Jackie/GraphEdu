-- ============================================================================
-- 7. 学生扩展信息表
-- ============================================================================
DROP TABLE IF EXISTS public.edu_student CASCADE;
CREATE TABLE public.edu_student
(
    student_id       BIGINT PRIMARY KEY,
    real_name        VARCHAR(64) NOT NULL,
    student_no       VARCHAR(32) UNIQUE,
    faculty          VARCHAR(64),
    major            VARCHAR(64),
    grade            VARCHAR(20),
    class_name       VARCHAR(64),
    gender           SMALLINT,
    age              INTEGER,

    -- 学习相关
    study_style      VARCHAR(255),
    study_habit      VARCHAR(255),
    continue_day     INTEGER     NOT NULL DEFAULT 0,

    -- 会员相关
    vip_level        SMALLINT    NOT NULL DEFAULT 0,
    vip_expire_time  TIMESTAMP,

    -- 统计信息
    total_study_time INTEGER              DEFAULT 0,
    course_count     INTEGER              DEFAULT 0,
    description      TEXT,

    status           CHAR(1)     NOT NULL DEFAULT '0',
    create_by        BIGINT               DEFAULT NULL,
    create_time      TIMESTAMP            DEFAULT CURRENT_TIMESTAMP,
    update_by        BIGINT               DEFAULT NULL,
    update_time      TIMESTAMP            DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.edu_student IS '学生扩展信息表';
COMMENT ON COLUMN public.edu_student.student_id IS '学生ID（关联user_id）';
COMMENT ON COLUMN public.edu_student.real_name IS '真实姓名';
COMMENT ON COLUMN public.edu_student.student_no IS '学号';
COMMENT ON COLUMN public.edu_student.faculty IS '学院';
COMMENT ON COLUMN public.edu_student.major IS '专业';
COMMENT ON COLUMN public.edu_student.grade IS '年级';
COMMENT ON COLUMN public.edu_student.class_name IS '班级';
COMMENT ON COLUMN public.edu_student.gender IS '性别，对照 sys_user_sex（1男 2女 0未知 9其他）';
COMMENT ON COLUMN public.edu_student.age IS '年龄';
COMMENT ON COLUMN public.edu_student.study_style IS '学习风格';
COMMENT ON COLUMN public.edu_student.study_habit IS '学习习惯';
COMMENT ON COLUMN public.edu_student.continue_day IS '连续签到天数';
COMMENT ON COLUMN public.edu_student.vip_level IS 'VIP等级';
COMMENT ON COLUMN public.edu_student.vip_expire_time IS 'VIP过期时间';
COMMENT ON COLUMN public.edu_student.total_study_time IS '总学习时长（分钟）';
COMMENT ON COLUMN public.edu_student.course_count IS '学习课程数';
COMMENT ON COLUMN public.edu_student.description IS '自我介绍';
COMMENT ON COLUMN public.edu_student.status IS '学生状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN public.edu_student.create_by IS '创建者';
COMMENT ON COLUMN public.edu_student.create_time IS '创建时间';
COMMENT ON COLUMN public.edu_student.update_by IS '更新者';
COMMENT ON COLUMN public.edu_student.update_time IS '更新时间（由应用程序更新）';

CREATE INDEX idx_edu_student_faculty_major ON public.edu_student (faculty, major);
CREATE INDEX idx_edu_student_grade_class_name ON public.edu_student (grade, class_name);
CREATE INDEX idx_edu_student_student_no ON public.edu_student (student_no);

-- ============================================================================
-- 8. 教师扩展信息表
-- ============================================================================
DROP TABLE IF EXISTS public.edu_teacher CASCADE;
CREATE TABLE public.edu_teacher
(
    teacher_id            BIGINT PRIMARY KEY,
    real_name             VARCHAR(64) NOT NULL,
    teacher_no            VARCHAR(32) UNIQUE,
    faculty               VARCHAR(64),
    title                 VARCHAR(32),
    research_direction    VARCHAR(255),

    -- 教学相关
    max_student_count     INTEGER     NOT NULL DEFAULT 100,
    current_student_count INTEGER              DEFAULT 0,

    description           TEXT,

    status                CHAR(1)     NOT NULL DEFAULT '0',
    create_by             BIGINT               DEFAULT NULL,
    create_time           TIMESTAMP            DEFAULT CURRENT_TIMESTAMP,
    update_by             BIGINT               DEFAULT NULL,
    update_time           TIMESTAMP            DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.edu_teacher IS '教师扩展信息表';
COMMENT ON COLUMN public.edu_teacher.teacher_id IS '教师ID（关联user_id）';
COMMENT ON COLUMN public.edu_teacher.real_name IS '真实姓名';
COMMENT ON COLUMN public.edu_teacher.teacher_no IS '工号';
COMMENT ON COLUMN public.edu_teacher.faculty IS '所属学院';
COMMENT ON COLUMN public.edu_teacher.title IS '职称，对照 public.edu_professional_title（011教授 012副教授 013讲师等）';
COMMENT ON COLUMN public.edu_teacher.research_direction IS '研究方向';
COMMENT ON COLUMN public.edu_teacher.max_student_count IS '最大带教学生数';
COMMENT ON COLUMN public.edu_teacher.current_student_count IS '当前学生数';
COMMENT ON COLUMN public.edu_teacher.description IS '个人简介';
COMMENT ON COLUMN public.edu_teacher.status IS '教师状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN public.edu_teacher.create_by IS '创建者';
COMMENT ON COLUMN public.edu_teacher.create_time IS '创建时间';
COMMENT ON COLUMN public.edu_teacher.update_by IS '更新者';
COMMENT ON COLUMN public.edu_teacher.update_time IS '更新时间（由应用程序更新）';

CREATE INDEX idx_edu_teacher_faculty ON public.edu_teacher (faculty);
CREATE INDEX idx_edu_teacher_title ON public.edu_teacher (title);
CREATE INDEX idx_edu_teacher_teacher_no ON public.edu_teacher (teacher_no);

-- ============================================================================
-- 9. 课程表（用于知识问答和学习管理）
-- ============================================================================
DROP TABLE IF EXISTS public.edu_course CASCADE;
CREATE TABLE public.edu_course
(
    course_id        BIGSERIAL PRIMARY KEY,
    course_code      VARCHAR(32) UNIQUE NOT NULL,
    course_name      VARCHAR(128)       NOT NULL,
    faculty          VARCHAR(64),
    description      TEXT,
    cover_file_id    BIGINT, -- 课程封面文件ID（引用sys_upload）

    -- 课程状态
    status           CHAR(1)   DEFAULT '0',
    is_public        CHAR(1)   DEFAULT 'Y',

    -- 统计信息
    student_count    INTEGER   DEFAULT 0,
    view_count       INTEGER   DEFAULT 0,

    -- 课程扩展信息
    category         VARCHAR(64),
    difficulty_level CHAR(1)   DEFAULT '1',
    total_hours      INTEGER   DEFAULT 0,
    course_outline   TEXT,
    target_audience  TEXT,
    learning_goals   TEXT,
    tags             JSONB,

    -- 时间信息
    create_by        BIGINT    DEFAULT NULL,
    create_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by        BIGINT    DEFAULT NULL,
    update_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.edu_course IS '课程信息表';
COMMENT ON COLUMN public.edu_course.course_id IS '课程ID';
COMMENT ON COLUMN public.edu_course.course_code IS '课程代码';
COMMENT ON COLUMN public.edu_course.course_name IS '课程名称';
COMMENT ON COLUMN public.edu_course.faculty IS '所属学院';
COMMENT ON COLUMN public.edu_course.description IS '课程描述';
COMMENT ON COLUMN public.edu_course.cover_file_id IS '课程封面文件ID';
COMMENT ON COLUMN public.edu_course.status IS '课程状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN public.edu_course.is_public IS '是否公开，对照 sys_data_option（Y是 N否）';
COMMENT ON COLUMN public.edu_course.student_count IS '学生人数';
COMMENT ON COLUMN public.edu_course.view_count IS '浏览次数';
COMMENT ON COLUMN public.edu_course.create_by IS '创建者';
COMMENT ON COLUMN public.edu_course.create_time IS '创建时间';
COMMENT ON COLUMN public.edu_course.update_by IS '更新者';
COMMENT ON COLUMN public.edu_course.update_time IS '更新时间（由应用程序更新）';
COMMENT ON COLUMN public.edu_course.category IS '课程分类（如：计算机科学、数学、物理等）';
COMMENT ON COLUMN public.edu_course.difficulty_level IS '难度级别（1初级 2中级 3高级）';
COMMENT ON COLUMN public.edu_course.total_hours IS '总学时（小时）';
COMMENT ON COLUMN public.edu_course.course_outline IS '课程大纲（富文本）';
COMMENT ON COLUMN public.edu_course.target_audience IS '适用人群（富文本）';
COMMENT ON COLUMN public.edu_course.learning_goals IS '学习目标（富文本）';
COMMENT ON COLUMN public.edu_course.tags IS '课程标签，JSONB数组格式：["Python", "数据结构"]';


CREATE INDEX idx_edu_course_course_code ON public.edu_course (course_code);
CREATE INDEX idx_edu_course_status ON public.edu_course (status);
CREATE INDEX idx_edu_course_category ON public.edu_course (category);
CREATE INDEX idx_edu_course_difficulty_level ON public.edu_course (difficulty_level);

-- ============================================================================
-- 10. 课程章节表
-- ============================================================================
DROP TABLE IF EXISTS public.edu_chapter CASCADE;
CREATE TABLE public.edu_chapter
(
    chapter_id   BIGSERIAL PRIMARY KEY,
    course_id    BIGINT       NOT NULL,
    parent_id    BIGINT       NOT NULL DEFAULT 0,
    chapter_name VARCHAR(128) NOT NULL,
    chapter_no   INTEGER      NOT NULL DEFAULT 0,
    description  TEXT,
    embedding    VECTOR(1024),
    status       CHAR(1)               DEFAULT '0',
    create_by    BIGINT                DEFAULT NULL,
    create_time  TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    update_by    BIGINT                DEFAULT NULL,
    update_time  TIMESTAMP             DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE public.edu_chapter IS '课程章节表';
COMMENT ON COLUMN public.edu_chapter.chapter_id IS '章节ID';
COMMENT ON COLUMN public.edu_chapter.course_id IS '课程ID';
COMMENT ON COLUMN public.edu_chapter.parent_id IS '父章节ID（0表示根节点）';
COMMENT ON COLUMN public.edu_chapter.chapter_name IS '章节名称';
COMMENT ON COLUMN public.edu_chapter.chapter_no IS '章节序号（用于排序）';
COMMENT ON COLUMN public.edu_chapter.description IS '章节描述';
COMMENT ON COLUMN public.edu_chapter.embedding IS '章节内容向量（用于知识问答检索）';
COMMENT ON COLUMN public.edu_chapter.status IS '章节状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN public.edu_chapter.create_by IS '创建者';
COMMENT ON COLUMN public.edu_chapter.create_time IS '创建时间';
COMMENT ON COLUMN public.edu_chapter.update_by IS '更新者';
COMMENT ON COLUMN public.edu_chapter.update_time IS '更新时间（由应用程序更新）';

-- 索引
CREATE INDEX idx_edu_chapter_course_id ON public.edu_chapter (course_id);
CREATE INDEX idx_edu_chapter_parent_id ON public.edu_chapter (parent_id);
CREATE INDEX idx_edu_chapter_status ON public.edu_chapter (status);
CREATE INDEX idx_edu_chapter_embedding ON public.edu_chapter USING ivfflat (embedding public.vector_cosine_ops);

-- ============================================================================
-- 10.1 章节学习资料表
-- ============================================================================
DROP TABLE IF EXISTS public.edu_resource CASCADE;
CREATE TABLE public.edu_resource
(
    resource_id   BIGSERIAL PRIMARY KEY,
    chapter_id    BIGINT       NOT NULL,
    resource_name VARCHAR(128) NOT NULL,
    resource_type VARCHAR(32)  NOT NULL,
    file_id       BIGINT,
    resource_url  VARCHAR(512),
    resource_data JSONB,
    text_file_id  INTEGER,
    parse_status  CHAR(1)               DEFAULT '0',
    display_order INTEGER      NOT NULL DEFAULT 0,
    description   VARCHAR(2048),
    is_visible    CHAR(1)               DEFAULT 'Y',
    status        CHAR(1)               DEFAULT '0',
    create_by     BIGINT,
    create_time   TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    update_by     BIGINT,
    update_time   TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_edu_resource_chapter_order UNIQUE (chapter_id, resource_name)
);

COMMENT ON TABLE public.edu_resource IS '章节学习资料表';
COMMENT ON COLUMN public.edu_resource.resource_id IS '资料ID';
COMMENT ON COLUMN public.edu_resource.chapter_id IS '所属章节ID';
COMMENT ON COLUMN public.edu_resource.resource_name IS '资料名称';
COMMENT ON COLUMN public.edu_resource.resource_type IS '资料类型（video视频/document文档/text文本）';
COMMENT ON COLUMN public.edu_resource.file_id IS '文件ID（引用sys_upload.file_id）';
COMMENT ON COLUMN public.edu_resource.resource_url IS '用户提供的外部链接URL';
COMMENT ON COLUMN public.edu_resource.resource_data IS '扩展数据（JSONB格式，存储视频时长、文档页数等元数据），如果是 pdf 将展示与 markdown的对照关系';
COMMENT ON COLUMN public.edu_resource.text_file_id IS '解析后的文本文件ID（引用sys_upload.file_id），用于存储文档解析后的纯文本内容，供AI知识问答使用）';
COMMENT ON COLUMN public.edu_resource.parse_status IS '文档解析状态（0未解析 1解析中 2解析成功 3解析失败）';
COMMENT ON COLUMN public.edu_resource.display_order IS '显示顺序';
COMMENT ON COLUMN public.edu_resource.description IS '资料描述';
COMMENT ON COLUMN public.edu_resource.is_visible IS '是否可见（Y/N）';
COMMENT ON COLUMN public.edu_resource.status IS '状态（0正常 1停用 2已删除）';
COMMENT ON COLUMN public.edu_resource.create_by IS '创建者';
COMMENT ON COLUMN public.edu_resource.create_time IS '创建时间';
COMMENT ON COLUMN public.edu_resource.update_by IS '更新者';
COMMENT ON COLUMN public.edu_resource.update_time IS '更新时间';

CREATE INDEX idx_edu_resource_chapter_id ON public.edu_resource (chapter_id);
CREATE INDEX idx_edu_resource_type ON public.edu_resource (resource_type);
CREATE INDEX idx_edu_resource_chapter_order ON public.edu_resource (chapter_id, display_order);

-- ============================================================================
-- 11. 课程与教师关联表
-- ============================================================================
DROP TABLE IF EXISTS public.edu_course_teacher CASCADE;
CREATE TABLE public.edu_course_teacher
(
    course_id     BIGINT NOT NULL,
    teacher_id    BIGINT NOT NULL,
    role_type     VARCHAR(32) DEFAULT 'instructor',
    display_order INTEGER     DEFAULT 0,
    PRIMARY KEY (course_id, teacher_id)
);

COMMENT ON TABLE public.edu_course_teacher IS '课程与教师关联表';
COMMENT ON COLUMN public.edu_course_teacher.course_id IS '课程 ID';
COMMENT ON COLUMN public.edu_course_teacher.teacher_id IS '教师 ID';
COMMENT ON COLUMN public.edu_course_teacher.role_type IS '教师角色（instructor主讲/assistant助教/consultant顾问）';
COMMENT ON COLUMN public.edu_course_teacher.display_order IS '显示顺序';

CREATE INDEX idx_edu_course_teacher_role_type ON public.edu_course_teacher (role_type);


-- ============================================================================
-- 13. 学生选课关联表
-- ============================================================================
DROP TABLE IF EXISTS public.edu_student_course CASCADE;
CREATE TABLE public.edu_student_course
(
    id              BIGSERIAL PRIMARY KEY,
    student_id      BIGINT NOT NULL,
    course_id       BIGINT NOT NULL,
    enroll_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    progress        INTEGER   DEFAULT 0,
    last_study_time TIMESTAMP,
    UNIQUE (student_id, course_id)
);

COMMENT ON TABLE public.edu_student_course IS '学生选课关联表';
COMMENT ON COLUMN public.edu_student_course.id IS '记录ID';
COMMENT ON COLUMN public.edu_student_course.student_id IS '学生ID';
COMMENT ON COLUMN public.edu_student_course.course_id IS '课程ID';
COMMENT ON COLUMN public.edu_student_course.enroll_time IS '选课时间';
COMMENT ON COLUMN public.edu_student_course.progress IS '学习进度（0-100）';
COMMENT ON COLUMN public.edu_student_course.last_study_time IS '最后学习时间';

CREATE INDEX idx_edu_student_course_student_id_course_id ON public.edu_student_course (student_id, course_id);

-- ============================================================================
-- 14. 对话会话表（知识问答记录）
-- ============================================================================
DROP TABLE IF EXISTS public.edu_chat_session CASCADE;
CREATE TABLE public.edu_chat_session
(
    session_id        BIGSERIAL PRIMARY KEY,
    session_uuid      VARCHAR(64) UNIQUE NOT NULL,
    user_id           BIGINT             NOT NULL,
    course_id         BIGINT,
    chapter_id        BIGINT,
    content_ids       JSONB,
    title             VARCHAR(255),

    -- 对话上下文
    context_summary   TEXT,
    message_count     INTEGER   DEFAULT 0,

    -- 状态信息
    status            CHAR(1)   DEFAULT '0',

    -- 时间信息
    create_by         BIGINT    DEFAULT NULL,
    create_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by         BIGINT    DEFAULT NULL,
    update_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.edu_chat_session IS '对话会话表';
COMMENT ON COLUMN public.edu_chat_session.session_id IS '会话ID';
COMMENT ON COLUMN public.edu_chat_session.session_uuid IS '会话UUID';
COMMENT ON COLUMN public.edu_chat_session.user_id IS '用户ID';
COMMENT ON COLUMN public.edu_chat_session.course_id IS '关联课程ID';
COMMENT ON COLUMN public.edu_chat_session.chapter_id IS '关联章节ID（可选，用于章节级问答）';
COMMENT ON COLUMN public.edu_chat_session.content_ids IS '关联的资料ID列表（JSONB数组，用于AI上下文）';
COMMENT ON COLUMN public.edu_chat_session.title IS '会话标题';
COMMENT ON COLUMN public.edu_chat_session.context_summary IS '上下文摘要';
COMMENT ON COLUMN public.edu_chat_session.message_count IS '消息数量';
COMMENT ON COLUMN public.edu_chat_session.status IS '聊天会话状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN public.edu_chat_session.create_by IS '创建者';
COMMENT ON COLUMN public.edu_chat_session.create_time IS '创建时间';
COMMENT ON COLUMN public.edu_chat_session.update_by IS '更新者';
COMMENT ON COLUMN public.edu_chat_session.update_time IS '更新时间（由应用程序更新）';
COMMENT ON COLUMN public.edu_chat_session.last_message_time IS '最后消息时间';

CREATE INDEX idx_edu_chat_session_session_uuid ON public.edu_chat_session (session_uuid);
CREATE INDEX idx_edu_chat_session_user_id_create_time ON public.edu_chat_session (user_id, create_time DESC);
CREATE INDEX idx_edu_chat_session_course_id ON public.edu_chat_session (course_id);
CREATE INDEX idx_edu_chat_session_chapter_id ON public.edu_chat_session (chapter_id);

-- ============================================================================
-- 15. 知识图谱信息表
-- ============================================================================
DROP TABLE IF EXISTS public.edu_knowledge_graph CASCADE;
CREATE TABLE public.edu_knowledge_graph
(
    graph_id                BIGSERIAL PRIMARY KEY,
    course_id               BIGINT       NOT NULL,
    graph_name              VARCHAR(128) NOT NULL,
    graph_database          VARCHAR(64)  NOT NULL,
    version                 VARCHAR(16)           DEFAULT '1.0.0',
    description             TEXT,
    -- 图谱统计信息
    total_nodes             INT                   DEFAULT 0,
    total_relationships     INT                   DEFAULT 0,
    -- 节点/关系类型统计 (JSON格式)
    node_type_stats         JSONB,
    relationship_type_stats JSONB,
    -- 图谱质量指标
    average_degree          DECIMAL(5, 2)         DEFAULT 0,
    connectivity_score      DECIMAL(5, 4)         DEFAULT 0,
    -- 构建信息
    build_method            VARCHAR(32),
    build_info              JSONB,
    last_extended           TIMESTAMP,
    -- 状态和管理
    is_draft                 CHAR(1)      DEFAULT 'N',
    task_status             VARCHAR(32)           DEFAULT NULL,
    status                  CHAR(1)      NOT NULL DEFAULT '0',
    create_by               BIGINT                DEFAULT NULL,
    create_time             TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    update_by               BIGINT                DEFAULT NULL,
    update_time             TIMESTAMP             DEFAULT CURRENT_TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE public.edu_knowledge_graph IS '知识图谱信息表';
COMMENT ON COLUMN public.edu_knowledge_graph.graph_id IS '图谱ID';
COMMENT ON COLUMN public.edu_knowledge_graph.course_id IS '课程ID';
COMMENT ON COLUMN public.edu_knowledge_graph.graph_name IS '图谱名称';
COMMENT ON COLUMN public.edu_knowledge_graph.graph_database IS '图数据库名称';
COMMENT ON COLUMN public.edu_knowledge_graph.version IS '图谱版本号';
COMMENT ON COLUMN public.edu_knowledge_graph.description IS '图谱描述';
COMMENT ON COLUMN public.edu_knowledge_graph.total_nodes IS '总节点数';
COMMENT ON COLUMN public.edu_knowledge_graph.total_relationships IS '总关系数';
COMMENT ON COLUMN public.edu_knowledge_graph.node_type_stats IS '节点类型统计（JSONB格式）';
COMMENT ON COLUMN public.edu_knowledge_graph.relationship_type_stats IS '关系类型统计（JSONB格式）';
COMMENT ON COLUMN public.edu_knowledge_graph.average_degree IS '平均度数';
COMMENT ON COLUMN public.edu_knowledge_graph.connectivity_score IS '连通性评分';
COMMENT ON COLUMN public.edu_knowledge_graph.build_method IS '构建方法，对照 kg_build_method（nlp llm llm_assisted 等）';
COMMENT ON COLUMN public.edu_knowledge_graph.build_info IS '构建信息（JSONB 格式，包含构建参数、模型信息等）';
COMMENT ON COLUMN public.edu_knowledge_graph.last_extended IS '最后扩展时间';
COMMENT ON COLUMN public.edu_knowledge_graph.is_draft IS '是否草稿，对照 sys_data_option（Y是 N否）';
COMMENT ON COLUMN public.edu_knowledge_graph.task_status IS '异步生成任务状态（pending/processing/success/failed），仅自动生成时有值';
COMMENT ON COLUMN public.edu_knowledge_graph.status IS '知识图谱状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN public.edu_knowledge_graph.create_by IS '创建者';
COMMENT ON COLUMN public.edu_knowledge_graph.create_time IS '创建时间';
COMMENT ON COLUMN public.edu_knowledge_graph.update_by IS '更新者';
COMMENT ON COLUMN public.edu_knowledge_graph.update_time IS '更新时间（由应用程序更新）';

-- 创建索引
CREATE INDEX idx_knowledge_graph_course_id ON public.edu_knowledge_graph (course_id);
CREATE INDEX idx_knowledge_graph_graph_database ON public.edu_knowledge_graph (graph_database);
CREATE INDEX idx_knowledge_graph_build_method ON public.edu_knowledge_graph (build_method);
CREATE INDEX idx_knowledge_graph_status ON public.edu_knowledge_graph (status);

-- ============================================================================
-- 17. 知识点、章节关系表
-- ============================================================================
DROP TABLE IF EXISTS public.edu_knowledge_node_chapter CASCADE;
CREATE TABLE public.edu_knowledge_node_chapter
(
    node_chapter_id BIGSERIAL PRIMARY KEY,
    chapter_id      BIGINT  NOT NULL,
    node_uuid       UUID    NOT NULL, -- 指向知识图谱中的知识点业务UUID
    relevance_score DECIMAL(5, 4)    DEFAULT 0,
    description     TEXT,
    is_primary      CHAR(1)          DEFAULT 'N',
    status          CHAR(1) NOT NULL DEFAULT '0',
    create_by       BIGINT           DEFAULT NULL,
    create_time     TIMESTAMP        DEFAULT CURRENT_TIMESTAMP,
    update_by       BIGINT           DEFAULT NULL,
    update_time     TIMESTAMP        DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE public.edu_knowledge_node_chapter IS '知识点、章节关系表';
COMMENT ON COLUMN public.edu_knowledge_node_chapter.node_chapter_id IS '关系ID';
COMMENT ON COLUMN public.edu_knowledge_node_chapter.chapter_id IS '章节ID';
COMMENT ON COLUMN public.edu_knowledge_node_chapter.node_uuid IS '知识点业务UUID，指向知识图谱中的知识点UUID';
COMMENT ON COLUMN public.edu_knowledge_node_chapter.relevance_score IS '知识点与章节的相关性评分（由教师或系统评定）';
COMMENT ON COLUMN public.edu_knowledge_node_chapter.description IS '关系描述（可选，教师可以添加备注说明为什么该知识点与章节相关）';
COMMENT ON COLUMN public.edu_knowledge_node_chapter.is_primary IS '是否主要关联（Y是 N否，表示该知识点是否是章节的核心知识点）';
COMMENT ON COLUMN public.edu_knowledge_node_chapter.status IS '关系状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN public.edu_knowledge_node_chapter.create_by IS '创建者';
COMMENT ON COLUMN public.edu_knowledge_node_chapter.create_time IS '创建时间';
COMMENT ON COLUMN public.edu_knowledge_node_chapter.update_by IS '更新者';
COMMENT ON COLUMN public.edu_knowledge_node_chapter.update_time IS '更新时间（由应用程序更新）';

CREATE UNIQUE INDEX idx_knowledge_point_chapter ON public.edu_knowledge_node_chapter (chapter_id, node_uuid);
CREATE INDEX idx_knowledge_point_chapter_point_id ON public.edu_knowledge_node_chapter (node_uuid);
CREATE INDEX idx_knowledge_point_chapter_chapter_id ON public.edu_knowledge_node_chapter (chapter_id);

-- ============================================================================
-- 19. GraphRAG 任务表
-- ============================================================================
DROP TABLE IF EXISTS public.edu_graphrag_task;
CREATE TABLE public.edu_graphrag_task
(
    task_id                BIGSERIAL PRIMARY KEY,
    course_id              BIGINT      NOT NULL,
    resource_ids           JSONB       NOT NULL,
    task_status            VARCHAR(20) NOT NULL DEFAULT 'pending',
    task_type              VARCHAR(32) NOT NULL,
    task_message           TEXT,
    entity_types           JSONB,
    prompt_template        VARCHAR(255),
    custom_prompt_template JSONB,
    stats                  JSONB,
    start_time             TIMESTAMP,
    end_time               TIMESTAMP,
    enabled                CHAR(1)     NOT NULL DEFAULT 'N',
    status                 CHAR(1)              DEFAULT '0',
    create_by              BIGINT               DEFAULT NULL,
    create_time            TIMESTAMP            DEFAULT CURRENT_TIMESTAMP,
    update_by              BIGINT               DEFAULT NULL,
    update_time            TIMESTAMP            DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE public.edu_graphrag_task IS 'GraphRAG 任务表';
COMMENT ON COLUMN public.edu_graphrag_task.task_id IS '任务ID';
COMMENT ON COLUMN public.edu_graphrag_task.course_id IS '关联课程ID';
COMMENT ON COLUMN public.edu_graphrag_task.resource_ids IS '处理的文档ID列表（JSONB数组，对照edu_resource_document.document_id）';
COMMENT ON COLUMN public.edu_graphrag_task.task_status IS '任务状态（pending待处理/processing处理中/success成功/failed失败）';
COMMENT ON COLUMN public.edu_graphrag_task.task_type IS '任务类型（如：graphrag_build构建、graphrag_update更新等）';
COMMENT ON COLUMN public.edu_graphrag_task.task_message IS '任务最后信息（如果任务失败，记录错误详情）';
COMMENT ON COLUMN public.edu_graphrag_task.entity_types IS '涉及的实体类型列表（JSONB数组，对照知识图谱中的实体类型）';
COMMENT ON COLUMN public.edu_graphrag_task.prompt_template IS '使用的提示词模板（从 default/en default/zh edu/en edu/zh中选择）;';
COMMENT ON COLUMN public.edu_graphrag_task.custom_prompt_template IS '自定义提示词模板（JSONB格式，允许用户覆盖默认模板中的某些部分，3.0.5版本可覆盖字段见 graphrag 官方文档）';
COMMENT ON COLUMN public.edu_graphrag_task.stats IS '任务统计信息（JSONB格式，包含处理的文档数量、提取的实体数量、构建的关系数量等）';
COMMENT ON COLUMN public.edu_graphrag_task.start_time IS '任务开始时间';
COMMENT ON COLUMN public.edu_graphrag_task.end_time IS '任务结束时间';
COMMENT ON COLUMN public.edu_graphrag_task.enabled IS '是否启用，对照 sys_data_option（Y是 N否）';
COMMENT ON COLUMN public.edu_graphrag_task.status IS '任务记录状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN public.edu_graphrag_task.create_by IS '创建者';
COMMENT ON COLUMN public.edu_graphrag_task.create_time IS '创建时间';
COMMENT ON COLUMN public.edu_graphrag_task.update_by IS '更新者';
COMMENT ON COLUMN public.edu_graphrag_task.update_time IS '更新时间（由应用程序更新）';

-- ============================================================================
-- 20. 课程资源表
-- ============================================================================
DROP TABLE IF EXISTS public.edu_course_resource;
CREATE TABLE public.edu_course_resource
(
    course_resource_id BIGSERIAL PRIMARY KEY,
    course_id          BIGINT       NOT NULL,
    parent_id          BIGINT       NOT NULL DEFAULT 0,
    resource_name      VARCHAR(128) NOT NULL,
    resource_type      VARCHAR(32)  NOT NULL,
    file_id            BIGINT,
    resource_url       VARCHAR(512),
    resource_text      TEXT,
    resource_data      JSONB,
    text_file_id       INTEGER,
    parse_status       CHAR(1)               DEFAULT '0',
    display_order      INTEGER      NOT NULL DEFAULT 0,
    is_visible         CHAR(1)               DEFAULT 'Y',
    status             CHAR(1)               DEFAULT '0',
    create_by          BIGINT,
    create_time        TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    update_by          BIGINT,
    update_time        TIMESTAMP             DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.edu_course_resource IS '课程资源表';
COMMENT ON COLUMN public.edu_course_resource.course_resource_id IS '课程资源ID';
COMMENT ON COLUMN public.edu_course_resource.course_id IS '课程ID';
COMMENT ON COLUMN public.edu_course_resource.parent_id IS '父资源ID（0表示根资源）';
COMMENT ON COLUMN public.edu_course_resource.resource_name IS '资源名称';
COMMENT ON COLUMN public.edu_course_resource.resource_type IS '资源类型（video视频/document文档/text文本/dir文件夹）';
COMMENT ON COLUMN public.edu_course_resource.file_id IS '文件ID（引用sys_upload.file_id）';
COMMENT ON COLUMN public.edu_course_resource.resource_url IS '用户提供的外部链接URL';
COMMENT ON COLUMN public.edu_course_resource.resource_text IS '用户提供的文本内容（富文本/Markdown）';
COMMENT ON COLUMN public.edu_course_resource.resource_data IS '扩展数据（JSONB格式，存储视频时长、文档页数等元数据），如果是 pdf 将展示与 markdown的对照关系';
COMMENT ON COLUMN public.edu_course_resource.text_file_id IS '解析后的文本文件ID（引用sys_upload.file_id），用于存储文档解析后的纯文本内容，供AI知识问答使用）';
COMMENT ON COLUMN public.edu_course_resource.parse_status IS '文档解析状态（0未解析 1解析中 2解析成功 3解析失败），对应 text_processing_status 字典';
COMMENT ON COLUMN public.edu_course_resource.display_order IS '显示顺序';
COMMENT ON COLUMN public.edu_course_resource.is_visible IS '是否可见（Y/N）';
COMMENT ON COLUMN public.edu_course_resource.status IS '状态（0正常 1停用 2已删除）';
COMMENT ON COLUMN public.edu_course_resource.create_by IS '创建者';
COMMENT ON COLUMN public.edu_course_resource.create_time IS '创建时间';
COMMENT ON COLUMN public.edu_course_resource.update_by IS '更新者';
COMMENT ON COLUMN public.edu_course_resource.update_time IS '更新时间';


DROP TABLE IF EXISTS public.edu_course_exercise CASCADE;
CREATE TABLE public.edu_course_exercise
(
    exercise_id BIGSERIAL PRIMARY KEY,
    course_id   BIGINT NOT NULL,
    chapter_id  BIGINT,
    exercise    JSONB,
    source      VARCHAR(255),
    status      CHAR(1)   DEFAULT '0',
    create_by   BIGINT    DEFAULT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by   BIGINT    DEFAULT NULL,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE public.edu_course_exercise IS '课程练习表';
COMMENT ON COLUMN public.edu_course_exercise.exercise_id IS '练习ID';
COMMENT ON COLUMN public.edu_course_exercise.course_id IS '课程ID';
COMMENT ON COLUMN public.edu_course_exercise.chapter_id IS '章节ID（可选，如果练习与特定章节相关联）';
COMMENT ON COLUMN public.edu_course_exercise.exercise IS '练习内容（JSONB格式，包含题目、选项、答案等信息）';
COMMENT ON COLUMN public.edu_course_exercise.source IS '练习来源（如：教师上传、系统生成等）';
COMMENT ON COLUMN public.edu_course_exercise.status IS '练习状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN public.edu_course_exercise.create_by IS '创建者';
COMMENT ON COLUMN public.edu_course_exercise.create_time IS '创建时间';
COMMENT ON COLUMN public.edu_course_exercise.update_by IS '更新者';
COMMENT ON COLUMN public.edu_course_exercise.update_time IS '更新时间（由应用程序更新）';

-- 索引
CREATE INDEX idx_edu_course_exercise_course_id ON public.edu_course_exercise (course_id);
CREATE INDEX idx_edu_course_exercise_chapter_id ON public.edu_course_exercise (chapter_id);
CREATE INDEX idx_edu_course_exercise_status ON public.edu_course_exercise (status);


-- ============================================================================
-- 习题作答记录表
-- ============================================================================
DROP TABLE IF EXISTS public.edu_exercise_attempt CASCADE;
CREATE TABLE public.edu_exercise_attempt
(
    attempt_id     BIGSERIAL PRIMARY KEY,
    exercise_id    BIGINT   NOT NULL,
    student_id     BIGINT   NOT NULL,
    student_answer JSONB,
    is_correct     BOOLEAN,
    time_spent     INTEGER,
    attempt_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.edu_exercise_attempt IS '习题作答记录表';
COMMENT ON COLUMN public.edu_exercise_attempt.attempt_id IS '作答记录ID';
COMMENT ON COLUMN public.edu_exercise_attempt.exercise_id IS '关联习题ID（FK → edu_course_exercise）';
COMMENT ON COLUMN public.edu_exercise_attempt.student_id IS '学生ID';
COMMENT ON COLUMN public.edu_exercise_attempt.student_answer IS '学生答案（JSONB，支持多选等复杂答案）';
COMMENT ON COLUMN public.edu_exercise_attempt.is_correct IS '是否正确（bool，简答题可为 null 待批改）';
COMMENT ON COLUMN public.edu_exercise_attempt.time_spent IS '用时（秒）';
COMMENT ON COLUMN public.edu_exercise_attempt.attempt_time IS '作答时间';

CREATE INDEX idx_edu_exercise_attempt_exercise_id ON public.edu_exercise_attempt (exercise_id);
CREATE INDEX idx_edu_exercise_attempt_student_id ON public.edu_exercise_attempt (student_id);
CREATE INDEX idx_edu_exercise_attempt_attempt_time ON public.edu_exercise_attempt (attempt_time);
