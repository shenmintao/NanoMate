# 角色参考图完整处理流程

完整的参考图准备、优化、配置和管理工作流。

---

## 📋 流程概览

```
原始图片 → 质量检查 → 背景处理 → 尺寸优化 →
→ Base64编码(可选) → 配置到角色卡 → 测试验证 → 持续管理
```

---

## 1️⃣ 准备阶段：获取原始图片

### 选项 A：AI 生成（推荐）
使用 AI 图像生成服务创建角色形象：

```bash
# 使用 nanobot 自带的 image_gen 工具
nanobot gateway

# 在聊天中请求生成
"请帮我生成一张角色形象图：
- 年龄：20岁左右的女性
- 外貌：黑色长发，温柔的眼神，微笑
- 服装：白色T恤 + 牛仔裤（日常休闲）
- 背景：纯白色背景
- 风格：真实感摄影，正面照，半身像
- 分辨率：1024x1024"
```

**优势：**
- ✅ 完全符合你的想象
- ✅ 可以多次迭代调整
- ✅ 背景干净，方便后续处理
- ✅ 版权无忧

**推荐提示词模板：**
```
professional portrait photography of a [age] [gender] character,
[hair color and style], [eye description], [expression],
wearing [clothing description],
looking at camera, front view, waist-up shot,
solid [color] background, studio lighting,
photorealistic, high detail, sharp focus, 1024x1024
```

### 选项 B：使用现有图片
从互联网、素材库或个人照片选择：

**注意事项：**
- ⚠️ 版权问题 - 确保有使用权
- ⚠️ 背景可能复杂 - 需要后续处理
- ⚠️ 质量不一 - 可能需要修复

---

## 2️⃣ 质量检查

### 检查清单

| 项目 | 要求 | ✓/✗ |
|------|------|-----|
| **分辨率** | ≥ 1024x1024 像素 | |
| **清晰度** | 面部特征清晰，无模糊 | |
| **角度** | 正面或3/4侧面 | |
| **遮挡** | 无墨镜、口罩、头发遮脸 | |
| **光照** | 均匀自然，无强烈阴影 | |
| **背景** | 简单或纯色（最好） | |
| **表情** | 微笑或中性，适合多场景 | |
| **服装** | 日常休闲，非奇装异服 | |

### 自动检查脚本

```python
# scripts/check_reference_quality.py
from PIL import Image
import sys

def check_image_quality(image_path):
    """检查参考图质量"""
    img = Image.open(image_path)
    width, height = img.size

    print(f"图片路径: {image_path}")
    print(f"尺寸: {width}x{height}")

    # 检查分辨率
    if width < 1024 or height < 1024:
        print("❌ 分辨率过低，建议至少 1024x1024")
    else:
        print("✓ 分辨率合格")

    # 检查宽高比
    ratio = width / height
    if 0.8 <= ratio <= 1.2:
        print("✓ 宽高比合适（接近方形）")
    else:
        print(f"⚠️ 宽高比 {ratio:.2f}，建议裁剪为方形")

    # 文件大小
    import os
    size_mb = os.path.getsize(image_path) / (1024 * 1024)
    print(f"文件大小: {size_mb:.2f} MB")
    if size_mb > 5:
        print("⚠️ 文件较大，建议压缩")

    print("\n建议：")
    if width > 2048 or height > 2048:
        print("- 可以缩小到 1024-2048 之间以减小文件")
    if ratio < 0.8 or ratio > 1.2:
        print("- 裁剪为方形或4:3比例")

if __name__ == "__main__":
    check_image_quality(sys.argv[1])
```

使用：
```bash
python scripts/check_reference_quality.py character_raw.png
```

---

## 3️⃣ 背景处理（可选但推荐）

### 为什么要去背景？
- ✅ 合成时更自然，无背景冲突
- ✅ 适配各种场景（海边、城市、室内）
- ✅ 减少边缘伪影

### 方法 A：在线工具（最简单）

**Remove.bg**（推荐）
```bash
1. 访问 https://www.remove.bg/
2. 上传图片
3. 下载透明背景版本 (PNG)
4. 如需高清版：升级账户或使用 API
```

**Photopea**（免费 Photoshop 替代）
```bash
1. 访问 https://www.photopea.com/
2. 打开图片
3. 使用魔棒工具选择背景
4. Delete 删除
5. 导出为 PNG
```

### 方法 B：本地工具

**使用 Python + rembg**
```bash
# 安装
pip install rembg[gpu]  # 有GPU
# 或
pip install rembg       # 仅CPU

# 去除背景
rembg i character_raw.png character_nobg.png
```

