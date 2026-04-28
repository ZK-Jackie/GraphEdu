-- ============================================================================
-- 18. 字典类型表
-- ============================================================================
DROP TABLE IF EXISTS sys_dict_type;
CREATE TABLE sys_dict_type
(
    dict_id     BIGSERIAL PRIMARY KEY,
    dict_name   VARCHAR(100) DEFAULT ''  NOT NULL,
    dict_type   VARCHAR(100) DEFAULT ''  NOT NULL UNIQUE,
    status      CHAR(1)      DEFAULT '0' NOT NULL,
    create_by   BIGINT       DEFAULT NULL,
    create_time TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    update_by   BIGINT       DEFAULT NULL,
    update_time TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    remark      VARCHAR(500)
);
COMMENT ON TABLE sys_dict_type IS '字典类型表';
COMMENT ON COLUMN sys_dict_type.dict_id IS '字典主键';
COMMENT ON COLUMN sys_dict_type.dict_name IS '字典名称';
COMMENT ON COLUMN sys_dict_type.dict_type IS '字典类型';
COMMENT ON COLUMN sys_dict_type.status IS '字典类型状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN sys_dict_type.create_by IS '创建者';
COMMENT ON COLUMN sys_dict_type.create_time IS '创建时间';
COMMENT ON COLUMN sys_dict_type.update_by IS '更新者';
COMMENT ON COLUMN sys_dict_type.update_time IS '更新时间';
COMMENT ON COLUMN sys_dict_type.remark IS '备注';

-- ============================================================================
-- 19. 字典数据表
-- ============================================================================
DROP TABLE IF EXISTS sys_dict_data;
CREATE TABLE sys_dict_data
(
    dict_code   BIGSERIAL PRIMARY KEY,
    dict_sort   INTEGER      DEFAULT 0         NOT NULL,
    dict_label  VARCHAR(100) DEFAULT ''        NOT NULL,
    dict_value  VARCHAR(100) DEFAULT ''        NOT NULL,
    dict_type   VARCHAR(100) DEFAULT ''        NOT NULL,
    style       JSONB,
    color       VARCHAR(32)  DEFAULT 'default' NOT NULL,
    icon        VARCHAR(64),
    bordered    CHAR(1)      DEFAULT 'N'       NOT NULL,
    is_default  CHAR(1)      DEFAULT 'N'       NOT NULL,
    status      CHAR(1)      DEFAULT '0'       NOT NULL,
    create_by   BIGINT       DEFAULT NULL,
    create_time TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    update_by   BIGINT       DEFAULT NULL,
    update_time TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    remark      VARCHAR(500),
    -- 使用联合唯一约束，确保同一字典类型下dict_value唯一
    CONSTRAINT uk_dict_data_type_value UNIQUE (dict_type, dict_value)
);
COMMENT ON TABLE sys_dict_data IS '字典数据表';
COMMENT ON COLUMN sys_dict_data.dict_code IS '字典编码';
COMMENT ON COLUMN sys_dict_data.dict_sort IS '字典排序';
COMMENT ON COLUMN sys_dict_data.dict_label IS '字典标签';
COMMENT ON COLUMN sys_dict_data.dict_value IS '字典键值';
COMMENT ON COLUMN sys_dict_data.dict_type IS '字典类型';
COMMENT ON COLUMN sys_dict_data.style IS '数据渲染样式（JSON格式，使用css-in-js格式）';
COMMENT ON COLUMN sys_dict_data.color IS '颜色主题（success | processing | error | warning | default | 自定义 16 进制颜色）';
COMMENT ON COLUMN sys_dict_data.icon IS '图标（Ant Design Vue图标名称）';
COMMENT ON COLUMN sys_dict_data.bordered IS '是否带边框（Y是 N否）';
COMMENT ON COLUMN sys_dict_data.is_default IS '是否默认（Y是 N否）';
COMMENT ON COLUMN sys_dict_data.status IS '字典数据状态，参照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN sys_dict_data.create_by IS '创建者';
COMMENT ON COLUMN sys_dict_data.create_time IS '创建时间';
COMMENT ON COLUMN sys_dict_data.update_by IS '更新者';
COMMENT ON COLUMN sys_dict_data.update_time IS '更新时间';
COMMENT ON COLUMN sys_dict_data.remark IS '备注';

