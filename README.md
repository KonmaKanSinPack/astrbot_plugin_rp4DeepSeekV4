# astrbot-plugin-helloworld

AstrBot 插件模板 / A template plugin for AstrBot plugin feature

> [!NOTE]
> This repo is just a template of [AstrBot](https://github.com/AstrBotDevs/AstrBot) Plugin.
> 
> [AstrBot](https://github.com/AstrBotDevs/AstrBot) is an agentic assistant for both personal and group conversations. It can be deployed across dozens of mainstream instant messaging platforms, including QQ, Telegram, Feishu, DingTalk, Slack, LINE, Discord, Matrix, etc. In addition, it provides a reliable and extensible conversational AI infrastructure for individuals, developers, and teams. Whether you need a personal AI companion, an intelligent customer support agent, an automation assistant, or an enterprise knowledge base, AstrBot enables you to quickly build AI applications directly within your existing messaging workflows.

# Supports

- [AstrBot Repo](https://github.com/AstrBotDevs/AstrBot)
- [AstrBot Plugin Development Docs (Chinese)](https://docs.astrbot.app/dev/star/plugin-new.html)
- [AstrBot Plugin Development Docs (English)](https://docs.astrbot.app/en/dev/star/plugin-new.html)

## Pinned First User Prompt

`main.py` 里的实现已经从模板指令改成了 `@filter.on_llm_request()` 钩子。

它做的不是把提示词写进 `system_prompt`，也不是把提示词追加到当前轮用户输入后面，而是在每次真正发给模型之前，把一条合成的 `user` 消息插回 `req.contexts` 的最前面。

这样做有两个直接效果：

- 这条提示词始终以第一条 `user message` 的身份参与推理。
- 即使 AstrBot 后续做历史裁剪，这条提示词也会在请求阶段重新钉回去，不会因为旧消息被顶掉而消失。

## How To Change The Prompt

直接修改 `main.py` 顶部这两个配置项：

- `PINNED_USER_PROMPT`: 你的固定 user prompt 主体。
- `DEFAULT_PROMPT_MODE`: 可选值为 `default`、`inner_os`、`no_inner_os`。

当前默认值是 `inner_os`，所以每轮请求都会注入：

1. 固定首条 user prompt。
2. 你定义的 `INNER_OS_MARKER`。

如果你只想保留固定 user prompt，不追加思维模式标记，把 `DEFAULT_PROMPT_MODE` 改成 `default` 即可。
