-- ============================================================================
-- GraphEdu 用户数据初始化脚本
-- ============================================================================
-- 说明：此脚本集中管理所有用户相关的数据初始化，包括：
--   - 用户账号创建
--   - 角色/部门绑定
--   - 学生/教师身份绑定
--   - 课程-教师关联
--   - 学生选课
-- 注意：执行前请确保已执行 2.4system_data.sql（角色/部门）和 3.2course_data.sql（课程数据）
-- ============================================================================


-- ============================================================================
-- 0. 清空用户相关表数据
-- ============================================================================
-- public.sys_user_role / public.sys_user_dept / public.sys_user 已在 2.4system_data.sql 中 TRUNCATE
-- public.edu_student / public.edu_teacher 在 3.1education.sql 中创建，需要在此处清空
TRUNCATE TABLE public.edu_student RESTART IDENTITY CASCADE;
TRUNCATE TABLE public.edu_teacher RESTART IDENTITY CASCADE;


-- ============================================================================
-- 1. 插入管理员账号（超级管理员）
-- ============================================================================
-- 用户名: admin  密码: admin123 (bcrypt加密)
-- 身份：管理员 + 教师 + 学生（三重角色）
INSERT INTO public.sys_user (user_id, user_name, nick_name, password, user_type, status, remark)
VALUES (10001, 'admin', '超级管理员', '$2b$12$bLMfvo1sGxR65DVt8ygLyOW.HBAbCdpgXMjBJ8BtX.r14A1UyMo8O', '3', '0',
        '系统超级管理员账号');

-- 管理员角色绑定：admin(role_id=1) + 教师(role_id=11) + 学生(role_id=12)
INSERT INTO public.sys_user_role (user_id, role_id) VALUES (10001, 1);
INSERT INTO public.sys_user_role (user_id, role_id) VALUES (10001, 11);
INSERT INTO public.sys_user_role (user_id, role_id) VALUES (10001, 12);

-- 管理员 → 教师身份
INSERT INTO public.edu_teacher (teacher_id, real_name, teacher_no, faculty, title, research_direction)
VALUES (10001, '系统管理员', 'ADMIN-TEACHER001', '计算机学院', '系统管理员', '教育平台管理与维护');

-- 管理员 → 学生身份
INSERT INTO public.edu_student (student_id, real_name, student_no, faculty, major, grade, class_name, gender, age)
VALUES (10001, '系统管理员', 'ADMIN-STUDENT001', '计算机学院', '计算机科学与技术', '2024', '管理员班', 1, 30);


-- ============================================================================
-- 2. 插入学生账号（仅学生身份）
-- ============================================================================
-- 用户名: student001  密码: student123
INSERT INTO public.sys_user (user_name, nick_name, password, email, phonenumber, user_type, status)
VALUES ('student001', '张三', '$2b$12$YJyeMETHlQ4nX6/fypqAseaJLVhoiIW8Fbpz3Vfg/KICBgJaoPCE6',
        'zhangsan@example.com', '13800138001', '1', '0');

-- 学生身份信息
INSERT INTO public.edu_student (student_id, real_name, student_no, faculty, major, grade, class_name, gender, age,
                         continue_day)
SELECT user_id, '张三', '2023001001', '计算机学院', '计算机科学与技术', '2023', '1班', 1, 20, 0
FROM public.sys_user
WHERE user_name = 'student001';

-- 学生角色绑定（role_id=12，仅学生角色）
INSERT INTO public.sys_user_role (user_id, role_id)
SELECT user_id, 12
FROM public.sys_user
WHERE user_name = 'student001';

-- 学生部门绑定 → 计算机学院
INSERT INTO public.sys_user_dept (user_id, dept_id, is_primary)
SELECT u.user_id, d.dept_id, '1'
FROM public.sys_user u,
     public.sys_dept d
WHERE u.user_name = 'student001'
  AND d.dept_key = 'CS_DEPT';


-- ============================================================================
-- 3. 插入教师账号（仅教师身份）
-- ============================================================================
-- 用户名: teacher001  密码: teacher123
INSERT INTO public.sys_user (user_name, nick_name, password, email, phonenumber, user_type, status)
VALUES ('teacher001', '李教授', '$2b$12$lA7TlYcvlaV2pZ2a5HQ5tehDBilGR7QvRm2cTBxmZwMfusigBXypK',
        'liprof@example.com', '13900139001', '2', '0');

-- 教师身份信息
INSERT INTO public.edu_teacher (teacher_id, real_name, teacher_no, faculty, title, research_direction)
SELECT user_id, '李明', 'T2023001', '计算机学院', '教授', '人工智能、机器学习'
FROM public.sys_user
WHERE user_name = 'teacher001';

