# Daily AI Product Post -> WhatsApp Status (Round 1, Project 2)

Every day at a set time, with zero manual input:
1. Picks the **product of the day** (rotates through `app/products.json`)
2. **AI image** - Pollinations.ai (free, no key), optional Hugging Face fallback, branded placeholder as last resort
3. **AI caption + hashtags** - Google Gemini free tier (or keyless Pollinations text), template fallback
4. Posts image + caption to **WhatsApp Status** through **WAHA** (free, open source, Docker)
5. Saves proof in `output/YYYY-MM-DD/` (`image.jpg`, `caption.txt`, `result.json`)

## Setup
```bash
cp .env.example .env        # edit: WAHA_API_KEY, optional GEMINI_API_KEY, TZ, POST_HOUR/MINUTE
docker compose up -d --build
```
1. Open **http://localhost:3000/dashboard** (user `admin`, password = your `WAHA_API_KEY`).
2. Start session `default` and scan the QR with your **secondary WhatsApp number** (WhatsApp > Linked devices).
3. Test it right now (no waiting for the schedule):
```bash
docker compose run --rm automation python -m app.main --dry-run   # image + caption only
docker compose run --rm automation python -m app.main --now       # real post to Status
```
The `automation` container then keeps running and posts daily at `POST_HOUR:POST_MINUTE` in your `TZ`.
A missed run (PC asleep/restart) still fires within 6 hours; the same day is never posted twice (`--force` overrides).

## Get a free Gemini key (recommended for better captions)
https://aistudio.google.com/apikey -> create key -> paste in `.env` as `GEMINI_API_KEY`.

## Run without Docker (alternative)
```bash
pip install -r requirements.txt
export WAHA_BASE_URL=http://localhost:3000 WAHA_API_KEY=... 
python -m app.main --now
```
Use Windows Task Scheduler / cron with `python -m app.main --now` if you prefer OS scheduling.

## Tool substitutions (state in your submission)
| Typical tool | Used | Reason |
|---|---|---|
| n8n / Make | Python + APScheduler in Docker | no account limits, fully local, easy to read |
| DALL-E / Midjourney | Pollinations.ai (+ HF optional) | free, no key |
| OpenAI GPT | Gemini free tier (+ Pollinations) | free |

If a free AI service is down or rate-limited, the fallbacks still produce a post, and `result.json` records which source was used.

## Troubleshooting
- `session ... is SCAN_QR_CODE` -> scan the QR in the dashboard.
- `401` from WAHA -> `WAHA_API_KEY` in `.env` must match what WAHA started with (`docker compose up -d --force-recreate`).
- WAHA env names/endpoints can change between versions - check https://waha.devlike.pro/docs/how-to/status/ if the Status endpoint returns 404.
- WhatsApp may restrict numbers that automate; use a secondary number and post once a day.

## Structure
```
app/
  main.py      CLI + daily scheduler
  pipeline.py  orchestrates one run, logs results
  ai.py        caption + image generation with fallbacks
  whatsapp.py  WAHA client (session check + status/image)
  products.py  product rotation
```
