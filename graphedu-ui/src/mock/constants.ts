/**
 * Mock 共享常量
 * 所有 mock 数据引用此处的 ID 和名称，确保跨页面一致
 */

/** 演示用户 ID */
export const MOCK_USER_ID = 10001

/** Mock 课程 ID */
export const MOCK_COURSE_ID = 1

// ==================== 学生数据 ====================

export const MOCK_STUDENTS = [
  {
    studentId: 10001,
    realName: '张三',
    studentNo: 'ADMIN-STUDENT001',
    className: '计算机2401班',
    faculty: '计算机科学与技术学院',
    gender: 1,
    progress: 88,
    mastery: 88,
  },
  {
    studentId: 10002,
    realName: '李思',
    studentNo: '2024001002',
    className: '计算机2401班',
    faculty: '计算机科学与技术学院',
    gender: 2,
    progress: 82,
    mastery: 82,
  },
  {
    studentId: 10003,
    realName: '王五',
    studentNo: '2024001003',
    className: '数学2401班',
    faculty: '数学与统计学院',
    gender: 1,
    progress: 75,
    mastery: 75,
  },
  {
    studentId: 10004,
    realName: '赵六',
    studentNo: '2024001004',
    className: '数学2401班',
    faculty: '数学与统计学院',
    gender: 1,
    progress: 68,
    mastery: 68,
  },
  {
    studentId: 10005,
    realName: '钱七',
    studentNo: '2024001005',
    className: '计算机2402班',
    faculty: '计算机科学与技术学院',
    gender: 2,
    progress: 62,
    mastery: 62,
  },
  {
    studentId: 10006,
    realName: '孙八',
    studentNo: '2024001006',
    className: '计算机2402班',
    faculty: '计算机科学与技术学院',
    gender: 1,
    progress: 55,
    mastery: 55,
  },
  {
    studentId: 10007,
    realName: '周九',
    studentNo: '2024001007',
    className: '数学2402班',
    faculty: '数学与统计学院',
    gender: 2,
    progress: 48,
    mastery: 48,
  },
  {
    studentId: 10008,
    realName: '吴十',
    studentNo: '2024001008',
    className: '数学2402班',
    faculty: '数学与统计学院',
    gender: 1,
    progress: 42,
    mastery: 42,
  },
  {
    studentId: 10009,
    realName: '郑十一',
    studentNo: '2024001009',
    className: '计算机2403班',
    faculty: '计算机科学与技术学院',
    gender: 1,
    progress: 35,
    mastery: 35,
  },
  {
    studentId: 10010,
    realName: '陈十二',
    studentNo: '2024001010',
    className: '计算机2403班',
    faculty: '计算机科学与技术学院',
    gender: 2,
    progress: 28,
    mastery: 28,
  },
] as const

// ==================== 章节数据 ====================

export const MOCK_CHAPTERS = [
  { chapterId: 1, chapterName: '命题逻辑', chapterNo: 1, parentId: 0 },
  { chapterId: 2, chapterName: '谓词逻辑', chapterNo: 2, parentId: 0 },
  { chapterId: 3, chapterName: '集合论', chapterNo: 3, parentId: 0 },
  { chapterId: 4, chapterName: '二元关系', chapterNo: 4, parentId: 0 },
  { chapterId: 5, chapterName: '函数', chapterNo: 5, parentId: 0 },
  { chapterId: 6, chapterName: '图论基础', chapterNo: 6, parentId: 0 },
  { chapterId: 7, chapterName: '树', chapterNo: 7, parentId: 0 },
  { chapterId: 8, chapterName: '组合数学', chapterNo: 8, parentId: 0 },
] as const

// ==================== 知识图谱节点 ====================

/** 节点 UUID → 节点信息映射 */
export const MOCK_NODES = [
  // 命题逻辑章 (chapterId=1)
  { uuid: 'node-prop', title: '命题', importance: 5, chapterId: 1 },
  { uuid: 'node-connective', title: '逻辑联结词', importance: 5, chapterId: 1 },
  { uuid: 'node-truthtable', title: '真值表', importance: 4, chapterId: 1 },
  { uuid: 'node-equiv', title: '等值演算', importance: 4, chapterId: 1 },
  { uuid: 'node-nf', title: '范式', importance: 5, chapterId: 1 },
  { uuid: 'node-inference', title: '推理理论', importance: 5, chapterId: 1 },
  // 谓词逻辑章 (chapterId=2)
  { uuid: 'node-predicate', title: '谓词', importance: 5, chapterId: 2 },
  { uuid: 'node-quantifier', title: '量词', importance: 4, chapterId: 2 },
  { uuid: 'node-predformula', title: '谓词公式', importance: 3, chapterId: 2 },
  // 集合论章 (chapterId=3)
  { uuid: 'node-set', title: '集合', importance: 5, chapterId: 3 },
  { uuid: 'node-setop', title: '集合运算', importance: 4, chapterId: 3 },
  { uuid: 'node-cartesian', title: '笛卡尔积', importance: 3, chapterId: 3 },
  // 二元关系章 (chapterId=4)
  { uuid: 'node-relation', title: '关系', importance: 5, chapterId: 4 },
  { uuid: 'node-equivrel', title: '等价关系', importance: 4, chapterId: 4 },
  { uuid: 'node-poset', title: '偏序关系', importance: 4, chapterId: 4 },
  // 函数章 (chapterId=5)
  { uuid: 'node-funcmap', title: '函数映射', importance: 5, chapterId: 5 },
  { uuid: 'node-injsurj', title: '单射与满射', importance: 4, chapterId: 5 },
  // 图论章 (chapterId=6)
  {
    uuid: 'node-graphbasic',
    title: '图的基本概念',
    importance: 5,
    chapterId: 6,
  },
  { uuid: 'node-path', title: '路径与回路', importance: 4, chapterId: 6 },
  // 树章 (chapterId=7)
  {
    uuid: 'node-treebasic',
    title: '树的基本概念',
    importance: 5,
    chapterId: 7,
  },
  { uuid: 'node-binarytree', title: '二叉树', importance: 4, chapterId: 7 },
  // 组合数学章 (chapterId=8)
  { uuid: 'node-combiperm', title: '排列与组合', importance: 5, chapterId: 8 },
] as const

