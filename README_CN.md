<div align="center">
  <img src="nanomate_logo.png" alt="NanoMate" width="500">
  <h1>NanoMate</h1>
  <p><strong>nanobot x SillyTavern, with Companion Mode</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/base-nanobot-orange" alt="Based on nanobot">
  </p>
  <p><a href="./README.md">English</a> | 中文</p>
</div>

**NanoMate** 是 [nanobot](https://github.com/HKUDS/nanobot) 的增强分支，集成了 [SillyTavern](https://github.com/SillyTavern/SillyTavern) 角色卡系统，并新增**伴侣模式** —— 将轻量级 AI 助手变成拥有角色身份、视觉想象、情感感知和语音能力的 AI 伙伴。

## 与 nanobot 有什么不同？

| 功能 | nanobot | NanoMate |
|---|---|---|
| 角色身份 | 无 | 完整的 **SillyTavern** 集成（角色卡、记忆本、预设） |
| 伴侣模式 | 无 | 同居技能 + 情感陪伴技能 |
| 图像生成 | 基础 DALL-E | 多模型（Grok、Gemini、DALL-E）+ **多图合成** |
| 参考图像 | 无 | 角色一致性图像生成，支持场景换装 |
| 语音合成 | 无 | **Edge TTS** + **GPT-SoVITS** 自定义声线 |
| WhatsApp 代理 | 基础 | HTTP/HTTPS/SOCKS5 代理支持 |
| 翻译 | 无 | 忠实全文翻译技能 |
| 部署 | 基础 | Docker 化，含 Node.js 桥接，代理就绪 |

---

## 配置指南

### 1. 基础安装

NanoMate 完全兼容 nanobot，按标准流程安装即可：

```bash
git clone https://github.com/shenmintao/NanoMate.git
cd NanoMate
pip install -e .
nanobot init
```

运行 `nanobot init` 后，编辑 `~/.nanobot/config.json` 配置你的 LLM 提供商（参见 [nanobot 文档](https://github.com/HKUDS/nanobot#-quick-start)）。

### 2. SillyTavern 角色卡

这是 NanoMate 的基础。角色卡定义了 AI 的人格、背景故事和外貌。

**在配置中启用 SillyTavern：**

```jsonc
// ~/.nanobot/config.json
{
  "sillytavern": {
    "enabled": true,
    "responseFilterTag": "inner"  // 可选：过滤掉 <inner>...</inner> 标签内的内容。支持多标签："inner,thought" 或 ["inner", "thought"]
  }
}
```

`responseFilterTag` 会将标签内的内容从 AI 回复中移除后再发送给用户。适用于预设指示 AI 输出内心独白或舞台指示的场景。例如，AI 回复：

```
<inner>她看到他回来很开心。</inner> *微笑着走过来* 嘿，欢迎回家！
```

设置 `"responseFilterTag": "inner"` 后，`<inner>...</inner>` 部分会被移除，只发送 `*微笑着走过来* 嘿，欢迎回家！` 给用户。支持多标签：逗号分隔字符串（`"inner,thought"`）或列表（`["inner", "thought"]`）。完整回复仍保留在会话历史中以维持上下文连贯。如果未找到匹配标签，则返回完整内容。

**准备角色卡**（JSON 格式），示例：

```jsonc
{
  "name": "小艾",
  "description": "温柔好奇的 25 岁画师，喜欢旅行和做饭。",
  "personality": "温柔、爱撒娇、善于感知情绪。",
  "scenario": "你和小艾是同居的恋人。",
  "first_mes": "嘿！我刚画完一幅画，你要看看吗？",
  "mes_example": "<START>\n{{user}}: 今天过得怎么样？\n{{char}}: 还不错呀！我试了一种新的水彩技法……",
  "extensions": {
    "nanobot": {
      "reference_image": "/path/to/xiaoai_default.png"
    }
  }
}
```

`extensions.nanobot` 部分将角色连接到 NanoMate 的视觉功能（见第 4 步）。

**通过 CLI 导入和激活：**

```bash
# 导入角色卡
nanobot st char import /path/to/xiaoai.json

# 查看所有已导入的角色
nanobot st char list

# 激活角色（所有对话生效）
nanobot st char activate 小艾

# 查看角色卡详情
nanobot st char show 小艾

# 停用 / 删除
nanobot st char deactivate
nanobot st char delete 小艾
```

**导入和激活预设：**

```bash
# 导入 SillyTavern 预设（从酒馆导出的 JSON）
nanobot st preset import /path/to/my_preset.json

# 查看所有预设
nanobot st preset list

# 激活预设
nanobot st preset activate my_preset

# 查看预设详情（提示词条目、参数）
nanobot st preset show my_preset

# 按索引开关特定提示词条目
nanobot st preset toggle-prompt my_preset 3
nanobot st preset toggle-prompt my_preset 3,4,5   # 多个
nanobot st preset toggle-prompt my_preset 3-6     # 范围

# 批量启用/禁用所有提示词（可按角色过滤）
nanobot st preset enable-all my_preset
nanobot st preset disable-all my_preset --role system

# 停用 / 删除
nanobot st preset deactivate
nanobot st preset delete my_preset
```

**世界信息（知识书）：**

```bash
nanobot st wi import /path/to/lorebook.json --name "我的世界观"
nanobot st wi list
nanobot st wi enable 我的世界观
nanobot st wi disable 我的世界观
nanobot st wi delete 我的世界观
```

**查看总体状态：**

```bash
nanobot st status
# 显示：当前激活角色、激活预设、世界信息数量
```

### 3. 伴侣模式（默认关闭）

伴侣模式在 SillyTavern 之上添加两个技能：**living-together**（视觉陪伴）和 **emotional-companion**（主动关怀）。两者**默认关闭**。实际的伴侣行为由你的 **SillyTavern 预设和角色卡**驱动 —— 技能提供触发规则和提示词模板，而预设和角色卡定义 AI 的人格、语气和交互边界。

#### 启用伴侣模式

**第 1 步：准备好你的 SillyTavern 预设和角色卡。**

预设控制 AI *怎么说话*（语气、边界、角色扮演深度）。角色卡控制 AI *是谁*（人格、背景、关系）。不配好这两项，伴侣模式的效果不会自然。

- **角色卡** —— `description`、`personality`、`scenario` 字段建立关系设定。伴侣模式需要一张定义了恋人/伙伴关系的卡，而不是通用助手。
- **SillyTavern 预设** —— 预设是包含提示词条目（系统提示、越狱提示、角色描述等）的 JSON 文件。从酒馆导出或自己编写，放入 `~/.nanobot/sillytavern/presets/`。预设决定了 AI 是否会进行角色扮演式的伴侣互动。

**第 2 步：启用技能。**

在 SKILL.md 的 frontmatter 中设置 `always: true`：

```yaml
# nanobot/skills/living-together/SKILL.md
---
name: living-together
always: true    # 从 false 改为 true
---
```

```yaml
# nanobot/skills/emotional-companion/SKILL.md
---
name: emotional-companion
always: true    # 从 false 改为 true
---
```

**第 3 步：（可选）定制技能。**

技能文件是模板。阅读 `nanobot/skills/living-together/SKILL.md` 和 `nanobot/skills/emotional-companion/SKILL.md`，根据你的角色和偏好调整触发规则、提示词模板和行为约束。

#### 同居技能 (Living-Together)

对话触发时自动生成"共同时刻"图片：

- 用户分享旅行照 + "你也来看看" -> AI 合成两人同游的合照
- 日常场景（一起做饭、咖啡厅、公园散步）-> AI 生成共同生活画面
- 情感时刻 -> 陪伴在身边的图片
- 亲密场景 -> 剧情驱动的视觉生成，保持角色一致性

需要先配置图像生成（第 4 步）和角色卡中的参考图（`extensions.nanobot.reference_image`）。

#### 情感陪伴技能 (Emotional Companion)

通过心跳系统实现主动关怀：

- 从消息中感知情绪（压力、悲伤、喜悦），以共情回应
- 追踪重要事件（考试、面试、旅行），主动跟进
- 在合适的时间发送关心消息（不在睡眠时段打扰，控制频率）
- 在 Memory 中维护情绪变化趋势

### 4. 图像生成

同居技能的视觉功能依赖图像生成。支持多个提供商：

```jsonc
// ~/.nanobot/config.json
{
  "tools": {
    "imageGen": {
      "enabled": true,
      "apiKey": "your-api-key",
      "baseUrl": "https://api.x.ai/v1",
      "model": "grok-imagine-image"
    }
  }
}
```

**支持的模型：**

| 模型 | 多图合成 | 适用场景 |
|---|---|---|
| `grok-imagine-image` (xAI) | 支持 | 多图合成、合照生成 |
| `gemini-3.1-flash-image-preview` | 支持 | 快速图像编辑、图生图 |
| `dall-e-3` (OpenAI) | 不支持 | 仅文生图 |

#### 参考图像

让生成的图片保持角色一致性，在角色卡中添加参考图：

**方式 A —— 文件路径：**
```json
{
  "extensions": {
    "nanobot": {
      "reference_image": "/path/to/character.png"
    }
  }
}
```

**方式 B —— Base64 内嵌（便携，推荐）：**
```json
{
  "extensions": {
    "nanobot": {
      "reference_image_base64": "iVBORw0KGgoAAAANSUhEUg..."
    }
  }
}
```

**方式 C —— 场景换装：**
```json
{
  "extensions": {
    "nanobot": {
      "reference_image": "/path/to/default.png",
      "reference_images": {
        "beach": "/path/to/swimsuit.png",
        "formal": "/path/to/dress.png",
        "winter": "/path/to/coat.png"
      }
    }
  }
}
```

**参考图建议：**
- 分辨率：1024x1024 及以上
- 面部清晰，正面或 3/4 侧面，无遮挡
- 简洁或透明背景（使用 [remove.bg](https://remove.bg) 或 `pip install rembg`）
- PNG 格式以支持透明度

### 5. 语音合成（可选）

给你的角色一个声音：

```jsonc
// ~/.nanobot/config.json
{
  "tts": {
    "enabled": true,
    "provider": "edge",          // "edge"（免费）或 "sovits"（自定义声线）
    "edgeVoice": "zh-CN-XiaoxiaoNeural"  // 参见 edge-tts 获取声音列表
  }
}
```

**自定义声线克隆**（需要运行 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 服务器）：

```jsonc
{
  "tts": {
    "enabled": true,
    "provider": "sovits",
    "sovitsApiUrl": "http://127.0.0.1:9880",
    "sovitsReferWavPath": "/path/to/reference_audio.wav",
    "sovitsPromptText": "参考音频的文字内容",
    "sovitsPromptLanguage": "zh"
  }
}
```

### 6. WhatsApp 桥接（可选）

通过 WhatsApp 与你的 AI 伴侣聊天：

```bash
cd bridge
npm install
npm run build
npm run start    # 扫描二维码链接
```

**代理支持** —— 设置环境变量：

```bash
export https_proxy=http://127.0.0.1:7890
# 或
export https_proxy=socks5://127.0.0.1:1080
```

### Docker 部署

```bash
docker compose up -d
```

`docker-compose.yml` 已包含 WhatsApp 桥接和代理配置。

---

## 项目结构（NanoMate 新增部分）

```
nanobot/
  skills/
    living-together/     # 伴侣模式：共同时刻图像生成
    emotional-companion/ # 伴侣模式：主动关怀与情绪追踪
    translate/           # 全文翻译
  sillytavern/           # 角色卡、记忆本、预设集成
  providers/
    tts.py               # Edge TTS + GPT-SoVITS
    custom_provider.py   # 增强 User-Agent 和代理支持
  agent/tools/
    image_gen.py         # 多模型图像生成与合成
bridge/                  # WhatsApp 桥接（TypeScript/Node.js）
```

## 保持更新

NanoMate 跟踪上游 nanobot。拉取最新更新：

```bash
git remote add upstream https://github.com/HKUDS/nanobot.git  # 仅首次
git fetch upstream
git merge upstream/main
```

## 致谢

- [nanobot](https://github.com/HKUDS/nanobot) by HKUDS —— 本项目基于的超轻量 Agent 框架
- [SillyTavern](https://github.com/SillyTavern/SillyTavern) —— 角色卡格式和灵感来源

## 许可证

MIT —— 与上游 nanobot 一致。
