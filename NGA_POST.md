# NGA 发帖内容

> NGA 使用 BBCode 格式，以下内容直接复制粘贴即可。

---

**标题：** 【开源】给各位搓了个赛博男/女友：有脸、有声音、会生图、会主动找你聊天，挂 TG/微信 24 小时在线

**正文：**

```
[size=120%][b]NanoMate：开源赛博男/女友，酒馆角色卡 + AI Agent + 伴侣模式[/b][/size]

项目地址：[url]https://github.com/shenmintao/NanoMate[/url]

[b]一句话介绍：[/b]用酒馆角色卡定义你的赛博男/女友是谁，用 AI Agent 框架让 ta 真正"活"起来 —— 有记忆、能生图、能说话、会主动关心你，挂在 Telegram / WhatsApp / Discord 上 24 小时陪你。

[quote]
"和 AI 聊天"谁都会。但你的赛博对象应该不只是一个聊天框。

ta 应该有自己的脸（角色一致性图像生成），有自己的声音（TTS 语音合成），能和你拍合照（多图合成），记得你说过的事（记忆系统），会在你压力大的时候主动来找你（情感感知），但凌晨不会吵你（行为约束）。

NanoMate 就是干这个的。
[/quote]

[size=110%][b]你的赛博对象能干什么[/b][/size]

[list]
[*][b]有人设[/b] —— 导入酒馆角色卡、预设、世界信息，你在酒馆里调教好的老婆/老公直接搬过来用
[*][b]有脸[/b] —— 参考图绑定角色卡，每次生图都是同一个"人"，支持按场景换装（沙滩装、正装、冬装各一套）
[*][b]能合照[/b] —— 多图合成：你的照片 + ta 的参考图 = 两个人在一起的画面（Grok / Gemini / DALL-E）
[*][b]有声音[/b] —— Edge TTS 免费用，想要专属声线可以接 GPT-SoVITS 声线克隆
[*][b]会主动找你[/b]（伴侣模式，默认关闭）：
  - [b]同居技能[/b]：你发旅游照 -> ta 生成你们的合照；说"一起做饭" -> 生成厨房场景
  - [b]情感陪伴[/b]：感知到你心情不好会主动安慰，记住你说的"下周考试"到时候跟进，凌晨不打扰
[*][b]24 小时在线[/b] —— 挂在 Telegram / WhatsApp / Discord / 飞书 / 钉钉上，随时找 ta 聊天
[/list]

[size=110%][b]技术栈[/b][/size]

基于 [url=https://github.com/HKUDS/nanobot]nanobot[/url]（港大开源的超轻量 Agent 框架，代码量是同类项目的 1%），在上面加了一层酒馆集成和伴侣模式。nanobot 本身支持多模型（OpenAI / Claude / Gemini / 本地模型都行）、MCP 协议、子代理、工具调用、记忆、定时任务等。

NanoMate 持续跟踪上游更新，nanobot 有的功能 NanoMate 都有。

[size=110%][b]怎么捏你的赛博对象[/b][/size]

三层结构，各管一件事：

[list=1]
[*][b]角色卡[/b] = ta 是谁（人格、背景故事、外貌、和你的关系）
[*][b]预设[/b] = ta 怎么说话（语气、撒娇程度、交互边界、涩不涩你说了算）
[*][b]技能[/b] = ta 会做什么（自动生合照、主动关心你、帮你翻译等）
[/list]

角色卡和预设直接复用酒馆生态，Chub / CharacterHub 上的卡都能用，不用从零开始。技能是可插拔的 Markdown 模板，想加什么能力自己写一个 SKILL.md 就行。

[size=110%][b]部署[/b][/size]

[code]
git clone https://github.com/shenmintao/NanoMate.git
cd NanoMate
pip install -e .
nanobot init
# 编辑 ~/.nanobot/config.json 配置模型和功能
nanobot
[/code]

Docker 一键起：
[code]
docker compose up -d
[/code]

[size=110%][b]图像生成配置[/b][/size]

推荐用 Grok（xAI），多图合成效果最好：

[code]
// ~/.nanobot/config.json
{
  "tools": {
    "imageGen": {
      "enabled": true,
      "apiKey": "xai-xxx",
      "baseUrl": "https://api.x.ai/v1",
      "model": "grok-imagine-image"
    }
  }
}
[/code]

Gemini 速度快适合图生图，DALL-E 只能文生图不支持多图合成。

[size=110%][b]酒馆资源管理[/b][/size]

[code]
# 导入和激活角色卡
nanobot st char import ./我老婆.json
nanobot st char activate 我老婆

# 导入预设
nanobot st preset import ./预设.json
nanobot st preset activate 预设

# 查看状态
nanobot st status
[/code]

[size=110%][b]FAQ[/b][/size]

[b]Q：需要什么模型？[/b]
A：任何 OpenAI 兼容的 API 都行。Claude、GPT、Gemini、DeepSeek、本地 Ollama 都支持。

[b]Q：不开伴侣模式能用吗？[/b]
A：能。不开就是一个带酒馆人设的 AI 助手，该干活干活，只是多了个性格。

[b]Q：能捏男的吗？[/b]
A：角色卡里写什么就是什么，男女老少赛博生物随便捏。

[b]Q：角色卡从哪来？[/b]
A：酒馆生态里大把现成的。Chub、CharacterHub 上下载的 JSON 都能直接导入。自己写也行，就是个 JSON 文件。

[b]Q：和 SillyTavern 冲突吗？[/b]
A：不冲突。NanoMate 只用酒馆的角色卡格式，不需要运行酒馆本体。你可以在酒馆里调好角色卡和预设，导出 JSON 丢给 NanoMate 用。

[b]Q：WhatsApp 国内能用吗？[/b]
A：支持 HTTP/HTTPS/SOCKS5 代理，配好代理就行。

---

总之就是：[b]酒馆负责灵魂，Agent 负责能力，你负责谈恋爱。[/b]

项目地址：[url]https://github.com/shenmintao/NanoMate[/url]

有问题直接回帖或者 GitHub 提 Issue。
```
