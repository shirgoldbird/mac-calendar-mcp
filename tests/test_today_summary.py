"""Tests for today summary functionality."""

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
async def test_today_summary_structure(calendar_server):
    """Test that today summary has correct structure."""
    server, event_calendar, reminder_calendar = calendar_server

    summary = await server.get_today_summary()

    assert "date" in summary
    assert "events_count" in summary
    assert "events" in summary
    assert "reminders_count" in summary
    assert "reminders" in summary
    assert isinstance(summary["events"], list)
    assert isinstance(summary["reminders"], list)


@pytest.mark.asyncio
async def test_today_summary_with_events(calendar_server):
    """Test today summary includes today's events."""
    server, event_calendar, reminder_calendar = calendar_server

    today = datetime.now()
    start = today.replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=1)

    # Create today's events
    event1 = MockEKEvent("Morning Meeting", start, end, event_calendar)
    event2 = MockEKEvent("Afternoon Review", start + timedelta(hours=4), end + timedelta(hours=4), event_calendar)
    server.event_store.add_event(event1)
    server.event_store.add_event(event2)

    # Create tomorrow's event (should not appear)
    tomorrow = today + timedelta(days=1)
    event3 = MockEKEvent("Tomorrow's Meeting", tomorrow, tomorrow + timedelta(hours=1), event_calendar)
    server.event_store.add_event(event3)

    summary = await server.get_today_summary()

    assert summary["events_count"] == 2
    assert len(summary["events"]) == 2
    titles = {e["title"] for e in summary["events"]}
    assert titles == {"Morning Meeting", "Afternoon Review"}


@pytest.mark.asyncio
async def test_today_summary_with_reminders(calendar_server):
    """Test today summary includes today's incomplete reminders."""
    server, event_calendar, reminder_calendar = calendar_server

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    # Create today's incomplete reminders
    reminder1 = MockEKReminder("Buy groceries", reminder_calendar, due_date, is_completed=False)
    reminder2 = MockEKReminder("Call doctor", reminder_calendar, due_date, is_completed=False)
    server.event_store.add_reminder(reminder1)
    server.event_store.add_reminder(reminder2)

    # Create today's completed reminder (should not appear)
    reminder3 = MockEKReminder(
        "Completed task",
        reminder_calendar,
        due_date,
        is_completed=True,
        completion_date=today,
    )
    server.event_store.add_reminder(reminder3)

    summary = await server.get_today_summary()

    assert summary["reminders_count"] == 2
    assert len(summary["reminders"]) == 2
    titles = {r["title"] for r in summary["reminders"]}
    assert titles == {"Buy groceries", "Call doctor"}


@pytest.mark.asyncio
async def test_today_summary_empty(calendar_server):
    """Test today summary when no events or reminders."""
    server, event_calendar, reminder_calendar = calendar_server

    summary = await server.get_today_summary()

    assert summary["events_count"] == 0
    assert summary["reminders_count"] == 0
    assert len(summary["events"]) == 0
    assert len(summary["reminders"]) == 0


@pytest.mark.asyncio
async def test_today_summary_date_format(calendar_server):
    """Test that summary date is in correct format."""
    server, event_calendar, reminder_calendar = calendar_server

    summary = await server.get_today_summary()

    # Date should be in YYYY-MM-DD format
    today_str = datetime.now().strftime("%Y-%m-%d")
    assert summary["date"] == today_str
