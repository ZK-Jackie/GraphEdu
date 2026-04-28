"""AI 聊天相关功能实体"""

import logging
from typing import Any, Literal, Self, TypedDict, TypeVar

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    HumanMessageChunk,
    ToolMessage,
    ToolMessageChunk,
)
from pydantic import BaseModel, Field, ValidationError, model_validator

from graphedu.common.models.shared import QuestionOptionContent
from graphedu.common.prompts.process import (
    AudioContentPrompt,
    FileContentPrompt,
    ImageContentPrompt,
    LinkContentPrompt,
    TextContentPrompt,
)
from graphedu.common.utils import get_timestamp_ms

logger = logging.getLogger(__name__)

_T_LCMessage = TypeVar("_T_LCMessage", bound=BaseMessage)
_T_AIMessage = AIMessage | AIMessageChunk
_T_ToolMessage = ToolMessage | ToolMessageChunk
_T_HumanMessage = HumanMessage | HumanMessageChunk

ChatContentTypeStr = Literal[
    "text",
    "quote_text",
    "image_url",
    "input_audio",
    "video_url",
    "file_object",
    "link",
    "topic_card",
    "collapse_start",
    "collapse_end",
    "question_option",
    "map",
]

ChatSseEvent = Literal["error", "message", "thought_chain", "tool", "end"]


class ChatSseResponse(TypedDict):
    """聊天 SSE 返回值"""

    type: ChatSseEvent
    data: str | dict[str, Any]


class RelationTypeEnum:
    """关系类型枚举"""

    AROUND = "around"

    SINGLE = "single"

    MULTI_NODE = "multi_node"


class RoleEnum:
    """Role of the message sender"""

    HUMAN = 0
    """用户"""

    AI = 1
    """AI"""

    THINKING = 2
    """AI 思考过程 / 工具推理过程"""

    TOOL = 3
    """工具响应结果"""

    SYSTEM = 4
    """系统"""

    UNKNOWN = 8
    """Unknown"""

    en = ["human", "ai", "thinking", "tool", "system", "unknown", "unknown", "unknown", "unknown"]

    zh = ["用户", "AI", "AI 思考", "工具响应", "系统", "未知", "未知", "未知", "未知"]


class ContentTypeEnum:
    """Content type of the message"""

    TEXT = "text"
    """字符串文本"""

    IMAGE_URL = "image_url"
    """图片链接 或 base64 数据"""

    INPUT_AUDIO = "input_audio"
    """音频 base64 数据"""

    VIDEO_URL = "video_url"
    """视频链接"""

    LINK = "link"
    """链接"""

    FILE_OBJECT = "file_object"
    """文档文件的 OSS 对象名称，仅给名称即可，无需链接/桶名"""

    TOPIC_CARD = "topic_card"
    """主题联想卡消息"""

    COLLAPSE_START = "collapse_start"
    """区块信息开始标记"""

    COLLAPSE_END = "collapse_end"
    """区块信息结束标记"""

    QUESTION_OPTION = "question_option"
    """交互性消息：题目选项"""

    MAP = "map"
    """交互性消息：知识图谱"""

    QUOTE_TEXT = "quote_text"
    """引用文本"""

    non_text: set[str] = {
        IMAGE_URL,
        INPUT_AUDIO,
        VIDEO_URL,
        LINK,
        FILE_OBJECT,
        TOPIC_CARD,
        COLLAPSE_START,
        COLLAPSE_END,
        QUESTION_OPTION,
        MAP,
    }

    ls: list[str] = [
        TEXT,
        QUOTE_TEXT,
        IMAGE_URL,
        INPUT_AUDIO,
        VIDEO_URL,
        LINK,
        FILE_OBJECT,
        TOPIC_CARD,
        COLLAPSE_START,
        COLLAPSE_END,
        QUESTION_OPTION,
        MAP,
    ]

    ordered: list[str] = [COLLAPSE_END, IMAGE_URL, INPUT_AUDIO, VIDEO_URL, LINK, FILE_OBJECT, TEXT]