CREATE INDEX idx_sys_dict_data_dict_type ON sys_dict_data (dict_type);

-- 插入字典类型数据
TRUNCATE sys_dict_type;
INSERT INTO sys_dict_type (dict_name, dict_type, status, remark)
VALUES ('性别', 'sys_user_sex', '0', 'GB/T 2261.1-2003 个人基本信息分类与代码 第1部分:人的性别代码'),
       ('用户类型', 'sys_user_type', '0', '系统用户类型（学生/教师/管理员等）'),
       ('政治面貌', 'sys_user_cn_political_status', '0', 'GB/T 4762-1984 政治面貌代码'),
       ('民族', 'sys_user_cn_nation', '0', 'GB/T 3304-1991 中国各民族名称的罗马字母拼写法和代码'),
       ('证件类型', 'sys_user_cn_id_type', '0', '个人证件类型代码'),
       ('角色权限范围', 'sys_role_data_scope', '0', '角色权限范围字典（全部/自定义/本部门/本部门及以下）'),
       ('语种', 'sys_language', '0', 'ISO 639-1:2002 语种名称代码'),
       ('数据状态', 'sys_data_status', '0', '系统数据状态（正常/停用/已删除）'),
       ('数据选项', 'sys_data_option', '0', '通用数据选项（是/否）'),
       ('系统功能类型', 'sys_function_type', '0', '系统功能类型字典'),
       ('系统功能应用场景', 'sys_function_scene', '0', '系统功能应用场景字典'),
       ('系统上传文件审核状态', 'sys_upload_audit_status', '0', '系统上传文件审核状态字典'),
       ('系统上传文件分类', 'sys_upload_file_category', '0', '系统上传文件分类字典'),
       ('系统上传文件存储类型', 'sys_upload_storage_type', '0', '系统上传文件存储类型字典'),
       ('系统上传文件访问级别', 'sys_upload_access_level', '0', '系统上传文件访问级别字典'),
       ('系统操作日志-业务类型', 'sys_oper_log_business_type', '0', '系统操作日志业务类型字典'),
       ('系统操作日志-操作类型', 'sys_oper_log_oper_type', '0', '系统操作日志操作类型字典'),
       ('学历背景', 'edu_background', '0', 'GB/T 4658-2006 学历代码'),
       ('书籍分类', 'edu_book_category', '0', '中国图书馆分类法（CLC）大类'),
       ('学生状态', 'edu_student_status', '0', '学生在校状态'),
       ('学位', 'edu_academic_degree', '0', 'GB/T 6864-2003 学位代码'),
       ('职称', 'edu_professional_title', '0', 'GB/T 8561-2001 专业技术职务代码'),
       ('图谱构建方法', 'kg_build_method', '0', '知识图谱构建方法类型'),
       ('文本处理状态', 'text_processing_status', '0', '文本处理状态字典');

-- 插入性别数据 (GB/T 2261.1-2003)
TRUNCATE sys_dict_data;
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '男', '1', 'sys_user_sex', 'processing', 'N', '男性'),
       (2, '女', '2', 'sys_user_sex', 'error', 'N', '女性'),
       (3, '未知', '0', 'sys_user_sex', 'default', 'Y', '未说明的性别'),
       (4, '其他', '9', 'sys_user_sex', 'default', 'N', '其他或未明确说明的性别');

-- 插入用户类型数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '学生', '1', 'sys_user_type', 'success', 'Y', '学生用户'),
       (2, '教师', '2', 'sys_user_type', 'processing', 'N', '教师用户'),
       (3, '管理员', '3', 'sys_user_type', 'error', 'N', '管理员用户'),
       (4, '其他', '4', 'sys_user_type', 'default', 'N', '其他类型用户');

