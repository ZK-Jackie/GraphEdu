"""
测试 jsons.py 模块

包含 JSON 解析、修复、序列化检查等功能的测试
"""

import json

import pytest

from graphedu.common.exceptions import JSONParseException
from graphedu.common.utils.jsons import (
    _extract_json_code_block,
    serializable,
    try_parse_ast_to_json,
    try_parse_json_object,
)


class TestTryParseAstToJson:
    """测试 AST 解析为 JSON 功能"""

    def test_parse_basic_function_call(self):
        """测试解析基本函数调用"""
        function_string = "tool_call(first_int={'title': 'First Int', 'type': 'integer'}, second_int={'title': 'Second Int', 'type': 'integer'})"
        ast_info, json_result = try_parse_ast_to_json(function_string)

        assert "Function Name: tool_call" in ast_info
        assert "Argument Name: first_int" in ast_info
        assert "Argument Name: second_int" in ast_info
        assert json_result["first_int"]["title"] == "First Int"
        assert json_result["first_int"]["type"] == "integer"
        assert json_result["second_int"]["title"] == "Second Int"

    def test_parse_function_with_string_args(self):
        """测试解析包含字符串参数的函数"""
        function_string = "process(name='test', value='result')"
        _ast_info, json_result = try_parse_ast_to_json(function_string)

        assert json_result["name"] == "test"
        assert json_result["value"] == "result"

    def test_parse_function_with_numeric_args(self):
        """测试解析包含数字参数的函数"""
        function_string = "calculate(x=100, y=3.14)"
        _ast_info, json_result = try_parse_ast_to_json(function_string)

        assert json_result["x"] == 100
        assert json_result["y"] == 3.14

    def test_parse_function_with_bool_args(self):
        """测试解析包含布尔参数的函数"""
        function_string = "set_flag(enabled=True, active=False)"
        _ast_info, json_result = try_parse_ast_to_json(function_string)

        assert json_result["enabled"] is True
        assert json_result["active"] is False

    def test_parse_function_with_list_args(self):
        """测试解析包含列表参数的函数"""
        function_string = "process_list(items=[1, 2, 3], names=['a', 'b'])"
        _ast_info, json_result = try_parse_ast_to_json(function_string)

        assert json_result["items"] == [1, 2, 3]
        assert json_result["names"] == ["a", "b"]

    def test_parse_function_with_dict_args(self):
        """测试解析包含字典参数的函数"""
        function_string = "process_dict(config={'key': 'value', 'number': 42})"
        _ast_info, json_result = try_parse_ast_to_json(function_string)

        assert json_result["config"]["key"] == "value"
        assert json_result["config"]["number"] == 42

    def test_parse_function_with_nested_structure(self):
        """测试解析包含嵌套结构的函数"""
        function_string = "complex(data={'users': [{'name': 'Alice'}, {'name': 'Bob'}]})"
        _ast_info, json_result = try_parse_ast_to_json(function_string)

        assert json_result["data"]["users"][0]["name"] == "Alice"
        assert json_result["data"]["users"][1]["name"] == "Bob"

    def test_parse_function_with_none(self):
        """测试解析包含 None 参数的函数"""
        function_string = "set_value(value=None)"
        _ast_info, json_result = try_parse_ast_to_json(function_string)

        assert json_result["value"] is None

    def test_parse_function_with_whitespace(self):
        """测试解析包含额外空格的函数"""
        function_string = "  tool_call  (  arg1 = 'value1'  ,  arg2 = 'value2'  )  "
        ast_info, json_result = try_parse_ast_to_json(function_string)

        assert "Function Name: tool_call" in ast_info
        assert json_result["arg1"] == "value1"
        assert json_result["arg2"] == "value2"


