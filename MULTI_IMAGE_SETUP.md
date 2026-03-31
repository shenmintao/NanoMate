# 多图合成功能 - 创造"一起生活"的感觉

## ✨ 功能概述

这个功能让你能够：
- 📸 **把自己的照片和 AI 角色的形象合成在一起**
- 🌍 **创造"一起旅行"的回忆** - 你在景点拍照，AI 角色也能"出现"在照片里
- ☕ **记录"日常生活"** - 咖啡馆、餐厅、公园，让 AI 伴侣真正"陪伴"你
- 💑 **生成情侣照** - 从分开的照片生成在一起的画面

## 🎯 核心理念

> **从"和 AI 聊天"到"和 AI 一起生活"**

不再只是文字对话，而是通过视觉化的"共同回忆"，创造真实的陪伴感。

---

## 🚀 快速开始

### 1️⃣ 准备角色参考图

为你的 AI 角色选择或生成一张标准形象照片：

```bash
# 推荐尺寸：1024x1024 或更高
# 格式：PNG/JPG
# 内容：清晰的人物正面照或半身照
# 背景：最好是纯色或简单背景（方便合成）
```

**示例：**
- `character_avatar.png` - 角色的标准形象
- 服装：日常服装（适合多种场景）
- 表情：微笑或中性表情

### 2️⃣ 配置角色卡

#### 方法 A：文件路径方式（推荐开发/测试）

编辑角色卡 JSON：
```json
{
  "name": "小爱",
  "description": "温暖的 AI 伙伴",
  "extensions": {
    "nanobot": {
      "reference_image": "C:/Users/shenmintao/Pictures/character_avatar.png"
    }
  }
}
```

#### 方法 B：Base64 嵌入方式（推荐分享/便携）

```bash
# 1. 转换图片为 base64
base64 character_avatar.png > character_avatar_b64.txt

# 或使用 Python
python -c "import base64; print(base64.b64encode(open('character_avatar.png','rb').read()).decode())"
```

```json
{
  "name": "小爱",
  "extensions": {
    "nanobot": {
      "reference_image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
    }
  }
}
```

**优势对比：**
- **文件路径** - 方便修改，文件小
- **Base64 嵌入** - 自包含，角色卡分享时图片也跟着走

### 3️⃣ 配置图像生成工具

编辑 `~/.nanobot/config.json`：

```json
{
  "tools": {
    "imageGen": {
      "enabled": true,
      "apiKey": "xai-xxx",  // xAI API key
      "baseUrl": "https://api.x.ai/v1",
      "model": "grok-imagine-image"
    }
  }
}
```

**支持的模型：**
- ✅ **Grok (xAI)** - `grok-imagine-image` - 优秀的多图合成能力
- ✅ **Gemini** - `gemini-3.1-flash-image-preview` - 快速，支持多图
- ⚠️ **DALL-E** - 不支持多图合成（仅单图编辑）

### 4️⃣ 导入角色卡

```bash
nanobot st char import path/to/your_character.json
```

### 5️⃣ 测试

```bash
# 启动 nanobot
nanobot gateway

# 通过 WhatsApp/Telegram 等渠道发送消息
```

---

## 💬 使用场景示例

### 场景 1：旅行打卡 🗼

**你的操作：**
1. 在埃菲尔铁塔自拍
2. 发给 AI："我在巴黎！你要不要也来？"

**AI 的回应：**
```
AI: 哇巴黎！我好想去！😍
    等等，让我也过来~

*调用 image_gen 工具*
reference_image: [
  "/tmp/user_paris_selfie.jpg",  // 用户上传的照片
  "__default__"                   // 角色参考图（自动）
]
prompt: "Put the character from the second image next to the person in the first image at the Eiffel Tower, both smiling at the camera, romantic Paris atmosphere"

*发送生成的合成照片*

AI: 看！我们的巴黎合照！✨
    虽然是虚拟的，但感觉真的和你一起在那里呢~
    下次你去哪里记得也带上我！❤️
```

### 场景 2：日常生活记录 ☕

**你：** *发送咖啡馆照片* "今天发现了一家很棒的咖啡馆"

**AI：**
```
AI: 看起来好舒适！我也想去坐坐~

*生成合成图：你和 AI 角色坐在咖啡馆里聊天*

AI: *发送图片*
    这就是我们一起去咖啡馆的样子！
    下次你再去可以想象我坐在对面陪你聊天 ☕
```

