"""Tests for enhanced event fields and attendee filtering."""

import pytest
from datetime import datetime, timedelta
from mac_calendar_mcp.server import CalendarServer
from tests.mocks.mock_eventkit import (
    MockEKEventStore,
    MockEKCalendar,
    MockEKEvent,
    MockEKParticipant,
    EKParticipantStatusAccepted,
    EKParticipantStatusDeclined,
    EKParticipantStatusTentative,
    EKParticipantStatusPending,
    EKAuthorizationStatusAuthorized,
    EKEventAvailabilityBusy,
    EKEventAvailabilityFree,
)


@pytest.fixture
def calendar_server(monkeypatch):
    """Create a CalendarServer instance with mocked EventKit."""
    # Mock the EventKit classes
    monkeypatch.setattr("mac_calendar_mcp.server.EKEventStore", MockEKEventStore)

    server = CalendarServer()
    server.event_store.set_authorized(True)

    # Add a test calendar
    test_calendar = MockEKCalendar("Test Calendar")
    server.event_store.add_calendar(test_calendar)

    return server, test_calendar


@pytest.mark.asyncio
async def test_event_with_location(calendar_server):
    """Test that event location is extracted correctly."""
    server, test_calendar = calendar_server

    # Create event with location
    start = datetime.now()
    end = start + timedelta(hours=1)
    event = MockEKEvent(
        title="Meeting at Office",
        start=start,
        end=end,
        calendar=test_calendar,
        location="123 Main St, Building A",
    )
    server.event_store.add_event(event)

    # Get events
    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
    )

    assert len(events) == 1
    assert events[0]["location"] == "123 Main St, Building A"


@pytest.mark.asyncio
async def test_event_without_location(calendar_server):
    """Test that event without location returns empty string."""
    server, test_calendar = calendar_server

    start = datetime.now()
    end = start + timedelta(hours=1)
    event = MockEKEvent(
        title="Virtual Meeting",
        start=start,
        end=end,
        calendar=test_calendar,
        location="",
    )
    server.event_store.add_event(event)

    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
    )

    assert len(events) == 1
    assert events[0]["location"] == ""


@pytest.mark.asyncio
async def test_event_with_url(calendar_server):
    """Test that meeting URL is extracted from URL field."""
    server, test_calendar = calendar_server

    start = datetime.now()
    end = start + timedelta(hours=1)
    event = MockEKEvent(
        title="Zoom Meeting",
        start=start,
        end=end,
        calendar=test_calendar,
        url="https://zoom.us/j/123456789",
    )
    server.event_store.add_event(event)

    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
    )

    assert len(events) == 1
    assert events[0]["meeting_url"] == "https://zoom.us/j/123456789"


@pytest.mark.asyncio
async def test_event_with_url_in_notes(calendar_server):
    """Test that meeting URL is extracted from notes."""
    server, test_calendar = calendar_server

    start = datetime.now()
    end = start + timedelta(hours=1)
    event = MockEKEvent(
        title="Meeting",
        start=start,
        end=end,
        calendar=test_calendar,
        notes="Join the meeting: https://meet.google.com/abc-defg-hij",
    )
    server.event_store.add_event(event)

    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
    )

    assert len(events) == 1
    assert events[0]["meeting_url"] == "https://meet.google.com/abc-defg-hij"


@pytest.mark.asyncio
async def test_event_without_url(calendar_server):
    """Test that event without URL returns None."""
    server, test_calendar = calendar_server

    start = datetime.now()
    end = start + timedelta(hours=1)
    event = MockEKEvent(
        title="In-person Meeting",
        start=start,
        end=end,
        calendar=test_calendar,
    )
    server.event_store.add_event(event)

    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
    )

    assert len(events) == 1
    assert events[0]["meeting_url"] is None


