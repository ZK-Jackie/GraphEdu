/**
 * AI 聊天会话 Mock 数据
 *
 * 包含一个演示会话（命题逻辑学习讨论），始终排在列表第一位。
 * 会话内有完整的问答交流、AI 出题、答题反馈等。
 */
import type { ChatMessage, ChatSessionDetailVO, ChatSessionListVO } from '@/types/api/education/agent'
import { MOCK_COURSE_ID, MOCK_USER_ID } from './constants'

/** Mock 会话 ID */
export const MOCK_CONV_ID = 90001

/** 最近消息时间（几分钟前） */
function recentTime(minutesAgo: number): string {
  return new Date(Date.now() - minutesAgo * 60000).toISOString()
}

// ==================== 会话列表 ====================

export function getMockSessionList(): ChatSessionListVO[] {
  return [
    {
      convId: MOCK_CONV_ID,
      userId: MOCK_USER_ID,
      courseId: MOCK_COURSE_ID,
      title: '命题逻辑学习讨论',
      messageCount: 10,
      status: '0',
      createTime: recentTime(120),
      lastMessageTime: recentTime(5),
      courseName: '离散数学',
    },
  ]
}

// ==================== 会话详情 ====================

export function getMockSessionDetail(): ChatSessionDetailVO {
  return {
    convId: MOCK_CONV_ID,
    userId: MOCK_USER_ID,
    courseId: MOCK_COURSE_ID,
    title: '命题逻辑学习讨论',
    contextSummary: '用户正在学习离散数学中的命题逻辑部分，讨论了等值演算、范式等概念，并完成了一道相关练习题。',
    messageCount: 10,
    status: '0',
    createBy: MOCK_USER_ID,
    createTime: recentTime(120),
    updateBy: MOCK_USER_ID,
    updateTime: recentTime(5),
    lastMessageTime: recentTime(5),
  }
}

// ==================== 会话消息历史 ====================

