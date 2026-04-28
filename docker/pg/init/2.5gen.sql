-- ============================================================================
-- GraphEdu Code Generator PostgreSQL 数据库初始化脚本
-- 版本: 0.0.1
-- 日期: 2026-02-13
-- ============================================================================
-- 代码生成器相关表

-- ============================================================================
-- 1. 代码生成业务表
-- ============================================================================
DROP TABLE IF EXISTS gen_table CASCADE;
CREATE TABLE gen_table
(
    table_id          BIGSERIAL PRIMARY KEY,
    table_name        VARCHAR(200)  DEFAULT ''  NOT NULL,
    table_comment     VARCHAR(500)  DEFAULT ''  NOT NULL,
    sub_table_name    VARCHAR(64)              DEFAULT NULL,
    sub_table_fk_name VARCHAR(64)              DEFAULT NULL,
    class_name        VARCHAR(100)  DEFAULT ''  NOT NULL,
    tpl_category      VARCHAR(200)  DEFAULT 'crud' NOT NULL,
    tpl_web_type      VARCHAR(30)   DEFAULT ''  NOT NULL,
    package_name      VARCHAR(100),
    module_name       VARCHAR(30),
    business_name     VARCHAR(30),
    function_name     VARCHAR(50),
    function_author   VARCHAR(50),
    gen_type          CHAR(1)        DEFAULT '0' NOT NULL,
    gen_path          VARCHAR(200)   DEFAULT '/' NOT NULL,
    options           VARCHAR(1000),
    create_by         VARCHAR(64)    DEFAULT ''  NOT NULL,
    create_time       TIMESTAMP,
    update_by         VARCHAR(64)    DEFAULT ''  NOT NULL,
    update_time       TIMESTAMP,
    remark            VARCHAR(500)             DEFAULT NULL
);

-- 添加注释
COMMENT ON TABLE gen_table IS '代码生成业务表';
COMMENT ON COLUMN gen_table.table_id IS '编号';
COMMENT ON COLUMN gen_table.table_name IS '表名称';
COMMENT ON COLUMN gen_table.table_comment IS '表描述';
COMMENT ON COLUMN gen_table.sub_table_name IS '关联子表的表名';
COMMENT ON COLUMN gen_table.sub_table_fk_name IS '子表关联的外键名';
COMMENT ON COLUMN gen_table.class_name IS '实体类名称';
COMMENT ON COLUMN gen_table.tpl_category IS '使用的模板（crud单表操作 tree树表操作）';
COMMENT ON COLUMN gen_table.tpl_web_type IS '前端模板类型（element-ui模版 element-plus模版）';
COMMENT ON COLUMN gen_table.package_name IS '生成包路径';
COMMENT ON COLUMN gen_table.module_name IS '生成模块名';
COMMENT ON COLUMN gen_table.business_name IS '生成业务名';
COMMENT ON COLUMN gen_table.function_name IS '生成功能名';
COMMENT ON COLUMN gen_table.function_author IS '生成功能作者';
COMMENT ON COLUMN gen_table.gen_type IS '生成代码方式（0zip压缩包 1自定义路径）';
COMMENT ON COLUMN gen_table.gen_path IS '生成路径（不填默认项目路径）';
COMMENT ON COLUMN gen_table.options IS '其它生成选项';
COMMENT ON COLUMN gen_table.create_by IS '创建者';
COMMENT ON COLUMN gen_table.create_time IS '创建时间';
COMMENT ON COLUMN gen_table.update_by IS '更新者';
COMMENT ON COLUMN gen_table.update_time IS '更新时间';
COMMENT ON COLUMN gen_table.remark IS '备注';

-- 创建索引
CREATE INDEX idx_gen_table_table_name ON gen_table (table_name);


-- ============================================================================
-- 2. 代码生成业务表字段
-- ============================================================================
DROP TABLE IF EXISTS gen_table_column CASCADE;
CREATE TABLE gen_table_column
(
    column_id       BIGSERIAL PRIMARY KEY,
    table_id        BIGINT,
    column_name     VARCHAR(200),
    column_comment  VARCHAR(500),
    column_type     VARCHAR(100),
    python_type     VARCHAR(500),
    python_field    VARCHAR(200),
    is_pk           CHAR(1),
    is_increment    CHAR(1),
    is_required     CHAR(1),
    is_unique       CHAR(1),
    is_insert       CHAR(1),
    is_edit         CHAR(1),
    is_list         CHAR(1),
    is_query        CHAR(1),
    query_type      VARCHAR(200)  DEFAULT 'EQ' NOT NULL,
    html_type       VARCHAR(200),
    dict_type       VARCHAR(200)  DEFAULT ''  NOT NULL,
    sort            INTEGER,
    create_by       VARCHAR(64)   DEFAULT ''  NOT NULL,
    create_time     TIMESTAMP,
    update_by       VARCHAR(64)   DEFAULT ''  NOT NULL,
    update_time     TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE gen_table_column IS '代码生成业务表字段';
COMMENT ON COLUMN gen_table_column.column_id IS '编号';
COMMENT ON COLUMN gen_table_column.table_id IS '归属表编号';
COMMENT ON COLUMN gen_table_column.column_name IS '列名称';
COMMENT ON COLUMN gen_table_column.column_comment IS '列描述';
COMMENT ON COLUMN gen_table_column.column_type IS '列类型';
COMMENT ON COLUMN gen_table_column.python_type IS 'PYTHON类型';
COMMENT ON COLUMN gen_table_column.python_field IS 'PYTHON字段名';
COMMENT ON COLUMN gen_table_column.is_pk IS '是否主键（1是）';
COMMENT ON COLUMN gen_table_column.is_increment IS '是否自增（1是）';
COMMENT ON COLUMN gen_table_column.is_required IS '是否必填（1是）';
COMMENT ON COLUMN gen_table_column.is_unique IS '是否唯一（1是）';
COMMENT ON COLUMN gen_table_column.is_insert IS '是否为插入字段（1是）';
COMMENT ON COLUMN gen_table_column.is_edit IS '是否编辑字段（1是）';
COMMENT ON COLUMN gen_table_column.is_list IS '是否列表字段（1是）';
COMMENT ON COLUMN gen_table_column.is_query IS '是否查询字段（1是）';
COMMENT ON COLUMN gen_table_column.query_type IS '查询方式（等于、不等于、大于、小于、范围）';
COMMENT ON COLUMN gen_table_column.html_type IS '显示类型（文本框、文本域、下拉框、复选框、单选框、日期控件）';
COMMENT ON COLUMN gen_table_column.dict_type IS '字典类型';
COMMENT ON COLUMN gen_table_column.sort IS '排序';
COMMENT ON COLUMN gen_table_column.create_by IS '创建者';
COMMENT ON COLUMN gen_table_column.create_time IS '创建时间';
COMMENT ON COLUMN gen_table_column.update_by IS '更新者';
COMMENT ON COLUMN gen_table_column.update_time IS '更新时间';

-- 创建索引
CREATE INDEX idx_gen_table_column_table_id ON gen_table_column (table_id);
CREATE INDEX idx_gen_table_column_sort ON gen_table_column (sort);
