-- ============================================================================
-- GraphEdu 批量学生数据初始化脚本
-- ============================================================================
-- 说明：创建 40 名学生用户，均选修离散数学（course_id=1）
--   - 密码统一为 student123（与 student001 相同的 bcrypt hash）
--   - 涵盖计算机学院、数学系、物理系、化学系
--   - 学习进度随机分布，选课时间分散在过去 30 天内
-- 注意：执行前请确保已执行 2.4system_data.sql、3.1education.sql、5.user.sql
-- ============================================================================


-- ============================================================================
-- 0. 使用临时表存储学生基础数据
-- ============================================================================
CREATE TEMP TABLE tmp_students (
    user_name       VARCHAR(32),
    nick_name       VARCHAR(32),
    email           VARCHAR(64),
    phonenumber     VARCHAR(16),
    real_name       VARCHAR(64),
    student_no      VARCHAR(32),
    faculty         VARCHAR(64),
    major           VARCHAR(64),
    grade           VARCHAR(20),
    class_name      VARCHAR(64),
    gender          SMALLINT,
    age             INTEGER,
    dept_key        VARCHAR(64),
    enroll_offset   INTEGER,   -- 选课距今天数
    progress        INTEGER    -- 学习进度 0-100
);


-- ============================================================================
-- 1. 插入学生数据（40 名）
-- ============================================================================

-- ---------- 计算机学院（25 名）----------
INSERT INTO tmp_students VALUES
-- 计算机科学与技术 2023 级
('student002', '王芳', 'wangfang@stu.edu.cn',  '13800138002', '王芳', '2023001002', '计算机学院', '计算机科学与技术', '2023', '1班', 2, 20, 'CS_DEPT', 28, 35),
('student003', '李伟', 'liwei@stu.edu.cn',      '13800138003', '李伟', '2023001003', '计算机学院', '计算机科学与技术', '2023', '1班', 1, 21, 'CS_DEPT', 27, 42),
('student004', '刘洋', 'liuyang@stu.edu.cn',    '13800138004', '刘洋', '2023001004', '计算机学院', '计算机科学与技术', '2023', '2班', 2, 20, 'CS_DEPT', 25, 18),
('student005', '陈静', 'chenjing@stu.edu.cn',   '13800138005', '陈静', '2023001005', '计算机学院', '计算机科学与技术', '2023', '2班', 2, 21, 'CS_DEPT', 23, 55),
-- 软件工程 2023 级
('student006', '杨帆', 'yangfan@stu.edu.cn',    '13800138006', '杨帆', '2023002001', '计算机学院', '软件工程',         '2023', '1班', 1, 22, 'CS_DEPT', 22, 30),
('student007', '赵雪', 'zhaoxue@stu.edu.cn',    '13800138007', '赵雪', '2023002002', '计算机学院', '软件工程',         '2023', '1班', 2, 20, 'CS_DEPT', 20, 48),
('student008', '周磊', 'zhoulei@stu.edu.cn',    '13800138008', '周磊', '2023002003', '计算机学院', '软件工程',         '2023', '2班', 1, 21, 'CS_DEPT', 19, 12),
('student009', '吴敏', 'wumin@stu.edu.cn',      '13800138009', '吴敏', '2023002004', '计算机学院', '软件工程',         '2023', '2班', 2, 20, 'CS_DEPT', 18, 38),
-- 人工智能 2023 级
('student010', '孙浩', 'sunhao@stu.edu.cn',     '13800138010', '孙浩', '2023003001', '计算机学院', '人工智能',         '2023', '1班', 1, 21, 'CS_DEPT', 17, 52),
('student011', '朱丽', 'zhuli@stu.edu.cn',      '13800138011', '朱丽', '2023003002', '计算机学院', '人工智能',         '2023', '1班', 2, 20, 'CS_DEPT', 15, 22),
('student012', '马超', 'machao@stu.edu.cn',     '13800138012', '马超', '2023003003', '计算机学院', '人工智能',         '2023', '1班', 1, 22, 'CS_DEPT', 14, 60),
-- 信息安全 2023 级
('student013', '黄鹏', 'huangpeng@stu.edu.cn',  '13800138013', '黄鹏', '2023004001', '计算机学院', '信息安全',         '2023', '1班', 1, 21, 'CS_DEPT', 12, 28),
('student014', '林婷', 'linting@stu.edu.cn',    '13800138014', '林婷', '2023004002', '计算机学院', '信息安全',         '2023', '1班', 2, 20, 'CS_DEPT', 10, 45),
-- 计算机科学与技术 2024 级
('student015', '徐凯', 'xukai@stu.edu.cn',      '13800138015', '徐凯', '2024001001', '计算机学院', '计算机科学与技术', '2024', '1班', 1, 19, 'CS_DEPT', 9,  20),
('student016', '何琳', 'helin@stu.edu.cn',      '13800138016', '何琳', '2024001002', '计算机学院', '计算机科学与技术', '2024', '1班', 2, 19, 'CS_DEPT', 8,  15),
('student017', '高明', 'gaoming@stu.edu.cn',    '13800138017', '高明', '2024001003', '计算机学院', '计算机科学与技术', '2024', '2班', 1, 20, 'CS_DEPT', 7,  32),
('student018', '郑宇', 'zhengyu@stu.edu.cn',    '13800138018', '郑宇', '2024001004', '计算机学院', '计算机科学与技术', '2024', '2班', 1, 19, 'CS_DEPT', 6,  8),
-- 软件工程 2024 级
('student019', '谢瑶', 'xieyao@stu.edu.cn',    '13800138019', '谢瑶', '2024002001', '计算机学院', '软件工程',         '2024', '1班', 2, 19, 'CS_DEPT', 5,  25),
('student020', '韩冰', 'hanbing@stu.edu.cn',    '13800138020', '韩冰', '2024002002', '计算机学院', '软件工程',         '2024', '1班', 1, 20, 'CS_DEPT', 4,  40),
-- 人工智能 2024 级
('student021', '唐杰', 'tangjie@stu.edu.cn',    '13800138021', '唐杰', '2024003001', '计算机学院', '人工智能',         '2024', '1班', 1, 19, 'CS_DEPT', 3,  10),
('student022', '董欣', 'dongxin@stu.edu.cn',    '13800138022', '董欣', '2024003002', '计算机学院', '人工智能',         '2024', '1班', 2, 20, 'CS_DEPT', 3,  18),
('student023', '萧然', 'xiaoran@stu.edu.cn',    '13800138023', '萧然', '2024003003', '计算机学院', '人工智能',         '2024', '1班', 1, 19, 'CS_DEPT', 2,  5),
-- 信息安全 2024 级
('student024', '彭辉', 'penghui@stu.edu.cn',    '13800138024', '彭辉', '2024004001', '计算机学院', '信息安全',         '2024', '1班', 1, 20, 'CS_DEPT', 2,  30),
('student025', '潘晓', 'panxiao@stu.edu.cn',    '13800138025', '潘晓', '2024004002', '计算机学院', '信息安全',         '2024', '1班', 2, 19, 'CS_DEPT', 1,  12),
-- 计算机科学与技术 2024 级 3 班
('student026', '范毅', 'fanyi@stu.edu.cn',      '13800138026', '范毅', '2024001005', '计算机学院', '计算机科学与技术', '2024', '3班', 1, 20, 'CS_DEPT', 1,  22);

