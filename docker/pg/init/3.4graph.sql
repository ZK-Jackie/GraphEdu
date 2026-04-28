-- 知识点向量嵌入表（pgvector）
-- 存储 AGE 图谱中 KnowledgePoint 节点的向量嵌入，支持 HNSW 高效相似度检索。
-- 与 EduStudentMastery.node_uuid、EduStudentLearningEvent.node_uuid 保持一致的 UUID 命名。
CREATE TABLE IF NOT EXISTS public.edu_knowledge_point_embedding
(
    node_uuid UUID PRIMARY KEY,      -- 知识点业务 UUID（对应 AGE 中 n.uuid）
    course_id BIGINT       NOT NULL, -- 课程 ID
    title     TEXT         NOT NULL, -- 知识点标题（冗余存储，避免联查 AGE）
    embedding VECTOR(1024) NOT NULL  -- 知识点向量嵌入（1024 维，与 EduChapter.embedding 一致）
);

CREATE INDEX IF NOT EXISTS idx_kp_embedding_course ON public.edu_knowledge_point_embedding (course_id);
CREATE INDEX IF NOT EXISTS idx_kp_embedding_vector ON public.edu_knowledge_point_embedding USING hnsw (embedding public.vector_cosine_ops);
COMMENT ON COLUMN public.edu_knowledge_point_embedding.node_uuid IS '知识点业务 UUID，对应 AGE 图谱中 KnowledgePoint 节点的 n.uuid，保持与 EduStudentMastery.node_uuid、EduStudentLearningEvent.node_uuid 一致。';
COMMENT ON COLUMN public.edu_knowledge_point_embedding.course_id IS '课程 ID，冗余存储，便于按课程检索知识点嵌入。';
COMMENT ON COLUMN public.edu_knowledge_point_embedding.title IS '知识点标题，冗余存储，避免每次查询都需要联查 AGE 图谱获取标题信息。';
COMMENT ON COLUMN public.edu_knowledge_point_embedding.embedding IS '知识点向量嵌入，1024 维，与 EduChapter.embedding 一致，支持 HNSW 高效相似度检索。';
COMMENT ON TABLE public.edu_knowledge_point_embedding IS '知识点向量嵌入表，存储 AGE 图谱中 KnowledgePoint 节点的向量嵌入，支持 HNSW 高效相似度检索。与 EduStudentMastery.node_uuid、EduStudentLearningEvent.node_uuid 保持一致的 UUID 命名。';

-- 习题-知识点关联表
-- 记录习题与知识图谱知识点的多对多关系，支持按知识点检索习题。

CREATE TABLE IF NOT EXISTS public.edu_exercise_knowledge_point
(
    id              BIGSERIAL PRIMARY KEY,
    exercise_id     BIGINT NOT NULL,
    node_uuid       UUID   NOT NULL,
    relevance_score NUMERIC(5, 4) DEFAULT 0,
    source          VARCHAR(16)   DEFAULT 'auto',
    create_time     TIMESTAMP     DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ekp_exercise ON public.edu_exercise_knowledge_point (exercise_id);
CREATE INDEX IF NOT EXISTS idx_ekp_node ON public.edu_exercise_knowledge_point (node_uuid);
COMMENT ON COLUMN public.edu_exercise_knowledge_point.exercise_id IS '习题 ID，关联 edu_exercise.exercise_id，表示该习题与哪些知识点相关。';
COMMENT ON COLUMN public.edu_exercise_knowledge_point.node_uuid IS '知识点业务 UUID，关联 AGE 图谱中 KnowledgePoint 节点的 n.uuid，表示该习题与哪些知识点相关。';
COMMENT ON COLUMN public.edu_exercise_knowledge_point.relevance_score IS '相关度分数，表示习题与知识点的相关程度，取值范围 0.0000 - 1.0000，默认为 0。';
COMMENT ON COLUMN public.edu_exercise_knowledge_point.source IS '关联来源，表示该习题与知识点关联的来源，默认为 "auto" 表示自动关联，其他可能值如 "manual" 表示人工关联。';
COMMENT ON COLUMN public.edu_exercise_knowledge_point.create_time IS '创建时间，记录该关联关系的创建时间，默认为当前时间。';
COMMENT ON TABLE public.edu_exercise_knowledge_point IS '习题-知识点关联表，记录习题与知识图谱知识点的多对多关系，支持按知识点检索习题。';