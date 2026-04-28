-- ============================================================================
-- 功能权限表（树形结构）
-- ============================================================================
DROP TABLE IF EXISTS sys_function CASCADE;
CREATE TABLE sys_function
(
    function_id      BIGSERIAL PRIMARY KEY,
    parent_id        BIGINT       NOT NULL DEFAULT 0,
    function_name    VARCHAR(50)  NOT NULL,
    function_key     VARCHAR(128),
    function_type    VARCHAR(20)  NOT NULL,
    route_path       VARCHAR(128),
    route_cache      CHAR(1)               DEFAULT NULL,
    route_external   CHAR(1)               DEFAULT NULL,
    route_query      JSONB,
    component        VARCHAR(256),
    layout_component VARCHAR(256),
    icon             VARCHAR(128),
    sort_order       INTEGER      NOT NULL DEFAULT 0,
    visible          CHAR(1)      NOT NULL DEFAULT 'Y',
    style            JSONB,
    option_style     JSONB,
    status           CHAR(1)      NOT NULL DEFAULT '0',
    scene            VARCHAR(20)  NOT NULL DEFAULT 'admin',
    create_by        BIGINT                DEFAULT NULL,
    create_time      TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    update_by        BIGINT                DEFAULT NULL,
    update_time      TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    remark           VARCHAR(500)
);

COMMENT ON TABLE sys_function IS '功能权限表';
COMMENT ON COLUMN sys_function.function_id IS '功能ID';
COMMENT ON COLUMN sys_function.parent_id IS '父功能ID（0表示根节点）';
COMMENT ON COLUMN sys_function.function_name IS '功能名称';
COMMENT ON COLUMN sys_function.function_key IS '权限标识（同一场景下全局唯一，如 student:list, course:add, api:user:*）；GROUP/DIVIDER 类型不需要权限标识，为 NULL';
COMMENT ON COLUMN sys_function.function_type IS '功能类型，对照 sys_function_type（DIR目录, MENU菜单, BUTTON按钮, INTERFACE接口, GROUP菜单分组, DIVIDER菜单分隔线）';
COMMENT ON COLUMN sys_function.route_path IS '路由路径';
COMMENT ON COLUMN sys_function.route_cache IS '路由路径页面是否缓存，对应 sys_data_option（Y是 N否）';
COMMENT ON COLUMN sys_function.route_query IS '路由传递参数';
COMMENT ON COLUMN sys_function.route_external IS '是否外链，对应 sys_data_option（Y是 N否）';
COMMENT ON COLUMN sys_function.component IS '组件路径';
COMMENT ON COLUMN sys_function.layout_component IS '布局组件路径，如 layout/CommonLayout/index，为空则不使用布局';
COMMENT ON COLUMN sys_function.icon IS '菜单图标';
COMMENT ON COLUMN sys_function.sort_order IS '显示顺序';
COMMENT ON COLUMN sys_function.visible IS '是否可见，对应 sys_data_option（Y是 N否）';
COMMENT ON COLUMN sys_function.style IS '菜单CSS样式（JSON格式，使用css-in-js格式）';
COMMENT ON COLUMN sys_function.option_style IS '菜单选项样式（JSON格式，使用css-in-js格式）';
COMMENT ON COLUMN sys_function.status IS '功能状态，对照 sys_data_status（0正常 1停用 2已删除）';
COMMENT ON COLUMN sys_function.scene IS '应用场景，对照 sys_function_scene（web用户应用, admin管理系统, userInfo个人中心等）';
COMMENT ON COLUMN sys_function.create_by IS '创建者';
COMMENT ON COLUMN sys_function.create_time IS '创建时间';
COMMENT ON COLUMN sys_function.update_by IS '更新者';
COMMENT ON COLUMN sys_function.update_time IS '更新时间（由应用程序更新）';
COMMENT ON COLUMN sys_function.remark IS '备注';

-- 创建索引
CREATE INDEX idx_sys_function_parent_id ON sys_function (parent_id);
CREATE INDEX idx_sys_function_function_key ON sys_function (function_key);
CREATE INDEX idx_sys_function_function_type ON sys_function (function_type);
CREATE INDEX idx_sys_function_scene ON sys_function (scene);