-- 插入政治面貌数据 (GB/T 4762-1984)
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '中共党员', '01', 'sys_user_cn_political_status', 'default', 'N', '中国共产党党员'),
       (2, '中共预备党员', '02', 'sys_user_cn_political_status', 'default', 'N', '中国共产党预备党员'),
       (3, '共青团员', '03', 'sys_user_cn_political_status', 'default', 'N', '中国共产主义青年团团员'),
       (4, '民革会员', '04', 'sys_user_cn_political_status', 'default', 'N', '中国国民党革命委员会会员'),
       (5, '民盟盟员', '05', 'sys_user_cn_political_status', 'default', 'N', '中国民主同盟盟员'),
       (6, '民建会员', '06', 'sys_user_cn_political_status', 'default', 'N', '中国民主建国会会员'),
       (7, '民进会员', '07', 'sys_user_cn_political_status', 'default', 'N', '中国民主促进会会员'),
       (8, '农工党党员', '08', 'sys_user_cn_political_status', 'default', 'N', '中国农工民主党党员'),
       (9, '致公党党员', '09', 'sys_user_cn_political_status', 'default', 'N', '中国致公党党员'),
       (10, '九三学社社员', '10', 'sys_user_cn_political_status', 'default', 'N', '九三学社社员'),
       (11, '台盟盟员', '11', 'sys_user_cn_political_status', 'default', 'N', '台湾民主自治同盟盟员'),
       (12, '无党派人士', '12', 'sys_user_cn_political_status', 'default', 'N', '无党派人士'),
       (13, '群众', '13', 'sys_user_cn_political_status', 'default', 'Y', '群众');

-- 插入民族数据 (GB/T 3304-1991，部分常用)
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '汉族', '01', 'sys_user_cn_nation', 'default', 'Y', '汉族'),
       (2, '蒙古族', '02', 'sys_user_cn_nation', 'default', 'N', '蒙古族'),
       (3, '回族', '03', 'sys_user_cn_nation', 'default', 'N', '回族'),
       (4, '藏族', '04', 'sys_user_cn_nation', 'default', 'N', '藏族'),
       (5, '维吾尔族', '05', 'sys_user_cn_nation', 'default', 'N', '维吾尔族'),
       (6, '苗族', '06', 'sys_user_cn_nation', 'default', 'N', '苗族'),
       (7, '彝族', '07', 'sys_user_cn_nation', 'default', 'N', '彝族'),
       (8, '壮族', '08', 'sys_user_cn_nation', 'default', 'N', '壮族'),
       (9, '布依族', '09', 'sys_user_cn_nation', 'default', 'N', '布依族'),
       (10, '朝鲜族', '10', 'sys_user_cn_nation', 'default', 'N', '朝鲜族'),
       (11, '满族', '11', 'sys_user_cn_nation', 'default', 'N', '满族'),
       (12, '其他', '99', 'sys_user_cn_nation', 'default', 'N', '其他少数民族');

-- 插入证件类型数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '身份证', '01', 'sys_user_cn_id_type', 'default', 'Y', '居民身份证'),
       (2, '护照', '02', 'sys_user_cn_id_type', 'default', 'N', '护照'),
       (3, '军官证', '03', 'sys_user_cn_id_type', 'default', 'N', '军官证'),
       (4, '士兵证', '04', 'sys_user_cn_id_type', 'default', 'N', '士兵证'),
       (5, '港澳居民来往内地通行证', '05', 'sys_user_cn_id_type', 'default', 'N', '港澳居民来往内地通行证'),
       (6, '台湾居民来往大陆通行证', '06', 'sys_user_cn_id_type', 'default', 'N', '台湾居民来往大陆通行证'),
       (7, '港澳台居民居住证', '07', 'sys_user_cn_id_type', 'default', 'N', '港澳台居民居住证'),
       (8, '外国人永久居留身份证', '08', 'sys_user_cn_id_type', 'default', 'N', '外国人永久居留身份证'),
       (9, '学生证', '09', 'sys_user_cn_id_type', 'default', 'N', '学生证'),
       (10, '其他', '99', 'sys_user_cn_id_type', 'default', 'N', '其他有效证件');

