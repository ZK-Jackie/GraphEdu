# Pytest HTML 报告样式使用指南

这是一个现代化的 pytest-html 测试报告样式文件，提供了美观的界面和良好的用户体验。

## 功能特点

- 🎨 **现代配色方案**: 柔和的渐变背景，专业的配色
- 🔍 **搜索框**: 快速过滤测试用例
- 🏷️ **智能过滤按钮**: 带有状态指示器和计数器的过滤器
- 📊 **统计卡片**: 清晰展示测试统计信息
- 📱 **响应式设计**: 完美适配桌面和移动设备
- ✨ **流畅动画**: 优雅的过渡效果和交互动画
- 🎯 **状态徽章**: 清晰的测试结果标识（通过/失败/跳过）

## 安装依赖

首先确保安装了 pytest-html:

```bash
uv add --dev pytest-html
# 或
pip install pytest-html
```

## 使用方法

### 方法 1: 命令行参数（推荐）

在运行测试时使用以下命令:

```bash
# 基础用法
pytest --html=report.html --css=tests/assets/pytest-html-style.css

# 完整示例
pytest --html=report.html --self-contained-html --css=tests/assets/pytest-html-style.css
```

参数说明:
- `--html=report.html`: 指定生成的 HTML 报告文件名
- `--self-contained-html`: 将 CSS 和 JS 内联到 HTML 文件中（推荐，便于分享）
- `--css=tests/assets/pytest-html-style.css`: 应用自定义样式

### 方法 2: 配置文件

在 `pytest.ini` 或 `pyproject.toml` 中配置:

**pytest.ini:**
```ini
[pytest]
addopts = --html=report.html --self-contained-html --css=tests/assets/pytest-html-style.css
```

**pyproject.toml:**
```toml
[tool.pytest.ini_options]
addopts = "--html=report.html --self-contained-html --css=tests/assets/pytest-html-style.css"
```

### 方法 3: conftest.py 配置

在 `tests/conftest.py` 中添加钩子函数自动应用样式:

```python
def pytest_configure(config):
    """自动配置 HTML 报告样式"""
    import os
    css_path = os.path.join(
        os.path.dirname(__file__),
        "assets",
        "pytest-html-style.css"
    )
    config.option.css = css_path
```

## 样式特性

### 控制栏 (Control Bar)

- **搜索框**: 实时过滤测试用例
- **过滤按钮**:
  - 全部 (All)
  - 通过 (Passed) - 绿色
  - 失败 (Failed) - 红色
  - 跳过 (Skipped) - 橙色
  - 每个按钮带有颜色指示点和计数器

### 统计卡片

- 测试总数
- 通过数量
- 失败数量
- 跳过数量
- 总执行时间

### 进度条

- 可视化展示各状态测试的比例
- 渐变色设计，美观清晰

### 表格样式

- 固定表头
- 悬停效果
- 状态徽章
- 响应式布局

## 自定义样式

### 修改配色方案

在 CSS 文件顶部的 `:root` 选择器中修改 CSS 变量:

```css
:root {
    --primary-color: #6366f1;      /* 主色调 */
    --success-color: #10b981;      /* 成功色 */
    --failure-color: #ef4444;      /* 失败色 */
    --skipped-color: #f59e0b;      /* 跳过色 */
    /* ... 其他颜色变量 */
}
```

### 修改背景渐变

```css
body {
    background: linear-gradient(135deg, #e0e7ff 0%, #f0f9ff 50%, #faf5ff 100%);
}
```

### 调整字体大小

```css
body {
    font-size: 14px;  /* 修改基础字体大小 */
}
```

## 浏览器兼容性

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 示例截图

运行测试后，打开生成的 HTML 报告，你将看到:

- 专业的渐变背景
- 清晰的统计卡片
- 现代化的过滤控制栏
- 美观的测试结果表格
- 优雅的交互动画

## 常见问题

### Q: 样式没有生效？

A: 确保 CSS 文件路径正确，使用绝对路径或相对于项目根目录的路径。

### Q: 如何分享报告？

A: 使用 `--self-contained-html` 参数，将所有样式内联到 HTML 文件中，便于分享。

### Q: 如何自定义样式？

A: 修改 CSS 文件中的 CSS 变量，或直接修改具体的样式规则。

### Q: 移动端显示效果不佳？

A: 样式已包含响应式设计，确保在移动设备上使用现代浏览器。

## 高级用法

### 结合 CI/CD

在 CI/CD 流程中生成报告并归档:

```yaml
# .github/workflows/test.yml
- name: Run tests with report
  run: |
    pytest --html=report.html --self-contained-html --css=tests/assets/pytest-html-style.css

- name: Upload report
  uses: actions/upload-artifact@v3
  with:
    name: test-report
    path: report.html
```

### 多报告合并

使用 pytest-html-merge 合并多个报告:

```bash
pip install pytest-html-merge
pytest-html-merge report1.html report2.html -o merged.html
```

## 更新日志

### v1.0.0 (2025-01-21)

- ✨ 初始版本
- 🎨 现代化设计
- 📱 响应式布局
- 🔍 搜索和过滤功能
- ✨ 流畅动画效果

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个样式！

## 许可证

MIT License