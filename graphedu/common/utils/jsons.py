# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""JSON parsing and utility functions.

This module provides utilities for parsing JSON with tolerance for malformed input,
including extracting JSON from LLM responses and AST-based parsing.
"""

import ast
import json
import logging
import re
from typing import Any

from ..exceptions import JSONParseException, JSONValidationException

logger = logging.getLogger(__name__)


def try_parse_ast_to_json(function_string: str) -> tuple[str, dict]:
    """Parse a function call string into information and JSON result.

    Example:
        function_string = (
            "tool_call(first_int={'title': 'First Int', 'type': 'integer'}, "
            "second_int={'title': 'Second Int', 'type': 'integer'})"
        )

    Args:
        function_string: Function call string to parse.

    Returns:
        Tuple of (ast_info, json_result) where ast_info is a formatted string
        and json_result is a dictionary of arguments.
    """
    tree = ast.parse(str(function_string).strip())
    ast_info = ""
    json_result = {}
    # 查找函数调用节点并提取信息
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function_name = node.func.id
            args = {kw.arg: kw.value for kw in node.keywords}
            ast_info += f"Function Name: {function_name}\r\n"
            for arg, value in args.items():
                ast_info += f"Argument Name: {arg}\n"
                ast_info += f"Argument Value: {ast.dump(value)}\n"
                json_result[arg] = ast.literal_eval(value)

    return ast_info, json_result


def _find_balanced(text: str, open_char: str = "[", close_char: str = "]") -> str | None:
    """在 text 中找到第一个完整匹配的括号对（平衡嵌套），返回含括号的子串。

    该函数会跳过 JSON 字符串内部的括号字符，避免误匹配。

    Args:
        text: 待搜索的文本
        open_char: 开括号字符
        close_char: 闭括号字符

    Returns:
        匹配到的子串（含括号），未找到返回 None
    """
    start = text.find(open_char)
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False

    for i in range(start, len(text)):
        ch = text[i]

        if escape_next:
            escape_next = False
            continue

        if ch == "\\":
            escape_next = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return None


def try_parse_json_object[ParseT: type[dict | list]](
    input_str: str, expect_type: ParseT = dict, strict: bool = False, try_fix: bool = False
) -> tuple[str, ParseT | None]:
    """JSON cleaning and formatting utilities."""
    # Sentinel value to indicate parsing hasn't succeeded yet
    UNPARSED = object()  # noqa: N806

    # Sometimes, the LLM returns a json string with some extra description, this function will clean it up.
    # 使用正则表达式找到需要转义的反斜杠
    input_str = re.sub(r'(?<!\\)\\(?!["\\/n])', r"\\\\", input_str)
    #  first try
    result = UNPARSED
    try:
        # Try parse first
        result = json.loads(input_str)
    except json.JSONDecodeError:
        logger.debug("Warning: Error decoding faulty json - 1/5")
    if result is not UNPARSED:
        return input_str, result
    if strict:
        raise JSONParseException("输出解析失败 - strict mode enabled", input_str=input_str, attempt=1)

    # second try
    result = UNPARSED
    try:
        result = json.loads(input_str.split("```")[1])
    except Exception as e:
        logger.debug("Warning: Error decoding faulty json - 2/5 - %s", e)
    if result is not UNPARSED:
        return input_str, result

    # third try
    result = UNPARSED
    try:
        result = _extract_json_code_block(input_str)
    except Exception as e:
        logger.debug("Warning: Error decoding faulty json - 3/5 - %s", e)
    if result is not UNPARSED:
        return json.dumps(result, ensure_ascii=False), result

    # forth try: 使用平衡括号提取完整的 [...] JSON 数组
    if expect_type is list:
        result = UNPARSED
        try:
            bracket_str = _find_balanced(input_str, "[", "]")
            if bracket_str:
                result = json.loads(bracket_str)
        except Exception as e:
            logger.debug("Warning: Error decoding faulty json - 4/5 - %s", e)
        if result is not UNPARSED:
            return json.dumps(result, ensure_ascii=False), result

    # fifth try: 使用平衡括号逐个提取 {...}，再组装为列表
    if expect_type is list:
        result = UNPARSED
        try:
            dict_objects: list[dict] = []
            remaining = input_str
            while True:
                obj_str = _find_balanced(remaining, "{", "}")
                if obj_str is None:
                    break
                try:
                    obj = json.loads(obj_str)
                    if isinstance(obj, dict):
                        dict_objects.append(obj)
                except Exception:
                    pass
                # 移动到本次匹配之后继续搜索
                remaining = remaining[remaining.index(obj_str) + len(obj_str) :]
            result = dict_objects
        except Exception as e:
            logger.warning("Error decoding faulty json, attempting repair - 5/5 - %s", e)
        if result is not UNPARSED:
            return json.dumps(result, ensure_ascii=False), result

    if try_fix:
        result = UNPARSED
        # repair json
        pattern_ = r"\{(.*)\}"
        match_ = re.search(pattern_, input_str)
        input_str = "{" + match_.group(1) + "}" if match_ else input_str

        # Clean up json string.
        input_str = (
            input_str.replace("{{", "{")
            .replace("}}", "}")
            .replace('"[{', "[{")
            .replace('}]"', "}]")
            .replace("\\", " ")
            .replace("\\n", " ")
            .replace("\n", " ")
            .replace("\r", "")
            .strip()
        )

        # Remove JSON Markdown Frame
        if input_str.startswith("```"):
            input_str = input_str[len("```") :]
        if input_str.startswith("```json"):
            input_str = input_str[len("```json") :]
        if input_str.endswith("```"):
            input_str = input_str[: len(input_str) - len("```")]

        try:
            result = json.loads(input_str)
        except json.JSONDecodeError:
            # Fixup potentially malformed json string using json_repair.
            from json_repair import repair_json

            json_info = str(repair_json(json_str=input_str, return_objects=False, ensure_ascii=False))

            # Generate JSON-string output using best-attempt prompting & parsing techniques.
            try:
                if len(json_info) < len(input_str):
                    json_info, result = try_parse_ast_to_json(input_str)
                else:
                    result = json.loads(json_info)

            except json.JSONDecodeError:
                logger.exception("error loading json, json=%s", input_str)
                raise JSONParseException(
                    "Failed to parse JSON after repair",
                    input_str=input_str,
                    attempt=5,
                    reason="JSONDecodeError after repair",
                ) from None
            else:
                expected_cls = dict if expect_type is dict else list
                if not isinstance(result, expected_cls):
                    logger.exception(
                        "not expected type. expected=%s, got=%s:", expected_cls.__name__, type(result).__name__
                    )
                    raise JSONValidationException(
                        f"Expected {expected_cls.__name__} type but got {type(result).__name__}",
                        json_obj=result,
                        expected_type=expected_cls.__name__,
                        actual_type=type(result).__name__,
                    )
                return json_info, result
        else:
            return input_str, result

    # If all attempts fail, raise an exception
    if result is UNPARSED:
        raise JSONParseException(
            "输出解析失败 - all attempts exhausted",
            input_str=input_str,
            attempt=5,
            reason="No parsing strategy succeeded",
        )
    return input_str, None


def _extract_json_code_block(raw_str: str):
    # Regular expression to match ```json ... ```
    pattern = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL)
    # Find all matches
    matches = pattern.findall(raw_str)
    return json.loads(matches[0])


def serializable(obj: Any) -> bool:
    """Check if an object is JSON serializable.

    Args:
        obj: Any object to check.

    Returns:
        True if the object is JSON serializable, False otherwise.
    """
    try:
        json.dumps(obj)
        return True
    except Exception as e:
        logger.debug(f"{obj} is not serializable. {e}")
        return False
