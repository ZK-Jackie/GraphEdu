# i18n 文件合并说明

代码生成器会生成独立的 i18n JSON 文件，需要手动或使用工具合并到主 i18n 文件中。

## 生成的 i18n 文件

代码生成器会生成以下两个文件：

- `frontend/src/locales/{moduleName}.{businessName}.zh.json` - 中文翻译
- `frontend/src/locales/{moduleName}.{businessName}.en.json` - 英文翻译

## 合并目标

需要将生成的内容合并到以下主文件：

- `frontend/src/locales/zh.json` - 中文主文件
- `frontend/src/locales/en.json` - 英文主文件

## 合并规则

### 1. 模块命名空间

生成的 i18n 内容使用以下命名空间结构：

```json
{
  "{moduleName}": {
    "{businessName}": {
      // 翻译内容
    }
  }
}
```

例如，用户管理模块会生成：

```json
{
  "system": {
    "user": {
      "title": "用户管理",
      "add": "新增用户",
      // ...
    }
  }
}
```

### 2. 合并步骤

1. **读取生成文件**
   ```bash
   cat frontend/src/locales/system.user.zh.json
   ```

2. **合并到主文件**
   - 将生成的内容追加到对应的主文件
   - 确保不覆盖已有的同名键
   - 保持 JSON 格式正确

3. **验证**
   - 运行前端项目检查是否有翻译错误
   - 检查浏览器控制台是否有警告

### 3. 自动合并脚本示例

```python
import json
from pathlib import Path

def merge_i18n_file(source_file: Path, target_file: Path):
    """合并 i18n 文件到主文件"""
    # 读取源文件
    with open(source_file, 'r', encoding='utf-8') as f:
        source_data = json.load(f)

    # 读取目标文件
    with open(target_file, 'r', encoding='utf-8') as f:
        target_data = json.load(f)

    # 递归合并
    def deep_merge(target: dict, source: dict):
        for key, value in source.items():
            if key in target:
                if isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value  # 覆盖
            else:
                target[key] = value

    deep_merge(target_data, source_data)

    # 写回目标文件
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(target_data, f, ensure_ascii=False, indent=2)

    print(f"Merged {source_file} -> {target_file}")

# 使用示例
merge_i18n_file(
    Path("frontend/src/locales/system.user.zh.json"),
    Path("frontend/src/locales/zh.json")
)
```

## 常见翻译键

### 通用操作（已存在于 common 命名空间）

- `common.search` - 搜索
- `common.reset` - 重置
- `common.add` - 新增
- `common.edit` - 修改
- `common.delete` - 删除
- `common.import` - 导入
- `common.export` - 导出
- `common.operation` - 操作
- `common.status` - 状态
- `common.systemTip` - 系统提示
- `common.pleaseInput` - 请输入
- `common.pleaseSelect` - 请选择
- `common.success` - 操作成功
- `common.failed` - 操作失败
- `common.deleteSuccess` - 删除成功
- `common.deleteFailed` - 删除失败
- `common.total` - 共
- `common.items` - 条
- `common.expand` - 展开
- `common.collapse` - 折叠

### 模块特定翻译（动态生成）

每个模块会生成以下翻译键：

- `{moduleName}.{businessName}.title` - 模块标题
- `{moduleName}.{businessName}.add` - 新增操作
- `{moduleName}.{businessName}.edit` - 修改操作
- `{moduleName}.{businessName}.delete` - 删除操作
- `{moduleName}.{businessName}.addChild` - 新增子节点（树表）
- `{moduleName}.{businessName}.getListFailed` - 获取列表失败
- `{moduleName}.{businessName}.deleteConfirm` - 删除确认消息
- `{moduleName}.{businessName}.deleteSelectedConfirm` - 批量删除确认消息
- `{moduleName}.{businessName}.exportInDevelopment` - 导出功能开发中

### 字段翻译

每个在查询或列表中显示的字段都会生成翻译：

- `{moduleName}.{businessName}.{field}` - 字段名称
- `{moduleName}.{businessName}.{field}Placeholder` - 字段占位符（查询字段）
- `{moduleName}.{businessName}.{field}Select` - 选择提示（select/radio 类型）
- `{moduleName}.{businessName}.{field}Start` - 开始时间（datetime 类型）
- `{moduleName}.{businessName}.{field}End` - 结束时间（datetime 类型）

## 注意事项

1. **命名冲突**：如果已存在相同的键，新生成的会覆盖旧的
2. **格式化**：保持 JSON 文件的格式化和缩进一致
3. **编码**：确保文件使用 UTF-8 编码
4. **验证**：合并后使用 JSON 验证工具检查格式是否正确
5. **测试**：在浏览器中测试翻译是否正常显示

## 后续工具支持

计划开发以下工具来简化 i18n 合并流程：

1. **CLI 命令**：一键合并所有生成的 i18n 文件
2. **前端插件**：开发时自动合并 i18n 文件
3. **可视化工具**：图形化界面查看和合并翻译
