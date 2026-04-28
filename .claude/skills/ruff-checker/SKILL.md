---
name: ruff-checker
description: Python 代码质量检查和自动修复工具，使用 Ruff 进行代码检查、linting 和格式化。在以下场景触发：(1) 用户要求检查代码质量或运行 linter，(2) 用户要求修复代码风格问题，(3) 用户提到 ruff、代码检查、lint 等，(4) 准备提交代码前进行质量检查。支持智能问题分类、自动修复安全问题和交互式处理风险问题。
---

# Ruff 代码检查和修复

## 快速开始

### 基本检查

对当前项目运行 ruff 检查：

```bash
ruff check .
```

对特定文件或目录：

```bash
ruff check path/to/file.py
ruff check path/to/directory/
```

### 自动修复

**安全修复**（可以自动运行）：
```bash
ruff check --fix .
```

**选择性修复**（需要检查风险）：
```bash
# 预览将要修复的内容
ruff check --fix --preview .
```

### 格式化代码

```bash
ruff format .
```

## 工作流程

### 1. 初始化阶段

- 检查项目根目录是否存在 `pyproject.toml` 或 `ruff.toml`
- 如果不存在，询问用户是否创建默认配置
- 推荐配置：使用项目标准设置（line-length=88，target-version=py311）

### 2. 运行检查

使用以下命令获取完整报告：

```bash
ruff check --output-format=json > ruff-report.json
```

解析 JSON 输出以：
- 统计问题总数
- 按严重程度分类（Error、Warning、Info）
- 识别可以自动修复的问题

### 3. 智能问题分类

根据错误代码判断处理方式：

**自动修复（安全）**：
- 格式化问题（E、W 系列大部分）
- 未使用导入（F401）
- 简单语法问题（F 系列大部分）
- 排序问题（I）

**需要询问（风险）**：
- 重构建议（PLR、PERF）
- 类型相关（T、FA）
- 可能改变语义的修复（RUF 规则子集）
- 删除可能被使用的代码

**始终询问（高风险）**：
- 复杂重构建议（PLR0913, PLR2004 等）
- 性能优化可能影响可读性
- 涉及多文件修改的建议

### 4. 修复流程

对于自动修复类别：
```bash
ruff check --fix .
```

对于需要询问的类别：
1. 显示问题描述和位置
2. 使用 `AskUserQuestion` 询问是否修复
3. 如果用户同意，运行修复

### 5. 验证结果

修复后再次运行检查确认：
```bash
ruff check .
```

## 常见场景

### 场景 1: 提交前检查

```bash
# 检查所有变更
git diff --name-only --cached | grep '\.py$' | xargs ruff check

# 自动修复可修复的问题
git diff --name-only --cached | grep '\.py$' | xargs ruff check --fix
```

### 场景 2: 特定规则检查

只检查特定规则：
```bash
ruff check --select F401,F841 .
```

排除特定规则：
```bash
ruff check --ignore F401 .
```

### 场景 3: 修复失败处理

如果自动修复失败：
1. 显示错误信息和位置
2. 尝试手动修复该文件
3. 如果无法确定，询问用户偏好

常见失败原因：
- 语法错误（需要先修复语法）
- 上下文复杂（需要人工判断）
- 多文件依赖（需要全局分析）

## Ruff 规则参考

当需要了解特定规则时，查阅 [RULES.md](references/RULES.md) 获取：
- 完整规则列表
- 规则严重程度分类
- 自动修复安全性说明

## 故障排除

修复过程中的常见问题处理方案参见 [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md)。