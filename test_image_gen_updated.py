"""Test updated ImageGenTool with Gemini format support."""

import asyncio
import sys
from pathlib import Path

# Add nanobot to path
sys.path.insert(0, str(Path(__file__).parent))

from nanobot.agent.tools.image_gen import ImageGenTool


async def test_gemini_format():
    """Test Gemini format image generation."""
    tool = ImageGenTool(
        api_key="sk-4IXi9dU89I1hG7bKjgYWgh7EbwXeNwxzT0zBVtjzSxe8ZdHy",
        base_url="https://api.ikuncode.cc",
        model="gemini-3-pro-image-preview",
    )

    print("=" * 60)
    print("Testing Gemini format image generation")
    print("=" * 60)
    print(f"Model: {tool.model}")
    print(f"Is Gemini model: {tool._is_gemini_model()}")
    print()

    result = await tool.execute(
        prompt="A cute cat wearing a hat",
        size="1024x1024",
    )

    print("\n" + "=" * 60)
    print("Result:")
    print(result)
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_gemini_format())