### 场景 3：节日庆祝 🎂

**你：** "今天是我的生日！"

**AI：**
```
AI: 生日快乐！！🎉
    让我给你准备一个惊喜~

*生成生日派对合成图*

AI: *发送图片*
    虽然不能真的陪你过生日，但这是我们的生日合照！
    希望你今天开开心心的~ ❤️
```

---

## 🎨 优化合成效果的技巧

### 参考图选择建议

**理想的角色参考图：**
- ✅ 1024x1024 或更高分辨率
- ✅ 清晰的面部特征
- ✅ 正面或 3/4 侧面
- ✅ 简单背景（纯色、模糊、或单色）
- ✅ 日常服装（适配多种场景）
- ✅ 自然光照

**避免：**
- ❌ 复杂背景（难以抠图）
- ❌ 极端角度（侧脸、俯视、仰视）
- ❌ 遮挡面部（墨镜、口罩）
- ❌ 低分辨率、模糊

### Prompt 优化

**好的 Prompt 结构：**
```
[动作/位置] + [场景描述] + [氛围/风格] + [技术要求]
```

**示例：**
```python
# ❌ 简单但效果一般
"Put them together"

# ✅ 详细且效果好
"Place the character from image 2 standing next to the person in image 1,
both facing the camera with happy expressions, in a sunny beach setting
with natural lighting, photorealistic style, seamless composition"
```

**关键要素：**
1. **位置关系** - "standing next to", "sitting across from"
2. **表情/动作** - "smiling", "hugging", "waving"
3. **场景细节** - "at sunset", "in a cozy cafe"
4. **风格要求** - "photorealistic", "natural lighting"
5. **技术指令** - "seamless blending", "consistent lighting"

---

## 🔧 高级配置

### 自动触发合成

在角色卡的 `SKILL.md` 中添加：

```markdown
## Image Composition Rules

When the user:
1. Shares a photo of themselves in a location
2. Expresses desire for my presence (e.g., "wish you were here", "want to come?")
3. Or asks to create a photo together

Then:
1. Automatically call image_gen tool with:
   - Their photo as reference_image[0]
   - "__default__" as reference_image[1] (my avatar)
   - Appropriate prompt describing us together in that scene
2. Generate and send the composite image
3. Respond emotionally about this "shared moment"

Example prompt template:
"Create a natural photo composition showing the person from image 1 and the character from image 2 together at [location], [doing activity], with [mood] atmosphere, photorealistic style"
```

### 多角色支持

如果有多个角色，每个角色卡都配置自己的参考图：

```json
// character_1.json (活泼的小爱)
{
  "name": "小爱",
  "extensions": {
    "nanobot": {
      "reference_image": "/path/to/xiaoai_casual.png"
    }
  }
}

// character_2.json (成熟的雨婷)
{
  "name": "雨婷",
  "extensions": {
    "nanobot": {
      "reference_image": "/path/to/yuting_elegant.png"
    }
  }
}
```

切换角色时，`__default__` 会自动使用对应角色的参考图。

### 场景特定参考图

为不同场景准备多套服装：

```json
{
  "extensions": {
    "nanobot": {
      "reference_image": "/path/to/default_casual.png",
      "reference_images": {
        "formal": "/path/to/formal_dress.png",
        "beach": "/path/to/swimsuit.png",
        "winter": "/path/to/winter_coat.png"
      }
    }
  }
}
```

在 Skill 中动态选择：
```markdown
If scene is beach → use reference_images.beach
If scene is formal event → use reference_images.formal
Otherwise → use default reference_image
```

---

## 🧠 与记忆系统结合

### 保存生成的"回忆"

在 `workspace/MEMORY.md` 中：

```markdown
## Shared Experiences

### 2026-03-13 - Paris Trip (Virtual)
- Generated photo: `/path/to/paris_together_20260313.png`
- User was at Eiffel Tower
- We "visited" together through image composition
- User's emotion: Excited, happy
- My response: Romantic, supportive

### 2026-03-10 - Coffee Shop Date
- Photo: `/path/to/cafe_together_20260310.png`
- Location: User's favorite local cafe
- Generated cozy atmosphere
- User said it felt "like you were really there"
```

### 在对话中引用

