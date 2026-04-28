"""
测试 graphedu.common.utils.objects 模块
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Union

import pytest

from graphedu.common.utils.objects import (
    cp_dict_attr,
    get_class,
    get_specific_class_from_union,
    import_from_string,
    is_primitive_object,
    is_primitive_type,
)

# ==================== 测试 cp_dict_attr ====================

class TestObject:
    """测试用的简单类"""
    pass


def test_cp_dict_attr_single_attribute():
    """测试复制单个属性"""
    obj = TestObject()
    d = {'name': 'Alice'}
    result = cp_dict_attr(d, obj)

    assert result is obj
    assert obj.name == 'Alice'


def test_cp_dict_attr_multiple_attributes():
    """测试复制多个属性"""
    obj = TestObject()
    d = {'name': 'Bob', 'age': 25, 'city': 'Beijing'}
    cp_dict_attr(d, obj)

    assert obj.name == 'Bob'
    assert obj.age == 25
    assert obj.city == 'Beijing'


def test_cp_dict_attr_empty_dict():
    """测试空字典"""
    obj = TestObject()
    d = {}
    result = cp_dict_attr(d, obj)

    assert result is obj


def test_cp_dict_attr_with_none_value():
    """测试属性值为 None"""
    obj = TestObject()
    d = {'name': None, 'age': 0}
    cp_dict_attr(d, obj)

    assert obj.name is None
    assert obj.age == 0


def test_cp_dict_attr_with_complex_types():
    """测试复杂类型的属性值"""
    obj = TestObject()
    d = {
        'list': [1, 2, 3],
        'dict': {'key': 'value'},
        'nested': {'a': {'b': 'c'}},
        'datetime': datetime(2024, 1, 1),
    }
    cp_dict_attr(d, obj)

    assert obj.list == [1, 2, 3]
    assert obj.dict == {'key': 'value'}
    assert obj.nested == {'a': {'b': 'c'}}
    assert obj.datetime == datetime(2024, 1, 1)


def test_cp_dict_attr_overwrites_existing():
    """测试覆盖已存在的属性"""
    obj = TestObject()
    obj.name = 'OldName'
    d = {'name': 'NewName'}
    cp_dict_attr(d, obj)

    assert obj.name == 'NewName'


# ==================== 测试 is_primitive_object ====================

def test_is_primitive_object_string():
    """测试字符串对象"""
    assert is_primitive_object("hello") is True
    assert is_primitive_object("") is True


def test_is_primitive_object_integer():
    """测试整数对象"""
    assert is_primitive_object(42) is True
    assert is_primitive_object(0) is True
    assert is_primitive_object(-100) is True


def test_is_primitive_object_float():
    """测试浮点数对象"""
    assert is_primitive_object(3.14) is True
    assert is_primitive_object(0.0) is True
    assert is_primitive_object(-2.5) is True


def test_is_primitive_object_bool():
    """测试布尔对象"""
    assert is_primitive_object(True) is True
    assert is_primitive_object(False) is True


def test_is_primitive_object_datetime():
    """测试 datetime 对象"""
    assert is_primitive_object(datetime(2024, 1, 1)) is True
    assert is_primitive_object(datetime.now()) is True


def test_is_primitive_object_date():
    """测试 date 对象"""
    assert is_primitive_object(date(2024, 1, 1)) is True
    assert is_primitive_object(date.today()) is True


def test_is_primitive_object_decimal():
    """测试 Decimal 对象"""
    assert is_primitive_object(Decimal('10.5')) is True
    assert is_primitive_object(Decimal('0')) is True


def test_is_primitive_object_bytes():
    """测试 bytes 对象"""
    assert is_primitive_object(b'hello') is True
    assert is_primitive_object(b'') is True


def test_is_primitive_object_none():
    """测试 None 对象"""
    assert is_primitive_object(None) is True


def test_is_primitive_object_list():
    """测试列表对象（非原始类型）"""
    assert is_primitive_object([1, 2, 3]) is False
    assert is_primitive_object([]) is False


def test_is_primitive_object_dict():
    """测试字典对象（非原始类型）"""
    assert is_primitive_object({'key': 'value'}) is False
    assert is_primitive_object({}) is False


def test_is_primitive_object_set():
    """测试集合对象（非原始类型）"""
    assert is_primitive_object({1, 2, 3}) is False
    assert is_primitive_object(set()) is False


def test_is_primitive_object_custom_class():
    """测试自定义类对象（非原始类型）"""
    assert is_primitive_object(TestObject()) is False


def test_is_primitive_object_tuple():
    """测试元组对象（非原始类型）"""
    assert is_primitive_object((1, 2, 3)) is False


# ==================== 测试 is_primitive_type ====================

def test_is_primitive_type_string():
    """测试字符串类型"""
    assert is_primitive_type(str) is True


def test_is_primitive_type_integer():
    """测试整数类型"""
    assert is_primitive_type(int) is True


def test_is_primitive_type_float():
    """测试浮点数类型"""
    assert is_primitive_type(float) is True


def test_is_primitive_type_bool():
    """测试布尔类型"""
    assert is_primitive_type(bool) is True


def test_is_primitive_type_datetime():
    """测试 datetime 类型"""
    assert is_primitive_type(datetime) is True


def test_is_primitive_type_date():
    """测试 date 类型"""
    assert is_primitive_type(date) is True


def test_is_primitive_type_decimal():
    """测试 Decimal 类型"""
    assert is_primitive_type(Decimal) is True


def test_is_primitive_type_none():
    """测试 None 类型"""
    assert is_primitive_type(type(None)) is True


def test_is_primitive_type_bytes():
    """测试 bytes 类型"""
    assert is_primitive_type(bytes) is True


def test_is_primitive_type_list():
    """测试列表类型（非原始类型）"""
    assert is_primitive_type(list) is False


def test_is_primitive_type_dict():
    """测试字典类型（非原始类型）"""
    assert is_primitive_type(dict) is False


def test_is_primitive_type_set():
    """测试集合类型（非原始类型）"""
    assert is_primitive_type(set) is False


def test_is_primitive_type_custom_class():
    """测试自定义类类型（非原始类型）"""
    assert is_primitive_type(TestObject) is False


def test_is_primitive_type_union_all_primitives():
    """测试 Union 类型，全部为原始类型"""
    assert is_primitive_type(Union[int, str]) is True
    assert is_primitive_type(Union[int, str, float, bool]) is True


def test_is_primitive_type_union_with_non_primitive():
    """测试 Union 类型，包含非原始类型"""
    assert is_primitive_type(Union[int, list]) is False
    assert is_primitive_type(Union[int, str, dict]) is False
    assert is_primitive_type(Union[str, TestObject]) is False


def test_is_primitive_type_optional():
    """测试 Optional 类型"""
    # Optional[int] 等同于 Union[int, None]
    assert is_primitive_type(Optional[int]) is True
    assert is_primitive_type(Optional[str]) is True
    assert is_primitive_type(Optional[list]) is False


def test_is_primitive_type_union_pipe_syntax():
    """测试 Python 3.10+ 的 | 语法"""
    # int | str
    assert is_primitive_type(int | str) is True
    # int | None
    assert is_primitive_type(int | None) is True
    # str | list
    assert is_primitive_type(str | list) is False


def test_is_primitive_type_list_generic():
    """测试泛型列表类型"""
    assert is_primitive_type(list[int]) is False
    assert is_primitive_type(list[str]) is False


def test_is_primitive_type_dict_generic():
    """测试泛型字典类型"""
    assert is_primitive_type(dict[str, int]) is False
    assert is_primitive_type(dict[str, str]) is False


# ==================== 测试 get_class ====================

def test_get_class_simple_type():
    """测试简单类型"""
    assert get_class(int) is int
    assert get_class(str) is str
    assert get_class(TestObject) is TestObject


def test_get_class_list_type():
    """测试列表类型"""
    assert get_class(list) is list
    assert get_class(list[int]) is list
    assert get_class(list[str]) is list


def test_get_class_dict_type():
    """测试字典类型"""
    assert get_class(dict) is dict
    assert get_class(dict[str, int]) is dict


def test_get_class_union_type():
    """测试 Union 类型"""
    assert get_class(Union[int, str]) is Union


def test_get_class_optional_type():
    """测试 Optional 类型"""
    assert get_class(Optional[int]) is Union


# ==================== 测试 get_specific_class_from_union ====================

def test_get_specific_class_from_union_int():
    """测试从 Union 中获取 int 类型"""
    assert get_specific_class_from_union(Union[int, str], int) is int
    assert get_specific_class_from_union(Union[int, str], object) is int


def test_get_specific_class_from_union_str():
    """测试从 Union 中获取 str 类型"""
    assert get_specific_class_from_union(Union[int, str], str) is str


def test_get_specific_class_from_union_with_none():
    """测试从 Union[int, None] 中获取 int 类型"""
    assert get_specific_class_from_union(Union[int, None], int) is int
    assert get_specific_class_from_union(int | None, int) is int


def test_get_specific_class_from_union_multiple():
    """测试从多个类型的 Union 中获取指定类型"""
    assert get_specific_class_from_union(Union[int, str, float], int) is int
    assert get_specific_class_from_union(Union[int, str, float], str) is str
    assert get_specific_class_from_union(Union[int, str, float], float) is float


def test_get_specific_class_from_union_custom_class():
    """测试从 Union 中获取自定义类"""
    assert get_specific_class_from_union(Union[int, TestObject], TestObject) is TestObject
    assert get_specific_class_from_union(Union[str, TestObject], TestObject) is TestObject


def test_get_specific_class_from_union_no_match():
    """测试 Union 中没有匹配的类型"""
    # 当没有匹配的类型时，函数返回 None
    result = get_specific_class_from_union(Union[int, str], list)
    assert result is None

    result = get_specific_class_from_union(Union[int, str], dict)
    assert result is None


def test_get_specific_class_from_union_pipe_syntax():
    """测试 Python 3.10+ 的 | 语法"""
    assert get_specific_class_from_union(int | str, int) is int
    assert get_specific_class_from_union(int | str, str) is str
    assert get_specific_class_from_union(int | None, int) is int


def test_get_specific_class_from_union_non_union():
    """测试非 Union 类型"""
    import warnings

    # 测试传入简单类型时返回 None 并发出警告
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = get_specific_class_from_union(int, int)
        assert result is None
        assert len(w) == 1
        assert issubclass(w[0].category, UserWarning)
        assert "不是 Union 类型" in str(w[0].message)

    # 测试传入 str 类型
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = get_specific_class_from_union(str, str)
        assert result is None
        assert len(w) == 1
        assert "不是 Union 类型" in str(w[0].message)

    # 测试传入自定义类
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = get_specific_class_from_union(TestObject, TestObject)
        assert result is None
        assert len(w) == 1
        assert "不是 Union 类型" in str(w[0].message)


# ==================== 测试 import_from_string ====================

def test_import_from_string_builtin_class():
    """测试导入内置类"""
    result = import_from_string('datetime.datetime')
    assert result is datetime

    result = import_from_string('decimal.Decimal')
    assert result is Decimal


def test_import_from_string_custom_class():
    """测试导入自定义类"""
    result = import_from_string('graphedu.common.utils.objects.cp_dict_attr')
    assert result is cp_dict_attr


def test_import_from_string_module():
    """测试导入模块中的函数"""
    result = import_from_string('graphedu.common.utils.objects.is_primitive_object')
    assert result is is_primitive_object


def test_import_from_string_invalid_format_no_dot():
    """测试无效格式：没有点"""
    with pytest.raises(ImportError, match="路径格式错误，必须包含至少一个点"):
        import_from_string('datetime')

    with pytest.raises(ImportError, match="路径格式错误，必须包含至少一个点"):
        import_from_string('')


def test_import_from_string_invalid_module():
    """测试无效的模块路径"""
    with pytest.raises(ModuleNotFoundError):
        import_from_string('nonexistent.module.Class')

    with pytest.raises(ModuleNotFoundError):
        import_from_string('graphedu.nonexistent.module.Class')


def test_import_from_string_invalid_attribute():
    """测试无效的属性名"""
    with pytest.raises(AttributeError):
        import_from_string('datetime.NonExistentClass')

    with pytest.raises(AttributeError):
        import_from_string('graphedu.common.utils.objects.nonexistent_function')


def test_import_from_string_nested_class():
    """测试导入嵌套类"""
    result = import_from_string('unittest.TestCase')
    assert result.__name__ == 'TestCase'


def test_import_from_string_with_submodules():
    """测试导入子模块中的类"""
    result = import_from_string('pytest.raises')
    assert result is pytest.raises
