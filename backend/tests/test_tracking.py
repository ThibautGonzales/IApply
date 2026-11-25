from datetime import UTC, datetime

import pytest

from app.models import ApplicationStatus
from app.tracking import close_stale_applications
from tests.test_applications_api import make_application

NOW = datetime(2026, 12, 31, tzinfo=UTC)


@pytest.mark.parametrize("status", [ApplicationStatus.WAITING, ApplicationStatus.INTERVIEW])
def test_open_application_without_news_for_a_month_is_closed(session, status):
    application = make_application(session, "1", day=30)  # 31 days before NOW
    application.status = status
    session.commit()

    close_stale_applications(session, now=NOW)

    session.refresh(application)
    assert application.status == ApplicationStatus.CLOSED


def test_recent_application_stays_open(session):
    application = make_application(session, "1", day=30)

    close_stale_applications(session, now=datetime(2026, 12, 29, tzinfo=UTC))  # 29 days later

    session.refresh(application)
    assert application.status == ApplicationStatus.WAITING


@pytest.mark.parametrize("status", [ApplicationStatus.REJECTED, ApplicationStatus.ACCEPTED])
def test_final_status_is_never_changed(session, status):
    application = make_application(session, "1", day=1)
    application.status = status
    session.commit()

    close_stale_applications(session, now=NOW)

    session.refresh(application)
    assert application.status == status
