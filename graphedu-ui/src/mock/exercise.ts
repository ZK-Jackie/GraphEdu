/**
 * 习题记录 Mock 数据
 */
import { seededRandom } from './helpers'

interface ExerciseAttemptVO {
  attemptId: number
  exerciseId: number
  studentId: number
  studentAnswer: string[] | string | null
  isCorrect: boolean | null
  timeSpent: number | null
  attemptTime: string | null
}

const EXERCISE_POOL = [
  {
    exerciseId: 1001,
    question: '命题 p∧q 的真值表中，当 p=T, q=F 时结果为？',
    answer: 'F',
    options: ['T', 'F'],
  },
  {
    exerciseId: 1002,
    question: '集合 A={1,2,3} 的子集个数为？',
    answer: '8',
    options: ['6', '8', '5', '7'],
  },
  {
    exerciseId: 1003,
    question: '等价关系必须满足哪些性质？',
    answer: '自反性、对称性、传递性',
    options: ['仅自反性', '自反性、对称性', '自反性、对称性、传递性'],
  },
  {
    exerciseId: 1004,
    question: '完全二叉树有 n 个叶子节点，则总节点数为？',
    answer: '2n-1',
    options: ['2n', '2n-1', 'n+1', 'n-1'],
  },
  {
    exerciseId: 1005,
    question: '命题 ¬(p∨q) 等值于？',
    answer: '¬p∧¬q',
    options: ['¬p∨¬q', '¬p∧¬q', 'p∧q'],
  },
  {
    exerciseId: 1006,
    question: '从5个元素中取3个的排列数 P(5,3) 为？',
    answer: '60',
    options: ['10', '20', '60', '120'],
  },
  {
    exerciseId: 1007,
    question: '集合 A×B 称为什么运算？',
    answer: '笛卡尔积',
    options: ['交集', '并集', '笛卡尔积'],
  },
  {
    exerciseId: 1008,
    question: '偏序关系中，任意两个元素是否一定可比？',
    answer: '否',
    options: ['是', '否'],
  },
  {
    exerciseId: 1009,
    question: '欧拉回路的条件是？',
    answer: '所有顶点度数为偶数且图连通',
    options: ['所有顶点度数为奇数', '所有顶点度数为偶数且图连通', '图是二部图'],
  },
  {
    exerciseId: 1010,
    question: '命题 p→q 的逆否命题是？',
    answer: '¬q→¬p',
    options: ['q→p', '¬q→¬p', '¬p→¬q'],
  },
]

export function getExerciseAttemptList(): {
  rows: ExerciseAttemptVO[]
  page: number
  size: number
  total: number
} {
  const rand = seededRandom(700)
  const rows: ExerciseAttemptVO[] = EXERCISE_POOL.map((ex, i) => {
    const isCorrect = rand() > 0.35
    const optionsArr = ex.options ?? [ex.answer]
    const wrongOption = optionsArr.filter((o: string) => o !== ex.answer)
    const studentAnswer = isCorrect ? ex.answer : (wrongOption[Math.floor(rand() * wrongOption.length)] ?? ex.answer)

    return {
      attemptId: 60001 + i,
      exerciseId: ex.exerciseId,
      studentId: 10001,
      studentAnswer,
      isCorrect,
      timeSpent: Math.floor(15 + rand() * 180),
      attemptTime: new Date(Date.now() - Math.floor(rand() * 14 * 86400000)).toISOString(),
    }
  })

  // 额外添加 10 条记录凑到 20 条
  for (let i = 10; i < 20; i++) {
    const ex = EXERCISE_POOL[i % EXERCISE_POOL.length]!
    const isCorrect = rand() > 0.4
    const optionsArr = ex.options ?? [ex.answer]
    const wrongOption = optionsArr.filter((o: string) => o !== ex.answer)
    const studentAnswer = isCorrect ? ex.answer : (wrongOption[Math.floor(rand() * wrongOption.length)] ?? ex.answer)

    rows.push({
      attemptId: 60001 + i,
      exerciseId: ex.exerciseId + 100,
      studentId: 10001,
      studentAnswer,
      isCorrect,
      timeSpent: Math.floor(20 + rand() * 240),
      attemptTime: new Date(Date.now() - Math.floor(rand() * 21 * 86400000)).toISOString(),
    })
  }

  return { rows, page: 1, size: 10, total: 20 }
}

export function getExerciseAttemptDetail(attemptId: number): ExerciseAttemptVO | null {
  const allRows = getExerciseAttemptList().rows
  return allRows.find((r) => r.attemptId === attemptId) ?? allRows[0] ?? null
}
