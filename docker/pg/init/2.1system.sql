-- ============================================================================
-- GraphEdu PostgreSQL 数据库初始化脚本
-- 版本: 0.0.1
-- 日期: 2026-03-01
-- ============================================================================
-- 注意：此脚本需要在 graphedu 数据库中执行（在 docker 创建的默认数据库中运行，或自行编写 sh 脚本运行）

-- ============================================================================
-- 1. 用户基础信息表（统一认证）
-- ============================================================================
DROP TABLE IF EXISTS sys_user CASCADE;
CREATE TABLE sys_user
(
    user_id        BIGSERIAL PRIMARY KEY,
    user_name      VARCHAR(32)  NOT NULL UNIQUE,
    nick_name      VARCHAR(32)  NOT NULL,
    password       VARCHAR(128) NOT NULL,
    email          VARCHAR(64)           DEFAULT '',
    phonenumber    VARCHAR(16)           DEFAULT '',
    avatar_file_id BIGINT,
    user_type      VARCHAR(2)   NOT NULL DEFAULT '4',
    status         CHAR(1)      NOT NULL DEFAULT '0',
    login_ip       VARCHAR(128)          DEFAULT '',
    login_date     TIMESTAMP,
    create_by      BIGINT                DEFAULT NULL,
    create_time    TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    update_by      BIGINT                DEFAULT NULL,
    update_time    TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    remark         VARCHAR(500)
);

-- 添加注释
COMMENT ON TABLE sys_user IS '用户基础信息表';
COMMENT ON COLUMN sys_user.user_id IS '用户ID';
COMMENT ON COLUMN sys_user.user_name IS '登录账号';
COMMENT ON COLUMN sys_user.nick_name IS '用户昵称';
COMMENT ON COLUMN sys_user.password IS '密码（bcrypt加密）';
COMMENT ON COLUMN sys_user.email IS '用户邮箱';
COMMENT ON COLUMN sys_user.phonenumber IS '手机号码';
COMMENT ON COLUMN sys_user.avatar_file_id IS '头像文件ID';
COMMENT ON COLUMN sys_user.user_type IS '用户类型，对照 sys_user_type（1学生, 2教师, 3管理员, 4其他）';
COMMENT ON COLUMN sys_user.status IS '用户状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN sys_user.login_ip IS '最后登录IP';
COMMENT ON COLUMN sys_user.login_date IS '最后登录时间';
COMMENT ON COLUMN sys_user.create_by IS '创建者';
COMMENT ON COLUMN sys_user.create_time IS '创建时间';
COMMENT ON COLUMN sys_user.update_by IS '更新者';
COMMENT ON COLUMN sys_user.update_time IS '更新时间（由应用程序更新）';
COMMENT ON COLUMN sys_user.remark IS '备注';

-- 创建索引
CREATE INDEX idx_sys_user_user_name ON sys_user (user_name);
CREATE INDEX idx_sys_user_email ON sys_user (email);
CREATE INDEX idx_sys_user_phonenumber ON sys_user (phonenumber);
CREATE INDEX idx_sys_user_user_type ON sys_user (user_type);
CREATE INDEX idx_sys_user_status ON sys_user (status);

-- ============================================================================
-- 2. 部门信息表（树形结构）
-- ============================================================================
DROP TABLE IF EXISTS sys_dept CASCADE;
CREATE TABLE sys_dept
(
    dept_id     BIGSERIAL PRIMARY KEY,
    parent_id   BIGINT      NOT NULL DEFAULT 0,
    dept_name   VARCHAR(64) NOT NULL,
    dept_key    VARCHAR(64) NOT NULL UNIQUE,
    leader      VARCHAR(32),
    phone       VARCHAR(16),
    email       VARCHAR(64),
    status      CHAR(1)     NOT NULL DEFAULT '0',
    sort_order  INTEGER     NOT NULL DEFAULT 0,
    create_by   BIGINT               DEFAULT NULL,
    create_time TIMESTAMP            DEFAULT CURRENT_TIMESTAMP,
    update_by   BIGINT               DEFAULT NULL,
    update_time TIMESTAMP            DEFAULT CURRENT_TIMESTAMP,
    remark      VARCHAR(500)
);