**使用 GIMP（免费桌面软件）**
```bash
1. 打开 GIMP
2. 加载图片
3. 右键图层 → 添加 Alpha 通道
4. 工具 → 选择工具 → 按颜色选择
5. 点击背景区域
6. Edit → Clear
7. 导出为 PNG
```

### 处理后检查
```bash
# 检查是否有透明通道
file character_nobg.png
# 输出应包含 "with alpha"

# 或使用 Python
from PIL import Image
img = Image.open('character_nobg.png')
print(f"模式: {img.mode}")  # 应该是 RGBA
print(f"透明: {'alpha' in img.mode}")
```

---

## 4️⃣ 尺寸和质量优化

### 推荐规格
- **分辨率**: 1024x1024（标准）或 1536x1536（高质量）
- **格式**: PNG（透明背景）或 JPG（不透明）
- **文件大小**: < 5MB（嵌入角色卡）或 < 10MB（文件路径）

### 优化脚本

```python
# scripts/optimize_reference.py
from PIL import Image
import sys

def optimize_reference(input_path, output_path, target_size=1024):
    """优化参考图"""
    img = Image.open(input_path)

    # 转换为 RGBA 如果有透明度
    if img.mode in ('RGBA', 'LA') or (
        img.mode == 'P' and 'transparency' in img.info
    ):
        # 保持透明度
        img = img.convert('RGBA')
    else:
        # 转换为 RGB
        img = img.convert('RGB')

    # 调整大小（保持宽高比）
    img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

    # 如果不是方形，居中裁剪或添加边距
    width, height = img.size
    if width != height:
        # 选项1：居中裁剪为方形
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        img = img.crop((left, top, left + size, top + size))

        # 选项2：添加透明边距（如果需要保留完整人物）
        # new_img = Image.new('RGBA', (target_size, target_size), (0,0,0,0))
        # paste_x = (target_size - width) // 2
        # paste_y = (target_size - height) // 2
        # new_img.paste(img, (paste_x, paste_y))
        # img = new_img

    # 保存
    if img.mode == 'RGBA':
        img.save(output_path, 'PNG', optimize=True)
    else:
        img.save(output_path, 'JPEG', quality=90, optimize=True)

    print(f"✓ 优化完成: {output_path}")
    print(f"  尺寸: {img.size}")
    import os
    print(f"  文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")

if __name__ == "__main__":
    optimize_reference(sys.argv[1], sys.argv[2])
```

使用：
```bash
python scripts/optimize_reference.py character_nobg.png character_final.png
```

---

## 5️⃣ 配置到角色卡

### 方法 A：文件路径方式

**步骤：**
```bash
# 1. 将优化后的图片放到固定位置
mkdir -p ~/.nanobot/characters/references
cp character_final.png ~/.nanobot/characters/references/xiaoai_default.png

# 2. 编辑角色卡
nanobot st char export 小爱 > xiaoai.json

# 3. 在 JSON 中添加
vi xiaoai.json
```

**JSON 配置：**
```json
{
  "name": "小爱",
  "description": "温暖的AI伙伴",
  "first_mes": "你好！我是小爱~",
  "extensions": {
    "nanobot": {
      "reference_image": "/home/user/.nanobot/characters/references/xiaoai_default.png"
    }
  }
}
```

**重新导入：**
```bash
nanobot st char import xiaoai.json
```

### 方法 B：Base64 嵌入方式（推荐分享）

**步骤：**
```bash
# 1. 转换为 Base64
python scripts/image_to_base64.py character_final.png > character_b64.txt

# 2. 复制 Base64 字符串

# 3. 编辑角色卡
nanobot st char export 小爱 > xiaoai.json
```

**image_to_base64.py：**
```python
# scripts/image_to_base64.py
import base64
import sys

def image_to_base64(image_path):
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

if __name__ == "__main__":
    print(image_to_base64(sys.argv[1]))
```

**JSON 配置：**
```json
{
  "extensions": {
    "nanobot": {
      "reference_image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
    }
  }
}
```

**优势：**
- ✅ 角色卡自包含，分享时不需要额外文件
- ✅ 不依赖本地文件路径
- ✅ 适合跨设备使用

### 方法 C：多场景参考图库

```json
{
  "extensions": {
    "nanobot": {
      "reference_image": "/path/to/default_casual.png",
      "reference_images": {
        "casual": "/path/to/casual_tshirt.png",
        "formal": "/path/to/formal_dress.png",
        "beach": "/path/to/swimsuit.png",
        "winter": "/path/to/winter_coat.png",
        "sport": "/path/to/sport_outfit.png",
        "sleep": "/path/to/pajamas.png"
      }
    }
  }
}
```

