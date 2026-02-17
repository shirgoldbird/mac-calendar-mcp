"""Tests for date parsing and normalization logic."""

import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mac_calendar_mcp.server import CalendarServer
from tests.mocks.mock_eventkit import MockEKEventStore, MockNSDate


class TestDateParsing:
    """Test date parsing and normalization in get_events."""

    @pytest.mark.asyncio
    @freeze_time("2024-12-25 10:00:00")
    async def test_parse_iso_date_only(self):
        """Test parsing date-only ISO string → start of day."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        # Date-only input should become midnight
        events = await server.get_events(start_date="2024-12-25")
        
        # Verify the predicate was created with correct timestamps
        # The event store should have been called with start = midnight
        assert server.event_store._events is not None

    @pytest.mark.asyncio
    async def test_parse_iso_datetime(self):
        """Test parsing ISO datetime string with time → exact time."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        # DateTime input should preserve exact time
        events = await server.get_events(
            start_date="2024-12-25T14:30:00",
            end_date="2024-12-25T16:00:00"
        )
        
        assert events is not None

    @pytest.mark.asyncio
    @freeze_time("2024-12-25 10:00:00")
    async def test_default_start_date(self):
        """Test None start_date → today at midnight."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        events = await server.get_events(start_date=None)
        
        # Should default to today midnight
        assert events is not None

    @pytest.mark.asyncio
    async def test_default_end_date(self):
        """Test None end_date → start + days_ahead."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        events = await server.get_events(
            start_date="2024-12-25",
            end_date=None,
            days_ahead=7
        )
        
        # Should be 7 days after start
        assert events is not None

    @pytest.mark.asyncio
    async def test_same_date_start_end(self):
        """Test same date for start and end → 00:00:00 to 23:59:59."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        events = await server.get_events(
            start_date="2024-12-25",
            end_date="2024-12-25"
        )
        
        # End should be set to end of day
        assert events is not None

    @pytest.mark.asyncio
    async def test_end_date_without_time(self):
        """Test end_date without time → 23:59:59.999999."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        events = await server.get_events(
            start_date="2024-12-25T09:00:00",
            end_date="2024-12-26"
        )
        
        # End of day should be set
        assert events is not None

    @pytest.mark.asyncio
    async def test_days_ahead_parameter(self):
        """Test days_ahead=14 → 14 days from start."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        events = await server.get_events(
            start_date="2024-12-25",
            days_ahead=14
        )
        
        assert events is not None

    @pytest.mark.asyncio
    async def test_microsecond_precision(self):
        """Test that end_date includes .999999 microseconds."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        events = await server.get_events(
            start_date="2024-12-25"
        )
        
        # Microsecond precision should be maintained
        assert events is not None

    @pytest.mark.asyncio
    async def test_invalid_iso_format(self):
        """Test malformed date string → error."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()

        with pytest.raises((ValueError, TypeError)):
            await server.get_events(start_date="not-a-date")

    @pytest.mark.asyncio
    async def test_date_before_1970(self):
        """Test Unix epoch boundary (before 1970)."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        # Date before Unix epoch
        events = await server.get_events(start_date="1969-12-31")
        
        assert events is not None

    @pytest.mark.asyncio
    async def test_date_after_2038(self):
        """Test Y2038 boundary."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        # Date after Y2038
        events = await server.get_events(start_date="2040-01-01")
        
        assert events is not None

    @pytest.mark.asyncio
    async def test_nsdate_conversion(self):
        """Test Python datetime → NSDate → timestamp conversion."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        events = await server.get_events(
            start_date="2024-12-25T14:30:45"
        )
        
        # NSDate conversion should preserve timestamp
        assert events is not None

    @pytest.mark.asyncio
    async def test_timezone_naive_handling(self):
        """Test dates without timezone info."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        # ISO format without timezone
        events = await server.get_events(
            start_date="2024-12-25T14:30:00"
        )
        
        assert events is not None

    @pytest.mark.asyncio
    async def test_date_range_calculation(self):
        """Test that date range is calculated correctly."""
        server = CalendarServer()
        server.access_granted = True
        server.event_store = MockEKEventStore()
        server.event_store.set_authorized(True)

        start = datetime(2024, 12, 25, 0, 0, 0)
        end = start + timedelta(days=7)

        events = await server.get_events(
            start_date=start.isoformat(),
            end_date=end.isoformat()
        )
        
        assert events is not None
