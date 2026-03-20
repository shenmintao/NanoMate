# nanobot + 酒馆 = NanoMate：给你的 AI 一张脸、一个声音、和一颗心

各位佬友好，分享一个我基于 [nanobot](https://github.com/HKUDS/nanobot) 做的增强分支 —— **NanoMate**。

简单来说：**nanobot 负责当大脑，SillyTavern 的角色卡负责当灵魂，再加上图像生成、语音合成和情感感知，拼出一个有模有样的 AI 伴侣。**

项目地址：https://github.com/shenmintao/NanoMate

---

## 这东西是什么

nanobot 本身是一个超轻量的 AI Agent 框架（代码量是 OpenClaw 的 1%），支持多模型、多渠道（Telegram、WhatsApp、Discord、飞书、钉钉等），自带工具调用、记忆、定时任务等能力。

NanoMate 在 nanobot 的基础上加了这些东西：

| 功能 | 说明 |
|---|---|
| **SillyTavern 集成** | 导入酒馆角色卡、预设、世界信息，用 `nanobot st` 命令管理 |
| **伴侣模式** | 同居技能 + 情感陪伴技能，默认关闭，开启后配合角色卡使用 |
| **多模型图像生成** | 支持 Grok / Gemini / DALL-E，多图合成（用户照片 + 角色参考图 = 合照） |
| **角色一致性** | 参考图嵌入角色卡，生成的每张图都保持角色外貌一致 |
| **语音合成** | Edge TTS（免费）+ GPT-SoVITS（自定义声线克隆） |
| **WhatsApp 代理** | HTTP/HTTPS/SOCKS5 全支持，解决国内网络问题 |
| **翻译技能** | 全文忠实翻译，不会偷偷摘要 |

---

## 核心玩法：酒馆生态 + Agent 能力

NanoMate 的核心思路是把 SillyTavern 的角色卡和预设系统接入到 nanobot 的 Agent 框架里。

**角色卡**定义"她是谁"（人格、背景、关系设定）。
**预设**定义"她怎么说话"（系统提示词、语气、边界）。
**技能**定义"她会做什么"（自动生成合照、主动关心你）。

三层叠加，效果比单独用酒馆或单独用 Agent 都好得多。

### CLI 管理酒馆资源

```bash
# 导入角色卡
nanobot st char import ./小艾.json
nanobot st char activate 小艾

# 导入预设
nanobot st preset import ./我的预设.json
nanobot st preset activate 我的预设

# 查看预设里的提示词条目，按索引开关
nanobot st preset show 我的预设
nanobot st preset toggle-prompt 我的预设 3-6

# 导入世界信息
nanobot st wi import ./lorebook.json --name "世界观"

# 看总体状态
nanobot st status
```

---

## 伴侣模式演示

伴侣模式默认关闭，需要手动开启。开启后的效果：

**同居技能 (living-together)**：
- 你发一张旅游照说"你也来看看" -> AI 自动生成你们的合照
- 你说"今天一起做饭吧" -> AI 生成你们在厨房的场景
- 日常聊天进入亲密剧情 -> AI 根据情节自动配图

**情感陪伴 (emotional-companion)**：
- AI 感知到你压力大 -> 主动安慰，不是模板式问候
- 你提到下周有考试 -> AI 记住了，考前考后都会跟进
- 凌晨不会打扰你，一天最多主动联系两次

### 开启方式

1. 先配好角色卡和预设（这是基础，不配好效果很差）
2. 改两个文件的 frontmatter：

```yaml
# nanobot/skills/living-together/SKILL.md
---
always: true
---

# nanobot/skills/emotional-companion/SKILL.md
---
always: true
---
```

3. 技能文件本身就是提示词模板，可以按自己的需求改

---

## 图像生成：多图合成是亮点

普通的 AI 图像生成只能文生图。NanoMate 支持**多图合成** —— 把用户的照片和角色的参考图组合在一起，生成"两个人在一起"的画面。

推荐模型：
- **Grok (xAI)** —— 多图合成效果最好
- **Gemini** —— 速度快，图生图强

参考图支持三种方式：文件路径、Base64 内嵌、场景换装（沙滩/正装/冬装各一套）。

配置很简单：

```jsonc
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
```

---

## 部署

```bash
git clone https://github.com/shenmintao/NanoMate.git
cd NanoMate
pip install -e .
nanobot init
# 编辑 ~/.nanobot/config.json 配置 LLM 和功能开关
nanobot
```

Docker 也支持：

```bash
docker compose up -d
```

自带 WhatsApp 桥接的 Docker Compose，代理环境变量开箱即用。

---

## 和原版 nanobot 的关系

NanoMate 持续跟踪上游 nanobot 的更新，定期合并。nanobot 的所有功能（多渠道、MCP、定时任务、子代理等）NanoMate 都有。

区别就是多了酒馆集成和伴侣模式这一层。如果你不需要角色扮演，直接用原版 nanobot 就行。如果你想要一个有"人设"的 AI 伙伴，试试 NanoMate。

---

项目地址：https://github.com/shenmintao/NanoMate

有问题欢迎提 Issue 或者在楼下讨论。
