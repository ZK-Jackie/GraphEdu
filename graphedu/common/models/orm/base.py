"""ORM 基础模型模块

本模块定义了 SQLAlchemy ORM 的基础类
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式基类

    所有通用 ORM 模型都应继承此基类

    使用方式:
        from sqlalchemy.orm import Mapped, mapped_column

        class MyModel(Base):
            __tablename__ = "my_table"
            id: Mapped[int] = mapped_column(primary_key=True)
    """
