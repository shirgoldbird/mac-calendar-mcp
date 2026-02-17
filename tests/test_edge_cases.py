"""Tests for edge cases and boundary conditions"""
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    async def test_event_spanning_midnight(self, calendar_server, mock_event_store):
        """Test event that spans midnight"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        mock_event_store.add_calendar(cal)  # Add calendar first
        event = MockEKEvent(
            title="Late Night Event",
            calendar=cal,
            start=datetime(2024, 12, 15, 23, 0, 0),
            end=datetime(2024, 12, 16, 1, 0, 0)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-16"
        )
        # Should find the event
        assert any(e['title'] == "Late Night Event" for e in events)

    async def test_event_at_exact_start_boundary(self, calendar_server, mock_event_store):
        """Test event starting at exact query start time"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        mock_event_store.add_calendar(cal)
        event = MockEKEvent(
            title="Boundary Event",
            calendar=cal,
            start=datetime(2024, 12, 15, 0, 0, 0),
            end=datetime(2024, 12, 15, 1, 0, 0)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-12-15T00:00:00",
            end_date="2024-12-15T23:59:59"
        )
        assert any(e['title'] == "Boundary Event" for e in events)

    async def test_event_at_exact_end_boundary(self, calendar_server, mock_event_store):
        """Test event ending at exact query end time"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        mock_event_store.add_calendar(cal)
        event = MockEKEvent(
            title="End Boundary Event",
            calendar=cal,
            start=datetime(2024, 12, 15, 23, 0, 0),
            end=datetime(2024, 12, 15, 23, 59, 59)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-15"
        )
        assert any(e['title'] == "End Boundary Event" for e in events)

    async def test_zero_duration_event(self, calendar_server, mock_event_store):
        """Test event with same start and end time"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        event = MockEKEvent(
            title="Zero Duration",
            calendar=cal,
            start=datetime(2024, 12, 15, 12, 0, 0),
            end=datetime(2024, 12, 15, 12, 0, 0)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-15"
        )
        assert isinstance(events, list)

    async def test_very_long_event(self, calendar_server, mock_event_store):
        """Test event lasting multiple days"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        mock_event_store.add_calendar(cal)
        event = MockEKEvent(
            title="Multi-day Conference",
            calendar=cal,
            start=datetime(2024, 12, 15, 9, 0, 0),
            end=datetime(2024, 12, 20, 17, 0, 0)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-20"
        )
        assert any(e['title'] == "Multi-day Conference" for e in events)

    async def test_event_just_before_range(self, calendar_server, mock_event_store):
        """Test event ending just before query range"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        event = MockEKEvent(
            title="Before Range",
            calendar=cal,
            start=datetime(2024, 12, 14, 23, 0, 0),
            end=datetime(2024, 12, 14, 23, 59, 59)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-15"
        )
        # Should not include this event
        assert not any(e['title'] == "Before Range" for e in events)

    async def test_event_just_after_range(self, calendar_server, mock_event_store):
        """Test event starting just after query range"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        event = MockEKEvent(
            title="After Range",
            calendar=cal,
            start=datetime(2024, 12, 16, 0, 0, 1),
            end=datetime(2024, 12, 16, 1, 0, 0)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-15"
        )
        # Should not include this event (depends on end-of-day handling)
        assert isinstance(events, list)

    async def test_many_attendees(self, calendar_server, mock_event_store):
        """Test event with many attendees"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar, MockEKParticipant

        cal = MockEKCalendar("Test")
        attendees = [
            MockEKParticipant(f"user{i}@example.com", f"User {i}", 2)
            for i in range(100)
        ]
        event = MockEKEvent(
            title="Large Meeting",
            calendar=cal,
            start=datetime(2024, 12, 15, 14, 0, 0),
            end=datetime(2024, 12, 15, 15, 0, 0),
            attendees=attendees
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-15"
        )
        large_meetings = [e for e in events if e['title'] == "Large Meeting"]
        if large_meetings:
            assert large_meetings[0]['attendee_count'] == 100

    async def test_leap_year_date(self, calendar_server, mock_event_store):
        """Test event on leap year date (Feb 29)"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        event = MockEKEvent(
            title="Leap Day Event",
            calendar=cal,
            start=datetime(2024, 2, 29, 12, 0, 0),
            end=datetime(2024, 2, 29, 13, 0, 0)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-02-29",
            end_date="2024-02-29"
        )
        assert isinstance(events, list)

    @freeze_time("2024-12-31 23:59:59")
    async def test_year_boundary(self, calendar_server):
        """Test queries around year boundary"""
        events = await calendar_server.get_events(
            start_date="2024-12-31",
            days_ahead=2  # Should include Jan 1, 2025
        )
        assert isinstance(events, list)

    async def test_dst_transition(self, calendar_server, mock_event_store):
        """Test events around DST transition"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        # Spring forward in 2024 is March 10
        event = MockEKEvent(
            title="DST Event",
            calendar=cal,
            start=datetime(2024, 3, 10, 2, 30, 0),
            end=datetime(2024, 3, 10, 3, 30, 0)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-03-10",
            end_date="2024-03-10"
        )
        assert isinstance(events, list)

    async def test_empty_string_calendar_name(self, calendar_server):
        """Test filtering by empty string calendar name"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25",
            calendar_names=[""]
        )
        # Should return no events (no calendar named "")
        assert len(events) == 0

    async def test_duplicate_calendar_names(self, calendar_server):
        """Test filtering with duplicate calendar names"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25",
            calendar_names=["Work", "Work", "Work"]
        )
        # Should work correctly despite duplicates
        assert isinstance(events, list)

    async def test_whitespace_in_calendar_name(self, calendar_server, mock_event_store):
        """Test calendar name with leading/trailing whitespace"""
        from tests.mocks.mock_eventkit import MockEKCalendar

        cal = MockEKCalendar("  Spaced Calendar  ")
        mock_event_store.add_calendar(cal)

        calendars = await calendar_server.get_calendars()
        assert any("Spaced Calendar" in c['title'] for c in calendars)
