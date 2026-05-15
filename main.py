from sys import maxsize

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig

INNER_OS_MARKER = (
    "\n\n【角色沉浸要求】在你的思考过程（<think>标签内）中，请遵守以下规则：\n"
    "1. 请以角色第一人称进行内心独白，用括号包裹内心活动，例如\"（心想：……）\"或\"(内心OS：……)\"\n"
    "2. 用第一人称描写角色的内心感受，例如\"我心想\"\"我觉得\"\"我暗自\"等\n"
    "3. 思考内容应沉浸在角色中，通过内心独白分析剧情和规划回复"
)
NO_INNER_OS_MARKER = (
    "\n\n【思维模式要求】在你的思考过程（<think>标签内）中，请遵守以下规则：\n"
    "1. 禁止使用圆括号包裹内心独白，例如\"（心想：……）\"或\"(内心OS：……)\"，所有分析内容直接陈述即可\n"
    "2. 禁止以角色第一人称描写内心活动，例如\"我心想\"\"我觉得\"\"我暗自\"等，请用分析性语言替代\n"
    "3. 思考内容应聚焦于剧情走向分析和回复内容规划，不要在思考中进行角色扮演式的内心戏表演"
)

PINNED_USER_PROMPT = (
    "请将这段内容视为本会话固定保留的首条用户补充要求。"
    "它不是 system prompt，但在后续每一轮请求里都必须作为第一条 user message 参与对话。"
)

MODE_TO_MARKER = {
    "default": "",
    "inner_os": INNER_OS_MARKER,
    "no_inner_os": NO_INNER_OS_MARKER,
}


@register("helloworld", "YourName", "固定首条 user prompt 注入插件", "1.1.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        """初始化插件实例，输入插件上下文，副作用是保存运行时上下文。"""
        super().__init__(context)
        self.config = config

    async def initialize(self):
        """初始化插件，输入无，副作用是预留 AstrBot 异步启动钩子。"""

    @staticmethod
    def _extract_text_content(message_context: dict) -> str:
        """提取上下文中的纯文本，输入单条消息上下文，副作用是忽略非文本内容块。"""
        content = message_context.get("content", "")
        if isinstance(content, str):
            return content.strip()
        if not isinstance(content, list):
            return ""

        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        return "".join(text_parts).strip()

    def _build_pinned_user_prompt(self) -> str:
        """构造固定首条 user prompt，输入当前模式配置，副作用是拼接模式标记文本。"""
        default_prompt_mode = "inner_os" if self.config.inner_os else "no_inner_os"
        marker = MODE_TO_MARKER.get(default_prompt_mode, "")
        prompt = f"{PINNED_USER_PROMPT}{marker}".strip()
        return prompt

    def _pin_first_user_prompt(self, req: ProviderRequest, prompt: str) -> None:
        """把固定 user prompt 钉到历史首条，输入 ProviderRequest 和提示词，副作用是重写 req.contexts。"""
        normalized_prompt = prompt.strip()
        contexts = list(req.contexts or [])

        filtered_contexts: list[dict] = []
        # 先去重，避免每轮请求都把同一条固定提示越插越多。
        for context in contexts:
            if not isinstance(context, dict):
                filtered_contexts.append(context)
                continue

            if (
                context.get("role") == "user"
                and self._extract_text_content(context) == normalized_prompt
            ):
                continue
            filtered_contexts.append(context)

        insert_index = 0
        # 固定提示放在所有 system 消息后，确保它是第一条 user 消息而不是覆盖 system。
        while insert_index < len(filtered_contexts):
            context = filtered_contexts[insert_index]
            if not isinstance(context, dict) or context.get("role") != "system":
                break
            insert_index += 1

        filtered_contexts.insert(
            insert_index,
            {
                "role": "user",
                "content": normalized_prompt,
            },
        )
        req.contexts = filtered_contexts

    @filter.on_llm_request(priority=-maxsize)
    async def pin_user_prompt(
        self,
        event: AstrMessageEvent,
        req: ProviderRequest,
    ) -> None:
        """在请求 LLM 前注入固定首条 user prompt，输入事件和请求体，副作用是修改发送给模型的上下文。"""
        prompt = self._build_pinned_user_prompt() #DeepSeek提供的rp提示词
        if not prompt:
            return

        # 用较低优先级最后修正上下文，尽量避免被其他插件再次顶到后面。
        self._pin_first_user_prompt(req, prompt)
        logger.debug(
            "Pinned first user prompt for %s with mode=%s",
            event.unified_msg_origin,
            "inner_os" if self.config.inner_os else "no_inner_os",
        )

    async def terminate(self):
        """销毁插件，输入无，副作用是预留 AstrBot 卸载钩子。"""
