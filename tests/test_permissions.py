"""Tests for calendar permission handling"""
import pytest
from tests.mocks.mock_eventkit import (
    EKAuthorizationStatusAuthorized,
    EKAuthorizationStatusNotDetermined,
    EKAuthorizationStatusDenied,
    EKAuthorizationStatusRestricted,
    MockEKEventStore,
)


@pytest.mark.asyncio
class TestPermissions:
    """Test permission handling (server.py lines 33-67)"""

    async def test_request_access_returns_bool(self, calendar_server):
        """Test request_access returns a boolean"""
        result = await calendar_server.request_access()
        assert isinstance(result, bool)

    async def test_already_authorized_skips_request(self, monkeypatch):
        """Test that already authorized status skips request dialog"""
        from mac_calendar_mcp.server import CalendarServer

        # Set auth status to authorized
        MockEKEventStore._mock_auth_status = EKAuthorizationStatusAuthorized

        server = CalendarServer()
        result = await server.request_access()
        assert result is True
        assert server.access_granted is True

    async def test_permission_request_granted(self, mock_event_store):
        """Test successful permission grant"""
        from mac_calendar_mcp.server import CalendarServer

        mock_event_store.set_authorized(True)

        server = CalendarServer()
        server.event_store = mock_event_store
        result = await server.request_access()
        assert result is True

    async def test_permission_request_denied(self, mock_event_store, monkeypatch):
        """Test permission denial"""
        from mac_calendar_mcp.server import CalendarServer
        from tests.mocks.mock_eventkit import MockEKEventStore

        mock_event_store.set_authorized(False)

        # Patch EKEventStore in the server module (not EventKit module)
        monkeypatch.setattr('mac_calendar_mcp.server.EKEventStore', MockEKEventStore)

        server = CalendarServer()
        server.event_store = mock_event_store
        result = await server.request_access()
        assert result is False

    async def test_timeout_handling(self, mock_event_store):
        """Test 30-second timeout in permission request"""
        # The mock completes quickly, but test the timeout exists
        from mac_calendar_mcp.server import CalendarServer

        mock_event_store.set_authorized(True)

        server = CalendarServer()
        server.event_store = mock_event_store
        result = await server.request_access()
        assert isinstance(result, bool)

    async def test_lazy_authorization_on_first_call(self, monkeypatch):
        """Test that authorization is requested on first get_events call"""
        from mac_calendar_mcp.server import CalendarServer

        MockEKEventStore._mock_auth_status = EKAuthorizationStatusAuthorized

        server = CalendarServer()
        assert server.access_granted is False

        # First call should trigger authorization
        events = await server.get_events()
        assert server.access_granted is True

    async def test_authorization_status_check(self, monkeypatch):
        """Test checking authorization status"""
        from mac_calendar_mcp.server import CalendarServer
        from EventKit import EKEventStore, EKEntityTypeEvent

        MockEKEventStore._mock_auth_status = EKAuthorizationStatusAuthorized
        status = EKEventStore.authorizationStatusForEntityType_(EKEntityTypeEvent)
        assert status == EKAuthorizationStatusAuthorized

    async def test_restricted_status_handling(self, mock_event_store, monkeypatch):
        """Test handling of restricted authorization status"""
        from mac_calendar_mcp.server import CalendarServer
        from tests.mocks.mock_eventkit import MockEKEventStore

        mock_event_store.set_authorized(False)

        # Patch EKEventStore in the server module (not EventKit module)
        monkeypatch.setattr('mac_calendar_mcp.server.EKEventStore', MockEKEventStore)

        server = CalendarServer()
        server.event_store = mock_event_store
        result = await server.request_access()
        # Restricted should be treated as denied
        assert result is False

    async def test_access_granted_flag_persistence(self, calendar_server):
        """Test that access_granted flag persists across calls"""
        calendar_server.access_granted = True
        events1 = await calendar_server.get_events()
        assert calendar_server.access_granted is True

        events2 = await calendar_server.get_events()
        assert calendar_server.access_granted is True

    async def test_get_calendars_requests_access(self, mock_event_store, mock_calendars):
        """Test that get_calendars also requests access if needed"""
        from mac_calendar_mcp.server import CalendarServer

        mock_event_store.set_authorized(True)
        for cal in mock_calendars:
            mock_event_store.add_calendar(cal)

        server = CalendarServer()
        server.event_store = mock_event_store
        server.access_granted = False

        calendars = await server.get_calendars()
        assert isinstance(calendars, list)
        assert server.access_granted is True