class TextContent(BaseModel):
    """文本消息"""

    text: str
    """文本内容"""

    additional_kwargs: dict | None = Field(default_factory=dict, exclude=True)
    """额外参数"""

    @property
    def markdown_str(self) -> str:
        """Markdown 格式文本"""
        return TextContentPrompt.content_template.format(content=self.text)


class LinkContent(BaseModel):
    """链接消息"""

    url: str
    """链接地址"""

    sitename: str | None = Field(default=None)
    """链接站点名称"""

    title: str | None = Field(default=None)
    """链接标题"""

    content: str | None = Field(default=None)
    """链接内容"""

    summary: str | None = Field(default=None)
    """链接摘要"""

    link_id: str | None = Field(default=None)
    """链接 ID / 后端记录标识 ID，用于标识/记录链接详情信息，不需要返回前端"""

    additional_kwargs: dict | None = Field(default_factory=dict, exclude=True)
    """额外参数"""

    @property
    def markdown_str(self) -> str:
        """Markdown 提示词"""
        return LinkContentPrompt.content_template.format(filename=self.title, content=self.content)


class FileContent(BaseModel):
    """文档消息"""

    filename: str
    """原始文档名称，带后缀"""

    url: str | None = Field(default=None)
    """文档文件的 OSS 对象链接"""

    content: str | None = Field(default=None)
    """文档完整内容"""

    summary: str | None = Field(default=None)
    """文档摘要"""

    file_id: str | None = Field(default=None)
    """智谱文件 ID / 后端记录标识 ID，用于标识/记录链接详情信息，不需要返回前端"""

    additional_kwargs: dict | None = Field(default_factory=dict, exclude=True)
    """额外参数"""

    @property
    def markdown_str(self) -> str:
        """Markdown 文本"""
        return FileContentPrompt.content_template.format(filename=self.filename, content=self.content)


class TopicCardContent(BaseModel):
    """主题联想卡消息，树状结构"""

    title: str
    """卡片标题标题"""

    topic: "ChatMessageContent"
    """主题联想卡驱动内容"""

    results: list["ChatMessageContent"]
    """主题联想卡搜索结果内容"""


class ImageContent(BaseModel):
    """图片(链接)消息，遵循 OpenAI 接口格式
    https://www.bigmodel.cn/dev/api/normal-model/glm-4v
    """

    filename: str
    """图片名称，带后缀"""

    url: str
    """图片链接，仅能为 url 或 base64
    图像大小上传限制为每张图像 5M 以下，且像素不超过 6000*6000
    支持 jpg、png、jpeg 格式
    """

    content: str | None = Field(default=None)
    """图片文本完整内容"""

    summary: str | None = Field(default=None)
    """图片文本摘要"""

    @property
    def markdown_str(self):
        """Markdown 提示词"""
        return ImageContentPrompt.content_template.format(filename=self.filename, content=self.content)


class AudioContent(BaseModel):
    """音频链接消息，遵循 OpenAI 接口格式
    https://www.bigmodel.cn/dev/api/rtav/GLM-4-Voice
    """

    data: str
    """音频链接，仅能为 base64
    音频大小限制为 20M 以内，音频时长不超过 2h
    """

    format: Literal["mp3", "wav"]
    """音频类型：mp3、wav"""

    filename: str | None = Field(default=None)
    """音频文件名称"""

    content: str | None = Field(default=None)
    """音频文本完整内容"""

    summary: str | None = Field(default=None)
    """音频文本摘要"""

    @property
    def markdown_str(self):
        """Markdown 文本"""
        return AudioContentPrompt.content_template.format(filename=self.filename, content=self.content)


class VideoContent(BaseModel):
    """视频链接消息，遵循 OpenAI 接口格式
    https://www.bigmodel.cn/dev/api/normal-model/glm-4v
    """

    ## type: Literal["video_url"]
    """视频链接消息类型名称，视频理解时，video_url 参数必须在第一个"""

    url: str
    """视频链接，仅能为 url
    GLM-4V-Plus视频大小限制为20M以内，视频时长不超过 30s
    GLM-4V-Plus-0111 视频大小限制为 200M 以内，视频时长不超过 2h
    视频类型：mp4
    """


