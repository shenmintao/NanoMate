<div align="center">
  <img src="nanomate_logo.png" alt="NanoMate" width="500">
  <h1>NanoMate</h1>
  <p><strong>nanobot x SillyTavern, with Companion Mode</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/base-nanobot-orange" alt="Based on nanobot">
  </p>
  <p>English | <a href="./README_CN.md">中文</a></p>
</div>

**NanoMate** is an enhanced fork of [nanobot](https://github.com/HKUDS/nanobot) that integrates [SillyTavern](https://github.com/SillyTavern/SillyTavern) character cards and adds a **Companion Mode** — turning a lightweight AI assistant into an AI partner with character identity, visual imagination, emotional awareness, and voice.

## What's Different from nanobot?

| Capability | nanobot | NanoMate |
|---|---|---|
| Character Identity | None | Full **SillyTavern** integration (character cards, memory books, presets) |
| Companion Mode | None | Living-together + emotional companion skills |
| Image Generation | Basic DALL-E | Multi-model (Grok, Gemini, DALL-E) with **multi-image composition** |
| Reference Images | None | Character-consistent image gen with scene-specific outfits |
| Text-to-Speech | None | **Edge TTS** + **GPT-SoVITS** custom voice synthesis |
| WhatsApp Proxy | Basic | HTTP/HTTPS/SOCKS5 proxy support with undici |
| Translation | None | Faithful full-document translation skill |
| Deployment | Basic | Dockerized with Node.js bridge, proxy-ready |

---

## Setup Guide

### 1. Basic Installation

NanoMate is fully compatible with nanobot. Start with the standard setup:

```bash
git clone https://github.com/shenmintao/nanobot.git
cd nanobot
pip install -e .
nanobot init
```

After `nanobot init`, edit `~/.nanobot/config.json` to configure your LLM provider (see [nanobot docs](https://github.com/HKUDS/nanobot#-quick-start)).

### 2. SillyTavern Character Card

This is the foundation of NanoMate. A character card defines your AI's personality, backstory, and appearance.

**Enable SillyTavern in config:**

```jsonc
// ~/.nanobot/config.json
{
  "sillytavern": {
    "enabled": true
  }
}
```

**Prepare a character card** (JSON format). A basic card looks like:

```jsonc
{
  "name": "Aria",
  "description": "A warm, curious 25-year-old artist who loves travel and cooking.",
  "personality": "Gentle, playful, emotionally perceptive.",
  "scenario": "You and Aria are partners living together.",
  "first_mes": "Hey! I just finished painting, want to see?",
  "mes_example": "<START>\n{{user}}: How was your day?\n{{char}}: Pretty good! I tried a new watercolor technique...",
  "extensions": {
    "nanobot": {
      "reference_image": "/path/to/aria_default.png"
    }
  }
}
```

The `extensions.nanobot` section connects the character to NanoMate's visual features (see Step 4).

**Import and activate via CLI:**

```bash
# Import a character card
nanobot st char import /path/to/aria.json

# List all imported characters
nanobot st char list

# Activate a character (used for all conversations)
nanobot st char activate Aria

# Show character card details
nanobot st char show Aria

# Deactivate / delete
nanobot st char deactivate
nanobot st char delete Aria
```

**Import and activate a preset:**

```bash
# Import a SillyTavern preset (JSON exported from SillyTavern)
nanobot st preset import /path/to/my_preset.json

# List all presets
nanobot st preset list

# Activate a preset
nanobot st preset activate my_preset

# Show preset details (prompt entries, parameters)
nanobot st preset show my_preset

# Toggle specific prompt entries on/off (by index)
nanobot st preset toggle-prompt my_preset 3
nanobot st preset toggle-prompt my_preset 3,4,5   # multiple
nanobot st preset toggle-prompt my_preset 3-6     # range

# Enable/disable all prompts (optionally filter by role)
nanobot st preset enable-all my_preset
nanobot st preset disable-all my_preset --role system

# Deactivate / delete
nanobot st preset deactivate
nanobot st preset delete my_preset
```

**World Info (lorebooks):**

```bash
nanobot st wi import /path/to/lorebook.json --name "my_world"
nanobot st wi list
nanobot st wi enable my_world
nanobot st wi disable my_world
nanobot st wi delete my_world
```

**Check overall status:**

```bash
nanobot st status
# Shows: active character, active preset, world info count
```

### 3. Companion Mode (Off by Default)

Companion Mode adds two skills on top of SillyTavern: **living-together** (visual companionship) and **emotional-companion** (proactive care). Both are **off by default**. The actual companion behavior is driven by your **SillyTavern preset and character card** — the skills provide trigger rules and prompt templates, while the preset and card define the AI's personality, tone, and interaction boundaries.

#### Enabling Companion Mode

**Step 1: Prepare your SillyTavern preset and character card.**

The preset controls *how* the AI talks (tone, boundaries, roleplay depth). The character card controls *who* the AI is (personality, backstory, relationship). Companion Mode won't feel natural without both being properly set up for your use case.

- **Character card** — The `description`, `personality`, `scenario` fields establish the relationship dynamic. For companion mode, write a card that defines your AI as a partner/companion, not a generic assistant.
- **SillyTavern preset** — A preset is a JSON file containing prompt entries (system prompt, jailbreak, persona description, etc.). Export one from SillyTavern or write your own, then place it in `~/.nanobot/sillytavern/presets/`. The preset determines whether the AI will engage in roleplay-style companion interactions or stay in assistant mode.

**Step 2: Enable the skills.**

Set `always: true` in the SKILL.md frontmatter:

```yaml
# nanobot/skills/living-together/SKILL.md
---
name: living-together
always: true    # Change from false to true
---
```

```yaml
# nanobot/skills/emotional-companion/SKILL.md
---
name: emotional-companion
always: true    # Change from false to true
---
```

**Step 3: (Optional) Customize the skills.**

The skills are templates. Read them (`nanobot/skills/living-together/SKILL.md`, `nanobot/skills/emotional-companion/SKILL.md`) and adjust trigger rules, prompt templates, and behavioral constraints to match your character and preferences.

#### Living-Together Skill

Automatically generates "shared moment" images when conversation triggers it:

- User shares a travel photo + "wish you were here" -> AI composes a photo of both of you there
- Daily life scenarios (cooking, coffee shop, park) -> AI creates scenes together
- Emotional moments -> companion presence images
- Intimate scenes -> plot-driven, character-consistent visuals

Requires image generation to be set up (Step 4) and a reference image in your character card (`extensions.nanobot.reference_image`).

#### Emotional Companion Skill

Proactive care via the heartbeat system:

- Detects emotion (stress, sadness, joy) from messages and responds with empathy
- Tracks important events (exams, interviews, trips) and follows up
- Sends caring messages at appropriate times (not during sleep, not too frequently)
- Maintains emotional trends in Memory

### 4. Image Generation

Required for the living-together skill's visual features. Supports multiple providers:

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

**Supported models:**

| Model | Multi-image | Best for |
|---|---|---|
| `grok-imagine-image` (xAI) | Yes | Multi-image composition, shared photos |
| `gemini-3.1-flash-image-preview` | Yes | Fast image editing, img2img |
| `dall-e-3` (OpenAI) | No | Single text-to-image only |

#### Reference Images

To keep generated images character-consistent, add a reference image to your character card:

**Option A — File path:**
```json
{
  "extensions": {
    "nanobot": {
      "reference_image": "/path/to/character.png"
    }
  }
}
```

**Option B — Base64 embedded (portable, recommended):**
```json
{
  "extensions": {
    "nanobot": {
      "reference_image_base64": "iVBORw0KGgoAAAANSUhEUg..."
    }
  }
}
```

**Option C — Scene-specific outfits:**
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

**Reference image tips:**
- Resolution: 1024x1024 or higher
- Clear face, front or 3/4 view, no occlusion
- Simple or transparent background (use [remove.bg](https://remove.bg) or `pip install rembg`)
- PNG format for transparency support

### 5. Text-to-Speech (Optional)

Give your character a voice:

```jsonc
// ~/.nanobot/config.json
{
  "tts": {
    "enabled": true,
    "provider": "edge",          // "edge" (free) or "sovits" (custom voice)
    "edgeVoice": "zh-CN-XiaoxiaoNeural"  // See edge-tts for voice list
  }
}
```

**For custom voice cloning** (requires a running [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) server):

```jsonc
{
  "tts": {
    "enabled": true,
    "provider": "sovits",
    "sovitsApiUrl": "http://127.0.0.1:9880",
    "sovitsReferWavPath": "/path/to/reference_audio.wav",
    "sovitsPromptText": "Reference audio transcript",
    "sovitsPromptLanguage": "zh"
  }
}
```

### 6. WhatsApp Bridge (Optional)

For chatting with your companion via WhatsApp:

```bash
cd bridge
npm install
npm run build
npm run start    # Scan QR code to link
```

**Proxy support** — set environment variables:

```bash
export https_proxy=http://127.0.0.1:7890
# or
export https_proxy=socks5://127.0.0.1:1080
```

### Docker Deployment

```bash
docker compose up -d
```

The `docker-compose.yml` includes the WhatsApp bridge and proxy configuration.

---

## Project Structure (NanoMate additions)

```
nanobot/
  skills/
    living-together/     # Companion Mode: shared-moment image generation
    emotional-companion/ # Companion Mode: proactive care & mood tracking
    translate/           # Full-document translation
  sillytavern/           # Character card, memory book, preset integration
  providers/
    tts.py               # Edge TTS + GPT-SoVITS
    custom_provider.py   # Enhanced with User-Agent & proxy support
  agent/tools/
    image_gen.py         # Multi-model image generation & composition
bridge/                  # WhatsApp bridge (TypeScript/Node.js)
```

## Staying Up to Date

NanoMate tracks upstream nanobot. To pull latest changes:

```bash
git remote add upstream https://github.com/HKUDS/nanobot.git  # first time only
git fetch upstream
git merge upstream/main
```

## Credits

- [nanobot](https://github.com/HKUDS/nanobot) by HKUDS — the ultra-lightweight agent framework this project builds on
- [SillyTavern](https://github.com/SillyTavern/SillyTavern) — character card format and inspiration

## License

MIT — same as upstream nanobot.