-- ---------- 数学系（8 名）----------
INSERT INTO tmp_students VALUES
('student027', '曹颖', 'caoying@stu.edu.cn',    '13800138027', '曹颖', '2023005001', '数学系', '数学与应用数学',   '2023', '1班', 2, 21, 'MATH_DEPT', 26, 50),
('student028', '袁博', 'yuanbo@stu.edu.cn',     '13800138028', '袁博', '2023005002', '数学系', '数学与应用数学',   '2023', '1班', 1, 20, 'MATH_DEPT', 24, 65),
('student029', '邓蕾', 'denglei@stu.edu.cn',    '13800138029', '邓蕾', '2023005003', '数学系', '数学与应用数学',   '2023', '2班', 2, 21, 'MATH_DEPT', 21, 33),
('student030', '许晨', 'xuchen@stu.edu.cn',     '13800138030', '许晨', '2023006001', '数学系', '信息与计算科学',   '2023', '1班', 1, 22, 'MATH_DEPT', 16, 58),
('student031', '傅文', 'fuwen@stu.edu.cn',      '13800138031', '傅文', '2023006002', '数学系', '信息与计算科学',   '2023', '1班', 1, 20, 'MATH_DEPT', 13, 42),
('student032', '苏婉', 'suwan@stu.edu.cn',      '13800138032', '苏婉', '2024005001', '数学系', '数学与应用数学',   '2024', '1班', 2, 19, 'MATH_DEPT', 5,  28),
('student033', '沈涛', 'shentao@stu.edu.cn',    '13800138033', '沈涛', '2024005002', '数学系', '数学与应用数学',   '2024', '1班', 1, 19, 'MATH_DEPT', 3,  15),
('student034', '卢茜', 'luqian@stu.edu.cn',     '13800138034', '卢茜', '2024006001', '数学系', '信息与计算科学',   '2024', '1班', 2, 20, 'MATH_DEPT', 2,  8);