class QuoteContent(BaseModel):
    """引用文本消息"""

    quotes: list[str] = Field(description="引用的文本片段列表")
    content: str | None = Field(default=None, description="用户附加的问题/内容")
    source: str | None = Field(default=None, description="引用来源，如：课程 > 章节 > 小节")

    @property
    def markdown_str(self) -> str:
        """组织为发送给 AI 的 Markdown 文本，包含引用来源"""
        parts: list[str] = []
        if self.quotes:
            quote_lines: list[str] = []
            for q in self.quotes:
                quote_lines.append(f"> {q}")
            if self.source:
                quote_lines.append(f"> — <cite>{self.source}</cite>")
            parts.append("\n".join(quote_lines))
        if self.content:
            parts.append(self.content)
        return "\n\n".join(parts)


class MapNode(BaseModel):
    """知识图谱节点"""

    uid: str
    """节点 ID"""

    name: str
    """节点名称"""

    labels: set | list | None = Field(default=None)
    """节点类型"""

    properties: dict | None = Field(default=None)
    """节点属性"""


class MapRelation(BaseModel):
    """知识图谱边"""

    source: str
    """源节点 ID"""

    target: str
    """目标节点 ID"""

    name: str | None
    """边名称"""

    uid: str
    """边 ID"""

    properties: dict | None = Field(default=None)
    """边属性"""


class MapContent(BaseModel):
    """知识图谱消息"""

    nodes: list[MapNode] | str
    """节点列表"""

    relations: list[MapRelation] | str
    """边列表"""

    additional_kwargs: dict | None = Field(default_factory=dict, exclude=True)
    """额外参数"""


T_ContentType = TypeVar(
    "T_ContentType",
    str,
    FileContent,
    ImageContent,
    AudioContent,
    VideoContent,
    LinkContent,
    TopicCardContent,
    QuestionOptionContent,
    MapContent,
    QuoteContent,
)
STRINGABLE_TYPE = [
    ContentTypeEnum.QUOTE_TEXT,
    ContentTypeEnum.FILE_OBJECT,
    ContentTypeEnum.LINK,
    ContentTypeEnum.IMAGE_URL,
    ContentTypeEnum.INPUT_AUDIO,
]


class ChatMessageContent(BaseModel):
    """聊天消息内容"""

    type: ChatContentTypeStr | str
    """消息类型"""

    text: str | None = Field(description="Content", default=None)
    """文本内容"""

    quote_text: QuoteContent | None = Field(description="Quote text", default=None)
    """引用文本"""

    file_object: FileContent | None = Field(description="File object", default=None)
    """文件对象信息"""

    image_url: ImageContent | None = Field(description="Image URL", default=None)
    """图片链接"""

    video_url: VideoContent | None = Field(description="Video URL", default=None)
    """视频链接"""

    input_audio: AudioContent | None = Field(description="Audio data", default=None)
    """音频数据"""

    topic_card: TopicCardContent | None = Field(description="Topic card", default=None)
    """主题联想卡"""

    collapse_start: str | None = Field(description="Collapse start", default=None)
    """区块信息开始标记的提示字符串"""

    collapse_end: str | None = Field(description="Collapse end", default=None)
    """区块信息结束标记的提示字符串"""

    question_option: QuestionOptionContent | None = Field(description="Question option", default=None)
    """题目选项消息"""

    map: MapContent | None = Field(description="Map", default=None)
    """知识图谱消息"""

    link: LinkContent | None = Field(description="Link", default=None)
    """网络链接消息"""

    @model_validator(mode="after")
    def validate_content(self) -> Self:
        """验证消息内容是否符合消息类型要求"""
        if self.type not in ContentTypeEnum.ls:
            raise ValidationError(f"未知的消息类型：{self.type}")
        if not hasattr(self, self.type) or getattr(self, self.type) is None:
            raise ValidationError(f"消息内容不能为空：{self.type}")
        return self

    @classmethod
    def auto_new_content(cls, content_type: ChatContentTypeStr, content: T_ContentType) -> "ChatMessageContent":
        """快速实例化消息内容实体"""
        if content_type in ContentTypeEnum.ls:
            d = {"type": content_type, content_type: content}
            return cls(**d)
        raise ValidationError("未知的消息类型")

    def auto_get_content(self) -> T_ContentType:
        """快速获取消息内容数据"""
        if self.type in ContentTypeEnum.ls:
            return getattr(self, self.type)
        raise ValidationError("未知的消息类型")

    def auto_set_content(self, content_type: ChatContentTypeStr, content: T_ContentType) -> Self:
        """自动设置消息内容，有且仅当当前消息类型与传入的消息类型一致时，才会设置成功

        :param content_type: 消息类型
        :param content: 消息内容
        :return: 当前对象
        """
        if self.type == content_type:
            setattr(self, content_type, content)
        else:
            raise ValidationError("未知的消息类型")
        return self

    def pretty_print(self):
        """打印内容"""
        print(f"{self.type}: {getattr(self, self.type)}")