-- ============================================================================
-- 插入功能权限数据（树形结构）
-- ============================================================================
--
-- 一、function_id 规划说明
-- ----------------------------------------------------------------------------
-- 本表数据明确指定 function_id，避免依赖自动增长导致 parent_id 关系混乱
--
-- ID 使用说明：
--   - 按顺序分配ID，不再严格限制区间
--   - 按钮ID紧接在对应页面ID后面，无间隔
--
-- 二、layout_component 字段说明
-- ----------------------------------------------------------------------------
-- - 用于指定该路由使用的布局组件路径（相对于 src/ 目录）
-- - 格式：layout/LayoutName/index，例如：layout/CommonLayout/index
-- - 为空（NULL）表示不使用独立布局，由前端默认处理或继承父级布局
--
-- 使用规则：
-- 1. DIR 类型（目录）：
--    - 通常设置 layout_component，作为该模块下所有子路由的布局容器
--    - web 场景使用：layout/CommonLayout/index、layout/StudentCourseLayout/index、layout/TeacherCourseLayout/index 等特定布局
--    - admin 场景使用：layout/WorkbenchLayout/index
--
-- 2. MENU 类型（菜单）：
--    - 一般不设置 layout_component（NULL），继承父级 DIR 的布局
--    - 特殊情况：如果某个页面需要特殊布局（如课程自学页使用 WorkbenchLayout），
--      可以单独设置 layout_component 覆盖父级布局
--
-- 3. BUTTON/INTERFACE/GROUP/DIVIDER 类型：
--    - 不设置 layout_component（这些类型不生成路由）
--
-- 示例场景：
-- - web 场景首页：DIR 类型，使用 layout/CommonLayout/index
-- - web 场景课程页：DIR 类型，使用 layout/CommonLayout/index
-- - web 场景特殊页：MENU 类型，使用 layout/WorkbenchLayout/index（课程自学页）
-- - admin 场景所有模块：DIR 类型，使用 layout/WorkbenchLayout/index
-- - 无布局页面：layout_component 为 NULL，前端直接渲染组件
--
-- 注意事项：
-- - 布局组件必须存在于 graphedu-ui/src/layout/ 目录下
-- - 前端会根据 layout_component 动态导入布局组件
-- - 如果 layout_component 指向的组件不存在，路由注册会失败
--
-- 三、功能权限树形结构总览
-- ----------------------------------------------------------------------------
-- web 场景：
--   2000. 首页（MENU）
--   2110. 课程列表（MENU）
--      ├─ 2111-2114. 课程操作（BUTTON×4）
--   2115. 课程门户（MENU，不可见）
--   2200. 学生学习页（DIR，不可见）
--      ├─ 2208. 学习首页（MENU）
--      ├─ 2201-2207. AI 对话（INTERFACE×7）
--      ├─ 2210. 章节资料（MENU）
--      │    └─ 2211-2212. 章节资料查看（INTERFACE×2）
--      ├─ 2220. 课程知识图谱（MENU）
--      │    └─ 2221-2223. 知识图谱查看（INTERFACE×3）
--      ├─ 2230. 学习路径（MENU）
--      │    └─ 2231-2234. 学习路径（INTERFACE×4）
--      └─ 2240. 习题（MENU）
--           └─ 2241-2248. 习题相关（INTERFACE×8）
--   2300. 教师课程页（DIR，不可见）
--      ├─ 2310. 课程首页（MENU）
--      │    └─ 2311. 课程详情（INTERFACE）
--      ├─ 2320. 课程门户设置（MENU）
--      ├─ 2330. 章节设置（MENU）
--      │    └─ 2331. 章节详情（INTERFACE）
--      ├─ 2340. 课程资源设置（MENU）
--      │    └─ 2341-2343. 资源管理（INTERFACE×3）
--      ├─ 2350. 课程知识图谱管理（MENU）
--      │    └─ 2351-2354. 知识图谱管理（INTERFACE×4）
--      ├─ 2360. AI问答知识图谱管理（MENU）
--      │    └─ 2361-2365. GraphRAG任务（INTERFACE×5）
--      └─ 2370. 学生管理（MENU）
--           └─ 2371-2374. 学生管理（INTERFACE×4）
--
-- userInfo 场景：
--   3000. 个人中心（DIR）
--      ├─ 3100. 个人信息（MENU）
--      ├─ 3400. 账号安全（MENU）
--      └─ 3300. 账号设置（MENU）
--
-- admin 场景：
--   900. 管理首页（MENU）
--   1000. 系统管理（DIR）
--        ├─ 1100. 用户管理（MENU）
--        │    ├─ 1110. 用户查询（BUTTON）
--        │    ├─ 1120. 用户新增（BUTTON）
--        │    ├─ 1130. 用户修改（BUTTON）
--        │    ├─ 1140. 用户删除（BUTTON）
--        │    ├─ 1150. 用户导出（BUTTON）
--        │    └─ 1160. 重置密码（BUTTON）
--        ├─ 1200. 角色管理（MENU）
--        │    ├─ 1210. 角色查询（BUTTON）
--        │    ├─ 1220. 角色新增（BUTTON）
--        │    ├─ 1230. 角色修改（BUTTON）
--        │    ├─ 1240. 角色删除（BUTTON）
--        │    └─ 1250. 分配权限（BUTTON）
--        ├─ 1300. 菜单管理（MENU）
--        │    ├─ 1310. 菜单查询（BUTTON）
--        │    ├─ 1320. 菜单新增（BUTTON）
--        │    ├─ 1330. 菜单修改（BUTTON）
--        │    └─ 1340. 菜单删除（BUTTON）
--        ├─ 1400. 部门管理（MENU）
--        │    ├─ 1410. 部门查询（BUTTON）
--        │    ├─ 1420. 部门新增（BUTTON）
--        │    ├─ 1430. 部门修改（BUTTON）
--        │    ├─ 1440. 部门删除（BUTTON）
--        │    ├─ 1450. 导出部门（BUTTON）
--        │    ├─ 1460. 展开/折叠（BUTTON）
--        │    └─ 1470. 查看用户（BUTTON）
--        ├─ 1500. 字典管理（MENU）
--        │    ├─ 1510. 字典查询（BUTTON）
--        │    ├─ 1520. 字典新增（BUTTON）
--        │    ├─ 1530. 字典修改（BUTTON）
--        │    ├─ 1540. 字典删除（BUTTON）
--        │    ├─ 1550. 字典导出（BUTTON）
--        │    ├─ 1560. 刷新缓存（BUTTON）
--        │    ├─ 1570. 字典数据查询（BUTTON）
--        │    ├─ 1580. 字典数据新增（BUTTON）
--        │    └─ 1590. 字典数据修改（BUTTON）
--        ├─ 1600. 操作日志（MENU）
--        │    ├─ 1610. 操作日志查询（BUTTON）
--        │    ├─ 1620. 删除操作日志（BUTTON）
--        │    ├─ 1630. 清空操作日志（BUTTON）
--        │    └─ 1640. 导出操作日志（BUTTON）
--        ├─ 1700. 登录日志（MENU）
--        │    ├─ 1710. 登录日志查询（BUTTON）
--        │    ├─ 1720. 删除登录日志（BUTTON）
--        │    ├─ 1730. 清空登录日志（BUTTON）
--        │    └─ 1740. 解锁用户（BUTTON）
--        ├─ 1800. 代码生成（MENU）
--        │    ├─ 1810. 查询（BUTTON）
--        │    ├─ 1820. 导入（BUTTON）
--        │    ├─ 1830. 修改（BUTTON）
--        │    ├─ 1840. 删除（BUTTON）
--        │    ├─ 1850. 预览（BUTTON）
--        │    ├─ 1860. 生成（BUTTON）
--        │    └─ 1870. 同步（BUTTON）
--        └─ 1900. 定时任务（MENU）
--             └─ 1910. 查询（BUTTON）
--   5000. 教学管理（DIR）
--        ├─ 5100. 课程管理（MENU）
--        │    ├─ 5110. 课程查询（BUTTON）
--        │    ├─ 5120. 课程新增（BUTTON）
--        │    ├─ 5130. 课程修改（BUTTON）
--        │    ├─ 5140. 课程删除（BUTTON）
--        │    ├─ 5150. 课程发布（BUTTON）
--        │    ├─ 5160. 课程章节管理（BUTTON）
--        │    │   ├─ 5161. 章节查询（BUTTON）
--        │    │   ├─ 5162. 章节新增（BUTTON）
--        │    │   ├─ 5163. 章节修改（BUTTON）
--        │    │   ├─ 5164. 章节删除（BUTTON）
--        │    │   └─ 5165. 章节排序（BUTTON）
--        │    ├─ 5170. 课程知识点知识图谱管理（BUTTON）
--        │    │   ├─ 5171. 节点查询（BUTTON）
--        │    │   ├─ 5172. 节点新增（BUTTON）
--        │    │   ├─ 5173. 节点修改（BUTTON）
--        │    │   └─ 5174. 节点删除（BUTTON）
--        │    ├─ 5180. 课程语义图谱管理（BUTTON）
--        │    │   ├─ 5181. 资料增补、更新图谱（BUTTON）
--        │    │   ├─ 5182. 构建图谱（BUTTON）
--        │    │   ├─ 5183. 创建图谱（BUTTON）
--        │    │   ├─ 5184. 查看图谱（BUTTON）
--        │    │   ├─ 5185. 修改图谱状态（BUTTON）
--        │    │   ├─ 5186. 查询图谱状态（BUTTON）
--        │    │   └─ 5187. 删除图谱（BUTTON）
--        │    └─ 5190. 课程资源管理（BUTTON）
--        ├─ 5200. 教师管理（MENU）
--        │    ├─ 5210. 教师查询（BUTTON）
--        │    ├─ 5220. 教师新增（BUTTON）
--        │    ├─ 5230. 教师修改（BUTTON）
--        │    ├─ 5240. 教师删除（BUTTON）
--        │    └─ 5250. 重置密码（BUTTON）
--        └─ 5300. 学生管理（MENU）
--             ├─ 5310. 学生查询（BUTTON）
--             ├─ 5320. 学生新增（BUTTON）
--             ├─ 5330. 学生修改（BUTTON）
--             ├─ 5340. 学生删除（BUTTON）
--             └─ 5350. 重置密码（BUTTON）
--
-- ============================================================================