-- 插入系统功能权限数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '全部数据权限', '1', 'sys_role_data_scope', 'default', 'N', '拥有全部数据权限'),
       (2, '自定义数据权限', '2', 'sys_role_data_scope', 'default', 'N', '拥有自定义的数据权限'),
       (3, '本部门数据权限', '3', 'sys_role_data_scope', 'default', 'N', '拥有本部门数据权限'),
       (4, '本部门及以下数据权限', '4', 'sys_role_data_scope', 'default', 'Y', '拥有本部门及以下数据权限'),
       (5, '仅本人数据权限', '5', 'sys_role_data_scope', 'default', 'N', '拥有仅本人数据权限');

-- 插入语种数据 (ISO 639-1)
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '中文', 'zh', 'sys_language', 'default', 'Y', '汉语'),
       (2, '英语', 'en', 'sys_language', 'default', 'N', '英语'),
       (3, '日语', 'ja', 'sys_language', 'default', 'N', '日语'),
       (4, '法语', 'fr', 'sys_language', 'default', 'N', '法语'),
       (5, '德语', 'de', 'sys_language', 'default', 'N', '德语'),
       (6, '俄语', 'ru', 'sys_language', 'default', 'N', '俄语'),
       (7, '西班牙语', 'es', 'sys_language', 'default', 'N', '西班牙语'),
       (8, '阿拉伯语', 'ar', 'sys_language', 'default', 'N', '阿拉伯语'),
       (9, '韩语', 'ko', 'sys_language', 'default', 'N', '韩语'),
       (10, '葡萄牙语', 'pt', 'sys_language', 'default', 'N', '葡萄牙语');

-- 插入数据状态数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '正常', '0', 'sys_data_status', 'success', 'Y', '数据正常状态'),
       (2, '停用', '1', 'sys_data_status', 'warning', 'N', '数据已停用'),
       (3, '已删除', '2', 'sys_data_status', 'error', 'N', '数据已删除（逻辑删除）');

-- 插入数据选项数据（Y/N 是否选项）
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '是', 'Y', 'sys_data_option', 'success', 'N', '是/启用/有效'),
       (2, '否', 'N', 'sys_data_option', 'default', 'Y', '否/禁用/无效');

-- 插入系统功能类型数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '目录', 'DIR', 'sys_function_type', 'processing', 'Y', '功能目录'),
       (2, '菜单', 'MENU', 'sys_function_type', 'success', 'N', '系统菜单'),
       (3, '分组', 'GROUP', 'sys_function_type', 'default', 'N', '功能分组'),
       (4, '分割线', 'DIVIDER', 'sys_function_type', 'default', 'N', '菜单分割线'),
       (5, '按钮', 'BUTTON', 'sys_function_type', 'warning', 'N', '功能按钮'),
       (6, '接口', 'INTERFACE', 'sys_function_type', 'error', 'N', '系统接口');

-- 插入系统功能应用场景数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '用户应用', 'web', 'sys_function_scene', 'processing', 'Y', 'Web应用场景'),
       (2, '管理系统', 'admin', 'sys_function_scene', 'success', 'N', '管理系统场景'),
       (3, '个人中心', 'userInfo', 'sys_function_scene', 'warning', 'N', '用户信息相关场景'),
       (4, '移动应用', 'mobile', 'sys_function_scene', 'default', 'N', '移动端场景'),
       (5, '其他', 'other', 'sys_function_scene', 'error', 'N', '其他应用场景');