-- 教师角色绑定（role_id=11，仅教师角色）
INSERT INTO public.sys_user_role (user_id, role_id)
SELECT user_id, 11
FROM public.sys_user
WHERE user_name = 'teacher001';

-- 教师部门绑定 → 计算机学院
INSERT INTO public.sys_user_dept (user_id, dept_id, is_primary)
SELECT u.user_id, d.dept_id, '1'
FROM public.sys_user u,
     public.sys_dept d
WHERE u.user_name = 'teacher001'
  AND d.dept_key = 'CS_DEPT';


-- ============================================================================
-- 4. 课程-教师关联
-- ============================================================================

-- admin（user_id=10001）教授 CS201 离散数学 和 CS301 计算机网络
INSERT INTO public.edu_course_teacher (course_id, teacher_id, role_type, display_order)
VALUES (1, 10001, 'instructor', 2);
INSERT INTO public.edu_course_teacher (course_id, teacher_id, role_type, display_order)
VALUES (2, 10001, 'instructor', 1);

-- teacher001（李教授）教授 CS201 离散数学
INSERT INTO public.edu_course_teacher (course_id, teacher_id, role_type, display_order)
VALUES (1, (SELECT teacher_id
            FROM public.edu_teacher
            WHERE teacher_id = (SELECT user_id FROM public.sys_user WHERE user_name = 'teacher001')), 'instructor', 1);


-- ============================================================================
-- 5. 学生选课数据
-- ============================================================================

-- student001（张三）选修 CS201 和 CS301
INSERT INTO public.edu_student_course (student_id, course_id, enroll_time, progress)
VALUES ((SELECT user_id FROM public.sys_user WHERE user_name = 'student001'), 1,
        CURRENT_TIMESTAMP - INTERVAL '7 days', 25);
INSERT INTO public.edu_student_course (student_id, course_id, enroll_time, progress)
VALUES ((SELECT user_id FROM public.sys_user WHERE user_name = 'student001'), 2,
        CURRENT_TIMESTAMP - INTERVAL '3 days', 10);

-- admin 选修 CS201 和 CS301（测试）
INSERT INTO public.edu_student_course (student_id, course_id, enroll_time, progress)
VALUES (10001, 1, CURRENT_TIMESTAMP - INTERVAL '10 days', 40);
INSERT INTO public.edu_student_course (student_id, course_id, enroll_time, progress)
VALUES (10001, 2, CURRENT_TIMESTAMP - INTERVAL '5 days', 15);

-- 更新课程学生人数
UPDATE public.edu_course
SET student_count = student_count + 2
WHERE course_id IN (1, 2);


-- ============================================================================
-- 6. 验证数据
-- ============================================================================

-- 查看用户-角色-身份完整绑定情况
SELECT u.user_id,
       u.user_name,
       u.nick_name,
       r.role_key,
       r.role_name,
       CASE WHEN t.teacher_id IS NOT NULL THEN 'Y' ELSE 'N' END AS is_teacher,
       CASE WHEN s.student_id IS NOT NULL THEN 'Y' ELSE 'N' END  AS is_student
FROM public.sys_user u
         LEFT JOIN public.sys_user_role ur ON u.user_id = ur.user_id
         LEFT JOIN public.sys_role r ON ur.role_id = r.role_id
         LEFT JOIN public.edu_teacher t ON u.user_id = t.teacher_id
         LEFT JOIN public.edu_student s ON u.user_id = s.student_id
ORDER BY u.user_id, r.role_id;

-- 查看课程-教师关联
SELECT c.course_id, c.course_name, t.real_name AS teacher_name, ct.role_type
FROM public.edu_course_teacher ct
         JOIN public.edu_course c ON ct.course_id = c.course_id
         JOIN public.edu_teacher t ON ct.teacher_id = t.teacher_id
ORDER BY c.course_id, ct.display_order;

-- 查看学生选课情况
SELECT u.user_name, u.nick_name, c.course_name, sc.progress, sc.enroll_time
FROM public.edu_student_course sc
         JOIN public.sys_user u ON sc.student_id = u.user_id
         JOIN public.edu_course c ON sc.course_id = c.course_id
ORDER BY u.user_name, c.course_id;

-- 登录账号提示
SELECT '超级管理员：admin / admin123（教师+学生双重身份）' AS info
UNION
SELECT '教师账号：teacher001 / teacher123（仅教师身份）'
UNION
SELECT '学生账号：student001 / student123（仅学生身份）';
