# TTS（文本转语音）配置指南

nanobot 支持两种 TTS 方案：**Edge TTS**（免费）和 **GPT-SoVITS**（自托管高质量）。

---

## 🎤 方案 1：Edge TTS（推荐入门）

### 优点
- ✅ 完全免费，无需 API 密钥
- ✅ 零配置，开箱即用
- ✅ 支持多种语言和声音
- ✅ 质量较好，自然流畅

### 安装

```bash
pip install edge-tts
```

### 配置

在 `~/.nanobot/config.json` 中添加：

```json
{
  "tts": {
    "enabled": true,
    "provider": "edge",
    "autoSend": true,
    "edgeVoice": "zh-CN-XiaoxiaoNeural",
    "edgeRate": "+0%",
    "edgeVolume": "+0%"
  },
  "sillytavern": {
    "enabled": true,
    "responseFilterTag": "speech"
  }
}
```

### 可用声音列表

**中文：**
- `zh-CN-XiaoxiaoNeural` - 晓晓（女声，温柔）
- `zh-CN-XiaoyiNeural` - 晓伊（女声，活泼）
- `zh-CN-YunjianNeural` - 云健（男声，成熟）
- `zh-CN-YunxiNeural` - 云希（男声，年轻）
- `zh-CN-YunyangNeural` - 云扬（男声，新闻播报）

**英文：**
- `en-US-JennyNeural` - 珍妮（女声，友好）
- `en-US-GuyNeural` - 盖伊（男声，自然）
- `en-US-AriaNeural` - 艾莉亚（女声，专业）

**日文：**
- `ja-JP-NanamiNeural` - 七海（女声）
- `ja-JP-KeitaNeural` - 启太（男声）

查看所有可用声音：
```bash
edge-tts --list-voices
```

---

## 🎵 方案 2：GPT-SoVITS（高级用户）

### 优点
- ✅ 声音克隆，可以使用自己的声音
- ✅ 音质更自然，情感表达更丰富
- ✅ 完全自托管，数据隐私

### 前置条件

1. 已在 NAS 上部署 GPT-SoVITS
2. GPT-SoVITS 服务运行在 `http://192.168.10.50:9880`（示例地址）
3. 准备好参考音频和对应文本

### 配置

在 `~/.nanobot/config.json` 中添加：

```json
{
  "tts": {
    "enabled": true,
    "provider": "sovits",
    "autoSend": true,
    "sovitsApiUrl": "http://192.168.10.50:9880",
    "sovitsReferWavPath": "/app/reference_audio/my_voice.wav",
    "sovitsPromptText": "这是参考音频的文本内容。",
    "sovitsPromptLanguage": "zh",
    "sovitsTextLanguage": "zh",
    "sovitsCutPunc": "，。",
    "sovitsSpeed": 1.0
  },
  "sillytavern": {
    "enabled": true,
    "responseFilterTag": "speech"
  }
}
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `sovitsApiUrl` | GPT-SoVITS API 地址 | `http://127.0.0.1:9880` |
| `sovitsReferWavPath` | 参考音频文件路径 | **必填** |
| `sovitsPromptText` | 参考音频的文本 | **必填** |
| `sovitsPromptLanguage` | 参考音频语言（zh/en/ja） | `zh` |
| `sovitsTextLanguage` | 合成文本语言 | `zh` |
| `sovitsSpeed` | 语速（0.5-2.0） | `1.0` |

---

## 🔧 启用语音模式

TTS 需要配合 **SillyTavern 的 speech 过滤模式** 使用，以去除动作描述。

### 1. 配置 response_filter_tag

```json
{
  "sillytavern": {
    "enabled": true,
    "responseFilterTag": "speech"  // ← 关键！
  }
}
```

### 2. 导入支持 speech 标签的角色卡

```bash
# 使用情感伙伴角色（已内置 speech 标签支持）
nanobot st char import nanobot/skills/emotional-companion/examples/companion_character_with_speech.json
nanobot st worldinfo import nanobot/skills/emotional-companion/examples/worldinfo_speech_format.json
```

### 工作原理

