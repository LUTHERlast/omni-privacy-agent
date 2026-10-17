import logging
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from models import PrivacyEvent

logger = logging.getLogger("notifier")

class NotifierService:
    async def log_event(self, db: AsyncSession, event_type: str, message: str, domain: str = None, severity: str = "INFO"):
        """Logs structured event into privacy_events table and console."""
        logger.info(f"[{severity}] {event_type} - {domain or 'GLOBAL'}: {message}")
        try:
            event = PrivacyEvent(
                event_type=event_type,
                domain=domain,
                severity=severity,
                message=message,
                timestamp=datetime.datetime.utcnow()
            )
            db.add(event)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

notifier = NotifierService()