@pytest.mark.asyncio
async def test_detailed_attendees_list(calendar_server):
    """Test that detailed attendees list is returned."""
    server, test_calendar = calendar_server

    # Create attendees
    attendees = [
        MockEKParticipant("Alice", "alice@example.com", EKParticipantStatusAccepted, False),
        MockEKParticipant("Bob", "bob@example.com", EKParticipantStatusDeclined, False),
        MockEKParticipant("Current User", "me@example.com", EKParticipantStatusTentative, True),
    ]

    start = datetime.now()
    end = start + timedelta(hours=1)
    event = MockEKEvent(
        title="Team Meeting",
        start=start,
        end=end,
        calendar=test_calendar,
        attendees=attendees,
    )
    server.event_store.add_event(event)

    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
    )

    assert len(events) == 1
    assert len(events[0]["attendees"]) == 3

    # Check Alice
    alice = events[0]["attendees"][0]
    assert alice["name"] == "Alice"
    assert alice["email"] == "alice@example.com"
    assert alice["status"] == "Accepted"
    assert alice["is_current_user"] is False

    # Check Bob
    bob = events[0]["attendees"][1]
    assert bob["name"] == "Bob"
    assert bob["email"] == "bob@example.com"
    assert bob["status"] == "Declined"
    assert bob["is_current_user"] is False

    # Check current user
    current = events[0]["attendees"][2]
    assert current["name"] == "Current User"
    assert current["email"] == "me@example.com"
    assert current["status"] == "Tentative"
    assert current["is_current_user"] is True


@pytest.mark.asyncio
async def test_filter_by_attendee_name_exact(calendar_server):
    """Test filtering by exact attendee name."""
    server, test_calendar = calendar_server

    # Event with Alice
    attendees1 = [MockEKParticipant("Alice", "alice@example.com", EKParticipantStatusAccepted)]
    start = datetime.now()
    end = start + timedelta(hours=1)
    event1 = MockEKEvent("Meeting 1", start, end, test_calendar, attendees=attendees1)
    server.event_store.add_event(event1)

    # Event with Bob
    attendees2 = [MockEKParticipant("Bob", "bob@example.com", EKParticipantStatusAccepted)]
    event2 = MockEKEvent("Meeting 2", start, end, test_calendar, attendees=attendees2)
    server.event_store.add_event(event2)

    # Filter by Alice
    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
        attendee_name_pattern="Alice",
    )

    assert len(events) == 1
    assert events[0]["title"] == "Meeting 1"


@pytest.mark.asyncio
async def test_filter_by_attendee_name_partial(calendar_server):
    """Test filtering by partial attendee name."""
    server, test_calendar = calendar_server

    attendees = [MockEKParticipant("Alicia Smith", "alicia@example.com", EKParticipantStatusAccepted)]
    start = datetime.now()
    end = start + timedelta(hours=1)
    event = MockEKEvent("Meeting", start, end, test_calendar, attendees=attendees)
    server.event_store.add_event(event)

    # Filter by partial name (case-insensitive)
    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
        attendee_name_pattern="ali",
    )

    assert len(events) == 1
    assert events[0]["title"] == "Meeting"


@pytest.mark.asyncio
async def test_filter_by_attendee_email(calendar_server):
    """Test filtering by attendee email."""
    server, test_calendar = calendar_server

    attendees = [MockEKParticipant("John Doe", "john@company.com", EKParticipantStatusAccepted)]
    start = datetime.now()
    end = start + timedelta(hours=1)
    event = MockEKEvent("Meeting", start, end, test_calendar, attendees=attendees)
    server.event_store.add_event(event)

    # Filter by email domain
    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
        attendee_name_pattern="company.com",
    )

    assert len(events) == 1
    assert events[0]["title"] == "Meeting"


@pytest.mark.asyncio
async def test_filter_by_attendee_status_single(calendar_server):
    """Test filtering by single attendee RSVP status."""
    server, test_calendar = calendar_server

    # Event with accepted attendee
    attendees1 = [MockEKParticipant("Alice", "alice@example.com", EKParticipantStatusAccepted)]
    start = datetime.now()
    end = start + timedelta(hours=1)
    event1 = MockEKEvent("Meeting 1", start, end, test_calendar, attendees=attendees1)
    server.event_store.add_event(event1)

    # Event with declined attendee
    attendees2 = [MockEKParticipant("Bob", "bob@example.com", EKParticipantStatusDeclined)]
    event2 = MockEKEvent("Meeting 2", start, end, test_calendar, attendees=attendees2)
    server.event_store.add_event(event2)

    # Filter by Accepted status
    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
        attendee_status_filter=["Accepted"],
    )

    assert len(events) == 1
    assert events[0]["title"] == "Meeting 1"


