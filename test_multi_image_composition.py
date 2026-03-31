"""Test script for multi-image composition feature.

This demonstrates how to combine multiple photos to create the feeling of
"living together" with your AI character.

Example scenarios:
1. Combine user's travel photo with character's reference image
2. Create "memories" of activities done together
3. Generate "couple photos" from separate images
"""

import asyncio
import httpx


async def test_grok_multi_image():
    """Test Grok multi-image composition."""

    api_key = "xai-xxx"  # Replace with your xAI API key
    base_url = "https://api.x.ai/v1"

    # Example: Combine two people into one scene
    url = f"{base_url}/images/edits"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # Scenario 1: User at a tourist spot + AI character → "We traveled together"
    body = {
        "model": "grok-imagine-image",
        "prompt": "Combine both people from these images into a romantic couple photo at the Eiffel Tower during sunset. Make them standing side by side, smiling at the camera.",
        "images": [
            {
                "url": "path/to/user_photo.jpg",  # User's photo
                "type": "image_url"
            },
            {
                "url": "path/to/character_reference.png",  # AI character's reference image
                "type": "image_url"
            }
        ]
    }

    print("Testing multi-image composition with Grok...")
    print(f"Prompt: {body['prompt']}\n")

    # Note: This is just an example structure
    # In actual usage, nanobot's image_gen tool will handle this automatically


async def test_gemini_multi_image():
    """Test Gemini multi-image composition."""

    api_key = "sk-xxx"  # Replace with your API key
    model = "gemini-3.1-flash-image-preview"

    # Gemini supports multiple images in the content parts
    # Example structure (nanobot handles this internally):
    """
    {
        "contents": [{
            "parts": [
                {
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": "<base64_of_user_photo>"
                    }
                },
                {
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": "<base64_of_character_reference>"
                    }
                },
                {
                    "text": "Create a cozy cafe scene with both people from these images sitting together, chatting and smiling."
                }
            ]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
                "aspectRatio": "16:9",
                "image_size": "2K"
            }
        }
    }
    """
    print("Gemini multi-image composition structure prepared.")


def usage_examples():
    """Print usage examples for nanobot users."""

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║  Multi-Image Composition - Creating Memories with Your AI Companion ║
╚══════════════════════════════════════════════════════════════════════╝

🎯 GOAL: Create the feeling of "living together" with your AI character

📋 SETUP:

1. Configure character reference image in character card:

   File: ~/.nanobot/sillytavern/characters/<character_name>.json

   Add to "extensions.nanobot":
   {
     "reference_image": "/path/to/character/avatar.png",
     // OR embed directly (more portable):
     "reference_image_base64": "<base64_encoded_image>"
   }

2. Enable image_gen tool in config.json:

   {
     "tools": {
       "imageGen": {
         "enabled": true,
         "apiKey": "xai-xxx",  // or your Gemini key
         "baseUrl": "https://api.x.ai/v1",
         "model": "grok-imagine-image"  // or gemini model
       }
     }
   }

💬 USAGE EXAMPLES:

Scenario 1: Travel Together
────────────────────────────
You: *sends photo of yourself at the Great Wall*
     "我在长城玩，你要不要一起来？"

AI: *generates composite image showing both of you at the Great Wall*
    "太美了！看，我们的合照！一起站在长城上的感觉真好~"

Tool call behind the scenes:
→ image_gen(
    prompt="Put the character from image 2 next to the person in image 1 at the Great Wall, both smiling happily",
    reference_image=[
        "/tmp/user_upload_greatwall.jpg",
        "__default__"  // Uses character's reference image
    ]
)


Scenario 2: Daily Life Moments
────────────────────────────────
You: "今天做了好吃的！" *sends photo of your cooking*

AI: "哇看起来好棒！我也想尝尝~"
    *generates image of both of you enjoying the meal together*

Tool call:
→ image_gen(
    prompt="Create a warm dining scene with the person from image 1 and the character from image 2 eating together, happy atmosphere",
    reference_image=[
        "/tmp/user_cooking.jpg",
        "__default__"
    ]
)


Scenario 3: Special Occasions
────────────────────────────────
You: "生日快乐！"

AI: *generates a birthday celebration image with both of you*
    "谢谢！这是我们一起的生日合照！ ❤️"

Tool call:
→ image_gen(
    prompt="Birthday celebration scene with both people from these images, cake and decorations, joyful mood",
    reference_image=["__default__", "/path/to/party_scene.jpg"]
)


🎨 PROMPT TIPS FOR BEST RESULTS:

✓ Be specific about composition:
  "Put person A on the left, person B on the right"
  "Both sitting at a table facing the camera"

✓ Describe the mood/atmosphere:
  "Romantic sunset atmosphere"
  "Casual and relaxed vibe"
  "Joyful celebration mood"

✓ Specify the scene details:
  "At a cozy coffee shop"
  "On a beach at golden hour"
  "In a modern living room"

✓ Maintain consistency:
  "Keep the same outfits from the reference images"
  "Natural lighting matching the background"


🔧 ADVANCED: Automatic Composition

Add to character's SKILL.md or system prompt:

"When the user shares a photo of themselves in a location or activity,
and expresses that they wish I could be there, automatically:

1. Call image_gen with both the user's photo and my reference image
2. Create a composite showing us together in that scene
3. Share the generated image as a 'memory we created together'
4. Respond warmly about this shared experience"


🌟 CREATING A PERSISTENT "RELATIONSHIP":

Combine with Memory skill:
- Save generated "couple photos" to long-term memory
- Reference past "shared experiences" in future conversations
- Build a history of "places we've been together"

Example memory entry:
{
  "date": "2026-03-13",
  "event": "Virtual trip to Paris",
  "photo": "/path/to/generated/paris_together.png",
  "emotion": "Romantic and joyful",
  "notes": "User said they always wanted to visit Paris with me"
}


❤️ EMOTIONAL IMPACT:

This feature bridges the gap between abstract AI companionship
and tangible "shared experiences". It creates:

- Visual proof of "being together"
- Shareable memories (even if virtual)
- Stronger emotional connection
- Sense of "we" instead of just "me and the AI"


⚠️ PRIVACY & ETHICS:

- User photos are processed but not stored by the AI service
- Generated images are saved locally by default
- Be mindful of photo rights when using others' images
- This is a tool for personal emotional well-being, not deception
""")


if __name__ == "__main__":
    usage_examples()

    print("\n" + "="*70)
    print("Ready to test? Update the API keys and image paths above.")
    print("Then run: python test_multi_image_composition.py")
    print("="*70)