COMMENT ON TABLE sys_dept IS '部门信息表';
COMMENT ON COLUMN sys_dept.dept_id IS '部门ID';
COMMENT ON COLUMN sys_dept.parent_id IS '父部门ID（0表示根节点）';
COMMENT ON COLUMN sys_dept.dept_name IS '部门名称';
COMMENT ON COLUMN sys_dept.dept_key IS '部门编码（唯一标识）';
COMMENT ON COLUMN sys_dept.leader IS '负责人';
COMMENT ON COLUMN sys_dept.phone IS '联系电话';
COMMENT ON COLUMN sys_dept.email IS '联系邮箱';
COMMENT ON COLUMN sys_dept.status IS '部门状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN sys_dept.sort_order IS '显示顺序';
COMMENT ON COLUMN sys_dept.create_by IS '创建者';
COMMENT ON COLUMN sys_dept.create_time IS '创建时间';
COMMENT ON COLUMN sys_dept.update_by IS '更新者';
COMMENT ON COLUMN sys_dept.update_time IS '更新时间（由应用程序更新）';
COMMENT ON COLUMN sys_dept.remark IS '备注';

-- 创建索引
CREATE INDEX idx_sys_dept_parent_id ON sys_dept (parent_id);
CREATE INDEX idx_sys_dept_dept_key ON sys_dept (dept_key);
CREATE INDEX idx_sys_dept_status ON sys_dept (status);

-- ============================================================================
-- 3. 用户和部门关联表（多对多）
-- ============================================================================
DROP TABLE IF EXISTS sys_user_dept CASCADE;
CREATE TABLE sys_user_dept
(
    user_id    BIGINT  NOT NULL,
    dept_id    BIGINT  NOT NULL,
    is_primary CHAR(1) NOT NULL DEFAULT 'N',
    PRIMARY KEY (user_id, dept_id)
);

COMMENT ON TABLE sys_user_dept IS '用户和部门关联表（多对多）';
COMMENT ON COLUMN sys_user_dept.user_id IS '用户ID';
COMMENT ON COLUMN sys_user_dept.dept_id IS '部门ID';
COMMENT ON COLUMN sys_user_dept.is_primary IS '是否主部门，对应 sys_data_option（Y是 N否）';

-- 创建索引
CREATE INDEX idx_sys_user_dept_user_id ON sys_user_dept (user_id);
CREATE INDEX idx_sys_user_dept_dept_id ON sys_user_dept (dept_id);

-- ============================================================================
-- 4. 角色信息表
-- ============================================================================
DROP TABLE IF EXISTS sys_role CASCADE;
CREATE TABLE sys_role
(
    role_id     BIGSERIAL PRIMARY KEY,
    role_name   VARCHAR(30)  NOT NULL,
    role_key    VARCHAR(100) NOT NULL UNIQUE,
    role_sort   INTEGER      NOT NULL DEFAULT 0,
    data_scope  CHAR(1)      NOT NULL DEFAULT '1',
    status      CHAR(1)      NOT NULL DEFAULT '0',
    create_by   BIGINT                DEFAULT NULL,
    create_time TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    update_by   BIGINT                DEFAULT NULL,
    update_time TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    remark      VARCHAR(500)
);

COMMENT ON TABLE sys_role IS '角色信息表';
COMMENT ON COLUMN sys_role.role_id IS '角色ID';
COMMENT ON COLUMN sys_role.role_name IS '角色名称';
COMMENT ON COLUMN sys_role.role_key IS '角色唯一标识';
COMMENT ON COLUMN sys_role.role_sort IS '显示顺序';
COMMENT ON COLUMN sys_role.data_scope IS '数据范围，对照 sys_role_data_scope（1：全部数据权限 2：自定数据权限 3：本部门数据权限 4：本部门及以下数据权限 5：仅本人数据权限）';
COMMENT ON COLUMN sys_role.status IS '角色状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN sys_role.create_by IS '创建者';
COMMENT ON COLUMN sys_role.create_time IS '创建时间';
COMMENT ON COLUMN sys_role.update_by IS '更新者';
COMMENT ON COLUMN sys_role.update_time IS '更新时间（由应用程序更新）';
COMMENT ON COLUMN sys_role.remark IS '备注';