TRUNCATE sys_function;

-- ============================================================================
-- 一、web 场景（2000-2999）
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2000. 首页（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, layout_component, icon, sort_order, visible, remark)
VALUES (2000, 0, '首页', 'web:home', 'MENU', '/', 'web', 'learn/home/index', 'layout/CommonLayout/index',
        'icon-outlined-home', 1, 'Y', '首页');

-- ----------------------------------------------------------------------------
-- 2110. 课程列表（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, layout_component, icon, sort_order, visible, remark)
VALUES (2110, 0, '课程列表', 'web:learn:course:list', 'MENU', '/learn/course', 'web',
        'learn/course/index', 'layout/CommonLayout/index', 'icon-outlined-project', 2, 'Y', '课程列表');

-- 2111-2114. 课程列表按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2111, 2110, '加入课程', 'web:learn:course:join', 'BUTTON', 'web', 1, 'N', '通过课程码加入课程按钮'),
       (2112, 2110, '继续学习', 'web:learn:course:learn', 'BUTTON', 'web', 2, 'N', '继续学习课程按钮'),
       (2113, 2110, '退出课程', 'web:learn:course:leave', 'BUTTON', 'web', 3, 'N', '退出课程按钮'),
       (2114, 2110, '管理课程', 'web:learn:course:manage', 'BUTTON', 'web', 4, 'N', '管理课程按钮（教师）');

-- ----------------------------------------------------------------------------
-- 2115. 课程门户（MENU，不可见）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, layout_component, icon, sort_order, visible, remark)
VALUES (2115, 0, '课程门户', 'web:learn:course:portal', 'MENU', '/learn/course/:courseId/portal', 'web',
        'learn/course/portal/index', 'layout/CommonLayout/index', 'icon-outlined-read', 3, 'N', '课程门户页');

-- ----------------------------------------------------------------------------
-- 2200. 学生学习页（DIR，不可见）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, layout_component, icon, sort_order, visible, remark)
VALUES (2200, 0, '学生学习页', 'web:course:learn', 'DIR', '/course/learn', 'web', NULL,
        'layout/StudentCourseLayout/index', 'icon-outlined-book', 3, 'N', '学生课程学习目录');

-- 2208. 学习首页（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2208, 2200, '学习首页', 'web:course:learn:home', 'MENU', '/course/learn/:courseId', 'web',
        'course/index', 'icon-outlined-home', 0, 'Y', '学生课程学习首页');

-- 2201-2207. AI 对话接口
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2201, 2200, '会话列表', 'admin:education:chat:session:list', 'INTERFACE', 'admin', 1, 'N', '会话列表接口'),
       (2202, 2200, '会话详情', 'admin:education:chat:session:query', 'INTERFACE', 'admin', 2, 'N', '会话详情接口'),
       (2203, 2200, '创建会话', 'admin:education:chat:session:add', 'INTERFACE', 'admin', 3, 'N', '创建会话接口'),
       (2204, 2200, '编辑会话', 'admin:education:chat:session:edit', 'INTERFACE', 'admin', 4, 'N', '编辑会话接口'),
       (2205, 2200, '删除会话', 'admin:education:chat:session:remove', 'INTERFACE', 'admin', 5, 'N', '删除会话接口'),
       (2206, 2200, '发送消息', 'admin:education:chat:message:send', 'INTERFACE', 'admin', 6, 'N', '发送消息接口'),
       (2207, 2200, '消息查询', 'admin:education:chat:message:query', 'INTERFACE', 'admin', 7, 'N', '消息查询接口');

-- 2210. 章节资料（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2210, 2200, '章节资料', 'web:course:learn:chapter', 'MENU', '/course/learn/:courseId/chapter/:chapterId', 'web',
        'course/ChapterResource', 'icon-outlined-file-text', 1, 'Y', '章节学习内容页');

-- 2211-2212. 章节资料查看接口
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2211, 2210, '章节资料列表', 'admin:education:chapter-resource:list', 'INTERFACE', 'admin', 1, 'N', '章节资料列表接口'),
       (2212, 2210, '章节资料详情', 'admin:education:chapter-resource:query', 'INTERFACE', 'admin', 2, 'N', '章节资料详情接口');

-- 2220. 课程知识图谱（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2220, 2200, '课程知识图谱', 'web:course:learn:knowledge-graph', 'MENU', '/course/learn/:courseId/knowledge-graph', 'web',
        'course/CourseKnowledgeGraphPage', 'icon-outlined-apartment', 2, 'Y', '课程知识图谱页');

-- 2221-2223. 知识图谱查看接口
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2221, 2220, '图谱列表', 'admin:education:knowledgeGraph:list', 'INTERFACE', 'admin', 1, 'N', '知识图谱列表接口'),
       (2222, 2220, '图谱详情', 'admin:education:knowledgeGraph:query', 'INTERFACE', 'admin', 2, 'N', '知识图谱详情接口'),
       (2223, 2220, '查看图谱', 'admin:education:knowledgeGraph:view', 'INTERFACE', 'admin', 3, 'N', '查看图谱数据接口');

-- 2230. 学习路径（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2230, 2200, '学习路径', 'web:course:learn:learning-path', 'MENU', '/course/learn/:courseId/learning-path', 'web',
        'course/CourseLearningPathPage', 'icon-outlined-node-index', 3, 'Y', '学习路径页');

-- 2231-2234. 学习路径接口
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2231, 2230, '学习路径列表', 'admin:education:learningPath:list', 'INTERFACE', 'admin', 1, 'N', '学习路径列表接口'),
       (2232, 2230, '学习路径详情', 'admin:education:learningPath:query', 'INTERFACE', 'admin', 2, 'N', '学习路径详情接口'),
       (2233, 2230, '编辑学习路径', 'admin:education:learningPath:edit', 'INTERFACE', 'admin', 3, 'N', '编辑学习路径接口'),
       (2234, 2230, '删除学习路径', 'admin:education:learningPath:remove', 'INTERFACE', 'admin', 4, 'N', '删除学习路径接口');

-- 2240. 习题（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2240, 2200, '习题', 'web:course:learn:exercises', 'MENU', '/course/learn/:courseId/exercises', 'web',
        'course/ExerciseRecord', 'icon-outlined-edit', 4, 'Y', '习题记录页');

