# astrbot_plugin_rp4DeepSeekV4

这个插件按 [victorchen96/deepseek_v4_rolepaly_instruct](https://github.com/victorchen96/deepseek_v4_rolepaly_instruct) 的要求，在 AstrBot 的 `on_llm_request` 阶段注入角色扮演提示词。

提示词不是 `system prompt`，而是作为固定的首条 `user message` 注入到请求上下文中。

## 配置项

插件当前只有一个配置项，定义见 `_conf_schema.json`。

- `inner_os`：布尔值，默认 `true`。

`inner_os = true` 时，注入 `INNER_OS_MARKER`，要求 `<think>` 使用角色第一人称内心独白。

`inner_os = false` 时，注入 `NO_INNER_OS_MARKER`，要求 `<think>` 使用分析性表述，不进行角色扮演式内心戏。

具体提示词内容见 `main.py`。