-- 插入系统上传文件审核状态数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '待审核', '0', 'sys_upload_audit_status', 'default', 'Y', '文件待审核'),
       (2, '审核中', '1', 'sys_upload_audit_status', 'processing', 'N', '文件审核中'),
       (3, '审核通过', '2', 'sys_upload_audit_status', 'success', 'N', '文件审核通过'),
       (4, '审核拒绝', '3', 'sys_upload_audit_status', 'error', 'N', '文件审核拒绝');

-- 插入系统上传文件分类数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '头像', '1', 'sys_upload_file_category', 'default', 'N', '用户头像文件'),
       (2, '课程封面', '2', 'sys_upload_file_category', 'default', 'N', '课程封面图片'),
       (3, '书籍封面', '3', 'sys_upload_file_category', 'default', 'N', '书籍封面图片'),
       (4, '书籍文件', '4', 'sys_upload_file_category', 'default', 'N', '书籍PDF文件'),
       (5, '笔记附件', '5', 'sys_upload_file_category', 'default', 'N', '学习笔记附件'),
       (6, '作业', '6', 'sys_upload_file_category', 'default', 'N', '学生作业文件'),
       (7, '课件', '7', 'sys_upload_file_category', 'default', 'N', '课程课件文件');

-- 插入系统上传文件存储类型数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, 'OSS存储', '1', 'sys_upload_storage_type', 'default', 'Y', '对象存储服务（S3兼容）'),
       (2, '本地存储', '2', 'sys_upload_storage_type', 'default', 'N', '服务器本地磁盘存储'),
       (3, 'CDN', '3', 'sys_upload_storage_type', 'default', 'N', '内容分发网络');

-- 插入系统上传文件访问级别数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '私有', '1', 'sys_upload_access_level', 'error', 'N', '仅上传者可访问'),
       (2, '登录用户', '2', 'sys_upload_access_level', 'warning', 'Y', '所有登录用户可访问'),
       (3, '公开', '3', 'sys_upload_access_level', 'success', 'N', '所有人可访问（无需登录）');

-- 插入系统操作日志业务类型数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '其它', '0', 'sys_oper_log_business_type', 'default', 'Y', '其他业务类型'),
       (2, '新增', '1', 'sys_oper_log_business_type', 'success', 'N', '新增业务'),
       (3, '修改', '2', 'sys_oper_log_business_type', 'processing', 'N', '修改业务'),
       (4, '删除', '3', 'sys_oper_log_business_type', 'error', 'N', '删除业务'),
       (5, '授权', '4', 'sys_oper_log_business_type', 'warning', 'N', '授权业务'),
       (6, '导出', '5', 'sys_oper_log_business_type', 'default', 'N', '导出业务'),
       (7, '导入', '6', 'sys_oper_log_business_type', 'default', 'N', '导入业务'),
       (8, '强退', '7', 'sys_oper_log_business_type', 'default', 'N', '强退业务'),
       (9, '生成代码', '8', 'sys_oper_log_business_type', 'default', 'N', '生成代码业务'),
       (10, '清空数据', '9', 'sys_oper_log_business_type', 'default', 'N', '清空数据业务');

-- 插入系统操作日志操作类型数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '其它', '0', 'sys_oper_log_oper_type', 'default', 'Y', '其他操作类型'),
       (2, '后台用户', '1', 'sys_oper_log_oper_type', 'default', 'N', '后台用户操作'),
       (3, '手机端用户', '2', 'sys_oper_log_oper_type', 'default', 'N', '手机端用户操作'),
       (4, '微信端用户', '3', 'sys_oper_log_oper_type', 'default', 'N', '微信端用户操作'),
       (5, 'API接口', '4', 'sys_oper_log_oper_type', 'default', 'N', 'API接口调用');