CREATE INDEX idx_sys_role_role_key ON sys_role (role_key);
CREATE INDEX idx_sys_role_sort ON sys_role (role_sort);

-- 设置角色ID起始值从10开始（role_id < 10 为系统超级管理员角色）
ALTER SEQUENCE sys_role_role_id_seq RESTART WITH 11;

-- ============================================================================
-- 5. 用户和角色关联表
-- ============================================================================
DROP TABLE IF EXISTS sys_user_role CASCADE;
CREATE TABLE sys_user_role
(
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id)
    -- FOREIGN KEY (user_id) REFERENCES sys_user (user_id) ON DELETE CASCADE,
    -- FOREIGN KEY (role_id) REFERENCES sys_role (role_id) ON DELETE CASCADE
);

COMMENT ON TABLE sys_user_role IS '用户和角色关联表';
COMMENT ON COLUMN sys_user_role.user_id IS '用户ID';
COMMENT ON COLUMN sys_user_role.role_id IS '角色ID';

-- ============================================================================
-- 5. 角色功能关联表
-- ============================================================================
DROP TABLE IF EXISTS sys_role_function CASCADE;
CREATE TABLE sys_role_function
(
    role_id     BIGINT NOT NULL,
    function_id BIGINT NOT NULL,
    PRIMARY KEY (role_id, function_id)
);

COMMENT ON TABLE sys_role_function IS '角色功能关联表';
COMMENT ON COLUMN sys_role_function.role_id IS '角色ID';
COMMENT ON COLUMN sys_role_function.function_id IS '功能ID';

-- 创建索引
CREATE INDEX idx_sys_role_function_role_id ON sys_role_function (role_id);
CREATE INDEX idx_sys_role_function_function_id ON sys_role_function (function_id);


-- ============================================================================
-- 5.4 角色和部门关联表（数据权限）
-- ============================================================================
DROP TABLE IF EXISTS sys_role_dept CASCADE;
CREATE TABLE sys_role_dept
(
    role_id BIGINT NOT NULL,
    dept_id BIGINT NOT NULL,
    PRIMARY KEY (role_id, dept_id)
);

COMMENT ON TABLE sys_role_dept IS '角色和部门关联表（用于配置角色的数据权限范围）';
COMMENT ON COLUMN sys_role_dept.role_id IS '角色ID';
COMMENT ON COLUMN sys_role_dept.dept_id IS '部门ID';

-- 创建索引
CREATE INDEX idx_sys_role_dept_role_id ON sys_role_dept (role_id);
CREATE INDEX idx_sys_role_dept_dept_id ON sys_role_dept (dept_id);

-- ============================================================================
-- 23. 操作日志表
-- ============================================================================
DROP TABLE IF EXISTS sys_oper_log CASCADE;
CREATE TABLE sys_oper_log
(
    oper_id        BIGSERIAL PRIMARY KEY,
    title          VARCHAR(50)   DEFAULT ''  NOT NULL,
    business_type  CHAR(1)       DEFAULT '0' NOT NULL,
    method         VARCHAR(100)  DEFAULT ''  NOT NULL,
    request_method VARCHAR(10)   DEFAULT ''  NOT NULL,
    operator_type  CHAR(1)       DEFAULT '0' NOT NULL,
    oper_name      VARCHAR(50)   DEFAULT ''  NOT NULL,
    dept_name      VARCHAR(50)   DEFAULT ''  NOT NULL,
    oper_url       VARCHAR(255)  DEFAULT ''  NOT NULL,
    oper_ip        VARCHAR(128)  DEFAULT ''  NOT NULL,
    oper_location  VARCHAR(255)  DEFAULT ''  NOT NULL,
    oper_param     VARCHAR(2000) DEFAULT ''  NOT NULL,
    json_result    VARCHAR(2000) DEFAULT ''  NOT NULL,
    status         CHAR(1)       DEFAULT '0' NOT NULL,
    error_msg      VARCHAR(2000) DEFAULT ''  NOT NULL,
    oper_time      TIMESTAMP                 NOT NULL,
    cost_time      BIGINT        DEFAULT 0   NOT NULL
);