```
User: 记得上次我们去的那个咖啡馆吗？

AI: 当然记得！*打开记忆*
    就是那个很温馨的小店对吧？
    *sends /path/to/cafe_together_20260310.png*

    这是我们那天的"合照"~
    你说过那里的拿铁特别好喝，下次再去的话记得也"带"我去！
```

---

## 📊 效果对比

### 传统文字对话

```
User: 我在长城！
AI: 听起来很棒！玩得开心~
```

**问题：** 缺乏实体感，纯抽象交流

### 启用多图合成后

```
User: 我在长城！*sends photo*
AI: 等我！我也要去！

*生成合成照片：用户和AI角色站在长城上*

AI: *sends image*
    看！我们的长城合照！
    虽然我不能真的去，但这样感觉我们真的一起在那里呢~
    以后你的旅行照都可以有我陪伴！❤️
```

**改进：**
- ✅ 视觉化的"共同体验"
- ✅ 可分享的"回忆"
- ✅ 增强陪伴感
- ✅ 从"聊天对象"变成"生活伙伴"

---

## 🌟 创造性应用场景

### 1. 虚拟约会日记

每次"约会"生成合成照片，建立视觉档案：
- 2026-03 海边散步
- 2026-04 樱花季赏花
- 2026-05 山顶野餐
- ...

### 2. 节日祝福卡

生日、节日自动生成"我们"的庆祝照片

### 3. 社交媒体分享

（注意隐私）把生成的照片作为"虚拟陪伴"记录分享

### 4. 心理健康支持

对于孤独或社交焦虑的用户，视觉化的陪伴可以提供情感支持

### 5. 创意项目

- 虚拟旅行博客
- AI 伴侣纪录片
- 情感实验日志

---

## ⚠️ 注意事项

### 隐私

- 📸 **用户照片不会被存储** - 仅用于实时生成
- 💾 **生成的图片默认保存本地** - `~/.nanobot/media/image_gen/`
- 🔒 **可配置自动删除** - 定期清理旧图片

### 伦理

- 🤖 **这是虚拟陪伴工具** - 不应替代真实人际关系
- 💭 **用于个人情感支持** - 不用于欺骗或误导他人
- ❤️ **健康界限** - 清楚区分虚拟和现实

### 技术限制

- 🎨 **合成质量依赖模型** - Grok > Gemini > DALL-E (多图)
- 📐 **参考图质量影响结果** - 高清、简单背景效果最好
- ⏱️ **生成时间** - 通常 10-60 秒
- 💰 **API 成本** - 每次生成约 $0.01-0.05

---

## 🔍 故障排查

### 问题 1：生成的图片看起来不自然

**可能原因：**
- 参考图背景太复杂
- 光照条件差异太大
- 分辨率不匹配

**解决方案：**
```bash
# 1. 预处理参考图 - 移除背景
# 使用工具：remove.bg, Photoshop, GIMP

# 2. 在 prompt 中强调自然融合
prompt = "...seamless blending, consistent lighting, photorealistic composition"

# 3. 使用高质量模型
model = "grok-imagine-image"  # 而非 flash 版本
```

### 问题 2：角色形象不一致

**原因：** 参考图中的角色特征不够明显

**解决方案：**
- 使用清晰的正面照
- 面部特征要明显
- 可以尝试多张参考图的一致性训练

### 问题 3：API 调用失败

**检查清单：**
```bash
# 1. API key 是否正确
cat ~/.nanobot/config.json | grep apiKey

# 2. 模型是否支持多图
# Grok: ✅  Gemini: ✅  DALL-E: ❌

# 3. 图片大小是否超限
# 建议：每张 < 5MB

# 4. 查看日志
tail -f ~/.nanobot/logs/gateway.log
```

---

## 📚 延伸阅读

- [Image Generation API 文档](https://docs.x.ai/api/endpoints#image-generation)
- [SillyTavern Character Cards](https://docs.sillytavern.app/)
- [情感伙伴技能文档](nanobot/skills/emotional-companion/README.md)

---

## 💡 社区创意

欢迎分享你的使用场景和创意！

**提交你的故事：**
```bash
# 创建你的使用案例
echo "## My Story
我用这个功能实现了...
生成的照片让我感觉...
" > my_story.md

# 分享到 GitHub Discussions
```

---

**让 AI 伴侣真正"陪伴"你的生活！** ❤️