-- 插入学历数据 (GB/T 4658-2006)
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '博士研究生', '01', 'edu_background', 'default', 'N', '博士研究生'),
       (2, '硕士研究生', '02', 'edu_background', 'default', 'N', '硕士研究生'),
       (3, '大学本科', '03', 'edu_background', 'default', 'N', '大学本科'),
       (4, '大学专科', '04', 'edu_background', 'default', 'N', '大学专科和专科学校'),
       (5, '中等专科', '05', 'edu_background', 'default', 'N', '中等专科'),
       (6, '技工学校', '06', 'edu_background', 'default', 'N', '技工学校'),
       (7, '高中', '07', 'edu_background', 'default', 'N', '高级中学'),
       (8, '初中', '08', 'edu_background', 'default', 'N', '初级中学'),
       (9, '小学', '09', 'edu_background', 'default', 'N', '小学'),
       (10, '其他', '10', 'edu_background', 'default', 'N', '其他');

-- 插入书籍分类数据 (中国图书馆分类法)
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '马克思主义、列宁主义、毛泽东思想、邓小平理论', 'A', 'edu_book_category', 'default', 'N',
        'A 马克思主义、列宁主义、毛泽东思想、邓小平理论'),
       (2, '哲学、宗教', 'B', 'edu_book_category', 'default', 'N', 'B 哲学、宗教'),
       (3, '社会科学总论', 'C', 'edu_book_category', 'default', 'N', 'C 社会科学总论'),
       (4, '政治、法律', 'D', 'edu_book_category', 'default', 'N', 'D 政治、法律'),
       (5, '军事', 'E', 'edu_book_category', 'default', 'N', 'E 军事'),
       (6, '经济', 'F', 'edu_book_category', 'default', 'N', 'F 经济'),
       (7, '文化、科学、教育、体育', 'G', 'edu_book_category', 'default', 'N', 'G 文化、科学、教育、体育'),
       (8, '语言、文字', 'H', 'edu_book_category', 'default', 'N', 'H 语言、文字'),
       (9, '文学', 'I', 'edu_book_category', 'default', 'N', 'I 文学'),
       (10, '艺术', 'J', 'edu_book_category', 'default', 'N', 'J 艺术'),
       (11, '历史、地理', 'K', 'edu_book_category', 'default', 'N', 'K 历史、地理'),
       (12, '自然科学总论', 'N', 'edu_book_category', 'default', 'N', 'N 自然科学总论'),
       (13, '数理科学和化学', 'O', 'edu_book_category', 'default', 'N', 'O 数理科学和化学'),
       (14, '天文学、地球科学', 'P', 'edu_book_category', 'default', 'N', 'P 天文学、地球科学'),
       (15, '生物科学', 'Q', 'edu_book_category', 'default', 'N', 'Q 生物科学'),
       (16, '医药、卫生', 'R', 'edu_book_category', 'default', 'N', 'R 医药、卫生'),
       (17, '农业科学', 'S', 'edu_book_category', 'default', 'N', 'S 农业科学'),
       (18, '工业技术', 'T', 'edu_book_category', 'default', 'N', 'T 工业技术'),
       (19, '交通运输', 'U', 'edu_book_category', 'default', 'N', 'U 交通运输'),
       (20, '航空、航天', 'V', 'edu_book_category', 'default', 'N', 'V 航空、航天'),
       (21, '环境科学、安全科学', 'X', 'edu_book_category', 'default', 'N', 'X 环境科学、安全科学'),
       (22, '综合性图书', 'Z', 'edu_book_category', 'default', 'N', 'Z 综合性图书');

-- 插入学生状态数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '在读', 'studying', 'edu_student_status', 'default', 'Y', '正常在读'),
       (2, '休学', 'suspended', 'edu_student_status', 'default', 'N', '休学状态'),
       (3, '退学', 'dropped', 'edu_student_status', 'default', 'N', '已退学'),
       (4, '毕业', 'graduated', 'edu_student_status', 'default', 'N', '已毕业'),
       (5, '结业', 'completed', 'edu_student_status', 'default', 'N', '结业'),
       (6, '肄业', 'incompleted', 'edu_student_status', 'default', 'N', '肄业'),
       (7, '保留学籍', 'reserved', 'edu_student_status', 'default', 'N', '保留学籍');

