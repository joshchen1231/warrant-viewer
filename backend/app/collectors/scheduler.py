"""Daily post-close collection scheduler (APScheduler). Implements PSM §8 M0 / PIM §4.1."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .. import config
from ..collect_runner import run_collection

logger = logging.getLogger("warrant-viewer")


def run_job() -> None:
    logger.info("scheduled collection start")
    try:
        result = run_collection()
        logger.info("scheduled collection done: %s", result)
    except Exception:
        logger.exception("scheduled collection crashed")


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=config.SCHEDULE_TIMEZONE)
    scheduler.add_job(
        run_job,
        trigger="cron",
        day_of_week="mon-fri",
        hour=config.SCHEDULE_HOUR,
        minute=config.SCHEDULE_MINUTE,
        id="daily_warrant_collect",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