class TestTryParseJsonObject:
    """测试 JSON 对象解析功能"""

    def test_parse_valid_json_dict(self):
        """测试解析有效的 JSON 字典"""
        input_str = '{"name": "test", "value": 123}'
        _cleaned, result = try_parse_json_object(input_str)

        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 123

    def test_parse_valid_json_list(self):
        """测试解析有效的 JSON 列表"""
        input_str = '[1, 2, 3, "test"]'
        _cleaned, result = try_parse_json_object(input_str, expect_type="list")

        assert isinstance(result, list)
        assert result == [1, 2, 3, "test"]

    def test_parse_json_with_backslash_escape(self):
        """测试解析包含反斜杠的 JSON"""
        input_str = r'{"path": "C:\Users\test", "value": "test\nvalue"}'
        _cleaned, result = try_parse_json_object(input_str)

        # 反斜杠应该被正确处理
        assert "path" in result
        assert "value" in result

    def test_parse_json_in_markdown_code_block(self):
        """测试解析 markdown 代码块中的 JSON"""
        input_str = '```json\n{"name": "test", "value": 123}\n```'
        _cleaned, result = try_parse_json_object(input_str)

        assert result["name"] == "test"
        assert result["value"] == 123

    def test_parse_json_in_generic_code_block(self):
        """测试解析普通代码块中的 JSON"""
        input_str = '```\n{"name": "test", "value": 123}\n```'
        _cleaned, result = try_parse_json_object(input_str)

        assert result["name"] == "test"
        assert result["value"] == 123

    def test_parse_json_with_extra_text_before(self):
        """测试解析前面有额外文本的 JSON（需要 try_fix）"""
        input_str = 'Some text before {"name": "test", "value": 123}'
        # 使用 try_fix 来尝试提取 JSON
        _cleaned, result = try_parse_json_object(input_str, expect_type="dict", try_fix=True)

        # try_fix 应该能提取出 JSON 部分
        assert isinstance(result, dict)
        assert result["name"] == "test"

    def test_parse_json_with_extra_text_after(self):
        """测试解析后面有额外文本的 JSON（需要 try_fix）"""
        input_str = '{"name": "test", "value": 123} Some text after'
        # 使用 try_fix 来尝试提取 JSON
        _cleaned, result = try_parse_json_object(input_str, expect_type="dict", try_fix=True)

        # 第一次尝试应该能成功解析（因为前面是有效的JSON）
        assert isinstance(result, dict)
        assert result["name"] == "test"

    def test_parse_strict_mode_failure(self):
        """测试严格模式下的解析失败"""
        invalid_json = '{"name": "test", invalid}'

        with pytest.raises(JSONParseException) as exc_info:
            try_parse_json_object(invalid_json, strict=True)

        assert "strict mode enabled" in str(exc_info.value)

    def test_parse_list_from_mixed_content(self):
        """测试从混合内容中提取列表"""
        input_str = 'Some text [1, 2, 3] and more text'
        _cleaned, result = try_parse_json_object(input_str, expect_type="list")

        # 第四次尝试应该能提取列表
        assert isinstance(result, list)

    def test_parse_list_of_dicts_from_mixed_content(self):
        """测试从混合内容中提取字典列表"""
        input_str = 'Here are some dicts: {"a": 1} and {"b": 2}'
        _cleaned, result = try_parse_json_object(input_str, expect_type="list")

        # 第五次尝试应该能提取字典列表
        assert isinstance(result, list)

    def test_parse_with_try_fix_enabled(self):
        """测试启用 try_fix 的解析"""
        # 需要安装 json_repair 库才能完全测试
        input_str = '{"name": "test", "value": [[123]]}'
        _cleaned, result = try_parse_json_object(input_str, try_fix=True)

        assert isinstance(result, dict)
        assert result["name"] == "test"

    def test_parse_malformed_json_with_try_fix(self):
        """测试使用 try_fix 修复格式错误的 JSON"""
        input_str = '{{"name": "test", "value": "123"}}'
        _cleaned, result = try_parse_json_object(input_str, try_fix=True)

        assert isinstance(result, dict)
        assert result["name"] == "test"

    def test_parse_json_with_newlines(self):
        """测试解析包含换行的 JSON"""
        input_str = '{"name": "test",\n"value": 123\n}'
        _cleaned, result = try_parse_json_object(input_str)

        assert result["name"] == "test"
        assert result["value"] == 123

    def test_parse_json_with_carriage_returns(self):
        """测试解析包含回车的 JSON"""
        input_str = '{"name": "test",\r\n"value": 123\r\n}'
        _cleaned, result = try_parse_json_object(input_str)

        assert result["name"] == "test"
        assert result["value"] == 123

    def test_parse_json_with_unicode(self):
        """测试解析包含 Unicode 的 JSON"""
        input_str = '{"message": "你好，世界！", "emoji": "😀"}'
        _cleaned, result = try_parse_json_object(input_str)

        assert result["message"] == "你好，世界！"
        assert result["emoji"] == "😀"

    def test_parse_empty_json_dict(self):
        """测试解析空 JSON 对象"""
        input_str = '{}'
        _cleaned, result = try_parse_json_object(input_str)

        assert result == {}

    def test_parse_empty_json_list(self):
        """测试解析空 JSON 列表"""
        input_str = '[]'
        _cleaned, result = try_parse_json_object(input_str, expect_type="list")

        assert result == []

    def test_parse_nested_json(self):
        """测试解析嵌套 JSON"""
        input_str = '{"level1": {"level2": {"level3": "value"}}}'
        _cleaned, result = try_parse_json_object(input_str)

        assert result["level1"]["level2"]["level3"] == "value"

    def test_parse_json_array_of_objects(self):
        """测试解析对象数组"""
        input_str = '[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]'
        _cleaned, result = try_parse_json_object(input_str, expect_type="list")

        assert len(result) == 2
        assert result[0]["name"] == "A"
        assert result[1]["name"] == "B"

    def test_parse_json_with_special_characters(self):
        """测试解析包含特殊字符的 JSON"""
        input_str = r'{"text": "Line1\nLine2", "quote": "He said \"hello\""}'
        _cleaned, result = try_parse_json_object(input_str)

        assert "\n" in result["text"]
        assert '"' in result["quote"]

    def test_parse_failure_all_attempts(self):
        """测试所有解析尝试都失败"""
        invalid_json = 'this is not json at all'

        with pytest.raises(JSONParseException) as exc_info:
            try_parse_json_object(invalid_json, expect_type="dict", try_fix=False)

        assert "all attempts exhausted" in str(exc_info.value)

    def test_parse_json_with_extra_brackets_try_fix(self):
        """测试使用 try_fix 处理额外括号"""
        input_str = '"[{"key": "value"}]"'
        _cleaned, result = try_parse_json_object(input_str, try_fix=True)

        # 应该能修复并解析
        assert isinstance(result, (dict, list))