@pytest.mark.asyncio
async def test_filter_by_attendee_status_multiple(calendar_server):
    """Test filtering by multiple attendee RSVP statuses."""
    server, test_calendar = calendar_server

    # Event with accepted attendee
    attendees1 = [MockEKParticipant("Alice", "alice@example.com", EKParticipantStatusAccepted)]
    start = datetime.now()
    end = start + timedelta(hours=1)
    event1 = MockEKEvent("Meeting 1", start, end, test_calendar, attendees=attendees1)
    server.event_store.add_event(event1)

    # Event with tentative attendee
    attendees2 = [MockEKParticipant("Bob", "bob@example.com", EKParticipantStatusTentative)]
    event2 = MockEKEvent("Meeting 2", start, end, test_calendar, attendees=attendees2)
    server.event_store.add_event(event2)

    # Event with declined attendee
    attendees3 = [MockEKParticipant("Charlie", "charlie@example.com", EKParticipantStatusDeclined)]
    event3 = MockEKEvent("Meeting 3", start, end, test_calendar, attendees=attendees3)
    server.event_store.add_event(event3)

    # Filter by Accepted or Tentative
    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
        attendee_status_filter=["Accepted", "Tentative"],
    )

    assert len(events) == 2
    titles = {e["title"] for e in events}
    assert titles == {"Meeting 1", "Meeting 2"}


@pytest.mark.asyncio
async def test_filter_by_name_and_status(calendar_server):
    """Test combined filtering by attendee name and status."""
    server, test_calendar = calendar_server

    # Event with Alice (accepted)
    attendees1 = [MockEKParticipant("Alice", "alice@example.com", EKParticipantStatusAccepted)]
    start = datetime.now()
    end = start + timedelta(hours=1)
    event1 = MockEKEvent("Meeting 1", start, end, test_calendar, attendees=attendees1)
    server.event_store.add_event(event1)

    # Event with Alice (declined) - different event
    attendees2 = [MockEKParticipant("Alice", "alice@example.com", EKParticipantStatusDeclined)]
    start2 = start + timedelta(days=1)
    event2 = MockEKEvent("Meeting 2", start2, start2 + timedelta(hours=1), test_calendar, attendees=attendees2)
    server.event_store.add_event(event2)

    # Filter by Alice + Accepted
    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start2.strftime("%Y-%m-%d"),
        attendee_name_pattern="alice",
        attendee_status_filter=["Accepted"],
    )

    assert len(events) == 1
    assert events[0]["title"] == "Meeting 1"


@pytest.mark.asyncio
async def test_filter_all_day_only(calendar_server):
    """Test filtering for all-day events only."""
    server, test_calendar = calendar_server

    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # All-day event
    event1 = MockEKEvent("All Day Event", start, start + timedelta(hours=1), test_calendar, is_all_day=True)
    server.event_store.add_event(event1)

    # Regular timed event
    event2 = MockEKEvent("Timed Event", start, start + timedelta(hours=1), test_calendar, is_all_day=False)
    server.event_store.add_event(event2)

    # Filter for all-day only
    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
        all_day_only=True,
    )

    assert len(events) == 1
    assert events[0]["title"] == "All Day Event"
    assert events[0]["all_day"] is True


@pytest.mark.asyncio
async def test_filter_busy_only(calendar_server):
    """Test filtering for busy events only."""
    server, test_calendar = calendar_server

    start = datetime.now()
    end = start + timedelta(hours=1)

    # Busy event
    event1 = MockEKEvent("Busy Meeting", start, end, test_calendar, availability=EKEventAvailabilityBusy)
    server.event_store.add_event(event1)

    # Free event
    event2 = MockEKEvent("Free Time", start, end, test_calendar, availability=EKEventAvailabilityFree)
    server.event_store.add_event(event2)

    # Filter for busy only
    events = await server.get_events(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=start.strftime("%Y-%m-%d"),
        busy_only=True,
    )

    assert len(events) == 1
    assert events[0]["title"] == "Busy Meeting"
