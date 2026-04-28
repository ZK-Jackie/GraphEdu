"""密码工具类
用于密码的加密和验证
"""

import logging

import bcrypt

from ..exceptions import PasswordException

logger = logging.getLogger(__name__)


class PasswordUtil:
    """密码工具类
    提供密码加密和验证功能
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """对密码进行哈希加密

        Args:
            password: 明文密码

        Returns:
            加密后的密码（bcrypt hash）

        Raises:
            PasswordException: 加密失败时抛出
            ValueError: 密码为空或长度不足时抛出

        Note:
            - 使用 bcrypt 自动生成随机盐值
            - 每次加密相同的密码会得到不同的哈希值（这是正常的）
            - 推荐密码长度至少 8 个字符
        """
        # 参数验证
        if not password:
            raise ValueError("Password cannot be empty")

        if len(password) < 6:
            logger.warning("Password is too weak (less than 6 characters)")

        try:
            # 生成盐值并加密密码
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        except (TypeError, ValueError) as e:
            # 参数类型错误或编码错误
            raise PasswordException(f"Invalid password format: {e}", reason=str(e)) from e
        except Exception as e:
            # 其他未预期的错误
            raise PasswordException("Failed to hash password", reason=str(e)) from e

    @staticmethod
    def verify_password(plain_password: str | None, hashed_password: str | None) -> bool:
        """验证密码是否正确

        Args:
            plain_password: 明文密码
            hashed_password: 加密后的密码

        Returns:
            密码是否匹配（True/False）

        Raises:
            PasswordException: 参数无效或验证过程出错时抛出

        Note:
            - 密码不匹配时返回 False，不抛出异常
            - 只有在参数格式错误或哈希格式无效时才抛出异常
        """
        # 参数验证
        if plain_password is None or hashed_password is None:
            logger.warning("Password or hashed password is None")
            return False

        if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
            logger.error("Password and hashed password must be strings")
            raise PasswordException("Invalid parameter type", reason="Both passwords must be strings")

        if not plain_password or not hashed_password:
            return False

        try:
            # bcrypt.checkpw 会在哈希格式错误时抛出 ValueError
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

        except ValueError as e:
            # 哈希格式无效
            raise PasswordException("Invalid hashed password format", reason=str(e)) from e
        except Exception as e:
            # 其他未预期的错误（通常是编码问题）
            raise PasswordException("Password verification failed", reason=str(e)) from e

    @staticmethod
    def check_password_strength(password: str) -> dict:
        """检查密码强度

        Args:
            password: 待检查的密码

        Returns:
            包含强度信息的字典:
            {
                'is_strong': bool,      # 是否强密码
                'score': int,           # 强度分数 (0-4)
                'issues': list[str]     # 问题列表
            }

        Note:
            强密码标准:
            - 长度 >= 8
            - 包含大小写字母
            - 包含数字
            - 包含特殊字符
        """
        issues = []
        score = 0

        if len(password) < 8:
            issues.append("密码长度至少8个字符")
        else:
            score += 1

        if not any(c.islower() for c in password):
            issues.append("密码应包含小写字母")
        else:
            score += 1

        if not any(c.isupper() for c in password):
            issues.append("密码应包含大写字母")
        else:
            score += 1

        if not any(c.isdigit() for c in password):
            issues.append("密码应包含数字")
        else:
            score += 1

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("密码应包含特殊字符")
        else:
            score += 1

        return {
            "is_strong": score == 5,  # 必须满足所有5个条件才是强密码
            "score": score,
            "issues": issues,
        }

    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """生成随机密码

        Args:
            length: 密码长度（默认12）

        Returns:
            随机密码字符串

        Raises:
            ValueError: 长度参数无效时抛出

        Note:
            生成的密码包含大小写字母、数字和特殊字符
        """
        import secrets
        import string

        if length < 8:
            raise ValueError("Password length must be at least 8")

        # 确保包含各种字符类型
        alphabet = string.ascii_lowercase + string.ascii_uppercase + string.digits + "!@#$%^&*"

        password = "".join(secrets.choice(alphabet) for _ in range(length))

        # 确保至少包含每种类型的一个字符
        while True:
            if (
                any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%^&*" for c in password)
            ):
                break
            password = "".join(secrets.choice(alphabet) for _ in range(length))

        return password