export function getMockSessionMessages(): ChatMessage[] {
  const now = Date.now()
  return [
    // 1. 用户提问
    {
      role: 0,
      conv_id: MOCK_CONV_ID,
      message_id: `msg-${now - 115 * 60000}`,
      contents: [
        {
          type: 'text',
          text: '请帮我解释一下命题逻辑中的等值演算是什么？',
        },
      ],
    },
    // 2. AI 思考
    {
      role: 2,
      conv_id: MOCK_CONV_ID,
      message_id: `msg-${now - 114 * 60000}`,
      contents: [
        {
          type: 'text',
          text: '用户询问等值演算的概念，需要从命题等值的定义出发，介绍基本的等值式，并说明等值演算的规则和应用场景。',
        },
      ],
    },
    // 3. AI 回答
    {
      role: 1,
      conv_id: MOCK_CONV_ID,
      message_id: `msg-${now - 113 * 60000}`,
      contents: [
        {
          type: 'text',
          text: `## 等值演算

**等值演算**是命题逻辑中的核心工具，用于判断两个命题公式是否**逻辑等值**（即在任何赋值下真值相同）。

### 基本概念

若两个公式 $A$ 和 $B$ 在所有赋值下真值相同，则称 $A \\Leftrightarrow B$（$A$ 等值于 $B$）。

### 常用等值式

| 名称 | 等值式 |
|------|--------|
| 双重否定律 | $\\neg(\\neg p) \\Leftrightarrow p$ |
| 德摩根律 | $\\neg(p \\land q) \\Leftrightarrow \\neg p \\lor \\neg q$ |
| 交换律 | $p \\land q \\Leftrightarrow q \\land p$ |
| 分配律 | $p \\land (q \\lor r) \\Leftrightarrow (p \\land q) \\lor (p \\land r)$ |
| 蕴含等值式 | $p \\rightarrow q \\Leftrightarrow \\neg p \\lor q$ |

### 等值演算的规则

通过已知的等值式，逐步替换子公式，最终化简或证明等值关系。这就是**等值演算**的过程。

> 💡 掌握等值演算是后续学习**范式**和**推理理论**的基础。`,
        },
      ],
    },
    // 4. AI 出题
    {
      role: 1,
      conv_id: MOCK_CONV_ID,
      message_id: `msg-${now - 112 * 60000}`,
      contents: [
        {
          type: 'text',
          text: '我们来练习一下！试试这道题：\n',
        },
        {
          type: 'question_option',
          question_option: {
            questionType: 'single',
            title: '等值演算练习',
            content: '下列哪个等值式是德摩根定律的正确形式？',
            options: ['A. ¬(p∧q)↔¬p∨¬q', 'B. ¬(p∧q)↔¬p∧¬q', 'C. ¬(p∨q)↔¬p∧¬q', 'D. ¬(p∨q)↔¬p∨¬q'],
            answer: ['A. ¬(p∧q)↔¬p∨¬q'],
            explanation:
              '德摩根定律有两种形式：\n1. ¬(p∧q)↔¬p∨¬q（否定合取等于析取的否定）\n2. ¬(p∨q)↔¬p∧¬q（否定析取等于合取的否定）\n\n选项 A 是第一种形式的正确表达。选项 B 错误地将外层的否定直接分配到内部且未改变联结词。选项 C 虽然也是德摩根定律，但它是第二种形式。选项 D 是错误的。',
          },
        },
      ],
    },
    // 5. 用户回答
    {
      role: 0,
      conv_id: MOCK_CONV_ID,
      message_id: `msg-${now - 60 * 60000}`,
      contents: [
        {
          type: 'text',
          text: '我选 A。¬(p∧q)↔¬p∨¬q，这是德摩根定律的第一种形式，将合取的否定转化为否定的析取，同时改变了联结词 ∧→∨。',
        },
      ],
    },
    // 6. AI 评价回答
    {
      role: 1,
      conv_id: MOCK_CONV_ID,
      message_id: `msg-${now - 59 * 60000}`,
      contents: [
        {
          type: 'text',
          text: `✅ **回答正确！**

你对德摩根定律的理解很到位。补充几个要点：

### 德摩根定律的本质

德摩根定律揭示了 **否定（¬）** 与 **合取（∧）/ 析取（∨）** 之间的对偶关系：

- 合取的否定 → 否定的析取：$\\neg(p \\land q) \\Leftrightarrow \\neg p \\lor \\neg q$
- 析取的否定 → 否定的合取：$\\neg(p \\lor q) \\Leftrightarrow \\neg p \\land \\neg q$

> 注意：否定符号从"外层"移到"内层"时，**联结词必须取反**（∧ 变 ∨，∨ 变 ∧）。

### 记忆口诀

> **"长横变短，联结词反"** —— 长的否定号拆成短的分别作用于每个命题，同时联结词取反。

这在化简复杂公式时非常有用，继续加油！💪`,
        },
      ],
    },
    // 7. 用户追问
    {
      role: 0,
      conv_id: MOCK_CONV_ID,
      message_id: `msg-${now - 30 * 60000}`,
      contents: [
        {
          type: 'text',
          text: '范式和等值演算有什么关系？求范式的过程就是在做等值演算吗？',
        },
      ],
    },
    // 8. AI 解释
    {
      role: 1,
      conv_id: MOCK_CONV_ID,
      message_id: `msg-${now - 29 * 60000}`,
      contents: [
        {
          type: 'text',
          text: `## 范式与等值演算的关系

是的，**求范式的过程本质上就是等值演算**。

### 核心关系

范式（Normal Form）是命题公式的**标准形式**。将任意公式化为范式的步骤，就是反复使用等值式进行替换：

1. **消去 → 和 ↔**
   - 用蕴含等值式：$p \\rightarrow q \\Leftrightarrow \\neg p \\lor q$
   - 用双条件等值式：$p \\leftrightarrow q \\Leftrightarrow (p \\rightarrow q) \\land (q \\rightarrow p)$

2. **否定号内移**（利用德摩根律）
   - $\\neg(p \\land q) \\Rightarrow \\neg p \\lor \\neg q$

3. **利用分配律展开**
   - 合取范式：用 $\\lor$ 对 $\\land$ 分配
   - 析取范式：用 $\\land$ 对 $\\lor$ 分配

### 举例

将 $(p \\rightarrow q) \\land r$ 化为析取范式：

$$
(p \\rightarrow q) \\land q \\Leftrightarrow (\\neg p \\lor q) \\land q \\Leftrightarrow (\\neg p \\land q) \\lor q
$$

每一步都是在用等值式做替换，这就是**等值演算**。

### 总结

| 概念 | 关系 |
|------|------|
| 等值演算 | **工具/方法** |
| 范式 | **目标/结果** |

> 等值演算是手段，范式是目的。掌握等值演算是求范式的前提条件。`,
        },
      ],
    },
    // 9. 用户请求更多练习
    {
      role: 0,
      conv_id: MOCK_CONV_ID,
      message_id: `msg-${now - 10 * 60000}`,
      contents: [
        {
          type: 'text',
          text: '能不能再给我出一道关于主析取范式的练习题？',
        },
      ],
    },
    // 10. AI 出第二道题
    {
      role: 1,
      conv_id: MOCK_CONV_ID,
      message_id: `msg-${now - 9 * 60000}`,
      contents: [
        {
          type: 'text',
          text: '好的，试试这道关于主析取范式的题目：\n',
        },
        {
          type: 'question_option',
          question_option: {
            questionType: 'single',
            title: '主析取范式',
            content: '公式 p→q 的主析取范式是以下哪一个？（设命题变元为 p, q）',
            options: ['A. (¬p∧¬q)∨(¬p∧q)∨(p∧q)', 'B. (p∧¬q)∨(¬p∧q)', 'C. (¬p∧q)∨(p∧q)', 'D. (¬p∧¬q)∨(p∧q)'],
            answer: ['A. (¬p∧¬q)∨(¬p∧q)∨(p∧q)'],
            explanation:
              '方法一：等值演算法\n\np→q\n⇔ ¬p∨q\n⇔ (¬p∧(q∨¬q))∨((p∨¬p)∧q) （补项）\n⇔ (¬p∧q)∨(¬p∧¬q)∨(p∧q)∨(¬p∧q)\n⇔ (¬p∧¬q)∨(¬p∧q)∨(p∧q)\n\n方法二：真值表法\n\np→q 仅在 p=1, q=0 时为假，其余三种赋值均为真，对应三个极小项：\n- 00 → ¬p∧¬q (m₀)\n- 01 → ¬p∧q  (m₁)\n- 11 → p∧q   (m₃)\n\n因此主析取范式为 m₀∨m₁∨m₃。',
          },
        },
      ],
    },
  ]
}