```
用户：今天好累...

AI 生成：*轻轻拍拍你的肩膀* <speech>听起来你今天很辛苦呢，要不要休息一下？</speech>

系统提取 <speech> 标签内容 → "听起来你今天很辛苦呢，要不要休息一下？"

TTS 合成 → 🔊 语音文件

发送给用户 → WhatsApp 语音消息
```

---

## 📱 在 NAS 上部署（docker-compose）

如果你的 GPT-SoVITS 已在 NAS 上运行，可以统一部署：

```yaml
version: '3.8'

services:
  nanobot-gateway:
    image: ghcr.io/shenmintao/nanobot:latest
    container_name: nanobot-gateway
    command: ["gateway"]
    volumes:
      - ./data:/root/.nanobot
    network_mode: host
    environment:
      - HTTP_PROXY=http://192.168.10.50:1080
      - HTTPS_PROXY=http://192.168.10.50:1080
    restart: unless-stopped

  nanobot-bridge:
    image: ghcr.io/shenmintao/nanobot:latest
    container_name: nanobot-bridge
    volumes:
      - ./data:/root/.nanobot
    working_dir: /app/bridge
    entrypoint: []
    command: ["npm", "start"]
    network_mode: host
    environment:
      - HTTP_PROXY=http://192.168.10.50:1080
      - HTTPS_PROXY=http://192.168.10.50:1080
    restart: unless-stopped

  # GPT-SoVITS（如果需要）
  # gpt-sovits:
  #   image: your-sovits-image:latest
  #   ports:
  #     - "9880:9880"
  #   volumes:
  #     - ./sovits-models:/app/models
  #   restart: unless-stopped
```

---

## 🧪 测试 TTS

### 使用 Python 测试

```python
import asyncio
from nanobot.providers.tts import create_tts_provider

async def test_edge_tts():
    """测试 Edge TTS"""
    tts = create_tts_provider("edge", voice="zh-CN-XiaoxiaoNeural")
    success = await tts.synthesize("你好，这是一个测试。", "test_edge.mp3")
    print(f"Edge TTS: {'成功' if success else '失败'}")

async def test_sovits():
    """测试 GPT-SoVITS"""
    tts = create_tts_provider(
        "sovits",
        api_url="http://192.168.10.50:9880",
        refer_wav_path="/path/to/reference.wav",
        prompt_text="参考音频的文本",
    )
    success = await tts.synthesize("你好，这是一个测试。", "test_sovits.wav")
    print(f"GPT-SoVITS: {'成功' if success else '失败'}")

# 运行测试
asyncio.run(test_edge_tts())
# asyncio.run(test_sovits())
```

### 命令行测试 Edge TTS

```bash
edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好，这是一个测试" --write-media test.mp3
```

---

## 📊 对比选择

| 特性 | Edge TTS | GPT-SoVITS |
|------|----------|------------|
| **成本** | 免费 | 需要 GPU（自托管） |
| **质量** | 较好 | 优秀 |
| **自然度** | 自然 | 非常自然 |
| **声音选择** | 预设声音库 | 可克隆任意声音 |
| **配置难度** | 简单 | 中等 |
| **适合场景** | 日常使用、多语言 | 个性化、高质量需求 |

### 推荐方案

- **新手/快速开始**：使用 **Edge TTS**
- **有 NAS/追求音质**：使用 **GPT-SoVITS**
- **需要多语言**：使用 **Edge TTS**（支持 70+ 语言）
- **需要特定声音**：使用 **GPT-SoVITS**（声音克隆）

---

## 🔍 常见问题

### Q1: TTS 生成的语音在哪里？
A: 默认保存在 `~/.nanobot/tts_output/` 目录

### Q2: 如何关闭 TTS？
A: 在配置中设置 `"tts": { "enabled": false }`

### Q3: Edge TTS 是否需要翻墙？
A: 不需要，Edge TTS 使用微软的公开 API

### Q4: GPT-SoVITS 如何获取参考音频？
A: 录制 5-30 秒清晰的音频，并准备对应的文本

### Q5: 能否同时用 Edge TTS 和 GPT-SoVITS？
A: 配置中只能选择一个 provider，但可以随时切换

---

## 📞 获取帮助

- 查看日志：`tail -f ~/.nanobot/logs/gateway.log`
- 提交 Issue：https://github.com/shenmintao/nanobot/issues
- 检查 TTS 配置：`nanobot status`
