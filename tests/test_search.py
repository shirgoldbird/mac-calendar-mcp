"""Tests for search functionality."""

import pytest
from datetime import datetime, timedelta
from mac_calendar_mcp.server import CalendarServer
from tests.mocks.mock_eventkit import (
    MockEKEventStore,
    MockEKCalendar,
    MockEKEvent,
    MockEKReminder,
    MockEKDateComponents,
    EKAuthorizationStatusAuthorized,
)


@pytest.fixture
def calendar_server(monkeypatch):
    """Create a CalendarServer instance with mocked EventKit."""
    monkeypatch.setattr("mac_calendar_mcp.server.EKEventStore", MockEKEventStore)

    server = CalendarServer()
    server.event_store.set_authorized(True)

    # Add test calendars
    event_calendar = MockEKCalendar("Calendar")
    reminder_calendar = MockEKCalendar("Reminders")
    server.event_store.add_calendar(event_calendar)
    server.event_store.add_calendar(reminder_calendar)

    return server, event_calendar, reminder_calendar


@pytest.mark.asyncio
async def test_search_in_event_title(calendar_server):
    """Test searching in event titles."""
    server, event_calendar, reminder_calendar = calendar_server

    start = datetime.now()
    end = start + timedelta(hours=1)

    # Create events with different titles
    event1 = MockEKEvent("Team Meeting", start, end, event_calendar)
    event2 = MockEKEvent("Project Review", start, end, event_calendar)
    server.event_store.add_event(event1)
    server.event_store.add_event(event2)

    # Search for "meeting"
    results = await server.search(
        query="meeting",
        search_reminders=False,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Team Meeting"
    assert results[0]["type"] == "event"


@pytest.mark.asyncio
async def test_search_in_event_notes(calendar_server):
    """Test searching in event notes."""
    server, event_calendar, reminder_calendar = calendar_server

    start = datetime.now()
    end = start + timedelta(hours=1)

    # Create event with search term in notes
    event = MockEKEvent(
        "Meeting",
        start,
        end,
        event_calendar,
        notes="Discuss the new feature implementation",
    )
    server.event_store.add_event(event)

    # Search for "feature"
    results = await server.search(
        query="feature",
        search_reminders=False,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Meeting"


@pytest.mark.asyncio
async def test_search_in_event_location(calendar_server):
    """Test searching in event location."""
    server, event_calendar, reminder_calendar = calendar_server

    start = datetime.now()
    end = start + timedelta(hours=1)

    # Create event with search term in location
    event = MockEKEvent(
        "Client Meeting",
        start,
        end,
        event_calendar,
        location="Conference Room B, Building 5",
    )
    server.event_store.add_event(event)

    # Search for "building"
    results = await server.search(
        query="building",
        search_reminders=False,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Client Meeting"


@pytest.mark.asyncio
async def test_search_in_reminder_title(calendar_server):
    """Test searching in reminder titles."""
    server, event_calendar, reminder_calendar = calendar_server

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    # Create reminders with different titles
    reminder1 = MockEKReminder("Buy groceries", reminder_calendar, due_date)
    reminder2 = MockEKReminder("Call dentist", reminder_calendar, due_date)
    server.event_store.add_reminder(reminder1)
    server.event_store.add_reminder(reminder2)

    # Search for "groceries"
    results = await server.search(
        query="groceries",
        search_events=False,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Buy groceries"
    assert results[0]["type"] == "reminder"


@pytest.mark.asyncio
async def test_search_in_reminder_notes(calendar_server):
    """Test searching in reminder notes."""
    server, event_calendar, reminder_calendar = calendar_server

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    # Create reminder with search term in notes
    reminder = MockEKReminder(
        "Shopping",
        reminder_calendar,
        due_date,
        notes="Don't forget the organic vegetables",
    )
    server.event_store.add_reminder(reminder)

    # Search for "organic"
    results = await server.search(
        query="organic",
        search_events=False,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Shopping"


@pytest.mark.asyncio
async def test_search_case_insensitive(calendar_server):
    """Test that search is case-insensitive."""
    server, event_calendar, reminder_calendar = calendar_server

    start = datetime.now()
    end = start + timedelta(hours=1)

    event = MockEKEvent("IMPORTANT Meeting", start, end, event_calendar)
    server.event_store.add_event(event)

    # Search with lowercase
    results = await server.search(
        query="important",
        search_reminders=False,
    )

    assert len(results) == 1
    assert results[0]["title"] == "IMPORTANT Meeting"


@pytest.mark.asyncio
async def test_search_combined_events_and_reminders(calendar_server):
    """Test searching both events and reminders."""
    server, event_calendar, reminder_calendar = calendar_server

    start = datetime.now()
    end = start + timedelta(hours=1)
    due_date = MockEKDateComponents(start.year, start.month, start.day, 10, 0, 0)

    # Create event and reminder with same keyword
    event = MockEKEvent("Project deadline meeting", start, end, event_calendar)
    reminder = MockEKReminder("Project deadline reminder", reminder_calendar, due_date)
    server.event_store.add_event(event)
    server.event_store.add_reminder(reminder)

    # Search for "project"
    results = await server.search(
        query="project",
        search_events=True,
        search_reminders=True,
    )

    assert len(results) == 2
    types = {r["type"] for r in results}
    assert types == {"event", "reminder"}


@pytest.mark.asyncio
async def test_search_no_results(calendar_server):
    """Test search with no matching results."""
    server, event_calendar, reminder_calendar = calendar_server

    start = datetime.now()
    end = start + timedelta(hours=1)

    event = MockEKEvent("Team Meeting", start, end, event_calendar)
    server.event_store.add_event(event)

    # Search for non-existent term
    results = await server.search(query="nonexistent")

    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_with_date_range(calendar_server):
    """Test search with date range filter."""
    server, event_calendar, reminder_calendar = calendar_server

    today = datetime.now()
    next_month = today + timedelta(days=40)

    # Create event today with "meeting" in title
    event1 = MockEKEvent("Meeting today", today, today + timedelta(hours=1), event_calendar)
    server.event_store.add_event(event1)

    # Create event next month with "meeting" in title
    event2 = MockEKEvent("Meeting next month", next_month, next_month + timedelta(hours=1), event_calendar)
    server.event_store.add_event(event2)

    # Search only in today's range
    results = await server.search(
        query="meeting",
        search_reminders=False,
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
    )

    assert len(results) == 1
    assert results[0]["title"] == "Meeting today"
