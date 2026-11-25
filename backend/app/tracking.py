from datetime import datetime, timedelta

from sqlmodel import Session, col, update

from app.models import Application, ApplicationStatus, utc_now

# After this long without news, an application is considered closed without answer.
NO_NEWS_DELAY = timedelta(days=30)

# The statuses that still wait for something. Rejected, accepted and closed are final.
OPEN_STATUSES = [ApplicationStatus.WAITING, ApplicationStatus.INTERVIEW]


def close_stale_applications(session: Session, now: datetime | None = None) -> None:
    """Close the open applications without news for a month. Run before reading them,
    so no scheduled job is needed."""
    limit = (now or utc_now()) - NO_NEWS_DELAY
    session.exec(
        update(Application)
        .where(col(Application.status).in_(OPEN_STATUSES))
        .where(col(Application.last_news_at) < limit)
        .values(status=ApplicationStatus.CLOSED)
    )
    session.commit()