-- 2241-2248. 习题相关接口
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2241, 2240, '课程练习列表', 'admin:education:course-exercise:list', 'INTERFACE', 'admin', 1, 'N', '课程练习列表接口'),
       (2242, 2240, '练习详情', 'admin:education:course-exercise:query', 'INTERFACE', 'admin', 2, 'N', '练习详情接口'),
       (2243, 2240, '新增练习', 'admin:education:course-exercise:add', 'INTERFACE', 'admin', 3, 'N', '新增练习接口'),
       (2244, 2240, '编辑练习', 'admin:education:course-exercise:edit', 'INTERFACE', 'admin', 4, 'N', '编辑练习接口'),
       (2245, 2240, '删除练习', 'admin:education:course-exercise:remove', 'INTERFACE', 'admin', 5, 'N', '删除练习接口'),
       (2246, 2240, '作答记录列表', 'admin:education:exercise-attempt:list', 'INTERFACE', 'admin', 6, 'N', '作答记录列表接口'),
       (2247, 2240, '作答详情', 'admin:education:exercise-attempt:query', 'INTERFACE', 'admin', 7, 'N', '作答详情接口'),
       (2248, 2240, '提交作答', 'admin:education:exercise-attempt:add', 'INTERFACE', 'admin', 8, 'N', '提交作答接口');

-- ----------------------------------------------------------------------------
-- 2300. 教师课程页（DIR，不可见）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, layout_component, icon, sort_order, visible, remark)
VALUES (2300, 0, '教师课程页', 'web:course:manage', 'DIR', '/course/manage', 'web', NULL,
        'layout/TeacherCourseLayout/index', 'icon-outlined-video-camera', 4, 'N', '教师课程管理目录');

-- 2310. 课程首页（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2310, 2300, '课程首页', 'web:course:manage:home', 'MENU', '/course/manage/:courseId', 'web',
        'course/manage/index', 'icon-outlined-home', 1, 'Y', '课程首页');

-- 2311. 课程详情接口
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2311, 2310, '课程详情', 'admin:education:course:query', 'INTERFACE', 'admin', 1, 'N', '课程详情查询接口');

-- 2320. 课程门户设置（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2320, 2300, '课程门户设置', 'web:course:manage:portal', 'MENU', '/course/manage/:courseId/portal', 'web',
        'course/manage/PortalManage', 'icon-outlined-global', 2, 'Y', '课程门户设置页');

-- 2330. 章节设置（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2330, 2300, '章节设置', 'web:course:manage:chapter', 'MENU', '/course/manage/:courseId/chapter', 'web',
        'course/manage/ChapterManage', 'icon-outlined-book', 3, 'Y', '章节设置页');

-- 2331. 章节详情接口
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2331, 2330, '章节详情', 'admin:education:chapter:query', 'INTERFACE', 'admin', 1, 'N', '章节详情查询接口');

-- 2340. 课程资源设置（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2340, 2300, '课程资源设置', 'web:course:manage:resource', 'MENU', '/course/manage/:courseId/resource', 'web',
        'course/manage/ResourceManage', 'icon-outlined-folder', 4, 'Y', '课程资源设置页');

-- 2341-2343. 课程资源管理接口
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2341, 2340, '章节资料新增', 'admin:education:chapter-resource:add', 'INTERFACE', 'admin', 1, 'N', '章节资料新增接口'),
       (2342, 2340, '章节资料编辑', 'admin:education:chapter-resource:edit', 'INTERFACE', 'admin', 2, 'N', '章节资料编辑接口'),
       (2343, 2340, '章节资料删除', 'admin:education:chapter-resource:remove', 'INTERFACE', 'admin', 3, 'N', '章节资料删除接口');

-- 2350. 课程知识图谱管理（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2350, 2300, '课程知识图谱管理', 'web:course:manage:knowledge-graph', 'MENU', '/course/manage/:courseId/knowledge-graph', 'web',
        'course/manage/KnowledgePointManage', 'icon-outlined-share-alt', 5, 'Y', '课程知识图谱管理页');

-- 2351-2354. 知识图谱管理接口
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2351, 2350, '创建图谱', 'admin:education:knowledgeGraph:add', 'INTERFACE', 'admin', 1, 'N', '创建知识图谱接口'),
       (2352, 2350, '编辑图谱', 'admin:education:knowledgeGraph:edit', 'INTERFACE', 'admin', 2, 'N', '编辑知识图谱接口'),
       (2353, 2350, '删除图谱', 'admin:education:knowledgeGraph:remove', 'INTERFACE', 'admin', 3, 'N', '删除知识图谱接口'),
       (2354, 2350, '提取节点', 'admin:education:knowledgeGraph:extract', 'INTERFACE', 'admin', 4, 'N', '提取知识节点接口');

-- 2360. AI问答知识图谱管理（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2360, 2300, 'AI问答知识图谱管理', 'web:course:manage:semantic-graph', 'MENU', '/course/manage/:courseId/semantic-graph', 'web',
        'course/manage/SemanticGraphManage', 'icon-outlined-robot', 6, 'Y', 'AI问答知识图谱管理页');

-- 2361-2365. GraphRAG任务接口
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2361, 2360, '任务列表', 'admin:education:graphrag-task:list', 'INTERFACE', 'admin', 1, 'N', 'GraphRAG任务列表接口'),
       (2362, 2360, '任务详情', 'admin:education:graphrag-task:query', 'INTERFACE', 'admin', 2, 'N', 'GraphRAG任务详情接口'),
       (2363, 2360, '创建任务', 'admin:education:graphrag-task:add', 'INTERFACE', 'admin', 3, 'N', '创建GraphRAG任务接口'),
       (2364, 2360, '编辑任务', 'admin:education:graphrag-task:edit', 'INTERFACE', 'admin', 4, 'N', '编辑GraphRAG任务接口'),
       (2365, 2360, '删除任务', 'admin:education:graphrag-task:remove', 'INTERFACE', 'admin', 5, 'N', '删除GraphRAG任务接口');

-- 2370. 学生管理（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (2370, 2300, '学生管理', 'web:course:manage:student', 'MENU', '/course/manage/:courseId/student', 'web',
        'course/manage/StudentManage', 'icon-outlined-team', 7, 'Y', '学生管理页');

-- 2371-2374. 学生管理接口
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (2371, 2370, '学生选课列表', 'admin:education:student:course:list', 'INTERFACE', 'admin', 1, 'N', '学生选课列表接口'),
       (2372, 2370, '选课详情', 'admin:education:student:course:query', 'INTERFACE', 'admin', 2, 'N', '选课详情接口'),
       (2373, 2370, '分配课程', 'admin:education:student:course:assign', 'INTERFACE', 'admin', 3, 'N', '分配课程接口'),
       (2374, 2370, '撤销选课', 'admin:education:student:course:revoke', 'INTERFACE', 'admin', 4, 'N', '撤销选课接口');


-- ============================================================================
-- 二、userInfo 场景（3000-3999）
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3000. 个人中心（DIR）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, layout_component, icon, sort_order, visible, remark)
VALUES (3000, 0, '个人中心', 'user:profile', 'DIR', '/profile', 'userInfo', 'profile/index',
        'layout/CommonLayout/index', 'icon-outlined-user', 1, 'Y', '个人中心目录');