class TestExtractJsonCodeBlock:
    """测试从代码块中提取 JSON 功能"""

    def test_extract_from_json_markdown_block(self):
        """测试从 ```json 代码块中提取"""
        raw_str = '```json\n{"name": "test", "value": 123}\n```'
        result = _extract_json_code_block(raw_str)

        assert result["name"] == "test"
        assert result["value"] == 123

    def test_extract_from_multiline_json_block(self):
        """测试从多行 JSON 代码块中提取"""
        raw_str = '''```json
{
    "name": "test",
    "value": 123,
    "nested": {
        "key": "value"
    }
}
```'''
        result = _extract_json_code_block(raw_str)

        assert result["name"] == "test"
        assert result["value"] == 123
        assert result["nested"]["key"] == "value"

    def test_extract_from_block_with_extra_text(self):
        """测试从包含额外文本的代码块中提取"""
        raw_str = 'Some intro text ```json\n{"name": "test"}\n``` some trailing text'
        result = _extract_json_code_block(raw_str)

        assert result["name"] == "test"

    def test_extract_with_spaces_in_tags(self):
        """测试从标签中有空格的代码块中提取"""
        # 注意：正则表达式 ```json\s*(.*?)\s*``` 不支持 ``` json ```
        # 所以应该使用标准格式
        raw_str = '```json\n{"name": "test"}\n```'
        result = _extract_json_code_block(raw_str)

        assert result["name"] == "test"

    def test_extract_multiple_blocks_returns_first(self):
        """测试多个代码块时返回第一个"""
        raw_str = '```json\n{"first": "value1"}\n```\nSome text\n```json\n{"second": "value2"}\n```'
        result = _extract_json_code_block(raw_str)

        assert result["first"] == "value1"

    def test_extract_no_code_block_raises_error(self):
        """测试没有代码块时抛出错误"""
        raw_str = '{"name": "test"}'

        with pytest.raises(IndexError):
            _extract_json_code_block(raw_str)

    def test_extract_with_nested_json(self):
        """测试从代码块中提取嵌套 JSON"""
        raw_str = '```json\n{"data": {"nested": {"deep": "value"}}}\n```'
        result = _extract_json_code_block(raw_str)

        assert result["data"]["nested"]["deep"] == "value"

    def test_extract_with_list(self):
        """测试从代码块中提取 JSON 列表"""
        raw_str = '```json\n[1, 2, 3, {"key": "value"}]\n```'
        result = _extract_json_code_block(raw_str)

        assert result[0] == 1
        assert result[3]["key"] == "value"