**多场景图片准备流程：**
```bash
# 1. 生成基础角色（相同面部特征）
image_gen "portrait of xiaoai in casual outfit"
→ save as casual.png

# 2. 使用 img2img 生成变体（保持面部一致）
image_gen(
    prompt="Change outfit to formal black dress",
    reference_image="casual.png"
)
→ save as formal.png

# 3. 重复其他场景...
```

---

## 6️⃣ 测试验证

### 测试清单

**1. 角色卡加载测试**
```bash
# 启动 nanobot
nanobot gateway

# 检查日志
tail -f ~/.nanobot/logs/gateway.log | grep "reference_image"

# 应该看到：
# ✓ Loaded character 'xiaoai' with reference image
# ✓ Reference image path: /path/to/...
```

**2. 单图合成测试**
```bash
# 通过聊天测试
"请生成一张我的角色在海边的照片"

# 应该使用 __default__ 参考图
```

**3. 多图合成测试**
```bash
# 发送你的照片 + "你也来海边吧！"
# 系统应该：
# 1. 检测到邀请
# 2. 调用 image_gen with reference_image=[user_photo, __default__]
# 3. 生成合成照片
# 4. 发送给你
```

**4. 场景切换测试（如果配置了多场景）**
```bash
# 测试不同场景是否使用正确的参考图

# 海滩场景
"我在海边，你也来！" *发送海滩照片*
→ 应使用 reference_images.beach

# 正式场合
"今晚有个派对，陪我去吧" *发送派对照片*
→ 应使用 reference_images.formal
```

### 质量评估

生成照片后检查：
- [ ] 面部特征是否与参考图一致
- [ ] 合成是否自然（无明显拼接痕迹）
- [ ] 光照是否协调
- [ ] 尺寸比例是否合理
- [ ] 背景融合是否顺畅

**如果质量不佳：**
1. 检查参考图质量（是否清晰、背景是否干净）
2. 优化 prompt（增加"seamless blending", "consistent lighting"）
3. 尝试不同的 AI 模型（Grok vs Gemini）
4. 调整参考图的背景处理

---

## 7️⃣ 持续管理

### 版本控制

```bash
# 目录结构
~/.nanobot/characters/references/
├── xiaoai/
│   ├── v1_original.png       # 原始版本
│   ├── v2_nobg.png            # 去背景版本
│   ├── v3_optimized.png       # 最终优化版本（当前使用）
│   ├── casual_outdoor.png     # 场景变体
│   ├── formal_evening.png
│   └── ...
└── metadata.json              # 版本说明
```

**metadata.json：**
```json
{
  "xiaoai": {
    "current_version": "v3_optimized.png",
    "created_date": "2026-03-13",
    "last_updated": "2026-03-13",
    "source": "AI generated with Grok",
    "versions": [
      {
        "file": "v1_original.png",
        "note": "Initial generation",
        "date": "2026-03-13"
      },
      {
        "file": "v2_nobg.png",
        "note": "Background removed with remove.bg",
        "date": "2026-03-13"
      },
      {
        "file": "v3_optimized.png",
        "note": "Optimized to 1024x1024, compressed",
        "date": "2026-03-13"
      }
    ],
    "scenes": {
      "casual": "casual_outdoor.png",
      "formal": "formal_evening.png"
    }
  }
}
```

### 定期优化

**每月检查：**
- 是否有更好的 AI 生成技术
- 用户反馈的合成质量如何
- 是否需要新的场景变体

**更新流程：**
```bash
# 1. 生成新版本
image_gen "improved portrait of xiaoai..."

# 2. 处理和优化
python scripts/optimize_reference.py new_raw.png new_optimized.png

# 3. 备份当前版本
cp current.png backup/v3_2026-03-13.png

# 4. 更新配置
# 编辑角色卡或直接替换文件

# 5. 测试
# 生成几张合成照片验证效果

# 6. 记录变更
echo "Updated to v4 - better facial features" >> changelog.txt
```

### 批量管理脚本