-- 3100. 个人信息（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (3100, 3000, '个人信息', 'user:profile:info', 'MENU', '/profile/info', 'userInfo',
        'profile/info/index', 'icon-outlined-idcard', 1, 'Y', '个人信息');

-- 3300. 账号设置（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (3300, 3000, '账号设置', 'user:profile:settings', 'MENU', '/profile/settings', 'userInfo',
        'profile/settings/index', 'icon-outlined-setting', 4, 'Y', '账号设置');

-- 3400. 账号安全（MENU）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (3400, 3000, '账号安全', 'user:profile:security', 'MENU', '/profile/security', 'userInfo',
        'profile/security/index', 'icon-outlined-safety', 3, 'Y', '账号安全');


-- ============================================================================
-- 三、admin 场景（900-999, 1000-1999, 5000-5999）
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 900. 管理首页（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, layout_component, icon, sort_order, visible, remark)
VALUES (900, 0, '管理首页', 'admin:dashboard', 'MENU', '/admin', 'admin',
        'admin/index', 'layout/WorkbenchLayout/index', 'icon-outlined-dashboard', 0, 'Y', '管理后台首页仪表盘');

-- ============================================================================
-- 1000. 系统管理（DIR）
-- ============================================================================
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, layout_component, icon, sort_order, visible, remark)
VALUES (1000, 0, '系统管理', 'admin:system', 'DIR', '/admin/system', 'admin', NULL,
        'layout/WorkbenchLayout/index', 'icon-outlined-setting', 1, 'Y', '系统管理目录');

-- ----------------------------------------------------------------------------
-- 1100. 用户管理（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (1100, 1000, '用户管理', 'admin:system:user', 'MENU', '/admin/system/user', 'admin',
        'admin/system/user/index', 'icon-outlined-user', 1, 'Y', '用户管理页面');

-- 1110-1160. 用户管理按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (1110, 1100, '用户查询', 'admin:system:user:list', 'BUTTON', 'admin', 1, 'N', '用户查询按钮'),
       (1120, 1100, '用户新增', 'admin:system:user:add', 'BUTTON', 'admin', 2, 'N', '用户新增按钮'),
       (1130, 1100, '用户修改', 'admin:system:user:edit', 'BUTTON', 'admin', 3, 'N', '用户修改按钮'),
       (1140, 1100, '用户删除', 'admin:system:user:remove', 'BUTTON', 'admin', 4, 'N', '用户删除按钮'),
       (1150, 1100, '用户导出', 'admin:system:user:export', 'BUTTON', 'admin', 5, 'N', '用户导出按钮'),
       (1160, 1100, '重置密码', 'admin:system:user:resetPwd', 'BUTTON', 'admin', 6, 'N', '重置密码按钮');

-- ----------------------------------------------------------------------------
-- 1200. 角色管理（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (1200, 1000, '角色管理', 'admin:system:role', 'MENU', '/admin/system/role', 'admin',
        'admin/system/role/index', 'icon-outlined-team', 2, 'Y', '角色管理页面');

-- 1210-1250. 角色管理按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (1210, 1200, '角色查询', 'admin:system:role:list', 'BUTTON', 'admin', 1, 'N', '角色查询按钮'),
       (1220, 1200, '角色新增', 'admin:system:role:add', 'BUTTON', 'admin', 2, 'N', '角色新增按钮'),
       (1230, 1200, '角色修改', 'admin:system:role:edit', 'BUTTON', 'admin', 3, 'N', '角色修改按钮'),
       (1240, 1200, '角色删除', 'admin:system:role:remove', 'BUTTON', 'admin', 4, 'N', '角色删除按钮'),
       (1250, 1200, '分配权限', 'admin:system:role:assign', 'BUTTON', 'admin', 5, 'N', '分配权限按钮');

-- ----------------------------------------------------------------------------
-- 1300. 菜单管理（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (1300, 1000, '菜单管理', 'admin:system:function', 'MENU', '/admin/system/function', 'admin',
        'admin/system/function/index', 'icon-outlined-menu', 3, 'Y', '菜单管理页面');

-- 1310-1340. 菜单管理按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (1310, 1300, '菜单查询', 'admin:system:function:list', 'BUTTON', 'admin', 1, 'N', '菜单查询按钮'),
       (1320, 1300, '菜单新增', 'admin:system:function:add', 'BUTTON', 'admin', 2, 'N', '菜单新增按钮'),
       (1330, 1300, '菜单修改', 'admin:system:function:edit', 'BUTTON', 'admin', 3, 'N', '菜单修改按钮'),
       (1340, 1300, '菜单删除', 'admin:system:function:remove', 'BUTTON', 'admin', 4, 'N', '菜单删除按钮');

-- ----------------------------------------------------------------------------
-- 1400. 部门管理（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (1400, 1000, '部门管理', 'admin:system:dept', 'MENU', '/admin/system/dept', 'admin',
        'admin/system/dept/index', 'icon-outlined-apartment', 4, 'Y', '部门管理页面');

-- 1410-1470. 部门管理按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (1410, 1400, '部门查询', 'admin:system:dept:list', 'BUTTON', 'admin', 1, 'N', '部门查询按钮'),
       (1420, 1400, '部门新增', 'admin:system:dept:add', 'BUTTON', 'admin', 2, 'N', '部门新增按钮'),
       (1430, 1400, '部门修改', 'admin:system:dept:edit', 'BUTTON', 'admin', 3, 'N', '部门修改按钮'),
       (1440, 1400, '部门删除', 'admin:system:dept:remove', 'BUTTON', 'admin', 4, 'N', '部门删除按钮'),
       (1450, 1400, '导出部门', 'admin:system:dept:export', 'BUTTON', 'admin', 5, 'N', '导出部门按钮'),
       (1460, 1400, '展开/折叠', 'admin:system:dept:expand', 'BUTTON', 'admin', 6, 'N', '展开/折叠按钮'),
       (1470, 1400, '查看用户', 'admin:system:dept:viewUsers', 'BUTTON', 'admin', 7, 'N', '查看用户按钮');

-- ----------------------------------------------------------------------------
-- 1500. 字典管理（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (1500, 1000, '字典管理', 'admin:system:dict', 'MENU', '/admin/system/dict', 'admin',
        'admin/system/dict/index', 'icon-outlined-book', 5, 'Y', '字典管理页面');

