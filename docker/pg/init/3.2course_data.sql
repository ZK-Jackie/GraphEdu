-- ============================================================================
-- 课程数据初始化
-- ============================================================================

-- 插入离散数学课程
TRUNCATE public.edu_course;
INSERT INTO public.edu_course (course_id, course_code, course_name, faculty, description, cover_file_id, category,
                               difficulty_level,
                               total_hours, course_outline, target_audience, learning_goals, tags, is_public, status,
                               create_time, update_time)
VALUES (1, 'CS201', '离散数学', '计算机学院',
        '离散数学是计算机科学的核心基础课程，主要研究离散结构和数学逻辑，为数据结构、算法分析、编译原理等后续课程提供必要的数学基础。',
        81, '数学', '2', 48,
        '课程大纲：\n1. 数理逻辑 - 命题逻辑、谓词逻辑、推理规则与证明方法\n2. 集合论 - 集合的概念与运算、二元关系、等价关系与偏序关系、函数\n3. 组合数学 - 排列与组合、二项式定理、鸽巢原理、包含-排斥原理\n4. 图论基础 - 图的基本概念、树的概念与应用、最短路径算法\n5. 代数结构 - 半群与群、环与域、格与布尔代数',
        '计算机科学与技术专业本科生，通常在大二学年学习。适合具备高等数学基础的学生。',
        '学习目标：\n- 掌握数理逻辑的基本概念和推理方法\n- 理解集合论的基本理论和关系运算\n- 学会组合计数的基本原理和方法\n- 掌握图论的基本概念和性质\n- 了解代数结构的基本理论\n- 培养数学思维和逻辑推理能力',
        '[
          "离散数学",
          "数理逻辑",
          "集合论",
          "图论",
          "组合数学",
          "代数结构",
          "数学基础"
        ]', 'Y', '0', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- 插入计算机网络课程
INSERT INTO public.edu_course (course_id, course_code, course_name, faculty, description, cover_file_id, category,
                               difficulty_level,
                               total_hours, course_outline, target_audience, learning_goals, tags, is_public, status,
                               create_time, update_time)
VALUES (2, 'CS301', '计算机网络', '计算机学院',
        '计算机网络是计算机专业的核心课程，系统介绍计算机网络的体系结构、协议原理和应用技术，涵盖从底层物理传输到高层应用服务的完整网络技术栈。',
        81, '计算机网络', '2', 48,
        '课程大纲：\n1. 概述 - 网络基本概念、网络体系结构、分层设计原则\n2. 物理层 - 数据通信基础、传输介质、信道复用技术\n3. 数据链路层 - 帧封装与差错控制、介质访问控制、以太网技术\n4. 网络层 - IP协议与路由、子网划分与CIDR、路由算法与协议\n5. 传输层 - 传输层服务、TCP协议详解、UDP协议、拥塞控制\n6. 应用层 - DNS域名系统、HTTP/HTTPS协议、电子邮件协议\n7. 网络安全 - 加密与认证、防火墙与入侵检测',
        '计算机科学与技术、软件工程等专业本科生，通常在大二或大三学年学习。需要具备一定的操作系统和编程基础。',
        '学习目标：\n- 理解计算机网络的五层体系结构\n- 掌握各层协议的工作原理和关键技术\n- 熟悉TCP/IP协议栈的核心协议\n- 学会网络配置和故障诊断的基本方法\n- 了解网络安全的威胁和防护措施\n- 培养网络编程能力',
        '[
          "计算机网络",
          "TCP/IP",
          "协议",
          "网络架构",
          "网络安全",
          "网络编程",
          "互联网"
        ]', 'Y', '0', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- ============================================================================
-- 文件上传数据
-- ============================================================================

INSERT INTO public.sys_upload (file_id, file_name, file_path, file_type, file_size, file_category, storage_type,
                               access_level,
                               download_flag, audit_status, status, create_by)
VALUES
-- CS201 PDF课件
(51, 'CS201-第1章-数理逻辑.pdf', 'uploads/course/CS201/chapter1-logic.pdf', 'application/pdf', 2048576, '7', '1', '2',
 'Y', '2', '0', 10001),
(52, 'CS201-第2章-集合论.pdf', 'uploads/course/CS201/chapter2-set.pdf', 'application/pdf', 1843200, '7', '1', '2', 'Y',
 '2', '0', 10001),
