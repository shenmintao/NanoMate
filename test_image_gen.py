"""Test script for imageGen API configuration."""

import asyncio
import httpx


async def test_image_gen():
    """Test the image generation API with current configuration."""

    # Your current configuration
    api_key = "sk-4IXi9dU89I1hG7bKjgYWgh7EbwXeNwxzT0zBVtjzSxe8ZdHy"
    base_url = "https://api.ikuncode.cc/v1"
    model = "gemini-3.1-flash-image-preview"

    url = f"{base_url}/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    body = {
        "model": model,
        "prompt": "A cute cat wearing a hat",
        "size": "1024x1024",
        "n": 1,
    }

    print(f"Testing image generation API...")
    print(f"URL: {url}")
    print(f"Model: {model}")
    print(f"Prompt: {body['prompt']}")
    print("-" * 60)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            print("Sending request...")
            resp = await client.post(url, json=body, headers=headers)

            print(f"Status Code: {resp.status_code}")
            print(f"Response Headers: {dict(resp.headers)}")
            print("-" * 60)

            if resp.status_code == 200:
                data = resp.json()
                print("✅ SUCCESS!")
                print(f"Response: {data}")

                if "data" in data and len(data["data"]) > 0:
                    image_data = data["data"][0]
                    if "url" in image_data:
                        print(f"\n🖼️  Image URL: {image_data['url']}")
                    elif "b64_json" in image_data:
                        print(f"\n🖼️  Image returned as base64 (length: {len(image_data['b64_json'])} chars)")
            else:
                print("❌ FAILED!")
                try:
                    error_data = resp.json()
                    print(f"Error Response: {error_data}")
                except:
                    print(f"Error Text: {resp.text[:500]}")

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        try:
            error_detail = e.response.json()
            print(f"Error Detail: {error_detail}")
        except:
            print(f"Error Text: {e.response.text[:500]}")
    except httpx.TimeoutException:
        print("❌ Request timed out (120s)")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_image_gen())
