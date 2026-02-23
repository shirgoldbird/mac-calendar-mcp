"""Tests for reminder support."""

import pytest
from datetime import datetime, timedelta
from mac_calendar_mcp.server import CalendarServer
from tests.mocks.mock_eventkit import (
    MockEKEventStore,
    MockEKCalendar,
    MockEKReminder,
    MockEKDateComponents,
    EKAuthorizationStatusAuthorized,
    EKReminderPriorityNone,
    EKReminderPriorityHigh,
    EKReminderPriorityMedium,
    EKReminderPriorityLow,
)


@pytest.fixture
def calendar_server(monkeypatch):
    """Create a CalendarServer instance with mocked EventKit."""
    monkeypatch.setattr("mac_calendar_mcp.server.EKEventStore", MockEKEventStore)

    server = CalendarServer()
    server.event_store.set_authorized(True)

    # Add a test calendar
    test_calendar = MockEKCalendar("Reminders")
    server.event_store.add_calendar(test_calendar)

    return server, test_calendar


@pytest.mark.asyncio
async def test_get_basic_reminder(calendar_server):
    """Test retrieving a basic reminder."""
    server, test_calendar = calendar_server

    # Create reminder with due date
    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)
    reminder = MockEKReminder(
        title="Buy groceries",
        calendar=test_calendar,
        due_date_components=due_date,
    )
    server.event_store.add_reminder(reminder)

    # Get reminders
    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
    )

    assert len(reminders) == 1
    assert reminders[0]["title"] == "Buy groceries"
    assert reminders[0]["calendar"] == "Reminders"
    assert reminders[0]["is_completed"] is False


@pytest.mark.asyncio
async def test_reminder_date_range_filter(calendar_server):
    """Test filtering reminders by date range."""
    server, test_calendar = calendar_server

    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)

    # Create reminders at different dates
    due_today = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)
    reminder1 = MockEKReminder("Today task", test_calendar, due_today)
    server.event_store.add_reminder(reminder1)

    due_tomorrow = MockEKDateComponents(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0, 0)
    reminder2 = MockEKReminder("Tomorrow task", test_calendar, due_tomorrow)
    server.event_store.add_reminder(reminder2)

    due_next_week = MockEKDateComponents(next_week.year, next_week.month, next_week.day, 10, 0, 0)
    reminder3 = MockEKReminder("Next week task", test_calendar, due_next_week)
    server.event_store.add_reminder(reminder3)

    # Get only today's reminders
    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
    )

    assert len(reminders) == 1
    assert reminders[0]["title"] == "Today task"


@pytest.mark.asyncio
async def test_reminder_calendar_filter(calendar_server):
    """Test filtering reminders by calendar name."""
    server, test_calendar = calendar_server

    # Add another calendar
    work_calendar = MockEKCalendar("Work")
    server.event_store.add_calendar(work_calendar)

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    # Create reminders in different calendars
    reminder1 = MockEKReminder("Personal task", test_calendar, due_date)
    server.event_store.add_reminder(reminder1)

    reminder2 = MockEKReminder("Work task", work_calendar, due_date)
    server.event_store.add_reminder(reminder2)

    # Filter by Reminders calendar only
    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
        calendar_names=["Reminders"],
    )

    assert len(reminders) == 1
    assert reminders[0]["title"] == "Personal task"


@pytest.mark.asyncio
async def test_reminder_completion_filter_exclude(calendar_server):
    """Test excluding completed reminders (default behavior)."""
    server, test_calendar = calendar_server

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    # Incomplete reminder
    reminder1 = MockEKReminder("Incomplete task", test_calendar, due_date, is_completed=False)
    server.event_store.add_reminder(reminder1)

    # Completed reminder
    reminder2 = MockEKReminder(
        "Completed task",
        test_calendar,
        due_date,
        is_completed=True,
        completion_date=today,
    )
    server.event_store.add_reminder(reminder2)

    # Get reminders (exclude completed by default)
    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
        include_completed=False,
    )

    assert len(reminders) == 1
    assert reminders[0]["title"] == "Incomplete task"


