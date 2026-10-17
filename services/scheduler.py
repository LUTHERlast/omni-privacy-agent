import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database import AsyncSessionLocal
from services.prospector import prospector
from config import settings

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler()

async def scheduled_discovery_job():
    logger.info("Running scheduled UAE PDPL domain discovery job...")
    async with AsyncSessionLocal() as db:
        try:
            audited = await prospector.seed_and_audit_all(db)
            logger.info(f"Scheduled discovery job finished. Audited {audited} domains.")
        except Exception as e:
            logger.error(f"Error in scheduled discovery job: {e}")

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            scheduled_discovery_job,
            trigger=IntervalTrigger(hours=settings.AUTO_DISCOVERY_INTERVAL_HOURS),
            id="pdpl_discovery_job",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler initialized for OmniPrivacy AI.")