-- 1510-1590. 字典管理按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (1510, 1500, '字典查询', 'admin:system:dict:list', 'BUTTON', 'admin', 1, 'N', '字典查询按钮'),
       (1520, 1500, '字典新增', 'admin:system:dict:add', 'BUTTON', 'admin', 2, 'N', '字典新增按钮'),
       (1530, 1500, '字典修改', 'admin:system:dict:edit', 'BUTTON', 'admin', 3, 'N', '字典修改按钮'),
       (1540, 1500, '字典删除', 'admin:system:dict:remove', 'BUTTON', 'admin', 4, 'N', '字典删除按钮'),
       (1550, 1500, '字典导出', 'admin:system:dict:export', 'BUTTON', 'admin', 5, 'N', '字典导出按钮'),
       (1560, 1500, '刷新缓存', 'admin:system:dict:refresh', 'BUTTON', 'admin', 6, 'N', '刷新缓存按钮'),
       (1570, 1500, '字典数据查询', 'admin:system:dict:data:list', 'BUTTON', 'admin', 7, 'N', '字典数据查询按钮'),
       (1580, 1500, '字典数据新增', 'admin:system:dict:data:add', 'BUTTON', 'admin', 8, 'N', '字典数据新增按钮'),
       (1590, 1500, '字典数据修改', 'admin:system:dict:data:edit', 'BUTTON', 'admin', 9, 'N', '字典数据修改按钮');

-- ----------------------------------------------------------------------------
-- 1600. 操作日志（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (1600, 1000, '操作日志', 'admin:monitor:log:operation', 'MENU', '/admin/system/monitor/log/operation', 'admin',
        'admin/system/log/operation', 'icon-outlined-file-text', 6, 'Y', '操作日志页面');

-- 1610-1640. 操作日志按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (1610, 1600, '操作日志查询', 'admin:monitor:log:operation:list', 'BUTTON', 'admin', 1, 'N', '操作日志查询按钮'),
       (1620, 1600, '删除操作日志', 'admin:monitor:log:operation:remove', 'BUTTON', 'admin', 2, 'N', '删除操作日志按钮'),
       (1630, 1600, '清空操作日志', 'admin:monitor:log:operation:clean', 'BUTTON', 'admin', 3, 'N', '清空操作日志按钮'),
       (1640, 1600, '导出操作日志', 'admin:monitor:log:operation:export', 'BUTTON', 'admin', 4, 'N', '导出操作日志按钮');

-- ----------------------------------------------------------------------------
-- 1700. 登录日志（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (1700, 1000, '登录日志', 'admin:monitor:log:login', 'MENU', '/admin/system/monitor/log/login', 'admin',
        'admin/system/log/login', 'icon-outlined-login', 7, 'Y', '登录日志页面');

-- 1710-1740. 登录日志按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (1710, 1700, '登录日志查询', 'admin:monitor:log:login:list', 'BUTTON', 'admin', 1, 'N', '登录日志查询按钮'),
       (1720, 1700, '删除登录日志', 'admin:monitor:log:login:remove', 'BUTTON', 'admin', 2, 'N', '删除登录日志按钮'),
       (1730, 1700, '清空登录日志', 'admin:monitor:log:login:clean', 'BUTTON', 'admin', 3, 'N', '清空登录日志按钮'),
       (1740, 1700, '解锁用户', 'admin:monitor:log:login:unlock', 'BUTTON', 'admin', 4, 'N', '解锁用户按钮');

-- ----------------------------------------------------------------------------
-- 1800. 代码生成（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (1800, 1000, '代码生成', 'admin:system:tool:gen', 'MENU', '/admin/system/tool/gen', 'admin',
        'admin/system/tool/gen/index', 'icon-outlined-code', 9, 'Y', '代码生成工具');

-- 1810-1870. 代码生成按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (1810, 1800, '查询', 'admin:system:tool:gen:list', 'BUTTON', 'admin', 1, 'N', '查询按钮'),
       (1820, 1800, '导入', 'admin:system:tool:gen:import', 'BUTTON', 'admin', 2, 'N', '导入按钮'),
       (1830, 1800, '修改', 'admin:system:tool:gen:edit', 'BUTTON', 'admin', 3, 'N', '修改按钮'),
       (1840, 1800, '删除', 'admin:system:tool:gen:remove', 'BUTTON', 'admin', 4, 'N', '删除按钮'),
       (1850, 1800, '预览', 'admin:system:tool:gen:preview', 'BUTTON', 'admin', 5, 'N', '预览按钮'),
       (1860, 1800, '生成', 'admin:system:tool:gen:generate', 'BUTTON', 'admin', 6, 'N', '生成按钮'),
       (1870, 1800, '同步', 'admin:system:tool:gen:sync', 'BUTTON', 'admin', 7, 'N', '同步按钮');

-- ----------------------------------------------------------------------------
-- 1900. 定时任务（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (1900, 1000, '定时任务', 'admin:system:job', 'MENU', '/admin/system/job', 'admin',
        'admin/system/job/index', 'icon-outlined-schedule', 8, 'Y', '定时任务管理页面');

-- 1910. 定时任务按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (1910, 1900, '查询', 'admin:system:job:list', 'BUTTON', 'admin', 1, 'N', '查询按钮');

-- ============================================================================
-- 5000. 教学管理（DIR）
-- ============================================================================
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, layout_component, icon, sort_order, visible, remark)
VALUES (5000, 0, '教学管理', 'admin:education', 'DIR', '/admin/education', 'admin', NULL,
        'layout/WorkbenchLayout/index', 'icon-outlined-video-camera', 2, 'Y', '教学管理目录');

-- ----------------------------------------------------------------------------
-- 5100. 课程管理（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (5100, 5000, '课程管理', 'admin:education:course', 'MENU', '/admin/education/course', 'admin',
        'admin/education/course/index', 'icon-outlined-video-camera', 1, 'Y', '课程管理页面');

-- 5110-5190. 课程管理按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (5110, 5100, '课程查询', 'admin:education:course:list', 'BUTTON', 'admin', 1, 'N', '课程查询按钮'),
       (5120, 5100, '课程新增', 'admin:education:course:add', 'BUTTON', 'admin', 2, 'N', '课程新增按钮'),
       (5130, 5100, '课程修改', 'admin:education:course:edit', 'BUTTON', 'admin', 3, 'N', '课程修改按钮'),
       (5140, 5100, '课程删除', 'admin:education:course:remove', 'BUTTON', 'admin', 4, 'N', '课程删除按钮'),
       (5150, 5100, '课程发布', 'admin:education:course:publish', 'BUTTON', 'admin', 5, 'N', '课程发布按钮'),
       (5160, 5100, '课程章节管理', 'admin:education:course:chapter', 'BUTTON', 'admin', 6, 'N', '课程章节管理按钮'),
       (5170, 5100, '课程知识点知识图谱管理', 'admin:education:course:knowledge:graph', 'BUTTON', 'admin', 7, 'N', '课程知识点知识图谱管理按钮'),
       (5180, 5100, '课程语义图谱管理', 'admin:education:course:semantic:graph', 'BUTTON', 'admin', 8, 'N', '课程语义图谱管理按钮'),
       (5190, 5100, '课程资源管理', 'admin:education:course:resource', 'BUTTON', 'admin', 9, 'N', '课程资源管理按钮');

