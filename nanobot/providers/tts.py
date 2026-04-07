"""Text-to-Speech providers for voice synthesis."""

from pathlib import Path
from typing import Protocol

import httpx
from loguru import logger


class TTSProvider(Protocol):
    """Protocol for TTS providers."""

    async def synthesize(self, text: str, output_path: str | Path) -> bool:
        """
        Synthesize text to speech and save to file.

        Args:
            text: Text to synthesize
            output_path: Path to save audio file

        Returns:
            True if successful, False otherwise
        """
        ...


class EdgeTTSProvider:
    """
    Text-to-Speech provider using Microsoft Edge TTS.

    Free, no API key required, supports multiple languages and voices.
    """

    def __init__(
        self,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        volume: str = "+0%",
    ):
        """
        Initialize EdgeTTS provider.

        Args:
            voice: Voice name (e.g., "zh-CN-XiaoxiaoNeural", "en-US-JennyNeural")
            rate: Speech rate (e.g., "+0%", "+20%", "-20%")
            volume: Speech volume (e.g., "+0%", "+20%", "-20%")
        """
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def synthesize(self, text: str, output_path: str | Path) -> bool:
        """Synthesize text using Edge TTS."""
        try:
            import edge_tts
        except ImportError:
            logger.error(
                "edge-tts not installed. Install with: pip install edge-tts"
            )
            return False

        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            communicate = edge_tts.Communicate(
                text, self.voice, rate=self.rate, volume=self.volume
            )
            await communicate.save(str(output_path))

            logger.info(f"Edge TTS synthesis complete: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Edge TTS synthesis error: {e}")
            return False

    @staticmethod
    async def list_voices() -> list[dict]:
        """List available voices."""
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            return voices
        except ImportError:
            logger.error("edge-tts not installed")
            return []


class GPTSoVITSProvider:
    """
    Text-to-Speech provider using GPT-SoVITS.

    Requires a running GPT-SoVITS server instance.
    """

    def __init__(
        self,
        api_url: str = "http://127.0.0.1:9880",
        refer_wav_path: str = "",
        prompt_text: str = "",
        prompt_language: str = "zh",
        text_language: str = "zh",
        cut_punc: str = "，。",
        top_k: int = 5,
        top_p: float = 1.0,
        temperature: float = 1.0,
        speed: float = 1.0,
    ):
        """
        Initialize GPT-SoVITS provider.

        Args:
            api_url: GPT-SoVITS API endpoint
            refer_wav_path: Reference audio file path for voice cloning
            prompt_text: Text corresponding to reference audio
            prompt_language: Language of prompt text ("zh", "en", "ja")
            text_language: Language of synthesis text
            cut_punc: Punctuation for sentence splitting
            top_k: Sampling top-k parameter
            top_p: Sampling top-p parameter
            temperature: Sampling temperature
            speed: Speech speed multiplier
        """
        self.api_url = api_url.rstrip("/")
        self.refer_wav_path = refer_wav_path
        self.prompt_text = prompt_text
        self.prompt_language = prompt_language
        self.text_language = text_language
        self.cut_punc = cut_punc
        self.top_k = top_k
        self.top_p = top_p
        self.temperature = temperature
        self.speed = speed

    async def synthesize(self, text: str, output_path: str | Path) -> bool:
        """Synthesize text using GPT-SoVITS."""
        if not self.refer_wav_path or not self.prompt_text:
            logger.error(
                "GPT-SoVITS requires refer_wav_path and prompt_text configuration"
            )
            return False

        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare request
            params = {
                "text": text,
                "text_language": self.text_language,
                "ref_audio_path": self.refer_wav_path,
                "prompt_text": self.prompt_text,
                "prompt_language": self.prompt_language,
                "cut_punc": self.cut_punc,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "temperature": self.temperature,
                "speed": self.speed,
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(f"{self.api_url}/", params=params)
                response.raise_for_status()

                # Save audio content
                with open(output_path, "wb") as f:
                    f.write(response.content)

            logger.info(f"GPT-SoVITS synthesis complete: {output_path}")
            return True

        except Exception as e:
            logger.error(f"GPT-SoVITS synthesis error: {e}")
            return False


def create_tts_provider(
    provider_type: str = "edge", **kwargs
) -> TTSProvider:
    """
    Create a TTS provider instance.

    Args:
        provider_type: "edge" or "sovits"
        **kwargs: Provider-specific configuration

    Returns:
        TTS provider instance

    Example:
        # Edge TTS
        tts = create_tts_provider("edge", voice="zh-CN-XiaoxiaoNeural")

        # GPT-SoVITS
        tts = create_tts_provider(
            "sovits",
            api_url="http://192.168.10.50:9880",
            refer_wav_path="/path/to/reference.wav",
            prompt_text="参考音频的文本内容",
        )
    """
    if provider_type.lower() == "edge":
        return EdgeTTSProvider(**kwargs)
    elif provider_type.lower() in ("sovits", "gpt-sovits"):
        return GPTSoVITSProvider(**kwargs)
    else:
        raise ValueError(f"Unknown TTS provider: {provider_type}")
