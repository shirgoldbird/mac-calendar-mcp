"""Pytest configuration and shared fixtures for mac-calendar-mcp tests."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.mocks.mock_eventkit import (
    MockEKEventStore,
    MockEKCalendar,
    MockEKEvent,
    MockEKParticipant,
    MockNSDate,
    EKEntityTypeEvent,
    EKParticipantStatusAccepted,
    EKParticipantStatusDeclined,
    EKParticipantStatusTentative,
    EKParticipantStatusPending,
    EKParticipantStatusUnknown,
    EKAuthorizationStatusAuthorized,
)


@pytest.fixture
def mock_event_store():
    """Mock EKEventStore with controlled behavior."""
    store = MockEKEventStore()
    store.set_authorized(True)
    return store


@pytest.fixture
def mock_calendar_work():
    """Mock Work calendar."""
    return MockEKCalendar(
        title="Work",
        cal_type="CalDAV",
        color="#0000FF",
        source_title="iCloud"
    )


@pytest.fixture
def mock_calendar_personal():
    """Mock Personal calendar."""
    return MockEKCalendar(
        title="Personal",
        cal_type="Local",
        color="#FF0000",
        source_title="Local"
    )


@pytest.fixture
def mock_calendars(mock_calendar_work, mock_calendar_personal):
    """List of mock calendars."""
    return [mock_calendar_work, mock_calendar_personal]


@pytest.fixture
def mock_attendee_accepted():
    """Mock attendee with Accepted status."""
    return MockEKParticipant(
        name="Alice Smith",
        email="alice@example.com",
        status=EKParticipantStatusAccepted,
        is_current_user=False
    )


@pytest.fixture
def mock_attendee_declined():
    """Mock attendee with Declined status."""
    return MockEKParticipant(
        name="Bob Jones",
        email="bob@example.com",
        status=EKParticipantStatusDeclined,
        is_current_user=False
    )


@pytest.fixture
def mock_attendee_current_user():
    """Mock attendee representing current user."""
    return MockEKParticipant(
        name="Current User",
        email="user@example.com",
        status=EKParticipantStatusAccepted,
        is_current_user=True
    )


@pytest.fixture
def sample_event_simple(mock_calendar_work):
    """Simple event with no attendees."""
    now = datetime(2024, 12, 25, 14, 0, 0)
    return MockEKEvent(
        title="Team Meeting",
        start=now,
        end=now + timedelta(hours=1),
        calendar=mock_calendar_work,
        notes="Discuss Q4 goals",
        organizer_name="Manager",
        is_all_day=False
    )


@pytest.fixture
def sample_event_with_attendees(mock_calendar_work, mock_attendee_accepted, mock_attendee_current_user):
    """Event with attendees."""
    now = datetime(2024, 12, 26, 10, 0, 0)
    return MockEKEvent(
        title="Project Sync",
        start=now,
        end=now + timedelta(minutes=30),
        calendar=mock_calendar_work,
        notes="Sprint planning",
        organizer_name="PM",
        attendees=[mock_attendee_accepted, mock_attendee_current_user],
        is_all_day=False
    )


@pytest.fixture
def sample_event_all_day(mock_calendar_personal):
    """All-day event."""
    date = datetime(2024, 12, 31, 0, 0, 0)
    return MockEKEvent(
        title="Holiday",
        start=date,
        end=date + timedelta(days=1),
        calendar=mock_calendar_personal,
        notes="New Year's Eve",
        is_all_day=True
    )


@pytest.fixture
def populated_event_store(
    mock_event_store,
    mock_calendars,
    sample_event_simple,
    sample_event_with_attendees,
    sample_event_all_day
):
    """Event store with calendars and events."""
    for calendar in mock_calendars:
        mock_event_store.add_calendar(calendar)
    
    mock_event_store.add_event(sample_event_simple)
    mock_event_store.add_event(sample_event_with_attendees)
    mock_event_store.add_event(sample_event_all_day)
    
    return mock_event_store


@pytest.fixture
def patch_eventkit(mock_event_store):
    """Patch EventKit imports to use mocks."""
    with patch('EventKit.EKEventStore', return_value=mock_event_store), \
         patch('EventKit.EKEntityTypeEvent', EKEntityTypeEvent), \
         patch('EventKit.EKParticipantStatusAccepted', EKParticipantStatusAccepted), \
         patch('EventKit.EKParticipantStatusDeclined', EKParticipantStatusDeclined), \
         patch('EventKit.EKParticipantStatusTentative', EKParticipantStatusTentative), \
         patch('EventKit.EKParticipantStatusPending', EKParticipantStatusPending), \
         patch('EventKit.EKParticipantStatusUnknown', EKParticipantStatusUnknown), \
         patch('EventKit.EKAuthorizationStatusAuthorized', EKAuthorizationStatusAuthorized):
        yield


@pytest.fixture
def freeze_time_2024():
    """Freeze time to a specific date for testing."""
    from freezegun import freeze_time
    with freeze_time("2024-12-25 10:00:00"):
        yield datetime(2024, 12, 25, 10, 0, 0)


@pytest.fixture
def calendar_server(populated_event_store):
    """CalendarServer instance with mocked EventKit and populated data."""
    from mac_calendar_mcp.server import CalendarServer

    server = CalendarServer()
    server.event_store = populated_event_store
    server.access_granted = True

    return server


@pytest.fixture(autouse=True)
def reset_mock_state():
    """Reset mock EventKit state before each test."""
    MockEKEventStore._class_auth_status = None
    yield
    MockEKEventStore._class_auth_status = None
