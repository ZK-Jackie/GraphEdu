"""
测试ErrorCode新结构
"""

from graphedu.common.exceptions.services.codes import ErrorCode


def test_error_code_structure():
    """测试错误码元组结构"""
    # 测试错误码和HTTP状态码绑定
    assert ErrorCode.AUTH_TOKEN_EXPIRED.code == "AUTH.10002"
    assert ErrorCode.AUTH_TOKEN_EXPIRED.http_status == 401

    assert ErrorCode.USER_NOT_FOUND.code == "USER.20001"
    assert ErrorCode.USER_NOT_FOUND.http_status == 404

    assert ErrorCode.REGISTER_USERNAME_ALREADY_EXISTS.code == "AUTH.12201"
    assert ErrorCode.REGISTER_USERNAME_ALREADY_EXISTS.http_status == 409

    print("✅ 错误码结构测试通过")


def test_error_code_properties():
    """测试错误码属性"""
    # 测试 module 属性
    assert ErrorCode.AUTH_TOKEN_EXPIRED.module == "AUTH"
    assert ErrorCode.USER_NOT_FOUND.module == "USER"

    # 测试 code_num 属性
    assert ErrorCode.AUTH_TOKEN_EXPIRED.code_num == 10002
    assert ErrorCode.USER_NOT_FOUND.code_num == 20001

    print("✅ 错误码属性测试通过")


def test_error_code_docstring():
    """测试错误码文档字符串"""
    # 每个错误码都应该有文档字符串
    assert ErrorCode.AUTH_TOKEN_EXPIRED.__doc__ != ""
    assert ErrorCode.USER_NOT_FOUND.__doc__ != ""

    print(f"AUTH_TOKEN_EXPIRED 文档: {ErrorCode.AUTH_TOKEN_EXPIRED.__doc__}")
    print(f"USER_NOT_FOUND 文档: {ErrorCode.USER_NOT_FOUND.__doc__}")

    print("✅ 错误码文档字符串测试通过")


if __name__ == "__main__":
    test_error_code_structure()
    test_error_code_properties()
    test_error_code_docstring()
    print("\n🎉 所有测试通过！")