class ChatFeature(BaseModel):
    """聊天额外功能"""

    graphrag: bool = Field(default=False)
    """是否开启知识问答？若开启的知识空间 ID > 0"""

    web_search: Literal["enable", "disable", "auto"] = Field(default="disable")
    """是否开启联网搜索学习资源"""

    thinking_mode: Literal["enable", "disable", "auto"] = Field(default="disable")
    """是否开启思考模式"""

    chapter_id: int | None = Field(default=None, description="当前会话关联的章节ID")


class ChatMessage(BaseModel):
    """消息实体"""

    role: int = Field(default=0, ge=0, le=8)
    """消息发送者的角色，0 表示用户，1 表示机器人，值可参考枚举类 RoleEnum"""

    contents: list[ChatMessageContent] = Field(default_factory=list)
    """输入或输出消息内容"""

    user_id: int | None = Field(default=0)
    """用户 ID，注意是 int 类型，对话标识键 1"""

    conv_id: int = Field(default=0)
    """对话 ID，注意是 int 类型，对话标识键 2"""

    message_id: str | None = Field(default=None)
    """消息 ID，注意是 str 类型，AI 的由 python 端决定，一般使用毫秒级的时间戳，对话标识键 3"""

    feature: ChatFeature | None = Field(default_factory=ChatFeature)
    """聊天额外功能"""

    @model_validator(mode="after")
    def validate_values(self):
        """验证消息内容"""
        # 1. 确保 contents 是列表，并且列表中的每个元素都是 ChatMessageContent 对象
        if isinstance(self.contents, list) and len(self.contents) > 0:
            c_list = []
            for c in self.contents:
                if isinstance(c, dict):
                    c = ChatMessageContent.model_validate(c)
                c_list.append(c)
            self.contents = c_list
        # 2. 确保 feature 是 ChatFeature 对象
        if self.feature is None:
            self.feature = ChatFeature()
        elif isinstance(self.feature, dict):
            self.feature = ChatFeature.model_validate(self.feature)
        return self

    @property
    def chat_uid(self) -> str:
        """生成对话唯一标识"""
        return f"{self.user_id}-{self.conv_id}"

    @classmethod
    def build_chat_uid(cls, user_id: int, conv_id: int) -> str:
        """构建对话唯一标识"""
        return f"{user_id}-{conv_id}"

    @classmethod
    def auto_new_message(
        cls,
        role: int,
        content_type: ChatContentTypeStr,
        content: T_ContentType | list[T_ContentType],
        user_id: int,
        conv_id: int,
        *,
        message_id: str | None = None,
        feature: ChatFeature | None = None,
    ) -> "ChatMessage":
        """自动生成消息"""
        message_id = message_id or get_timestamp_ms()
        if not isinstance(content, list):
            content = [content]
        return cls(
            role=role,
            contents=[ChatMessageContent.auto_new_content(content_type, item) for item in content],
            user_id=user_id,
            conv_id=conv_id,
            message_id=message_id,
            feature=feature,
        )

    @classmethod
    def from_lc_message(
        cls,
        user_id: int,
        conv_id: int,
        lc_message: _T_LCMessage,
        *,
        thinking: bool = False,
    ) -> "ChatMessage":
        """将 LangChain 消息转换为 ChatMessage，只能产生 AI、Tool、Human 类型信息，暂时仅支持文本类型消息

        :param user_id: 用户 ID
        :param conv_id: 对话 ID
        :param lc_message: langchain_core.messages.ChatMessage 对象
        :param thinking: 是否为思考消息（AI 类型消息专属选项）
        :return: ChatMessage 对象
        """
        lc_content = lc_message.content
        if isinstance(lc_message, _T_AIMessage):
            role = RoleEnum.AI
            if thinking:
                role = RoleEnum.THINKING
                lc_content = lc_message.additional_kwargs["reasoning_content"]
        elif isinstance(lc_message, _T_ToolMessage):
            role = RoleEnum.TOOL
        elif isinstance(lc_message, HumanMessage):
            role = RoleEnum.HUMAN
        else:
            logger.warning(
                f"Unrecognized message type, expecting Langchain Message, "
                f"but get `{type(lc_message)}`, transforming failed."
            )
            return ChatMessage()
        return cls.auto_new_message(
            role=role,
            content_type=ContentTypeEnum.TEXT,
            content=lc_content,
            message_id=lc_message.id,
            user_id=user_id,
            conv_id=conv_id,
        )

    def new_message(
        self, role: int, content: ChatMessageContent | list[ChatMessageContent], message_id: str = None
    ) -> "ChatMessage":
        """快速创建消息"""
        if isinstance(content, ChatMessageContent):
            content = [content]
        return self.model_copy(update={"role": role, "contents": content, "message_id": message_id}, deep=True)

    def to_lc_message(self) -> AIMessage | HumanMessage:
        """将 ChatMessage 转换为 LangChain 消息"""
        if self.role == RoleEnum.HUMAN:
            other_contents = []
            text_content = ""
            for item in self.contents:
                if item.type == ContentTypeEnum.TEXT:
                    text_content = item.text
                elif item.type in STRINGABLE_TYPE:
                    content_obj = getattr(item, item.type)
                    if content_obj and hasattr(content_obj, "markdown_str"):
                        other_contents.append(content_obj.markdown_str)
            if other_contents:
                text_content = "\n".join(other_contents) + "\n### 用户输入\n" + text_content
            return HumanMessage(
                id=self.message_id,
                content=text_content,
            )
        raise ValidationError("未知的消息角色")

    def order_contents(self):
        """为内容列表排序"""
        # 1 分类
        type_message: dict[str, list[ChatMessageContent]] = {}
        for content in self.contents:
            if content.type in type_message:
                type_message[content.type] += [content]
            else:
                type_message[content.type] = [content]
        # 2 排序
        ordered_messages = []
        rest_messages = []
        for key in ContentTypeEnum.ordered:
            if key in type_message:
                ordered_messages += type_message[key]
        for key in type_message:
            if key not in ContentTypeEnum.ordered:
                rest_messages += type_message[key]
        if rest_messages:
            logger.warning(
                "Unresolved message types in received: "
                f"`{[k for k in type_message if k not in ContentTypeEnum.ordered]}`"
            )
        # 3 赋值
        self.contents = rest_messages + ordered_messages  # 末尾消息按顺序，其他消息放前面

    def get_text(self) -> str:
        """获取消息中的文本内容"""
        if not self.contents:
            return ""
        for item in self.contents:
            if item.type == ContentTypeEnum.TEXT:
                return item.text
        raise ValidationError("没有可供发送的文本内容")

    def auto_set_contents(self, content_type: ChatContentTypeStr, content: T_ContentType | list[T_ContentType]) -> None:
        """快速填充消息内容"""
        if not isinstance(content, list):
            content = [content]
        if len(self.contents) == 1 and self.contents[0].type == content_type:
            # 1 如果当前消息只有一条内容，并且类型一致，则直接替换内容
            self.contents[0].auto_set_content(content_type, content[0])
        else:
            # 2 否则，重新创建消息内容
            self.contents = [ChatMessageContent.auto_new_content(content_type, item) for item in content]

    def pretty_print(self) -> None:
        """美化输出"""
        print(f" == {RoleEnum.zh[self.role]} == ")
        for item in self.contents:
            item.pretty_print()
