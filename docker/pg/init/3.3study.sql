-- ============================================================================
-- 学习数据模型架构说明
-- ============================================================================
-- 本模块包含四类数据表，各有分工：
--
-- 1. 行为日志表（edu_student_learning_event）
--    记录学生的学习行为流：提问、兴趣点、章节打开、地图交互等。
--    仅记录"学生做了什么行为"，不含答题详情（见2）和掌握度评估（见3）。
--
-- 2. 业务实体表（定义在 3.4education.sql）
--    - edu_course_exercise：习题定义（关联课程和章节）
--    - edu_exercise_attempt：习题作答详细记录（答案、正确性、用时）
--
-- 3. 成长记录表（edu_student_mastery）
--    AI 对学生知识掌握度的评估历史，记录学生在各知识点上的成长轨迹。
--
-- 4. 状态快照表
--    - edu_chapter_progress：章节学习进度（完成率、断点位置、累计时长）
--    - edu_student_resource_progress：资料阅读进度（完成率、阅读次数、断点位置）
--
-- 职责边界：
--   行为日志表 → "学生做了什么"（行为流，不可变追加）
--   业务实体表 → "学生答了什么"（结构化业务数据）
--   成长记录表 → "学生掌握了什么"（评估历史，可追溯成长）
--   状态快照表 → "学生现在到哪了"（可变状态，由应用层同步更新）
--
-- 视图从上述多数据源中聚合，提供多维分析视角。
-- 注意：原 8 个 SQL 视图已迁移至 SQLAlchemy Core 查询（Mapper 层），仅保留物化视图。
-- ============================================================================