(53, 'CS201-第3章-图论基础.pdf', 'uploads/course/CS201/chapter3-set.pdf', 'application/pdf', 2150400, '7', '1', '2',
 'Y', '2', '0', 10001),
-- CS301 PDF课件
(54, 'CS301-第1章-网络概述.pdf', 'uploads/course/CS301/chapter1-intro.pdf', 'application/pdf', 1536000, '7', '1', '2',
 'Y', '2', '0', 10001),
(55, 'CS301-第2章-数据链路层.pdf', 'uploads/course/CS301/chapter2-datalink.pdf', 'application/pdf', 1769472, '7', '1',
 '2', 'Y', '2', '0', 10001),
(56, 'CS301-第3章-网络层.pdf', 'uploads/course/CS301/chapter3-network.pdf', 'application/pdf', 1992294, '7', '1', '2',
 'Y', '2', '0', 10001),
(57, 'CS301-第4章-传输层.pdf', 'uploads/course/CS301/chapter4-transport.pdf', 'application/pdf', 2097152, '7', '1', '2',
 'Y', '2', '0', 10001),
-- CS201 学习指导
(61, 'CS201-第1章-学习指导.md', 'uploads/course/CS201/离散-ch1指导.md', 'text/markdown', 2048, '6', '1', '2', 'Y', '2',
 '0', 10001),
(62, 'CS201-第2章-学习指导.md', 'uploads/course/CS201/离散-ch2指导.md', 'text/markdown', 2048, '6', '1', '2', 'Y', '2',
 '0', 10001),
(63, 'CS201-第3章-学习指导.md', 'uploads/course/CS201/离散-ch3指导.md', 'text/markdown', 2048, '6', '1', '2', 'Y', '2',
 '0', 10001),
-- CS301 学习指导
(64, 'CS301-第1章-学习指导.md', 'uploads/course/CS301/计网-ch1指导.md', 'text/markdown', 2048, '6', '1', '2', 'Y', '2',
 '0', 10001),
(65, 'CS301-第2章-学习指导.md', 'uploads/course/CS301/计网-ch2指导.md', 'text/markdown', 2048, '6', '1', '2', 'Y', '2',
 '0', 10001),
(66, 'CS301-第3章-学习指导.md', 'uploads/course/CS301/计网-ch3指导.md', 'text/markdown', 2048, '6', '1', '2', 'Y', '2',
 '0', 10001),
(67, 'CS301-第4章-学习指导.md', 'uploads/course/CS301/计网-ch4指导.md', 'text/markdown', 2048, '6', '1', '2', 'Y', '2',
 '0', 10001),
-- CS201 新增 PDF 教材
(68, 'CS201-教材-前言与目录.pdf', 'uploads/course/CS201/离散数学及其应用前言与目录等-汪荣贵.pdf', 'application/pdf',
 485104, '7',
 '1', '2', 'Y', '2', '0', 10001),
(69, 'CS201-教材-第1章-集合与计数基础.pdf', 'uploads/course/CS201/第1章  集合与计数基础-汪荣贵.pdf', 'application/pdf',
 2138337,
 '7', '1', '2', 'Y', '2', '0', 10001),
(70, 'CS201-教材-第2章-整数与算法基础.pdf', 'uploads/course/CS201/第2章  整数与算法基础-汪荣贵.pdf', 'application/pdf',
 2474770,
 '7', '1', '2', 'Y', '2', '0', 10001),
(71, 'CS201-教材-第3章-命题演算与推理.pdf', 'uploads/course/CS201/第3章  命题演算与推理-汪荣贵.pdf', 'application/pdf',
 2760618,
 '7', '1', '2', 'Y', '2', '0', 10001),
(72, 'CS201-教材-第4章-谓词演算与推理.pdf', 'uploads/course/CS201/第4章  谓词演算与推理-汪荣贵.pdf', 'application/pdf',
 1836976,
 '7', '1', '2', 'Y', '2', '0', 10001),
(73, 'CS201-教材-第5章-关系模型与理论.pdf', 'uploads/course/CS201/第5章  关系模型与理论-汪荣贵.pdf', 'application/pdf',
 2039472,
 '7', '1', '2', 'Y', '2', '0', 10001),