-- 5161-5165. 课程章节管理子按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (5161, 5160, '章节查询', 'admin:education:chapter:list', 'BUTTON', 'admin', 1, 'N', '章节查询按钮'),
       (5162, 5160, '章节新增', 'admin:education:chapter:add', 'BUTTON', 'admin', 2, 'N', '章节新增按钮'),
       (5163, 5160, '章节修改', 'admin:education:chapter:edit', 'BUTTON', 'admin', 3, 'N', '章节修改按钮'),
       (5164, 5160, '章节删除', 'admin:education:chapter:remove', 'BUTTON', 'admin', 4, 'N', '章节删除按钮'),
       (5165, 5160, '章节排序', 'admin:education:chapter:sort', 'BUTTON', 'admin', 5, 'N', '章节排序按钮');

-- 5171-5174. 课程知识点知识图谱管理子按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (5171, 5170, '节点查询', 'admin:education:knowledge:node:list', 'BUTTON', 'admin', 1, 'N', '节点查询按钮'),
       (5172, 5170, '节点新增', 'admin:education:knowledge:node:add', 'BUTTON', 'admin', 2, 'N', '节点新增按钮'),
       (5173, 5170, '节点修改', 'admin:education:knowledge:node:edit', 'BUTTON', 'admin', 3, 'N', '节点修改按钮'),
       (5174, 5170, '节点删除', 'admin:education:knowledge:node:remove', 'BUTTON', 'admin', 4, 'N', '节点删除按钮');

-- 5181-5187. 课程语义图谱管理子按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (5181, 5180, '资料增补、更新图谱', 'admin:education:semantic:graph:edit', 'BUTTON', 'admin', 1, 'N', '资料增补、更新图谱按钮'),
       (5182, 5180, '构建图谱', 'admin:education:semantic:graph:build', 'BUTTON', 'admin', 2, 'N', '构建图谱按钮'),
       (5183, 5180, '创建图谱', 'admin:education:semantic:graph:add', 'BUTTON', 'admin', 3, 'N', '创建图谱按钮'),
       (5184, 5180, '查看图谱', 'admin:education:semantic:graph:view', 'BUTTON', 'admin', 4, 'N', '查看图谱按钮'),
       (5185, 5180, '修改图谱状态', 'admin:education:semantic:graph:editStatus', 'BUTTON', 'admin', 5, 'N', '修改图谱状态按钮'),
       (5186, 5180, '查询图谱状态', 'admin:education:semantic:graph:query', 'BUTTON', 'admin', 6, 'N', '查询图谱状态按钮'),
       (5187, 5180, '删除图谱', 'admin:education:semantic:graph:remove', 'BUTTON', 'admin', 7, 'N', '删除图谱按钮');

-- ----------------------------------------------------------------------------
-- 5200. 教师管理（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (5200, 5000, '教师管理', 'admin:education:teacher', 'MENU', '/admin/education/teacher', 'admin',
        'admin/education/teacher/index', 'icon-outlined-user', 2, 'Y', '教师管理页面');

-- 5210-5250. 教师管理按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (5210, 5200, '教师查询', 'admin:education:teacher:list', 'BUTTON', 'admin', 1, 'N', '教师查询按钮'),
       (5220, 5200, '教师新增', 'admin:education:teacher:add', 'BUTTON', 'admin', 2, 'N', '教师新增按钮'),
       (5230, 5200, '教师修改', 'admin:education:teacher:edit', 'BUTTON', 'admin', 3, 'N', '教师修改按钮'),
       (5240, 5200, '教师删除', 'admin:education:teacher:remove', 'BUTTON', 'admin', 4, 'N', '教师删除按钮'),
       (5250, 5200, '重置密码', 'admin:education:teacher:resetPwd', 'BUTTON', 'admin', 5, 'N', '重置密码按钮');

-- 5251. 教师详情接口（区别于 5210 的列表查询）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (5251, 5200, '教师详情', 'admin:education:teacher:query', 'INTERFACE', 'admin', 6, 'N', '教师详情查询接口');

-- ----------------------------------------------------------------------------
-- 5300. 学生管理（MENU）
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, route_path, scene,
                          component, icon, sort_order, visible, remark)
VALUES (5300, 5000, '学生管理', 'admin:education:student', 'MENU', '/admin/education/student', 'admin',
        'admin/education/student/index', 'icon-outlined-team', 3, 'Y', '学生管理页面');

-- 5310-5350. 学生管理按钮权限
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (5310, 5300, '学生查询', 'admin:education:student:list', 'BUTTON', 'admin', 1, 'N', '学生查询按钮'),
       (5320, 5300, '学生新增', 'admin:education:student:add', 'BUTTON', 'admin', 2, 'N', '学生新增按钮'),
       (5330, 5300, '学生修改', 'admin:education:student:edit', 'BUTTON', 'admin', 3, 'N', '学生修改按钮'),
       (5340, 5300, '学生删除', 'admin:education:student:remove', 'BUTTON', 'admin', 4, 'N', '学生删除按钮'),
       (5350, 5300, '重置密码', 'admin:education:student:resetPwd', 'BUTTON', 'admin', 5, 'N', '重置密码按钮');

-- 5351. 学生详情接口（区别于 5310 的列表查询）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (5351, 5300, '学生详情', 'admin:education:student:query', 'INTERFACE', 'admin', 6, 'N', '学生详情查询接口');

-- ============================================================================
-- 四、新增缺失的 INTERFACE 权限条目（6000-6999）
-- ============================================================================
-- 这些条目不在菜单中显示，仅用于 API 接口权限校验
-- 教育模块的 INTERFACE 已内联到 web 场景对应的 MENU 下方（2201-2374）

-- ----------------------------------------------------------------------------
-- 6000-6060. 系统通用权限
-- ----------------------------------------------------------------------------

-- 用户详情查询（区别于 1110 的列表查询）
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (6000, 1100, '用户详情', 'admin:system:user:query', 'INTERFACE', 'admin', 10, 'N', '用户详情查询接口');

-- 异步任务管理
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (6010, 1000, '异步任务管理', 'admin:system:asyncTask', 'INTERFACE', 'admin', 20, 'N', '异步任务管理接口组'),
       (6011, 6010, '异步任务列表', 'admin:system:asyncTask:list', 'INTERFACE', 'admin', 1, 'N', '异步任务列表接口'),
       (6012, 6010, '异步任务详情', 'admin:system:asyncTask:query', 'INTERFACE', 'admin', 2, 'N', '异步任务详情接口'),
       (6013, 6010, '异步任务编辑', 'admin:system:asyncTask:edit', 'INTERFACE', 'admin', 3, 'N', '异步任务编辑接口');

-- 文件上传下载
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES (6040, 0, '文件上传', 'admin:common:upload:upload', 'INTERFACE', 'admin', 1, 'N', '文件上传接口'),
       (6050, 0, '文件下载', 'admin:common:upload:download', 'INTERFACE', 'admin', 2, 'N', '文件下载接口'),
       (6060, 0, '文件查询', 'admin:common:upload:query', 'INTERFACE', 'admin', 3, 'N', '文件查询接口');