-- ============================================================================
-- 1. 学生学习行为事件表
-- ============================================================================
DROP TABLE IF EXISTS edu_student_learning_event CASCADE;
CREATE TABLE edu_student_learning_event
(
    event_id         BIGSERIAL PRIMARY KEY,
    student_id       BIGINT      NOT NULL,
    course_id        BIGINT      NOT NULL,
    session_id       BIGINT,
    chapter_id       BIGINT,
    node_uuid        UUID,
    event_type       VARCHAR(32) NOT NULL,
    event_source     VARCHAR(32),
    message_id       VARCHAR(64),
    event_content    TEXT,
    event_payload    JSONB,
    duration_seconds INTEGER,
    effective_duration_seconds INTEGER,
    is_review        BOOLEAN   DEFAULT FALSE,
    event_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status           CHAR(1)   DEFAULT '0',
    create_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE edu_student_learning_event IS '学生学习行为事件表（纯行为日志，不含答题和评估；答题见 edu_exercise_attempt，评估见 edu_student_mastery）';
COMMENT ON COLUMN edu_student_learning_event.event_id IS '事件ID';
COMMENT ON COLUMN edu_student_learning_event.student_id IS '学生ID';
COMMENT ON COLUMN edu_student_learning_event.course_id IS '课程ID';
COMMENT ON COLUMN edu_student_learning_event.session_id IS '会话ID';
COMMENT ON COLUMN edu_student_learning_event.chapter_id IS '关联章节ID';
COMMENT ON COLUMN edu_student_learning_event.node_uuid IS '知识点业务UUID';
COMMENT ON COLUMN edu_student_learning_event.event_type IS '事件类型（question/interest/explain_request/map_click/tool_map_query/chapter_open）';
COMMENT ON COLUMN edu_student_learning_event.event_source IS '事件来源（chat/ui/tool/system）';
COMMENT ON COLUMN edu_student_learning_event.event_content IS '事件文本内容（question类型存用户原始问题）';
COMMENT ON COLUMN edu_student_learning_event.event_payload IS '事件扩展数据（JSONB，按事件类型存储附加信息）';
COMMENT ON COLUMN edu_student_learning_event.message_id IS '关联的聊天消息ID（用于回溯对话上下文）';
COMMENT ON COLUMN edu_student_learning_event.duration_seconds IS '事件持续时长（秒）';
COMMENT ON COLUMN edu_student_learning_event.effective_duration_seconds IS '有效持续时长（秒），排除空闲';
COMMENT ON COLUMN edu_student_learning_event.is_review IS '是否为复习（资源已完成后的再次阅读）';
COMMENT ON COLUMN edu_student_learning_event.event_time IS '事件发生时间';
COMMENT ON COLUMN edu_student_learning_event.status IS '状态（0正常 1停用 2已删除）';

-- 索引
CREATE INDEX idx_edu_student_learning_event_student_course_time
    ON edu_student_learning_event (student_id, course_id, event_time DESC);
CREATE INDEX idx_edu_student_learning_event_node_type
    ON edu_student_learning_event (node_uuid, event_type, event_time DESC);
CREATE INDEX idx_edu_student_learning_event_session_time
    ON edu_student_learning_event (session_id, event_time DESC);
CREATE INDEX idx_edu_student_learning_event_course_type_time
    ON edu_student_learning_event (course_id, event_type, event_time DESC);
CREATE INDEX idx_edu_student_learning_event_event_payload_gin
    ON edu_student_learning_event USING GIN (event_payload);
CREATE INDEX idx_edu_student_learning_event_date
    ON edu_student_learning_event (student_id, course_id, DATE(event_time) DESC);


-- ============================================================================
-- 2. AI 评估记录表（学生成长轨迹）
-- ============================================================================
DROP TABLE IF EXISTS edu_student_mastery CASCADE;
CREATE TABLE edu_student_mastery
(
    mastery_id    BIGSERIAL PRIMARY KEY,
    student_id    BIGINT NOT NULL,
    course_id     BIGINT NOT NULL,
    node_uuid     UUID,
    session_id    BIGINT,
    mastery_score NUMERIC(5, 2),
    mastery_level VARCHAR(16),
    trigger_type  VARCHAR(32),
    reason        TEXT,
    assessed_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status        CHAR(1)   DEFAULT '0',
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE edu_student_mastery IS '学生知识点掌握度评估记录表（成长轨迹，每次AI评估生成一条记录）';
COMMENT ON COLUMN edu_student_mastery.mastery_id IS '评估记录ID';
COMMENT ON COLUMN edu_student_mastery.student_id IS '学生ID';
COMMENT ON COLUMN edu_student_mastery.course_id IS '课程ID';
COMMENT ON COLUMN edu_student_mastery.node_uuid IS '知识点业务UUID';
COMMENT ON COLUMN edu_student_mastery.session_id IS '触发评估的会话ID';
COMMENT ON COLUMN edu_student_mastery.mastery_score IS '掌握度评分（0-100）';
COMMENT ON COLUMN edu_student_mastery.mastery_level IS '掌握等级（unknown/low/medium/high）';
COMMENT ON COLUMN edu_student_mastery.trigger_type IS '触发类型（quiz_complete/periodic/manual/system）';
COMMENT ON COLUMN edu_student_mastery.assessed_at IS '评估时间';
COMMENT ON COLUMN edu_student_mastery.status IS '状态（0正常 1停用 2已删除）';

CREATE INDEX idx_edu_student_mastery_student_course_node
    ON edu_student_mastery (student_id, course_id, node_uuid);
CREATE INDEX idx_edu_student_mastery_student_course_time
    ON edu_student_mastery (student_id, course_id, assessed_at DESC);
CREATE INDEX idx_edu_student_mastery_level
    ON edu_student_mastery (mastery_level);


-- ============================================================================
-- [已删除] v_student_daily_summary 视图
-- 原因：已迁移至 SQLAlchemy Core 查询（StudyAnalyticsMapper.get_my_daily_summary）
-- ============================================================================


-- ============================================================================
-- [已删除] v_student_node_profile 视图
-- 原因：已迁移至 SQLAlchemy Core 查询（StudyAnalyticsMapper.get_my_node_profile）
-- ============================================================================


-- ============================================================================
-- [已删除] v_course_learning_overview 视图
-- 原因：已迁移至 SQLAlchemy Core 查询（StudyAnalyticsMapper.get_course_overview）
-- ============================================================================


-- ============================================================================
-- [已删除] v_course_chapter_stats 视图
-- 原因：已迁移至 SQLAlchemy Core 查询（StudyAnalyticsMapper.get_chapter_stats）
-- ============================================================================


-- ============================================================================
-- [已删除] v_student_course_progress 视图
-- 原因：已迁移至 SQLAlchemy Core 查询（StudyAnalyticsMapper.get_student_rankings）
-- ============================================================================


-- ============================================================================
-- 9. 课程评价表
-- ============================================================================
DROP TABLE IF EXISTS edu_course_review CASCADE;
CREATE TABLE edu_course_review
(
    review_id        BIGSERIAL PRIMARY KEY,
    course_id        BIGINT  NOT NULL,
    student_id       BIGINT  NOT NULL,
    rating           INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    content          TEXT,
    dimension_scores JSONB,
    like_count       INTEGER   DEFAULT 0,
    status           CHAR(1)   DEFAULT '0',
    is_visible       CHAR(1)   DEFAULT 'Y',
    create_by        BIGINT,
    create_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by        BIGINT,
    update_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE edu_course_review IS '课程评价表';
COMMENT ON COLUMN edu_course_review.review_id IS '评价ID';
COMMENT ON COLUMN edu_course_review.course_id IS '课程ID';
COMMENT ON COLUMN edu_course_review.student_id IS '学生ID';
COMMENT ON COLUMN edu_course_review.rating IS '整体评分（1-5星）';
COMMENT ON COLUMN edu_course_review.content IS '评价内容';
COMMENT ON COLUMN edu_course_review.dimension_scores IS '分项评分（JSONB格式）';
COMMENT ON COLUMN edu_course_review.like_count IS '点赞数';
COMMENT ON COLUMN edu_course_review.status IS '状态（0正常 1停用 2已删除）';
COMMENT ON COLUMN edu_course_review.is_visible IS '是否可见（Y/N）';

CREATE INDEX idx_edu_course_review_course_id ON edu_course_review (course_id);
CREATE INDEX idx_edu_course_review_student_id ON edu_course_review (student_id);
CREATE INDEX idx_edu_course_review_rating ON edu_course_review (rating);
CREATE INDEX idx_edu_course_review_create_time ON edu_course_review (create_time DESC);


-- ============================================================================
-- 10. 学生资料阅读进度表
-- ============================================================================
DROP TABLE IF EXISTS edu_student_resource_progress CASCADE;
CREATE TABLE edu_student_resource_progress
(
    progress_id     BIGSERIAL PRIMARY KEY,
    student_id      BIGINT      NOT NULL,
    course_id       BIGINT      NOT NULL,
    chapter_id      BIGINT      NOT NULL,
    resource_id     BIGINT      NOT NULL,
    resource_type   VARCHAR(32) NOT NULL,

    -- 进度数据
    completion_rate INTEGER   DEFAULT 0,
    is_completed    CHAR(1)   DEFAULT 'N',
    view_count      INTEGER   DEFAULT 0,
    total_duration  INTEGER   DEFAULT 0,
    effective_duration  INTEGER   DEFAULT 0,
    review_duration     INTEGER   DEFAULT 0,
    first_read_duration INTEGER   DEFAULT 0,

    -- 位置快照（用于断点续学）
    last_position   JSONB,

    -- 时间
    first_view_time TIMESTAMP,
    last_view_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    complete_time   TIMESTAMP,

    status          CHAR(1)   DEFAULT '0',
    create_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_edu_srp_student_resource UNIQUE (student_id, resource_id)
);

COMMENT ON TABLE edu_student_resource_progress IS '学生资料阅读进度表（状态快照，记录当前阅读状态；行为流见 edu_student_learning_event）';
COMMENT ON COLUMN edu_student_resource_progress.progress_id IS '进度记录ID';
COMMENT ON COLUMN edu_student_resource_progress.student_id IS '学生ID';
COMMENT ON COLUMN edu_student_resource_progress.course_id IS '课程ID';
COMMENT ON COLUMN edu_student_resource_progress.chapter_id IS '章节ID';
COMMENT ON COLUMN edu_student_resource_progress.resource_id IS '资料ID（关联edu_resource.resource_id）';
COMMENT ON COLUMN edu_student_resource_progress.resource_type IS '资料类型（video/document/text）';
COMMENT ON COLUMN edu_student_resource_progress.completion_rate IS '完成度（0-100）';
COMMENT ON COLUMN edu_student_resource_progress.is_completed IS '是否完成（Y/N）';
COMMENT ON COLUMN edu_student_resource_progress.view_count IS '阅读次数';
COMMENT ON COLUMN edu_student_resource_progress.total_duration IS '累计阅读时长（秒）';
COMMENT ON COLUMN edu_student_resource_progress.effective_duration IS '有效阅读时长（秒），排除空闲时间';
COMMENT ON COLUMN edu_student_resource_progress.review_duration IS '复习时长（秒），资源完成后再次阅读的有效时长';
COMMENT ON COLUMN edu_student_resource_progress.first_read_duration IS '首次阅读时长（秒），资源完成前的有效累计时长';
COMMENT ON COLUMN edu_student_resource_progress.last_position IS '最后阅读位置（JSONB格式，如 {page:12}、{video_second:145.5}、{scroll_percent:45}）';
COMMENT ON COLUMN edu_student_resource_progress.first_view_time IS '首次阅读时间';
COMMENT ON COLUMN edu_student_resource_progress.last_view_time IS '最后阅读时间';
COMMENT ON COLUMN edu_student_resource_progress.complete_time IS '完成时间';
COMMENT ON COLUMN edu_student_resource_progress.status IS '状态（0正常 1停用 2已删除）';

CREATE INDEX idx_edu_srp_student_course ON edu_student_resource_progress (student_id, course_id);
CREATE INDEX idx_edu_srp_chapter ON edu_student_resource_progress (chapter_id);
CREATE INDEX idx_edu_srp_resource_type ON edu_student_resource_progress (resource_type);
CREATE INDEX idx_edu_srp_is_completed ON edu_student_resource_progress (is_completed);
CREATE INDEX idx_edu_srp_student_chapter ON edu_student_resource_progress (student_id, chapter_id);


-- ============================================================================
-- [已删除] v_student_weak_points 视图
-- 原因：已迁移至 Python 端过滤（StudyAnalyticsMapper.get_my_weak_points）
-- ============================================================================


-- ============================================================================
-- [已删除] v_course_student_ranking 视图
-- 原因：已迁移至 Python 端百分位计算（StudyAnalyticsMapper.get_student_rankings）
-- ============================================================================


-- ============================================================================
-- [已删除] v_student_study_streak 视图
-- 原因：已迁移至 Python 端连续天数计算（StudyAnalyticsMapper.get_my_study_streak / DashboardMapper._compute_streaks）
-- ============================================================================


DROP MATERIALIZED VIEW IF EXISTS mv_chapter_progress CASCADE;
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chapter_progress AS
SELECT rp.student_id,
       c.course_id,
       rp.chapter_id,
       COALESCE(FLOOR(SUM(rp.completion_rate)::NUMERIC / NULLIF(cr.total_resources, 0)), 0)::INT
                                                                        AS completion_rate,
       CASE WHEN cr.total_resources > 0
                 AND COUNT(CASE WHEN rp.is_completed = 'Y' THEN 1 END) >= cr.total_resources
            THEN 'Y' ELSE 'N' END                                      AS is_completed,
       MIN(rp.first_view_time)                                         AS first_visit_time,
       MAX(rp.last_view_time)                                          AS last_visit_time,
       MIN(CASE WHEN rp.is_completed = 'Y' THEN rp.last_view_time END) AS complete_time
FROM edu_student_resource_progress rp
         JOIN public.edu_chapter c ON c.chapter_id = rp.chapter_id
         JOIN (
             SELECT chapter_id, COUNT(*) AS total_resources
             FROM public.edu_resource
             WHERE status != '2'
             GROUP BY chapter_id
         ) cr ON cr.chapter_id = rp.chapter_id
WHERE rp.status != '2'
GROUP BY rp.student_id, c.course_id, rp.chapter_id, cr.total_resources;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_chapter_progress_pk ON mv_chapter_progress (student_id, chapter_id);
CREATE INDEX IF NOT EXISTS idx_mv_chapter_progress_course ON mv_chapter_progress (course_id);
CREATE INDEX IF NOT EXISTS idx_mv_chapter_progress_completed ON mv_chapter_progress (is_completed);
COMMENT ON MATERIALIZED VIEW mv_chapter_progress IS '章节学习进度物化视图（从学生资料阅读进度聚合而来，定期刷新）';
