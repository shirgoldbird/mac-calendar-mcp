"""Tests for RSVP status mapping logic."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mac_calendar_mcp.server import CalendarServer
from tests.mocks.mock_eventkit import (
    MockEKParticipant,
    EKParticipantStatusAccepted,
    EKParticipantStatusDeclined,
    EKParticipantStatusTentative,
    EKParticipantStatusPending,
    EKParticipantStatusUnknown,
)


class TestRSVPStatus:
    """Test RSVP status mapping."""

    def test_rsvp_accepted(self):
        """Test EKParticipantStatusAccepted → 'Accepted'."""
        server = CalendarServer()
        participant = MockEKParticipant(
            name="Alice",
            email="alice@example.com",
            status=EKParticipantStatusAccepted
        )
        
        result = server.get_rsvp_status(participant)
        assert result == "Accepted"

    def test_rsvp_declined(self):
        """Test EKParticipantStatusDeclined → 'Declined'."""
        server = CalendarServer()
        participant = MockEKParticipant(
            name="Bob",
            status=EKParticipantStatusDeclined
        )
        
        result = server.get_rsvp_status(participant)
        assert result == "Declined"

    def test_rsvp_tentative(self):
        """Test EKParticipantStatusTentative → 'Tentative'."""
        server = CalendarServer()
        participant = MockEKParticipant(
            name="Charlie",
            status=EKParticipantStatusTentative
        )
        
        result = server.get_rsvp_status(participant)
        assert result == "Tentative"

    def test_rsvp_pending(self):
        """Test EKParticipantStatusPending → 'Pending'."""
        server = CalendarServer()
        participant = MockEKParticipant(
            name="Diana",
            status=EKParticipantStatusPending
        )
        
        result = server.get_rsvp_status(participant)
        assert result == "Pending"

    def test_rsvp_unknown(self):
        """Test EKParticipantStatusUnknown → 'Unknown'."""
        server = CalendarServer()
        participant = MockEKParticipant(
            name="Eve",
            status=EKParticipantStatusUnknown
        )
        
        result = server.get_rsvp_status(participant)
        assert result == "Unknown"

    def test_rsvp_none_participant(self):
        """Test None participant → 'Unknown'."""
        server = CalendarServer()
        
        result = server.get_rsvp_status(None)
        assert result == "Unknown"

    def test_rsvp_invalid_status(self):
        """Test unknown status code → 'Unknown' (fallback)."""
        server = CalendarServer()
        participant = MockEKParticipant(
            name="Frank",
            status=999  # Invalid status code
        )
        
        result = server.get_rsvp_status(participant)
        assert result == "Unknown"

    def test_current_user_detection(self):
        """Test isCurrentUser() = True."""
        server = CalendarServer()
        participant = MockEKParticipant(
            name="Current User",
            email="user@example.com",
            status=EKParticipantStatusAccepted,
            is_current_user=True
        )
        
        # Verify current user flag
        assert participant.isCurrentUser() is True
        assert server.get_rsvp_status(participant) == "Accepted"

    @pytest.mark.asyncio
    async def test_organizer_without_attendees(self):
        """Test no attendees → user_status = 'Organizer'."""
        from datetime import datetime
        from tests.mocks.mock_eventkit import MockEKEventStore, MockEKCalendar, MockEKEvent
        
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)
        
        # Create calendar
        calendar = MockEKCalendar(title="Work")
        server.event_store.add_calendar(calendar)
        
        # Create event without attendees
        event = MockEKEvent(
            title="Solo Meeting",
            start=datetime(2024, 12, 25, 10, 0),
            end=datetime(2024, 12, 25, 11, 0),
            calendar=calendar,
            organizer_name="Me"
        )
        server.event_store.add_event(event)
        
        events = await server.get_events(start_date="2024-12-25")
        
        assert len(events) == 1
        assert events[0]["user_rsvp_status"] == "Organizer"
        assert events[0]["attendee_count"] == 0

    @pytest.mark.asyncio
    async def test_organizer_with_attendees(self):
        """Test event where user is organizer but has attendees."""
        from datetime import datetime
        from tests.mocks.mock_eventkit import MockEKEventStore, MockEKCalendar, MockEKEvent
        
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)
        
        # Create calendar
        calendar = MockEKCalendar(title="Work")
        server.event_store.add_calendar(calendar)
        
        # Create event with attendees but no current user
        attendee = MockEKParticipant(
            name="Other",
            status=EKParticipantStatusAccepted,
            is_current_user=False
        )
        
        event = MockEKEvent(
            title="Team Meeting",
            start=datetime(2024, 12, 25, 14, 0),
            end=datetime(2024, 12, 25, 15, 0),
            calendar=calendar,
            organizer_name="Me",
            attendees=[attendee]
        )
        server.event_store.add_event(event)
        
        events = await server.get_events(start_date="2024-12-25")
        
        assert len(events) == 1
        # User is organizer (not in attendee list)
        assert events[0]["user_rsvp_status"] == "Organizer"
        assert events[0]["attendee_count"] == 1