-- ----------------------------------------------------------------------------
-- 6100-6130. 系统管理 — 详情查询接口
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES
(6100, 1200, '角色详情', 'admin:system:role:query', 'INTERFACE', 'admin', 10, 'N', '角色详情查询接口'),
(6110, 1300, '菜单详情', 'admin:system:function:query', 'INTERFACE', 'admin', 10, 'N', '菜单详情查询接口'),
(6120, 1400, '部门详情', 'admin:system:dept:query', 'INTERFACE', 'admin', 10, 'N', '部门详情查询接口'),
(6130, 1500, '字典详情', 'admin:system:dict:query', 'INTERFACE', 'admin', 10, 'N', '字典详情查询接口'),
(6140, 1600, '操作日志详情', 'admin:monitor:log:operation:query', 'INTERFACE', 'admin', 10, 'N', '操作日志详情查询接口');

-- ----------------------------------------------------------------------------
-- 6200-6230. 定时任务 — 完整 CRUD + 执行/状态/日志
-- ----------------------------------------------------------------------------
INSERT INTO sys_function (function_id, parent_id, function_name, function_key, function_type, scene, sort_order,
                          visible, remark)
VALUES
(6200, 1900, '任务详情', 'admin:system:job:query', 'INTERFACE', 'admin', 2, 'N', '定时任务详情接口'),
(6210, 1900, '任务新增', 'admin:system:job:add', 'INTERFACE', 'admin', 3, 'N', '定时任务新增接口'),
(6220, 1900, '任务编辑', 'admin:system:job:edit', 'INTERFACE', 'admin', 4, 'N', '定时任务编辑接口'),
(6230, 1900, '任务删除', 'admin:system:job:remove', 'INTERFACE', 'admin', 5, 'N', '定时任务删除接口'),
(6240, 1900, '任务状态变更', 'admin:system:job:changeStatus', 'INTERFACE', 'admin', 6, 'N', '定时任务状态变更接口'),
(6250, 1900, '立即执行', 'admin:system:job:execute', 'INTERFACE', 'admin', 7, 'N', '定时任务立即执行接口'),
(6260, 1900, '任务日志查询', 'admin:system:job:log:query', 'INTERFACE', 'admin', 8, 'N', '定时任务日志查询接口'),
(6270, 1900, '任务日志删除', 'admin:system:job:log:remove', 'INTERFACE', 'admin', 9, 'N', '定时任务日志删除接口');

-- ============================================================================
-- 五、序列起始值设置
-- ============================================================================
-- 更新序列起始值，用户从 10000 开始（包括 10000）新增功能权限数据，避免与预设数据冲突
SELECT setval('sys_function_function_id_seq', 10000, false);

-- ============================================================================
-- 六、角色-功能权限分配
-- ============================================================================
-- 注意：此部分必须在 sys_function 数据填充后执行，因此放在本文件末尾
-- 角色数据已在 2.4system_data.sql 中初始化

-- 清空角色-功能权限表
TRUNCATE TABLE sys_role_function;

-- 1. 为超级管理员角色（role_id=1）分配所有功能权限
INSERT INTO sys_role_function (role_id, function_id)
SELECT 1, function_id
FROM sys_function
WHERE status = '0';

-- 2. 为教师角色（role_id=11）分配权限
-- web 场景：学习中心（体验学生视角）
-- admin 场景：教学管理全部模块（课程、章节、资料、图谱、练习、对话、任务、路径）+ 文件上传
INSERT INTO sys_role_function (role_id, function_id)
SELECT 11, function_id
FROM sys_function
WHERE status = '0'
  AND (
    scene = 'web'
    OR function_key LIKE 'admin:education:%'
    OR function_key LIKE 'admin:common:%'
  );

-- 3. 为学生角色（role_id=12）分配权限
-- web 场景 + userInfo 场景 + 学习相关 INTERFACE 权限 + 文件上传下载
INSERT INTO sys_role_function (role_id, function_id)
SELECT 12, function_id
FROM sys_function
WHERE status = '0'
  AND (
    -- web 场景菜单（排除教师课程管理 2300 及其子菜单、管理课程按钮 2114）
    (scene = 'web' AND function_id != 2300 AND parent_id != 2300 AND function_id != 2114)
    -- userInfo 场景菜单（个人中心）
    OR scene = 'userInfo'
    -- 文件上传下载
    OR function_key IN (
        'admin:common:upload:upload',
        'admin:common:upload:download',
        'admin:common:upload:query'
    )
    -- 课程浏览
    OR function_key IN (
        'admin:education:course:list',
        'admin:education:course:query'
    )
    -- 章节浏览
    OR function_key IN (
        'admin:education:chapter:list',
        'admin:education:chapter:query'
    )
    -- 章节资料浏览
    OR function_key IN (
        'admin:education:chapter-resource:list',
        'admin:education:chapter-resource:query'
    )
    -- 学生选课
    OR function_key IN (
        'admin:education:student:course:list',
        'admin:education:student:course:query',
        'admin:education:student:course:assign',
        'admin:education:student:course:revoke'
    )
    -- 课程练习（只读）
    OR function_key IN (
        'admin:education:course-exercise:list',
        'admin:education:course-exercise:query'
    )
    -- 习题作答
    OR function_key IN (
        'admin:education:exercise-attempt:list',
        'admin:education:exercise-attempt:query',
        'admin:education:exercise-attempt:add'
    )
    -- AI 对话
    OR function_key IN (
        'admin:education:chat:session:list',
        'admin:education:chat:session:query',
        'admin:education:chat:session:add',
        'admin:education:chat:session:edit',
        'admin:education:chat:session:remove',
        'admin:education:chat:message:send',
        'admin:education:chat:message:query'
    )
    -- 知识图谱（只读）
    OR function_key IN (
        'admin:education:knowledgeGraph:list',
        'admin:education:knowledgeGraph:query',
        'admin:education:knowledgeGraph:view'
    )
    -- 学习路径（只读）
    OR function_key IN (
        'admin:education:learningPath:list',
        'admin:education:learningPath:query'
    )
  );

-- ============================================================================
-- 七、验证角色权限数据
-- ============================================================================

-- 查看各角色的权限数量
SELECT r.role_id,
       r.role_key,
       r.role_name,
       COUNT(rf.function_id) as function_count
FROM sys_role r
         LEFT JOIN sys_role_function rf ON r.role_id = rf.role_id
GROUP BY r.role_id, r.role_key, r.role_name
ORDER BY r.role_id;

-- 查看各角色的权限分布（按场景）
SELECT r.role_name,
       f.scene,
       COUNT(*) as function_count
FROM sys_role_function rf
         JOIN sys_role r ON rf.role_id = r.role_id
         JOIN sys_function f ON rf.function_id = f.function_id
WHERE f.status = '0'
GROUP BY r.role_name, f.scene
ORDER BY r.role_name, f.scene;

-- 查看学生角色的具体权限列表
SELECT f.function_key, f.function_name, f.function_type, f.scene
FROM sys_role_function rf
         JOIN sys_function f ON rf.function_id = f.function_id
WHERE rf.role_id = 12
  AND f.status = '0'
ORDER BY f.scene, f.function_key;