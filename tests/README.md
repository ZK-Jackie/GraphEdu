# GraphEdu 测试框架

这是一个基于 pytest 的专业测试框架，为 GraphEdu 项目提供全面的测试支持。

## 测试目录结构

```
tests/
├── __init__.py
├── conftest.py                 # 全局 fixtures 和配置
├── fixtures/                   # 测试数据和工具
│   ├── __init__.py
│   ├── factories.py           # 测试数据工厂
│   ├── helpers.py             # 测试辅助函数
│   └── mocks.py               # Mock 对象
├── unit/                       # 单元测试
│   ├── __init__.py
│   ├── test_utils.py          # 工具函数测试
│   └── test_config.py         # 配置测试
├── integration/                # 集成测试
│   ├── __init__.py
│   ├── test_database.py       # 数据库集成测试
│   └── test_api.py            # API 集成测试
└── e2e/                        # 端到端测试
    ├── __init__.py
    └── test_user_workflow.py  # 用户工作流测试
```

## 测试类型

### 单元测试 (Unit Tests)
- 测试单个函数、类或模块
- 不依赖外部服务（数据库、Redis、API等）
- 使用 mock 对象模拟依赖
- 运行速度快

**示例**:
```bash
pytest tests/unit -v
```

### 集成测试 (Integration Tests)
- 测试多个组件之间的交互
- 需要真实的数据库、Redis 等服务
- 测试 API 端点、数据库操作等

**示例**:
```bash
pytest tests/integration -v
```

### 端到端测试 (E2E Tests)
- 模拟完整的用户场景
- 测试完整的工作流程
- 最接近真实使用情况

**示例**:
```bash
pytest tests/e2e -v
```

## 安装测试依赖

```bash
# 安装测试依赖
uv sync --extra test

# 或安装完整的开发环境
uv sync --extra dev
```

## 运行测试

### 基本命令

```bash
# 运行所有测试
pytest

# 运行特定目录的测试
pytest tests/unit

# 运行特定文件的测试
pytest tests/unit/test_utils.py

# 运行特定测试函数
pytest tests/unit/test_utils.py::test_hash_password_returns_hash

# 运行特定测试类
pytest tests/unit/test_utils.py::TestPasswordUtils
```

### 使用标记运行测试

```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 只运行端到端测试
pytest -m e2e

# 排除慢速测试
pytest -m "not slow"

# 组合标记
pytest -m "unit and not slow"
```

### 代码覆盖率

```bash
# 生成覆盖率报告
pytest --cov=graphedu --cov-report=html

# 在浏览器中查看覆盖率报告
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

### 其他有用的选项

```bash
# 显示详细的输出（包括 print 语句）
pytest -v -s

# 在第一个失败时停止
pytest -x

# 进入调试器
pytest --pdb

# 显示本地变量
pytest -l

# 运行上次失败的测试
pytest --lf

# 并行运行测试（需要安装 pytest-xdist）
pytest -n auto
```

## 编写测试

### 单元测试示例

```python
import pytest

@pytest.mark.unit
class TestMyFeature:
    """测试我的功能。"""

    def test_something_simple(self):
        """测试简单的功能。"""
        assert 1 + 1 == 2

    def test_with_fixture(self, mock_config):
        """使用 fixture 的测试。"""
        assert mock_config is not None

    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
    ])
    def test_with_parameters(self, input, expected):
        """参数化测试。"""
        assert input * 2 == expected
```

### 集成测试示例

```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
class TestDatabaseIntegration:
    """数据库集成测试。"""

    async def test_database_connection(self, db_client):
        """测试数据库连接。"""
        result = await db_client.admin.command("ping")
        assert result["ok"] == 1
```

### 使用 Fixtures

```python
# 在 conftest.py 中定义 fixture
@pytest.fixture
def sample_data():
    """提供测试数据。"""
    return {"key": "value"}

# 在测试中使用
def test_with_sample_data(sample_data):
    assert sample_data["key"] == "value"
```

### 使用 Mock 对象

```python
from unittest.mock import MagicMock, AsyncMock

def test_with_mock():
    """使用 mock 对象测试。"""
    mock = MagicMock()
    mock.method.return_value = "test"

    result = mock.method()
    assert result == "test"

async def test_with_async_mock():
    """使用异步 mock 测试。"""
    mock = AsyncMock()
    mock.method.return_value = "test"

    result = await mock.method()
    assert result == "test"
```

## 测试最佳实践

1. **命名规范**
   - 测试文件: `test_*.py` 或 `*_test.py`
   - 测试类: `Test*`
   - 测试函数: `test_*`

2. **测试结构**
   - 使用 Given-When-Then 模式
   - Arrange: 准备测试数据
   - Act: 执行被测试的功能
   - Assert: 验证结果

3. **保持测试独立**
   - 每个测试应该独立运行
   - 不依赖测试执行顺序
   - 使用 fixture 进行 setup/teardown

4. **使用适当的断言**
   - 具体的断言优于通用的
   - 使用 pytest 的丰富断言
   - 断言消息要清晰

5. **Mock 外部依赖**
   - 单元测试不应该访问数据库
   - 使用 mock 对象模拟 API 调用
   - 使用 fixture 管理测试状态

## 常见问题

### 导入错误

确保你的项目根目录在 PYTHONPATH 中：

```bash
# Windows
set PYTHONPATH=%CD%

# Linux/macOS
export PYTHONPATH=$(pwd)
```

### 数据库连接失败

确保测试数据库正在运行：

```bash
# MongoDB
docker run -d -p 27017:27017 mongo:latest

# Redis
docker run -d -p 6379:6379 redis:latest
```

### Async 测试问题

确保在异步测试中正确使用 `@pytest.mark.asyncio` 装饰器：

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

## 持续集成

测试框架配置了代码覆盖率报告，适用于 CI/CD 环境：

```yaml
# .github/workflows/test.yml 示例
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync --extra test
      - name: Run tests
        run: pytest --cov=graphedu --cov-report=xml
```

## 参考资源

- [Pytest 文档](https://docs.pytest.org/)
- [Pytest Asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [Pytest Mock 文档](https://docs.pytest.org/en/stable/how-to/unittest.html)
- [Python 测试最佳实践](https://docs.python-guide.org/writing/tests/)