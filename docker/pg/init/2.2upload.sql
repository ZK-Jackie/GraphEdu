-- ============================================================================
-- 6. 文件上传表
-- ============================================================================
DROP TABLE IF EXISTS sys_upload CASCADE;
CREATE TABLE sys_upload
(
    file_id        BIGSERIAL PRIMARY KEY,
    file_name      VARCHAR(255) NOT NULL,
    file_path      VARCHAR(500) NOT NULL,
    file_type      VARCHAR(64),
    file_size      BIGINT,
    file_category  VARCHAR(2),
    storage_type   VARCHAR(2)   NOT NULL DEFAULT '1',

    -- 访问控制
    access_level   CHAR(1)      NOT NULL DEFAULT '1',
    download_flag  CHAR(1)      NOT NULL DEFAULT 'Y',

    -- 统计信息
    view_count     INTEGER      NOT NULL DEFAULT 0,
    download_count INTEGER      NOT NULL DEFAULT 0,
    ref_count      INTEGER      NOT NULL DEFAULT 0,

    -- 审核信息
    audit_status   CHAR(1)      NOT NULL DEFAULT '0',
    audit_by       BIGINT,
    audit_time     TIMESTAMP,
    audit_remark   VARCHAR(500),

    -- 数据状态
    status         CHAR(1)      NOT NULL DEFAULT '0',

    -- 上传信息
    create_ip      VARCHAR(128)          DEFAULT '',
    create_by      BIGINT,
    create_time    TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    update_by      BIGINT,
    update_time    TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    remark         VARCHAR(500)
);

COMMENT ON TABLE sys_upload IS '文件上传表';
COMMENT ON COLUMN sys_upload.file_id IS '文件ID';
COMMENT ON COLUMN sys_upload.file_name IS '原始文件名';
COMMENT ON COLUMN sys_upload.file_path IS '存储路径或URL';
COMMENT ON COLUMN sys_upload.file_type IS 'MIME类型（如: image/jpeg, application/pdf）';
COMMENT ON COLUMN sys_upload.file_size IS '文件大小（字节）';
COMMENT ON COLUMN sys_upload.file_category IS '文件分类，对照 sys_upload_file_category（1头像 2课程封面 3书籍封面 4书籍文件 5笔记附件 6作业 7课件）';
COMMENT ON COLUMN sys_upload.storage_type IS '存储类型，对照 sys_upload_storage_type（1OSS存储 2本地存储 3CDN存储）';
COMMENT ON COLUMN sys_upload.access_level IS '访问级别，对照 sys_upload_access_level（1私有 2登录 3公开）';
COMMENT ON COLUMN sys_upload.download_flag IS '是否允许下载，对照 sys_data_option（Y是 N否）';
COMMENT ON COLUMN sys_upload.view_count IS '查看次数';
COMMENT ON COLUMN sys_upload.download_count IS '下载次数';
COMMENT ON COLUMN sys_upload.ref_count IS '被引用次数';
COMMENT ON COLUMN sys_upload.audit_status IS '审核状态，对照 sys_upload_audit_status（0待审核 1审核中 2审核通过 3审核拒绝）';
COMMENT ON COLUMN sys_upload.audit_by IS '审核人ID';
COMMENT ON COLUMN sys_upload.audit_time IS '审核时间';
COMMENT ON COLUMN sys_upload.audit_remark IS '审核备注';
COMMENT ON COLUMN sys_upload.status IS '上传文件状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN sys_upload.create_ip IS '上传者IP地址';
COMMENT ON COLUMN sys_upload.create_by IS '上传者ID';
COMMENT ON COLUMN sys_upload.create_time IS '上传时间';
COMMENT ON COLUMN sys_upload.update_by IS '更新者';
COMMENT ON COLUMN sys_upload.update_time IS '更新时间';
COMMENT ON COLUMN sys_upload.remark IS '备注';

-- 创建索引
CREATE INDEX idx_sys_upload_file_category ON sys_upload (file_category);
CREATE INDEX idx_sys_upload_create_by ON sys_upload (create_by);
CREATE INDEX idx_sys_upload_audit_status ON sys_upload (audit_status);
CREATE INDEX idx_sys_upload_status ON sys_upload (status);
CREATE INDEX idx_sys_upload_access_level ON sys_upload (access_level);

-- 默认头像
INSERT INTO sys_upload (file_id, file_name, file_path, file_type, file_size, file_category, storage_type, access_level,
                        download_flag, view_count, download_count, ref_count, audit_status, status, create_by)
VALUES (1, 'default-avatar-1', 'avatar/2327ef54724b45a5923951fe62b94faa.png',
        'image/png', null, 1, 1, 2, 'Y', 0, 0, 0, '2', '0', 1),
       (7, 'default-avatar-7', 'avatar/e4253161d93a4ebfa4013db82b1e0ca8.png',
        'image/png', null, 1, 1, 2, 'Y', 0, 0, 0, '2', '0', 1),
       (6, 'default-avatar-6', 'avatar/4e1d35f4f7304215aec14f10778ee224.png',
        'image/png', null, 1, 1, 2, 'Y', 0, 0, 0, '2', '0', 1),
       (5, 'default-avatar-5', 'avatar/4baeeb0b024d4478b6596b45f3ad5a37.png',
        'image/png', null, 1, 1, 2, 'Y', 0, 0, 0, '2', '0', 1),
       (4, 'default-avatar-4', 'avatar/435140056a7b4062817955f0a0670c56.png',
        'image/png', null, 1, 1, 2, 'Y', 0, 0, 0, '2', '0', 1),
       (3, 'default-avatar-3', 'avatar/395accd9e2dc4f07a0cd3e4281cf7577.png',
        'image/png', null, 1, 1, 2, 'Y', 0, 0, 0, '2', '0', 1),
       (2, 'default-avatar-2', 'avatar/2a377a4abd4d4848b6931c03db67f1c0.png',
        'image/png', null, 1, 1, 2, 'Y', 0, 0, 0, '2', '0', 1),
       (8, 'default-avatar-8', 'avatar/f8a2bb7fe9424183a54c57f7b299b489.png',
        'image/png', null, 1, 1, 2, 'Y', 0, 0, 0, '2', '0', 1);

SELECT setval('sys_upload_file_id_seq', 10000, true);