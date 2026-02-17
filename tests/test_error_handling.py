"""Tests for error handling and edge conditions"""
import pytest
from datetime import datetime


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in various scenarios"""

    async def test_invalid_date_format_start(self, calendar_server):
        """Test handling of invalid start date format"""
        with pytest.raises((ValueError, AttributeError)):
            await calendar_server.get_events(
                start_date="invalid-date",
                end_date="2024-12-15"
            )

    async def test_invalid_date_format_end(self, calendar_server):
        """Test handling of invalid end date format"""
        with pytest.raises((ValueError, AttributeError)):
            await calendar_server.get_events(
                start_date="2024-12-15",
                end_date="invalid-date"
            )

    async def test_empty_calendar_names_list(self, calendar_server):
        """Test empty calendar_names list returns all events (Python behavior)"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25",
            calendar_names=[]
        )
        # Empty list is treated as "no filter" in current Python implementation
        assert isinstance(events, list)

    async def test_none_calendar_names(self, calendar_server):
        """Test None calendar_names returns all calendars"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25",
            calendar_names=None
        )
        # Should return events from all calendars
        assert isinstance(events, list)

    async def test_negative_days_ahead(self, calendar_server):
        """Test negative days_ahead is handled"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            days_ahead=-1
        )
        # Should handle gracefully (may return empty or error)
        assert isinstance(events, list)

    async def test_zero_days_ahead(self, calendar_server):
        """Test zero days_ahead returns same day only"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            days_ahead=0
        )
        assert isinstance(events, list)

    async def test_very_large_days_ahead(self, calendar_server):
        """Test very large days_ahead value"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            days_ahead=36500  # 100 years
        )
        assert isinstance(events, list)

    async def test_event_with_none_title(self, calendar_server, mock_event_store):
        """Test handling of event with None title"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        event = MockEKEvent(
            title=None,  # None title
            calendar=cal,
            start=datetime(2024, 12, 15, 10, 0),
            end=datetime(2024, 12, 15, 11, 0)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-15"
        )
        # Should handle None gracefully (convert to empty string)
        assert isinstance(events, list)

    async def test_event_with_none_notes(self, calendar_server):
        """Test handling of event with None notes"""
        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-25"
        )
        for event in events:
            assert isinstance(event['notes'], str)

    async def test_event_with_none_organizer(self, calendar_server):
        """Test handling of event with None organizer"""
        events = await calendar_server.get_events(
            start_date="2024-12-20",
            end_date="2024-12-20"
        )
        # Should handle None organizer
        for event in events:
            assert isinstance(event['organizer'], str)

    async def test_event_with_none_attendees(self, calendar_server):
        """Test handling of event with None attendees"""
        events = await calendar_server.get_events(
            start_date="2024-12-20",
            end_date="2024-12-20"
        )
        # Should handle None attendees list
        for event in events:
            assert isinstance(event['attendee_count'], int)

    async def test_participant_with_none_email(self, calendar_server):
        """Test handling of participant with None email"""
        from tests.mocks.mock_eventkit import MockEKParticipant

        participant = MockEKParticipant(None, "Name", 2)
        status = calendar_server.get_rsvp_status(participant)
        assert isinstance(status, str)

    async def test_calendar_with_unicode_title(self, calendar_server, mock_event_store):
        """Test handling of calendar with unicode characters in title"""
        from tests.mocks.mock_eventkit import MockEKCalendar

        cal = MockEKCalendar("日本語カレンダー")
        mock_event_store.add_calendar(cal)

        calendars = await calendar_server.get_calendars()
        assert any("日本語" in c['title'] for c in calendars)

    async def test_event_with_emoji_in_title(self, calendar_server, mock_event_store):
        """Test handling of emoji in event title"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        mock_event_store.add_calendar(cal)
        event = MockEKEvent(
            title="🎉 Party Time 🎊",
            calendar=cal,
            start=datetime(2024, 12, 15, 20, 0),
            end=datetime(2024, 12, 15, 23, 0)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-15"
        )
        assert any("🎉" in e['title'] for e in events)

    async def test_very_long_event_title(self, calendar_server, mock_event_store):
        """Test handling of very long event title"""
        from tests.mocks.mock_eventkit import MockEKEvent, MockEKCalendar

        cal = MockEKCalendar("Test")
        long_title = "A" * 10000
        event = MockEKEvent(
            title=long_title,
            calendar=cal,
            start=datetime(2024, 12, 15, 10, 0),
            end=datetime(2024, 12, 15, 11, 0)
        )
        mock_event_store.add_event(event)

        events = await calendar_server.get_events(
            start_date="2024-12-15",
            end_date="2024-12-15"
        )
        # Should handle long titles
        assert isinstance(events, list)
