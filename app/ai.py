"""AI generation: caption with hashtags + product image. Every step has a free fallback
so the daily workflow never fails silently."""
import io
import logging
import random
import re
from urllib.parse import quote

from PIL import Image, ImageDraw, ImageFont

from . import config
from .http_util import retry, session

log = logging.getLogger("ai")

# ------------------------------------------------------------------ caption
def _caption_prompt(p: dict) -> str:
    return (
        f"You write WhatsApp Status posts for an online store called {config.BRAND_NAME}.\n"
        f"Product of the day: {p['name']} ({p['category']}) - {p['description']}.\n"
        "Write ONE catchy caption: 2 short lines, friendly tone, 2-3 emojis, a call to action "
        f"(e.g. 'Order now on {config.BRAND_NAME}'). Then a blank line and 6-8 relevant hashtags. "
        "Output only the caption text, no quotes, no markdown."
    )

def _gemini(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent"
    r = session.post(url, params={"key": config.GEMINI_API_KEY}, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=40)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

def _pollinations_text(prompt: str) -> str:
    r = session.get(f"https://text.pollinations.ai/{quote(prompt)}", timeout=60)
    r.raise_for_status()
    return r.text.strip()

def _template_caption(p: dict) -> str:
    tags = " ".join(f"#{t}" for t in p["tags"])
    return (
        f"✨ Today's pick: {p['name']}!\n{p['description'].capitalize()}. Order now on {config.BRAND_NAME} 🛒\n\n"
        f"{tags} #{config.BRAND_NAME.lower()} #dailydeals #shopnow"
    )

def _ensure_hashtags(text: str, p: dict) -> str:
    if len(re.findall(r"#\w+", text)) >= 5:
        return text
    extra = " ".join(f"#{t}" for t in p["tags"]) + f" #{config.BRAND_NAME.lower()} #dailydeals"
    return f"{text.rstrip()}\n\n{extra}"

def generate_caption(p: dict) -> tuple[str, str]:
    """Returns (caption, source)."""
    prompt = _caption_prompt(p)
    attempts = []
    if config.GEMINI_API_KEY:
        attempts.append(("gemini", _gemini))
    attempts.append(("pollinations", _pollinations_text))
    for name, fn in attempts:
        try:
            text = retry(lambda: fn(prompt), attempts=2)
            if len(text) > 20:
                return _ensure_hashtags(text, p), name
        except Exception as e:  # noqa: BLE001
            log.warning("caption via %s failed: %s", name, e)
    return _template_caption(p), "template"

# -------------------------------------------------------------------- image
def _image_prompt(p: dict) -> str:
    return (
        f"Professional e-commerce product photo of {p['name']}, {p['description']}, "
        f"centered on a clean {p['color']} studio background, soft natural lighting, "
        "sharp focus, high detail, no text, no watermark"
    )

def _pollinations_image(prompt: str) -> bytes:
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}"
    r = session.get(url, timeout=120)
    r.raise_for_status()
    if not r.headers.get("content-type", "").startswith("image") or len(r.content) < 5000:
        raise ValueError("not a valid image response")
    return r.content

def _hf_image(prompt: str) -> bytes:
    r = session.post(
        f"https://router.huggingface.co/hf-inference/models/{config.HF_IMAGE_MODEL}",
        headers={"Authorization": f"Bearer {config.HF_TOKEN}"},
        json={"inputs": prompt}, timeout=120,
    )
    r.raise_for_status()
    if len(r.content) < 5000:
        raise ValueError("not a valid image response")
    return r.content

def _font(size: int):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

def _placeholder(p: dict) -> bytes:
    """Last-resort branded card so the post can still go out."""
    img = Image.new("RGB", (1024, 1024))
    d = ImageDraw.Draw(img)
    for y in range(1024):
        d.line([(0, y), (1024, y)], fill=(79 - y // 14, 70 + y // 20, 229 - y // 8))
    d.text((512, 430), p["name"], fill="white", font=_font(56), anchor="mm")
    d.text((512, 520), p["category"].upper(), fill=(220, 220, 255), font=_font(32), anchor="mm")
    d.text((512, 940), config.BRAND_NAME, fill="white", font=_font(40), anchor="mm")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()

def _to_jpeg(raw: bytes) -> bytes:
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()

def generate_image(p: dict) -> tuple[bytes, str]:
    """Returns (jpeg_bytes, source)."""
    prompt = _image_prompt(p)
    attempts = [("pollinations", _pollinations_image)]
    if config.HF_TOKEN:
        attempts.append(("huggingface", _hf_image))
    for name, fn in attempts:
        try:
            return _to_jpeg(retry(lambda: fn(prompt), attempts=2, delay=5)), name
        except Exception as e:  # noqa: BLE001
            log.warning("image via %s failed: %s", name, e)
    return _placeholder(p), "placeholder"
