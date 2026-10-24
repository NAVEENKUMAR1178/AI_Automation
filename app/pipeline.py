import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from . import ai, config, products, whatsapp

log = logging.getLogger("pipeline")


def run(dry_run: bool = False, force: bool = False) -> dict:
    now = datetime.now(ZoneInfo(config.TZ))
    folder = Path(config.OUTPUT_DIR) / now.strftime("%Y-%m-%d")
    result_file = folder / "result.json"

    if result_file.exists() and not (force or dry_run):
        prev = json.loads(result_file.read_text())
        if prev.get("posted"):
            log.info("Already posted today - skipping (use --force to repost)")
            return prev

    folder.mkdir(parents=True, exist_ok=True)
    product = products.product_of_the_day(now.date())
    log.info("Product of the day: %s", product["name"])

    caption, caption_src = ai.generate_caption(product)
    log.info("Caption via %s", caption_src)
    image, image_src = ai.generate_image(product)
    log.info("Image via %s (%d KB)", image_src, len(image) // 1024)

    (folder / "image.jpg").write_bytes(image)
    (folder / "caption.txt").write_text(caption, encoding="utf-8")

    result = {
        "time": now.isoformat(), "product": product["name"], "caption_source": caption_src,
        "image_source": image_src, "posted": False, "dry_run": dry_run, "error": None,
    }
    if dry_run:
        log.info("Dry run - not posting. Files saved in %s", folder)
    else:
        try:
            whatsapp.ensure_session()
            whatsapp.post_status_image(image, caption)
            result["posted"] = True
            log.info("Posted to WhatsApp Status")
        except Exception as e:  # noqa: BLE001
            result["error"] = str(e)
            log.error("WhatsApp post failed: %s", e)

    result_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result