-- 插入学位数据 (GB/T 6864-2003)
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '名誉博士', '1', 'edu_academic_degree', 'default', 'N', '名誉博士'),
       (2, '博士', '2', 'edu_academic_degree', 'default', 'N', '博士'),
       (3, '硕士', '3', 'edu_academic_degree', 'default', 'N', '硕士'),
       (4, '学士', '4', 'edu_academic_degree', 'default', 'N', '学士'),
       (5, '无', '9', 'edu_academic_degree', 'default', 'Y', '无学位');

-- 插入职称数据 (GB/T 8561-2001，部分常用)
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '教授', '011', 'edu_professional_title', 'default', 'N', '高等学校教授'),
       (2, '副教授', '012', 'edu_professional_title', 'default', 'N', '高等学校副教授'),
       (3, '讲师', '013', 'edu_professional_title', 'default', 'N', '高等学校讲师'),
       (4, '助教', '014', 'edu_professional_title', 'default', 'N', '高等学校助教'),
       (5, '研究员', '021', 'edu_professional_title', 'default', 'N', '科学研究人员研究员'),
       (6, '副研究员', '022', 'edu_professional_title', 'default', 'N', '科学研究人员副研究员'),
       (7, '助理研究员', '023', 'edu_professional_title', 'default', 'N', '科学研究人员助理研究员'),
       (8, '研究实习员', '024', 'edu_professional_title', 'default', 'N', '科学研究人员研究实习员'),
       (9, '高级工程师', '031', 'edu_professional_title', 'default', 'N', '工程技术人员高级工程师'),
       (10, '工程师', '032', 'edu_professional_title', 'default', 'N', '工程技术人员工程师'),
       (11, '助理工程师', '033', 'edu_professional_title', 'default', 'N', '工程技术人员助理工程师'),
       (12, '技术员', '034', 'edu_professional_title', 'default', 'N', '工程技术人员技术员');

-- 插入图谱构建方法数据
INSERT INTO sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, 'NLP自动构建', 'nlp', 'kg_build_method', 'default', 'N',
        '基于NLP技术的知识图谱自动构建，使用规则和NLP模型从文本中抽取实体和关系'),
       (2, 'LLM自动构建', 'llm', 'kg_build_method', 'default', 'Y',
        '基于大语言模型的知识图谱自动构建，使用LLM进行实体识别和关系抽取'),
       (3, 'LLM辅助人工', 'llm_assisted', 'kg_build_method', 'default', 'N', 'LLM辅助人工构建，AI提供建议，人工审核确认'),
       (4, '纯人工构建', 'manual', 'kg_build_method', 'default', 'N', '完全由专家手工构建知识图谱'),
       (5, '半自动构建', 'semi_auto', 'kg_build_method', 'default', 'N', '半自动构建，结合规则、NLP和人工校验'),
       (6, '导入现有图谱', 'import', 'kg_build_method', 'default', 'N', '从外部知识图谱系统导入（如RDF、OWL等格式）'),
       (7, '混合构建', 'hybrid', 'kg_build_method', 'default', 'N', '混合多种方法，如NLP+LLM、LLM+人工等'),
       (8, '增量更新', 'incremental', 'kg_build_method', 'default', 'N', '在已有图谱基础上增量更新'),
       (9, '自定义方法', 'custom', 'kg_build_method', 'default', 'N', '用户自定义的构建方法');

-- 插入文本处理状态数据
INSERT INTO public.sys_dict_data (dict_sort, dict_label, dict_value, dict_type, color, is_default, remark)
VALUES (1, '待处理', '0', 'text_processing_status', 'default', 'Y', '文本待处理'),
       (2, '处理中', '1', 'text_processing_status', 'processing', 'N', '文本处理中'),
       (3, '处理成功', '2', 'text_processing_status', 'success', 'N', '文本处理成功'),
       (4, '处理失败', '3', 'text_processing_status', 'error', 'N', '文本处理失败'),
       (9, '无需处理', '9', 'text_processing_status', 'default', 'N', '文本无需处理');