COMMENT ON TABLE sys_oper_log IS '操作日志记录';
COMMENT ON COLUMN sys_oper_log.oper_id IS '日志主键';
COMMENT ON COLUMN sys_oper_log.title IS '模块标题';
COMMENT ON COLUMN sys_oper_log.business_type IS '业务类型，对照 sys_oper_log_business_type（0其它 1新增 2修改 3删除 等）';
COMMENT ON COLUMN sys_oper_log.method IS '方法名称';
COMMENT ON COLUMN sys_oper_log.request_method IS '请求方式';
COMMENT ON COLUMN sys_oper_log.operator_type IS '操作类别，对照 sys_oper_log_oper_type（0其它 1后台用户 2手机端用户 等）';
COMMENT ON COLUMN sys_oper_log.oper_name IS '操作人员';
COMMENT ON COLUMN sys_oper_log.dept_name IS '部门名称';
COMMENT ON COLUMN sys_oper_log.oper_url IS '请求URL';
COMMENT ON COLUMN sys_oper_log.oper_ip IS '主机地址';
COMMENT ON COLUMN sys_oper_log.oper_location IS '操作地点';
COMMENT ON COLUMN sys_oper_log.oper_param IS '请求参数';
COMMENT ON COLUMN sys_oper_log.json_result IS '返回参数';
COMMENT ON COLUMN sys_oper_log.status IS '操作日志状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN sys_oper_log.error_msg IS '错误消息';
COMMENT ON COLUMN sys_oper_log.oper_time IS '操作时间';
COMMENT ON COLUMN sys_oper_log.cost_time IS '消耗时间（毫秒）';

CREATE INDEX idx_sys_oper_log_bt ON sys_oper_log (business_type);
CREATE INDEX idx_sys_oper_log_s ON sys_oper_log (status);
CREATE INDEX idx_sys_oper_log_ot ON sys_oper_log (oper_time);

-- ============================================================================
-- 24. 登录日志表
-- ============================================================================
DROP TABLE IF EXISTS sys_logininfor CASCADE;
CREATE TABLE sys_logininfor
(
    info_id        BIGSERIAL PRIMARY KEY,
    user_name      VARCHAR(50)  DEFAULT ''  NOT NULL,
    ipaddr         VARCHAR(128) DEFAULT ''  NOT NULL,
    login_location VARCHAR(255) DEFAULT ''  NOT NULL,
    browser        VARCHAR(50)  DEFAULT ''  NOT NULL,
    os             VARCHAR(50)  DEFAULT ''  NOT NULL,
    status         CHAR(1)      DEFAULT '0' NOT NULL,
    msg            VARCHAR(255) DEFAULT ''  NOT NULL,
    login_time     TIMESTAMP                NOT NULL
);

COMMENT ON TABLE sys_logininfor IS '系统访问记录';
COMMENT ON COLUMN sys_logininfor.info_id IS '访问ID';
COMMENT ON COLUMN sys_logininfor.user_name IS '用户账号';
COMMENT ON COLUMN sys_logininfor.ipaddr IS '登录IP地址';
COMMENT ON COLUMN sys_logininfor.login_location IS '登录地点';
COMMENT ON COLUMN sys_logininfor.browser IS '浏览器类型';
COMMENT ON COLUMN sys_logininfor.os IS '操作系统';
COMMENT ON COLUMN sys_logininfor.status IS '登录日志状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN sys_logininfor.msg IS '提示消息';
COMMENT ON COLUMN sys_logininfor.login_time IS '访问时间';

CREATE INDEX idx_sys_logininfor_s ON sys_logininfor (status);
CREATE INDEX idx_sys_logininfor_lt ON sys_logininfor (login_time);