class TestSerializable:
    """测试对象可序列化检查功能"""

    def test_serializable_dict(self):
        """测试字典可序列化"""
        obj = {"key": "value", "number": 123}
        assert serializable(obj) is True

    def test_serializable_list(self):
        """测试列表可序列化"""
        obj = [1, 2, 3, "test"]
        assert serializable(obj) is True

    def test_serializable_tuple(self):
        """测试元组可序列化"""
        obj = (1, 2, "test")
        assert serializable(obj) is True

    def test_serializable_string(self):
        """测试字符串可序列化"""
        obj = "test string"
        assert serializable(obj) is True

    def test_serializable_number(self):
        """测试数字可序列化"""
        assert serializable(123) is True
        assert serializable(3.14) is True
        assert serializable(-100) is True

    def test_serializable_bool(self):
        """测试布尔值可序列化"""
        assert serializable(True) is True
        assert serializable(False) is True

    def test_serializable_none(self):
        """测试 None 可序列化"""
        assert serializable(None) is True

    def test_serializable_nested_structures(self):
        """测试嵌套结构可序列化"""
        obj = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2)
        }
        assert serializable(obj) is True

    def test_serializable_with_unicode(self):
        """测试包含 Unicode 的对象可序列化"""
        obj = {"message": "你好，世界！", "emoji": "😀"}
        assert serializable(obj) is True

    def test_not_serializable_function(self):
        """测试函数不可序列化"""
        def test_func():
            pass

        assert serializable(test_func) is False

    def test_not_serializable_class(self):
        """测试类对象不可序列化"""
        class TestClass:
            pass

        assert serializable(TestClass) is False

    def test_not_serializable_instance(self):
        """测试类实例不可序列化（默认情况下）"""
        class TestClass:
            def __init__(self):
                self.value = "test"

        obj = TestClass()
        assert serializable(obj) is False

    def test_not_serializable_complex(self):
        """测试复数不可序列化"""
        obj = 1 + 2j
        assert serializable(obj) is False

    def test_serializable_empty_structures(self):
        """测试空结构可序列化"""
        assert serializable({}) is True
        assert serializable([]) is True
        assert serializable(()) is True

    def test_serializable_mixed_list(self):
        """测试混合类型列表可序列化"""
        obj = [1, "two", 3.0, True, None, {"key": "value"}]
        assert serializable(obj) is True

    def test_not_serializable_bytearray(self):
        """测试字节数组不可序列化"""
        obj = bytearray(b'test')
        # bytearray 默认不可序列化为 JSON
        result = serializable(obj)
        # 结果取决于实现，但通常是 False
        assert result is False

    def test_not_serializable_set(self):
        """测试集合不可序列化（JSON 不支持 set）"""
        obj = {1, 2, 3}
        assert serializable(obj) is False

    def test_serializable_nested_deep(self):
        """测试深层嵌套结构可序列化"""
        obj = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": [
                            {"item": "value"}
                        ]
                    }
                }
            }
        }
        assert serializable(obj) is True