@pytest.mark.asyncio
async def test_reminder_completion_filter_include(calendar_server):
    """Test including completed reminders."""
    server, test_calendar = calendar_server

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    # Incomplete reminder
    reminder1 = MockEKReminder("Incomplete task", test_calendar, due_date, is_completed=False)
    server.event_store.add_reminder(reminder1)

    # Completed reminder
    reminder2 = MockEKReminder(
        "Completed task",
        test_calendar,
        due_date,
        is_completed=True,
        completion_date=today,
    )
    server.event_store.add_reminder(reminder2)

    # Get reminders including completed
    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
        include_completed=True,
    )

    assert len(reminders) == 2
    titles = {r["title"] for r in reminders}
    assert titles == {"Incomplete task", "Completed task"}


@pytest.mark.asyncio
async def test_reminder_completion_date(calendar_server):
    """Test that completion date is extracted correctly."""
    server, test_calendar = calendar_server

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    reminder = MockEKReminder(
        "Completed task",
        test_calendar,
        due_date,
        is_completed=True,
        completion_date=today,
    )
    server.event_store.add_reminder(reminder)

    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
        include_completed=True,
    )

    assert len(reminders) == 1
    assert reminders[0]["is_completed"] is True
    assert reminders[0]["completion_date_str"] is not None


@pytest.mark.asyncio
async def test_reminder_priority_high(calendar_server):
    """Test high priority reminder."""
    server, test_calendar = calendar_server

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    reminder = MockEKReminder(
        "Urgent task",
        test_calendar,
        due_date,
        priority=EKReminderPriorityHigh,
    )
    server.event_store.add_reminder(reminder)

    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
    )

    assert len(reminders) == 1
    assert reminders[0]["priority"] == "High"


@pytest.mark.asyncio
async def test_reminder_priority_medium(calendar_server):
    """Test medium priority reminder."""
    server, test_calendar = calendar_server

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    reminder = MockEKReminder(
        "Normal task",
        test_calendar,
        due_date,
        priority=EKReminderPriorityMedium,
    )
    server.event_store.add_reminder(reminder)

    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
    )

    assert len(reminders) == 1
    assert reminders[0]["priority"] == "Medium"


@pytest.mark.asyncio
async def test_reminder_priority_low(calendar_server):
    """Test low priority reminder."""
    server, test_calendar = calendar_server

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    reminder = MockEKReminder(
        "Low priority task",
        test_calendar,
        due_date,
        priority=EKReminderPriorityLow,
    )
    server.event_store.add_reminder(reminder)

    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
    )

    assert len(reminders) == 1
    assert reminders[0]["priority"] == "Low"


@pytest.mark.asyncio
async def test_reminder_priority_none(calendar_server):
    """Test reminder with no priority."""
    server, test_calendar = calendar_server

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    reminder = MockEKReminder(
        "Task",
        test_calendar,
        due_date,
        priority=EKReminderPriorityNone,
    )
    server.event_store.add_reminder(reminder)

    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
    )

    assert len(reminders) == 1
    assert reminders[0]["priority"] == "None"


@pytest.mark.asyncio
async def test_reminder_with_notes(calendar_server):
    """Test reminder with notes field."""
    server, test_calendar = calendar_server

    today = datetime.now()
    due_date = MockEKDateComponents(today.year, today.month, today.day, 10, 0, 0)

    reminder = MockEKReminder(
        "Task with details",
        test_calendar,
        due_date,
        notes="Remember to bring the report and presentation slides",
    )
    server.event_store.add_reminder(reminder)

    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
    )

    assert len(reminders) == 1
    assert reminders[0]["notes"] == "Remember to bring the report and presentation slides"


@pytest.mark.asyncio
async def test_reminder_days_ahead(calendar_server):
    """Test days_ahead parameter for reminders."""
    server, test_calendar = calendar_server

    today = datetime.now()
    three_days = today + timedelta(days=3)
    ten_days = today + timedelta(days=10)

    # Create reminders at different dates
    due_3_days = MockEKDateComponents(three_days.year, three_days.month, three_days.day, 10, 0, 0)
    reminder1 = MockEKReminder("Near future", test_calendar, due_3_days)
    server.event_store.add_reminder(reminder1)

    due_10_days = MockEKDateComponents(ten_days.year, ten_days.month, ten_days.day, 10, 0, 0)
    reminder2 = MockEKReminder("Far future", test_calendar, due_10_days)
    server.event_store.add_reminder(reminder2)

    # Get reminders for next 7 days (default)
    reminders = await server.get_reminders(
        start_date=today.strftime("%Y-%m-%d"),
        days_ahead=7,
    )

    assert len(reminders) == 1
    assert reminders[0]["title"] == "Near future"