-- ---------- 物理系（4 名）----------
INSERT INTO tmp_students VALUES
('student035', '贺强', 'heqiang@stu.edu.cn',    '13800138035', '贺强', '2023007001', '物理系', '应用物理学',       '2023', '1班', 1, 21, 'PHYSICS_DEPT', 20, 36),
('student036', '方颖', 'fangying@stu.edu.cn',   '13800138036', '方颖', '2023007002', '物理系', '应用物理学',       '2023', '1班', 2, 20, 'PHYSICS_DEPT', 11, 44),
('student037', '邹阳', 'zouyang@stu.edu.cn',    '13800138037', '邹阳', '2024007001', '物理系', '应用物理学',       '2024', '1班', 1, 19, 'PHYSICS_DEPT', 4,  16),
('student038', '熊梅', 'xiongmei@stu.edu.cn',   '13800138038', '熊梅', '2024007002', '物理系', '应用物理学',       '2024', '1班', 2, 19, 'PHYSICS_DEPT', 1,  6);

-- ---------- 化学系（3 名）----------
INSERT INTO tmp_students VALUES
('student039', '康健', 'kangjian@stu.edu.cn',   '13800138039', '康健', '2023008001', '化学系', '应用化学',         '2023', '1班', 1, 21, 'CHEM_DEPT', 15, 24),
('student040', '田园', 'tianyuan@stu.edu.cn',   '13800138040', '田园', '2023008002', '化学系', '应用化学',         '2023', '1班', 2, 20, 'CHEM_DEPT', 8,  38),
('student041', '石磊', 'shilei@stu.edu.cn',     '13800138041', '石磊', '2024008001', '化学系', '应用化学',         '2024', '1班', 1, 19, 'CHEM_DEPT', 3,  10);


-- ============================================================================
-- 2. 批量创建用户账号
-- ============================================================================
INSERT INTO sys_user (user_name, nick_name, password, email, phonenumber, user_type, status)
SELECT user_name,
       nick_name,
       '$2b$12$YJyeMETHlQ4nX6/fypqAseaJLVhoiIW8Fbpz3Vfg/KICBgJaoPCE6',
       email,
       phonenumber,
       '1',
       '0'
FROM tmp_students;


-- ============================================================================
-- 3. 批量创建学生身份
-- ============================================================================
INSERT INTO edu_student (student_id, real_name, student_no, faculty, major, grade, class_name, gender, age, continue_day)
SELECT u.user_id, t.real_name, t.student_no, t.faculty, t.major, t.grade, t.class_name, t.gender, t.age, 0
FROM tmp_students t
         INNER JOIN sys_user u ON t.user_name = u.user_name;


-- ============================================================================
-- 4. 批量绑定学生角色（role_id=12）
-- ============================================================================
INSERT INTO sys_user_role (user_id, role_id)
SELECT u.user_id, 12
FROM tmp_students t
         INNER JOIN sys_user u ON t.user_name = u.user_name;


-- ============================================================================
-- 5. 批量绑定所属部门
-- ============================================================================
INSERT INTO sys_user_dept (user_id, dept_id, is_primary)
SELECT u.user_id, d.dept_id, '1'
FROM tmp_students t
         INNER JOIN sys_user u ON t.user_name = u.user_name
         INNER JOIN sys_dept d ON t.dept_key = d.dept_key;


-- ============================================================================
-- 6. 批量选课（离散数学 course_id=1）
-- ============================================================================
INSERT INTO edu_student_course (student_id, course_id, enroll_time, progress)
SELECT u.user_id,
       1,
       CURRENT_TIMESTAMP - (t.enroll_offset || ' days')::INTERVAL,
       t.progress
FROM tmp_students t
         INNER JOIN sys_user u ON t.user_name = u.user_name;


-- ============================================================================
-- 7. 更新课程学生人数
-- ============================================================================
UPDATE edu_course
SET student_count = student_count + (SELECT COUNT(*) FROM tmp_students)
WHERE course_id = 1;


-- ============================================================================
-- 8. 清理临时表
-- ============================================================================
DROP TABLE tmp_students;


-- ============================================================================
-- 9. 验证数据
-- ============================================================================

-- 查看新增学生概况
SELECT d.dept_name  AS 学院,
       s.major      AS 专业,
       s.grade      AS 年级,
       COUNT(*)     AS 人数
FROM edu_student s
         INNER JOIN sys_user u ON s.student_id = u.user_id
         INNER JOIN sys_user_dept ud ON u.user_id = ud.user_id AND ud.is_primary = '1'
         INNER JOIN sys_dept d ON ud.dept_id = d.dept_id
WHERE u.user_name LIKE 'student%'
GROUP BY d.dept_name, s.major, s.grade
ORDER BY d.dept_name, s.major, s.grade;

-- 查看离散数学选课统计
SELECT '离散数学选课总人数' AS 统计项, COUNT(*) AS 数量
FROM edu_student_course
WHERE course_id = 1;

-- 登录账号提示
SELECT '学生账号：student002~student041 / student123（共 40 名）' AS info;
