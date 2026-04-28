"""
密码生成工具脚本

用于生成 bcrypt 密码哈希，用于数据库初始化
"""

import bcrypt
import getpass


def generate_password_hash(plain_password: str) -> str:
    """生成密码的 bcrypt 哈希

    Args:
        plain_password: 明文密码

    Returns:
        bcrypt 哈希值
    """
    # 生成盐值并加密密码
    salt = bcrypt.gensalt(rounds=12)  # 使用 12 rounds，与 SQL 中的 $2b$12$ 对应
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password_hash(plain_password: str, hashed_password: str) -> bool:
    """验证密码哈希

    Args:
        plain_password: 明文密码
        hashed_password: bcrypt 哈希值

    Returns:
        是否匹配
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def main():
    """主函数"""
    # 设置控制台输出编码为 UTF-8
    import sys
    import io

    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    print("=" * 60)
    print("Password Hash Generator")
    print("=" * 60)
    print()

    # 测试 SQL 中的现有哈希值
    print("1. Verify existing password hashes in SQL")
    print("-" * 60)

    # SQL 中的管理员密码
    sql_admin_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYKKRgKKpNS"
    test_passwords = ["admin123", "admin", "password", "Admin@123"]

    for pwd in test_passwords:
        is_valid = verify_password_hash(pwd, sql_admin_hash)
        status = "[OK] Match" if is_valid else "[FAIL] No match"
        print(f"  Test password: '{pwd}' -> {status}")

    print()

    # 生成新的密码哈希
    print("2. Generate new password hashes")
    print("-" * 60)

    default_passwords = {
        "admin": "admin123",
        "teacher": "teacher123",
        "student": "student123",
    }

    print("Default account passwords:")
    for username, password in default_passwords.items():
        hashed = generate_password_hash(password)
        print(f"  {username:10} : password='{password}'")
        print(f"                hash='{hashed}'")
        print()

    # 交互式生成
    print("3. Interactive password hash generation")
    print("-" * 60)

    while True:
        print()
        custom_password = input("Enter password to hash (press Enter to skip): ").strip()

        if not custom_password:
            break

        hashed = generate_password_hash(custom_password)
        print(f"Password hash: {hashed}")

        # 验证生成的哈希
        is_valid = verify_password_hash(custom_password, hashed)
        print(f"Verification: {'[OK] Success' if is_valid else '[FAIL] Failed'}")

    print()
    print("=" * 60)
    print("Usage Instructions:")
    print("=" * 60)
    print("""
Copy the generated hash to SQL initialization script, for example:

INSERT INTO sys_user (user_name, nick_name, password, ...)
VALUES ('admin', 'Super Admin', 'PASTE_HASH_HERE', ...);
    """)


if __name__ == "__main__":
    main()