/** 节点关系列表 */
export const MOCK_RELATIONSHIPS = [
  // 命题逻辑内部
  { from: 'node-prop', to: 'node-connective', type: 'PRIOR_TO' as const },
  { from: 'node-connective', to: 'node-truthtable', type: 'PRIOR_TO' as const },
  { from: 'node-truthtable', to: 'node-equiv', type: 'PRIOR_TO' as const },
  { from: 'node-equiv', to: 'node-nf', type: 'PRIOR_TO' as const },
  { from: 'node-nf', to: 'node-inference', type: 'PRIOR_TO' as const },
  // 谓词逻辑
  { from: 'node-inference', to: 'node-predicate', type: 'PRIOR_TO' as const },
  { from: 'node-predicate', to: 'node-quantifier', type: 'PRIOR_TO' as const },
  {
    from: 'node-quantifier',
    to: 'node-predformula',
    type: 'PRIOR_TO' as const,
  },
  {
    from: 'node-predicate',
    to: 'node-predformula',
    type: 'SUBTOPIC_OF' as const,
  },
  {
    from: 'node-quantifier',
    to: 'node-predformula',
    type: 'SUBTOPIC_OF' as const,
  },
  // 集合论
  { from: 'node-set', to: 'node-setop', type: 'PRIOR_TO' as const },
  { from: 'node-setop', to: 'node-cartesian', type: 'PRIOR_TO' as const },
  // 二元关系
  { from: 'node-cartesian', to: 'node-relation', type: 'PRIOR_TO' as const },
  { from: 'node-relation', to: 'node-equivrel', type: 'PRIOR_TO' as const },
  { from: 'node-relation', to: 'node-poset', type: 'PRIOR_TO' as const },
  { from: 'node-equivrel', to: 'node-poset', type: 'RELATED_TO' as const },
  // 函数
  { from: 'node-relation', to: 'node-funcmap', type: 'PRIOR_TO' as const },
  { from: 'node-funcmap', to: 'node-injsurj', type: 'PRIOR_TO' as const },
  // 图论
  { from: 'node-set', to: 'node-graphbasic', type: 'PRIOR_TO' as const },
  { from: 'node-graphbasic', to: 'node-path', type: 'PRIOR_TO' as const },
  // 树
  { from: 'node-graphbasic', to: 'node-treebasic', type: 'PRIOR_TO' as const },
  { from: 'node-treebasic', to: 'node-binarytree', type: 'PRIOR_TO' as const },
  // 组合数学
  { from: 'node-setop', to: 'node-combiperm', type: 'PRIOR_TO' as const },
  // 跨章节关联
  { from: 'node-prop', to: 'node-predicate', type: 'RELATED_TO' as const },
  { from: 'node-set', to: 'node-relation', type: 'RELATED_TO' as const },
  { from: 'node-relation', to: 'node-funcmap', type: 'RELATED_TO' as const },
  {
    from: 'node-graphbasic',
    to: 'node-treebasic',
    type: 'RELATED_TO' as const,
  },
  { from: 'node-path', to: 'node-treebasic', type: 'RELATED_TO' as const },
  { from: 'node-treebasic', to: 'node-combiperm', type: 'RELATED_TO' as const },
] as const

/** 图谱列表 */
export const MOCK_GRAPHS = [
  {
    graphId: 1,
    courseId: 1,
    graphName: '离散数学-核心概念图谱',
    graphDatabase: 'apache_age',
    isDraft: 'N',
    version: '1.0',
    totalNodes: 22,
    totalRelationships: 30,
    buildMethod: 'manual',
    status: '0',
    taskStatus: 'completed',
    createTime: '2026-03-15T10:30:00Z',
    courseName: '离散数学',
  },
  {
    graphId: 2,
    courseId: 1,
    graphName: '离散数学-命题逻辑专项',
    graphDatabase: 'apache_age',
    isDraft: 'N',
    version: '1.0',
    totalNodes: 6,
    totalRelationships: 5,
    buildMethod: 'manual',
    status: '0',
    taskStatus: 'completed',
    createTime: '2026-03-20T14:00:00Z',
    courseName: '离散数学',
  },
] as const

/** 学习计划 */
export const MOCK_PLANS = [
  {
    plan_id: 'plan-001',
    course_id: 1,
    title: '命题逻辑基础学习路径',
    status: 'active' as const,
    create_time: '2026-04-01T08:00:00Z',
  },
  {
    plan_id: 'plan-002',
    course_id: 1,
    title: '集合论学习路径',
    status: 'completed' as const,
    create_time: '2026-03-20T08:00:00Z',
  },
] as const