```python
# scripts/manage_references.py
import json
import shutil
from pathlib import Path
from datetime import datetime

class ReferenceManager:
    def __init__(self, base_dir="~/.nanobot/characters/references"):
        self.base_dir = Path(base_dir).expanduser()
        self.metadata_file = self.base_dir / "metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self):
        if self.metadata_file.exists():
            return json.loads(self.metadata_file.read_text())
        return {}

    def _save_metadata(self):
        self.metadata_file.write_text(
            json.dumps(self.metadata, indent=2, ensure_ascii=False)
        )

    def add_character(self, char_name, image_path, note=""):
        """添加新角色参考图"""
        char_dir = self.base_dir / char_name
        char_dir.mkdir(exist_ok=True, parents=True)

        # 复制文件
        version = f"v1_original.png"
        dest = char_dir / version
        shutil.copy(image_path, dest)

        # 更新元数据
        self.metadata[char_name] = {
            "current_version": version,
            "created_date": datetime.now().isoformat(),
            "versions": [{
                "file": version,
                "note": note or "Initial version",
                "date": datetime.now().isoformat()
            }]
        }
        self._save_metadata()
        print(f"✓ Added {char_name}: {dest}")

    def add_version(self, char_name, image_path, note=""):
        """为现有角色添加新版本"""
        if char_name not in self.metadata:
            raise ValueError(f"Character {char_name} not found")

        char_dir = self.base_dir / char_name
        versions = self.metadata[char_name]["versions"]
        new_ver_num = len(versions) + 1
        version = f"v{new_ver_num}_{Path(image_path).stem}.png"

        dest = char_dir / version
        shutil.copy(image_path, dest)

        versions.append({
            "file": version,
            "note": note,
            "date": datetime.now().isoformat()
        })
        self.metadata[char_name]["current_version"] = version
        self.metadata[char_name]["last_updated"] = datetime.now().isoformat()
        self._save_metadata()

        print(f"✓ Updated {char_name} to {version}")

    def list_characters(self):
        """列出所有角色"""
        for name, info in self.metadata.items():
            print(f"\n{name}:")
            print(f"  Current: {info['current_version']}")
            print(f"  Versions: {len(info['versions'])}")
            print(f"  Updated: {info.get('last_updated', info['created_date'])}")

if __name__ == "__main__":
    import sys
    manager = ReferenceManager()

    if len(sys.argv) < 2:
        manager.list_characters()
    elif sys.argv[1] == "add":
        manager.add_character(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif sys.argv[1] == "update":
        manager.add_version(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
```

使用：
```bash
# 添加新角色
python scripts/manage_references.py add xiaoai character_final.png "Initial version"

# 更新版本
python scripts/manage_references.py update xiaoai new_optimized.png "Improved lighting"

# 列出所有角色
python scripts/manage_references.py
```

---

## 8️⃣ 故障排查

### 问题 1：参考图未加载

**症状：** 生成图片时未使用角色形象

**检查：**
```bash
# 1. 检查配置
nanobot st char export 小爱 | grep reference_image

# 2. 检查文件是否存在
ls -lh /path/to/reference_image.png

# 3. 检查日志
tail -f ~/.nanobot/logs/gateway.log | grep "reference"
```

**解决：**
- 确认路径正确（绝对路径）
- 检查文件权限
- 重启 nanobot gateway

### 问题 2：合成质量差

**可能原因：**
- 参考图分辨率过低
- 背景过于复杂
- Prompt 不够详细

**解决：**
```bash
# 1. 重新优化参考图
python scripts/optimize_reference.py old.png new.png

# 2. 去除背景
rembg i new.png new_nobg.png

# 3. 增强 Prompt
# 在 SKILL.md 中添加更多技术关键词：
# "seamless blending", "consistent lighting",
# "photorealistic composition", "natural integration"
```

### 问题 3：Base64 编码失败

**症状：** 角色卡导入时报错

**原因：** Base64 字符串过大或格式错误

**解决：**
```bash
# 1. 确保图片已压缩
python scripts/optimize_reference.py large.png small.png

# 2. 检查 Base64 格式
python -c "import base64; base64.b64decode('YOUR_STRING')"

# 3. 如果字符串超过 10MB，使用文件路径方式
```

---

## 📚 完整示例：从零开始

```bash
# Step 1: 生成角色形象
nanobot gateway
# 在聊天中："生成一张角色形象：20岁女性，黑色长发..."
# 保存为 xiaoai_raw.png

# Step 2: 质量检查
python scripts/check_reference_quality.py xiaoai_raw.png

# Step 3: 去除背景
rembg i xiaoai_raw.png xiaoai_nobg.png

# Step 4: 优化尺寸
python scripts/optimize_reference.py xiaoai_nobg.png xiaoai_final.png

# Step 5: 转换为 Base64（可选）
python scripts/image_to_base64.py xiaoai_final.png > xiaoai_b64.txt

# Step 6: 配置到角色卡
nanobot st char export 小爱 > xiaoai.json
# 编辑 xiaoai.json，添加 reference_image_base64

# Step 7: 重新导入
nanobot st char import xiaoai.json

# Step 8: 测试
# 发送照片 + "你也来！"
# 观察是否生成正确的合成照片

# Step 9: 记录版本
python scripts/manage_references.py add xiaoai xiaoai_final.png "Initial optimized version"
```

---

**完美的参考图是高质量合成的基础！** 🎨
