"""Tests for core CalendarServer functionality"""
import pytest
from datetime import datetime


@pytest.mark.asyncio
class TestCalendarServer:
    """Test core functionality of CalendarServer"""

    async def test_get_events_returns_list(self, calendar_server):
        """Test get_events returns a list"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25"
        )
        assert isinstance(events, list)

    async def test_get_events_date_range_filtering(self, calendar_server):
        """Test events are filtered by date range"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-16"
        )
        # Should only get events in this range
        for event in events:
            start = datetime.fromisoformat(event['start_date_str'])
            assert start.date() >= datetime(2024, 12, 15).date()
            assert start.date() <= datetime(2024, 12, 16).date()

    async def test_get_events_calendar_filtering(self, calendar_server):
        """Test filtering by calendar names"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25",
            calendar_names=["Work"]
        )
        # Should only get Work calendar events
        for event in events:
            assert event['calendar'] == "Work"

    async def test_get_events_multiple_calendars(self, calendar_server):
        """Test filtering by multiple calendar names"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25",
            calendar_names=["Work", "Personal"]
        )
        # Should get events from both calendars
        calendars = set(event['calendar'] for event in events)
        assert calendars.issubset({"Work", "Personal"})

    async def test_event_serialization_all_fields(self, calendar_server):
        """Test event dict contains all required fields"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25"
        )
        assert len(events) > 0
        event = events[0]

        # Check all required fields are present
        required_fields = [
            'title', 'calendar', 'start_date_str', 'end_date_str',
            'all_day', 'notes', 'organizer', 'user_rsvp_status', 'attendee_count'
        ]
        for field in required_fields:
            assert field in event, f"Missing field: {field}"

    async def test_attendee_count_extraction(self, calendar_server):
        """Test attendee_count is correctly extracted"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25"
        )
        for event in events:
            assert 'attendee_count' in event
            assert isinstance(event['attendee_count'], int)
            assert event['attendee_count'] >= 0

    async def test_all_day_event_detection(self, calendar_server):
        """Test all-day events are correctly detected"""
        events = await calendar_server.get_events(
            start_date="2024-12-31",
            end_date="2024-12-31"
        )
        # Find the all-day event (Holiday on Dec 31)
        all_day_events = [e for e in events if e['all_day']]
        assert len(all_day_events) > 0

    async def test_event_title_extraction(self, calendar_server):
        """Test event titles are correctly extracted"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25"
        )
        titles = [event['title'] for event in events]
        assert "Team Meeting" in titles

    async def test_event_notes_extraction(self, calendar_server):
        """Test event notes/descriptions are extracted"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25"
        )
        for event in events:
            assert 'notes' in event
            assert isinstance(event['notes'], str)

    async def test_organizer_extraction(self, calendar_server):
        """Test organizer information is extracted"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-15"
        )
        # Find event with organizer
        for event in events:
            if event['organizer']:
                assert isinstance(event['organizer'], str)
                break

    async def test_datetime_iso_format(self, calendar_server):
        """Test dates are in ISO format"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25"
        )
        for event in events:
            # Should be able to parse as ISO format
            start = datetime.fromisoformat(event['start_date_str'])
            end = datetime.fromisoformat(event['end_date_str'])
            assert isinstance(start, datetime)
            assert isinstance(end, datetime)

    async def test_get_calendars_returns_list(self, calendar_server):
        """Test get_calendars returns a list"""
        calendars = await calendar_server.get_calendars()
        assert isinstance(calendars, list)
        assert len(calendars) > 0

    async def test_calendar_info_structure(self, calendar_server):
        """Test calendar info contains required fields"""
        calendars = await calendar_server.get_calendars()
        for cal in calendars:
            assert 'title' in cal
            assert 'type' in cal
            assert 'color' in cal
            assert 'source' in cal

    async def test_empty_date_range_returns_empty(self, calendar_server):
        """Test empty date range returns empty list"""
        events = await calendar_server.get_events(
            start_date="2025-01-01",
            end_date="2025-01-01"
        )
        # No events in this range
        assert isinstance(events, list)

    async def test_nonexistent_calendar_filter(self, calendar_server):
        """Test filtering by nonexistent calendar returns empty"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25",
            calendar_names=["Nonexistent Calendar"]
        )
        assert len(events) == 0