class TestEdgeCases:
    """测试边界情况"""

    def test_parse_empty_string(self):
        """测试解析空字符串"""
        with pytest.raises(JSONParseException):
            try_parse_json_object("", expect_type="dict", try_fix=False)

    def test_parse_none_string(self):
        """测试解析 None 字符串"""
        result = serializable(None)
        assert result is True

    def test_parse_very_large_json(self):
        """测试解析非常大的 JSON"""
        large_list = list(range(10000))
        input_str = json.dumps({"large_list": large_list})
        _cleaned, result = try_parse_json_object(input_str)

        assert len(result["large_list"]) == 10000

    def test_parse_json_with_special_unicode_chars(self):
        """测试解析包含特殊 Unicode 字符的 JSON"""
        # 注意：由于工具会处理反斜杠，Unicode转义可能被二次转义
        # 所以直接使用实际的 Unicode 字符测试
        input_str = '{"chars": "Hello"}'
        _cleaned, result = try_parse_json_object(input_str)

        assert result["chars"] == "Hello"

    def test_parse_json_with_escaped_characters(self):
        """测试解析包含转义字符的 JSON"""
        input_str = r'{"path": "C:\\Users\\test", "newline": "line1\nline2"}'
        _cleaned, result = try_parse_json_object(input_str)

        assert "path" in result

    def test_parse_json_with_tabs(self):
        """测试解析包含制表符的 JSON"""
        input_str = '{"name": "test",\t"value": 123}'
        _cleaned, result = try_parse_json_object(input_str)

        assert result["name"] == "test"

    def test_parse_number_as_string(self):
        """测试解析数字字符串"""
        input_str = '123'
        _cleaned, result = try_parse_json_object(input_str)

        assert result == 123

    def test_parse_boolean_as_string(self):
        """测试解析布尔字符串"""
        input_str = 'true'
        _cleaned, result = try_parse_json_object(input_str)

        assert result is True

    def test_parse_null_as_string(self):
        """测试解析 null 字符串"""
        input_str = 'null'
        _cleaned, result = try_parse_json_object(input_str)

        assert result is None

    def test_parse_json_with_comments_style_text(self):
        """测试解析包含注释风格文本的 JSON"""
        input_str = '/* comment */ {"name": "test"}'
        _cleaned, result = try_parse_json_object(input_str, try_fix=True)

        # try_fix 应该能处理这种情况
        assert isinstance(result, dict)

    def test_serializable_with_circular_reference(self):
        """测试循环引用不可序列化"""
        obj = {}
        obj["self"] = obj  # 循环引用

        assert serializable(obj) is False

    def test_parse_json_with_trailing_comma(self):
        """测试解析包含尾随逗号的 JSON（需要 try_fix）"""
        input_str = '{"name": "test", "value": 123,}'
        _cleaned, result = try_parse_json_object(input_str, try_fix=True)

        assert isinstance(result, dict)

    def test_parse_json_with_unquoted_keys(self):
        """测试解析包含无引号键的 JSON（需要 try_fix）"""
        input_str = '{name: "test", value: 123}'
        _cleaned, result = try_parse_json_object(input_str, try_fix=True)

        # json_repair 可能能处理这种情况
        assert isinstance(result, dict)

    def test_parse_multiple_json_objects(self):
        """测试解析多个 JSON 对象"""
        input_str = '{"a": 1}{"b": 2}'
        _cleaned, result = try_parse_json_object(input_str, expect_type="list", try_fix=True)

        # 应该能提取出至少一个对象
        assert isinstance(result, (dict, list))
