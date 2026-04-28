#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ruff 问题分类器
解析 ruff 输出并按风险级别分类问题
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# 设置标准输出编码为 UTF-8（Windows 兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# 规则分类
SAFE_AUTO_FIX = {
    # 格式化
    "E", "W",
    # 导入
    "F401", "F403", "I",
    # 简单语法
    "F841", "F821", "F601", "F811",
}

ASK_USER_FIX = {
    # 重构
    "PLR", "PERF",
    # 类型
    "T", "FA",
    # 部分复杂规则
    "RUF017", "RUF019", "RUF015",
}

ALWAYS_ASK = {
    "PLR0912",  # 分支过多
    "PLR0911",  # 返回语句过多
    "C901",     # 函数过于复杂
    "UP",       # 语法升级
}


def classify_issue(issue: Dict) -> str:
    """
    分类单个问题

    返回: "safe", "ask", "always_ask"
    """
    code = issue.get("code", "")

    # 检查是否在始终询问列表
    if any(code.startswith(prefix) for prefix in ALWAYS_ASK):
        return "always_ask"

    # 检查是否在需要询问列表
    if any(code.startswith(prefix) for prefix in ASK_USER_FIX):
        return "ask"

    # 检查是否安全
    if code in SAFE_AUTO_FIX or any(code.startswith(prefix) for prefix in ["E", "W", "I"]):
        return "safe"

    # 默认需要询问
    return "ask"


def parse_ruff_output(json_file: str) -> List[Dict]:
    """解析 ruff JSON 输出"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {json_file}")
        return []
    except json.JSONDecodeError:
        print(f"错误: JSON 解析失败")
        return []


def print_summary(issues: List[Dict]):
    """打印问题摘要"""
    safe = []
    ask = []
    always_ask = []

    for issue in issues:
        category = classify_issue(issue)
        if category == "safe":
            safe.append(issue)
        elif category == "ask":
            ask.append(issue)
        else:
            always_ask.append(issue)

    print("\n" + "=" * 60)
    print("Ruff 检查结果摘要")
    print("=" * 60)

    print(f"\n✓ 可自动修复（安全）: {len(safe)} 个")
    if safe:
        print(f"  涉及文件: {len(set(i['filename'] for i in safe))} 个")

    print(f"\n⚠ 需要询问（风险）: {len(ask)} 个")
    if ask:
        print(f"  涉及文件: {len(set(i['filename'] for i in ask))} 个")
        # 按规则分组
        by_code = {}
        for issue in ask:
            code = issue['code']
            by_code[code] = by_code.get(code, 0) + 1
        print("  主要问题:")
        for code, count in sorted(by_code.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {code}: {count} 个")

    print(f"\n❌ 始终询问（高风险）: {len(always_ask)} 个")
    if always_ask:
        print(f"  涉及文件: {len(set(i['filename'] for i in always_ask))} 个")

    print(f"\n总计: {len(issues)} 个问题")

    return safe, ask, always_ask


def print_fix_plan(safe: List[Dict], ask: List[Dict], always_ask: List[Dict]):
    """打印修复计划"""
    print("\n" + "=" * 60)
    print("建议修复计划")
    print("=" * 60)

    if safe:
        print(f"\n1. 自动修复 {len(safe)} 个安全问题")
        print("   命令: ruff check --fix .")

    if ask:
        print(f"\n2. 处理 {len(ask)} 个风险问题")
        print("   需要逐个确认")

    if always_ask:
        print(f"\n3. 审查 {len(always_ask)} 个高风险问题")
        print("   需要详细审查")


def export_fixable_files(issues: List[Dict], output_file: str = "fixable_files.txt"):
    """导出可修复的文件列表"""
    fixable = [issue['filename'] for issue in issues if classify_issue(issue) != "always_ask"]
    unique_files = sorted(set(fixable))

    with open(output_file, 'w', encoding='utf-8') as f:
        for filepath in unique_files:
            f.write(filepath + '\n')

    print(f"\n可修复文件列表已导出到: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("用法: python ruff_classifier.py <ruff-json-output.json>")
        print("\n生成 ruff JSON 输出:")
        print("  ruff check --output-format=json > ruff-report.json")
        sys.exit(1)

    json_file = sys.argv[1]
    issues = parse_ruff_output(json_file)

    if not issues:
        print("未发现任何问题！")
        return

    safe, ask, always_ask = print_summary(issues)
    print_fix_plan(safe, ask, always_ask)

    if ask or always_ask:
        export_fixable_files(issues)


if __name__ == "__main__":
    main()
