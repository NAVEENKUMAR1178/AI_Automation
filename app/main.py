import argparse
import logging

from . import config, pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("main")


def main() -> None:
    ap = argparse.ArgumentParser(description="Daily AI product post -> WhatsApp Status")
    ap.add_argument("--now", action="store_true", help="run once immediately and exit")
    ap.add_argument("--dry-run", action="store_true", help="generate image + caption but do not post")
    ap.add_argument("--force", action="store_true", help="post even if already posted today")
    args = ap.parse_args()

    if args.now or args.dry_run:
        pipeline.run(dry_run=args.dry_run, force=args.force)
        return

    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    sched = BlockingScheduler(timezone=config.TZ)
    # misfire_grace_time lets a missed run (machine asleep/restart) still fire within 6 hours
    sched.add_job(pipeline.run, CronTrigger(hour=config.POST_HOUR, minute=config.POST_MINUTE, timezone=config.TZ),
                  misfire_grace_time=6 * 3600, coalesce=True, id="daily-post")
    log.info("Scheduler started: daily at %02d:%02d %s. Waiting...", config.POST_HOUR, config.POST_MINUTE, config.TZ)
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