(74, 'CS201-教材-第6章-特殊关系模型.pdf', 'uploads/course/CS201/第6章  特殊关系模型-汪荣贵.pdf', 'application/pdf',
 1698781,
 '7', '1', '2', 'Y', '2', '0', 10001),
(75, 'CS201-教材-第7章-函数与特殊函数.pdf', 'uploads/course/CS201/第7章  函数与特殊函数-汪荣贵.pdf', 'application/pdf',
 1549902,
 '7', '1', '2', 'Y', '2', '0', 10001),
(76, 'CS201-教材-第8章-图的基本理论与算法.pdf', 'uploads/course/CS201/第8章  图的基本理论与算法-汪荣贵.pdf',
 'application/pdf',
 3250317, '7', '1', '2', 'Y', '2', '0', 10001),
(77, 'CS201-教材-第9章-树的基本理论与算法.pdf', 'uploads/course/CS201/第9章  树的基本理论与算法-汪荣贵.pdf',
 'application/pdf',
 2102523, '7', '1', '2', 'Y', '2', '0', 10001),
(78, 'CS201-教材-第10章-特殊图模型与算法.pdf', 'uploads/course/CS201/第10章 特殊图模型与算法-汪荣贵.pdf',
 'application/pdf',
 3346162, '7', '1', '2', 'Y', '2', '0', 10001),
(79, 'CS201-教材-第11章-抽象代数结构通论.pdf', 'uploads/course/CS201/第11章 抽象代数结构通论-汪荣贵1.pdf',
 'application/pdf',
 2025498, '7', '1', '2', 'Y', '2', '0', 10001),
(80, 'CS201-教材-第12章-典型抽象代数结构.pdf', 'uploads/course/CS201/第12章-典型抽象代数结构-汪荣贵1.pdf',
 'application/pdf',
 2441415, '7', '1', '2', 'Y', '2', '0', 10001),
-- 课程封面图片
(81, 'CS201-course-image.png', 'uploads/course-image/CS201/course-image.png', 'image/png', 204347, '2', '1', '2', 'Y',
 '2', '0', 10001),
(82, 'CS301-course-image.png', 'uploads/course-image/CS301/cs301-course-image.png', 'image/png', 183976, '2', '1', '2',
 'Y', '2', '0', 10001),
-- CS201 教材文本化 Markdown
(83, 'CS201-教材-第1章-文本化.md', 'md/course/CS201/ch1.md', 'text/markdown', 51466, '6', '1', '2', 'Y', '2', '0',
 10001),
(84, 'CS201-教材-第2章-文本化.md', 'md/course/CS201/ch2.md', 'text/markdown', 60281, '6', '1', '2', 'Y', '2', '0',
 10001),
(85, 'CS201-教材-第3章-文本化.md', 'md/course/CS201/ch3.md', 'text/markdown', 69073, '6', '1', '2', 'Y', '2', '0',
 10001),
(86, 'CS201-教材-第4章-文本化.md', 'md/course/CS201/ch4.md', 'text/markdown', 55270, '6', '1', '2', 'Y', '2', '0',
 10001),
(87, 'CS201-教材-第5章-文本化.md', 'md/course/CS201/ch5.md', 'text/markdown', 47645, '6', '1', '2', 'Y', '2', '0',
 10001),
(88, 'CS201-教材-第6章-文本化.md', 'md/course/CS201/ch6.md', 'text/markdown', 30968, '6', '1', '2', 'Y', '2', '0',
 10001),
(89, 'CS201-教材-第7章-文本化.md', 'md/course/CS201/ch7.md', 'text/markdown', 36255, '6', '1', '2', 'Y', '2', '0',
 10001),
(90, 'CS201-教材-第8章-文本化.md', 'md/course/CS201/ch8.md', 'text/markdown', 70507, '6', '1', '2', 'Y', '2', '0',
 10001),
(91, 'CS201-教材-第9章-文本化.md', 'md/course/CS201/ch9.md', 'text/markdown', 44578, '6', '1', '2', 'Y', '2', '0',
 10001),
(92, 'CS201-教材-第10章-文本化.md', 'md/course/CS201/ch10.md', 'text/markdown', 59161, '6', '1', '2', 'Y', '2', '0',
 10001),
