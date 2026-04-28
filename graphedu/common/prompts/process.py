"""提示词处理模板类。"""


class BasePrompt:
    """基础提示词类。"""

    pass


class FileContentPrompt(BasePrompt):
    """文件内容提示词模板。"""

    content_template = "## 文件：{filename}\n**内容：**\n```\n{content}\n```\n"

    summary_template = "## 文件：{filename}\n**总结：**\n```\n{summary}\n```\n"


class LinkContentPrompt(BasePrompt):
    """链接内容提示词模板。"""

    content_template = "## 网页：{filename}\n**内容：**\n```\n{content}\n```\n"

    summary_template = "## 网页：{filename}\n**总结：**\n```\n{summary}\n```\n"


class ImageContentPrompt(BasePrompt):
    """图片内容提示词模板。"""

    content_template = "## 图片：{filename}\n**内容：**\n```\n{content}\n```\n"

    summary_template = "## 图片：{filename}\n**总结：**\n```\n{summary}\n```\n"


class AudioContentPrompt(BasePrompt):
    """音频内容提示词模板。"""

    content_template = "## 音频：{filename}\n**内容：**\n```\n{content}\n```\n"

    summary_template = "## 音频：{filename}\n**总结：**\n```\n{summary}\n```\n"


class TextContentPrompt(BasePrompt):
    """文本内容提示词模板。"""

    content_template = "## 用户输入\n{content}\n"