(93, 'CS201-教材-第11章-文本化.md', 'md/course/CS201/ch11.md', 'text/markdown', 48580, '6', '1', '2', 'Y', '2', '0',
 10001),
(94, 'CS201-教材-第12章-文本化.md', 'md/course/CS201/ch12.md', 'text/markdown', 77088, '6', '1', '2', 'Y', '2', '0',
 10001);

-- ============================================================================
-- 课程章节数据
-- ============================================================================
TRUNCATE public.edu_chapter;
INSERT INTO public.edu_chapter (chapter_id, course_id, parent_id, chapter_name, chapter_no, description, status,
                                create_by,
                                create_time, update_time)
VALUES
-- CS201 章节
(1, 1, 0, '第1章 数理逻辑', 1,
 '本章介绍数理逻辑的基本概念，包括命题逻辑、谓词逻辑以及推理规则与证明方法。数理逻辑是离散数学的基础，也是计算机科学理论的重要组成部分。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2, 1, 0, '第2章 集合论', 2,
 '本章讲解集合论的基本理论，包括集合的概念与运算、二元关系、等价关系与偏序关系以及函数。集合论是现代数学的基础，在计算机科学中有广泛应用。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(3, 1, 0, '第3章 图论基础', 3,
 '本章介绍图论的基本概念，包括图的定义、图的表示方法、树的概念与应用以及最短路径算法。图论在计算机科学中有重要应用，如网络路由、社交网络分析等。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
-- CS301 章节
(4, 2, 0, '第1章 概述', 1,
 '本章介绍计算机网络的基本概念，包括网络的定义、分类、性能指标以及网络体系结构。重点讲解OSI七层模型和TCP/IP五层模型，为后续章节的学习奠定基础。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(5, 2, 0, '第2章 数据链路层', 2,
 '本章详细讲解数据链路层的功能，包括组帧、差错控制、流量控制以及介质访问控制。重点介绍以太网技术和交换机的工作原理。', '0',
 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(6, 2, 0, '第3章 网络层', 3,
 '本章讲解网络层的核心协议和技术，包括IP协议、子网划分、CIDR、路由算法以及路由协议（RIP、OSPF等）。介绍网络层如何实现数据包的端到端传输。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(7, 2, 0, '第4章 传输层', 4,
 '本章介绍传输层的服务和协议，重点讲解TCP协议的可靠传输机制、流量控制、拥塞控制以及UDP协议的特点。传输层为应用程序提供端到端的通信服务。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
-- CS201 新增章节（第4-12章）
(8, 1, 0, '第4章 谓词演算与推理', 4,
 '本章围绕谓词逻辑展开，介绍量词、谓词公式、推理规则与常用证明方法。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(9, 1, 0, '第5章 关系模型与理论', 5,
 '本章系统讲解二元关系及其性质，包含等价关系、偏序关系与关系闭包等核心内容。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(10, 1, 0, '第6章 特殊关系模型', 6,
 '本章聚焦函数关系、相容关系等特殊关系模型，强化离散结构抽象建模能力。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(11, 1, 0, '第7章 函数与特殊函数', 7,
 '本章介绍函数、复合函数、逆函数与常见特殊函数，结合离散问题进行分析。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(12, 1, 0, '第8章 图的基本理论与算法', 8,
 '本章介绍图的基本概念、图的表示及遍历算法，为后续图算法学习打基础。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(13, 1, 0, '第9章 树的基本理论与算法', 9,
 '本章讲解树与二叉树的性质、遍历与典型应用，强调树结构在计算中的作用。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(14, 1, 0, '第10章 特殊图模型与算法', 10,
 '本章面向网络流、匹配等特殊图模型，介绍常见问题与求解思路。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(15, 1, 0, '第11章 抽象代数结构通论', 11,
 '本章引入群、环、域等抽象代数结构，说明其在离散数学中的统一刻画作用。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(16, 1, 0, '第12章 典型抽象代数结构', 12,
 '本章通过典型代数结构案例深化抽象概念理解，训练形式化推理能力。',
 '0', 10001, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- ============================================================================
-- 章节学习资料数据
-- ============================================================================
TRUNCATE public.edu_resource;
INSERT INTO public.edu_resource (resource_id, chapter_id, resource_name, resource_type, file_id, display_order,
                                 is_visible, text_file_id, status, parse_status, create_by, create_time)
VALUES
-- CS201 第1章
(1, 1, '第1章学习指导', 'text', 61, 1, 'Y', NULL, '0', '9', 10001, CURRENT_TIMESTAMP),
(2, 1, '第1章课件', 'document', 51, 2, 'Y', NULL, '0', '0', 10001, CURRENT_TIMESTAMP),
-- CS201 第2章
(3, 2, '第2章学习指导', 'text', 62, 1, 'Y', NULL, '0', '9', 10001, CURRENT_TIMESTAMP),
(4, 2, '第2章课件', 'document', 52, 2, 'Y', NULL, '0', '0', 10001, CURRENT_TIMESTAMP),
-- CS201 第3章
(5, 3, '第3章学习指导', 'text', 63, 1, 'Y', NULL, '0', '9', 10001, CURRENT_TIMESTAMP),
(6, 3, '第3章课件', 'document', 53, 2, 'Y', NULL, '0', '0', 10001, CURRENT_TIMESTAMP),
-- CS301 第1章
(7, 4, '第1章学习指导', 'text', 64, 1, 'Y', NULL, '0', '9', 10001, CURRENT_TIMESTAMP),
(8, 4, '第1章课件', 'document', 54, 2, 'Y', NULL, '0', '0', 10001, CURRENT_TIMESTAMP),
-- CS301 第2章
(9, 5, '第2章学习指导', 'text', 65, 1, 'Y', NULL, '0', '9', 10001, CURRENT_TIMESTAMP),
(10, 5, '第2章课件', 'document', 55, 2, 'Y', NULL, '0', '0', 10001, CURRENT_TIMESTAMP),
-- CS301 第3章
(11, 6, '第3章学习指导', 'text', 66, 1, 'Y', NULL, '0', '9', 10001, CURRENT_TIMESTAMP),
(12, 6, '第3章课件', 'document', 56, 2, 'Y', NULL, '0', '0', 10001, CURRENT_TIMESTAMP),
-- CS301 第4章
(13, 7, '第4章学习指导', 'text', 67, 1, 'Y', NULL, '0', '9', 10001, CURRENT_TIMESTAMP),
(14, 7, '第4章课件', 'document', 57, 2, 'Y', NULL, '0', '0', 10001, CURRENT_TIMESTAMP),
-- CS201 新增资源（前言 + 第1-12章教材）
(15, 1, '前言与目录（教材）', 'document', 68, 3, 'Y', NULL, '0', '0', 10001, CURRENT_TIMESTAMP),
(16, 1, '第1章教材（新版）', 'document', 69, 4, 'Y', 83, '0', '2', 10001, CURRENT_TIMESTAMP),
(17, 2, '第2章教材（新版）', 'document', 70, 3, 'Y', 84, '0', '2', 10001, CURRENT_TIMESTAMP),
(18, 3, '第3章教材（新版）', 'document', 71, 3, 'Y', 85, '0', '2', 10001, CURRENT_TIMESTAMP),
(19, 8, '第4章教材', 'document', 72, 1, 'Y', 86, '0', '2', 10001, CURRENT_TIMESTAMP),
(20, 9, '第5章教材', 'document', 73, 1, 'Y', 87, '0', '2', 10001, CURRENT_TIMESTAMP),
(21, 10, '第6章教材', 'document', 74, 1, 'Y', 88, '0', '2', 10001, CURRENT_TIMESTAMP),
(22, 11, '第7章教材', 'document', 75, 1, 'Y', 89, '0', '2', 10001, CURRENT_TIMESTAMP),
(23, 12, '第8章教材', 'document', 76, 1, 'Y', 90, '0', '2', 10001, CURRENT_TIMESTAMP),
(24, 13, '第9章教材', 'document', 77, 1, 'Y', 91, '0', '2', 10001, CURRENT_TIMESTAMP),
(25, 14, '第10章教材', 'document', 78, 1, 'Y', 92, '0', '2', 10001, CURRENT_TIMESTAMP),
(26, 15, '第11章教材', 'document', 79, 1, 'Y', 93, '0', '2', 10001, CURRENT_TIMESTAMP),
(27, 16, '第12章教材', 'document', 80, 1, 'Y', 94, '0', '2', 10001, CURRENT_TIMESTAMP);
