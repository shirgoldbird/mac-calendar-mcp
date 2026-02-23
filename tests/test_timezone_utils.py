"""Tests for timezone utilities."""

import pytest
from datetime import datetime
from mac_calendar_mcp.server import CalendarServer
from tests.mocks.mock_eventkit import MockEKEventStore, EKAuthorizationStatusAuthorized


@pytest.fixture
def calendar_server(monkeypatch):
    """Create a CalendarServer instance with mocked EventKit."""
    monkeypatch.setattr("mac_calendar_mcp.server.EKEventStore", MockEKEventStore)

    server = CalendarServer()
    server.event_store.set_authorized(True)

    return server


@pytest.mark.asyncio
async def test_get_current_time_utc(calendar_server):
    """Test getting current time in UTC."""
    server = calendar_server

    result = await server.get_current_time(timezone="UTC")

    assert result["timezone"] == "UTC"
    assert "datetime" in result
    assert "timestamp" in result
    assert isinstance(result["timestamp"], float)


@pytest.mark.asyncio
async def test_get_current_time_new_york(calendar_server):
    """Test getting current time in New York timezone."""
    server = calendar_server

    result = await server.get_current_time(timezone="America/New_York")

    assert result["timezone"] == "America/New_York"
    assert "datetime" in result
    # Datetime should have timezone info
    assert "T" in result["datetime"]


@pytest.mark.asyncio
async def test_get_current_time_london(calendar_server):
    """Test getting current time in London timezone."""
    server = calendar_server

    result = await server.get_current_time(timezone="Europe/London")

    assert result["timezone"] == "Europe/London"
    assert "datetime" in result


@pytest.mark.asyncio
async def test_get_current_time_invalid_timezone(calendar_server):
    """Test error handling for invalid timezone."""
    server = calendar_server

    with pytest.raises(ValueError, match="Unknown timezone"):
        await server.get_current_time(timezone="Invalid/Timezone")


@pytest.mark.asyncio
async def test_convert_time_utc_to_pst(calendar_server):
    """Test converting time from UTC to PST."""
    server = calendar_server

    result = await server.convert_time(
        datetime_str="2024-01-15T12:00:00",
        from_timezone="UTC",
        to_timezone="America/Los_Angeles",
    )

    assert result["from_timezone"] == "UTC"
    assert result["to_timezone"] == "America/Los_Angeles"
    assert "original_datetime" in result
    assert "converted_datetime" in result


@pytest.mark.asyncio
async def test_convert_time_with_timezone_aware(calendar_server):
    """Test converting already timezone-aware datetime."""
    server = calendar_server

    result = await server.convert_time(
        datetime_str="2024-01-15T12:00:00+00:00",
        from_timezone="UTC",
        to_timezone="Asia/Tokyo",
    )

    assert result["from_timezone"] == "UTC"
    assert result["to_timezone"] == "Asia/Tokyo"


@pytest.mark.asyncio
async def test_convert_time_invalid_from_timezone(calendar_server):
    """Test error handling for invalid from_timezone."""
    server = calendar_server

    with pytest.raises(ValueError, match="Unknown timezone"):
        await server.convert_time(
            datetime_str="2024-01-15T12:00:00",
            from_timezone="Invalid/Timezone",
            to_timezone="UTC",
        )


@pytest.mark.asyncio
async def test_convert_time_invalid_to_timezone(calendar_server):
    """Test error handling for invalid to_timezone."""
    server = calendar_server

    with pytest.raises(ValueError, match="Unknown timezone"):
        await server.convert_time(
            datetime_str="2024-01-15T12:00:00",
            from_timezone="UTC",
            to_timezone="Invalid/Timezone",
        )


@pytest.mark.asyncio
async def test_convert_time_invalid_datetime(calendar_server):
    """Test error handling for invalid datetime string."""
    server = calendar_server

    with pytest.raises(ValueError, match="Invalid datetime string"):
        await server.convert_time(
            datetime_str="not-a-datetime",
            from_timezone="UTC",
            to_timezone="America/New_York",
        )


@pytest.mark.asyncio
async def test_list_timezones_all(calendar_server):
    """Test listing all timezones."""
    server = calendar_server

    timezones = await server.list_timezones()

    assert isinstance(timezones, list)
    assert len(timezones) > 0
    # Check for some common timezones
    assert "UTC" in timezones
    assert "America/New_York" in timezones
    assert "Europe/London" in timezones


@pytest.mark.asyncio
async def test_list_timezones_america_region(calendar_server):
    """Test listing timezones filtered by America region."""
    server = calendar_server

    timezones = await server.list_timezones(region="America")

    assert isinstance(timezones, list)
    assert len(timezones) > 0
    # All should start with "America/"
    assert all(tz.startswith("America/") for tz in timezones)
    # Check for specific timezones
    assert "America/New_York" in timezones
    assert "America/Los_Angeles" in timezones


@pytest.mark.asyncio
async def test_list_timezones_europe_region(calendar_server):
    """Test listing timezones filtered by Europe region."""
    server = calendar_server

    timezones = await server.list_timezones(region="Europe")

    assert isinstance(timezones, list)
    assert len(timezones) > 0
    # All should start with "Europe/"
    assert all(tz.startswith("Europe/") for tz in timezones)
    # Check for specific timezones
    assert "Europe/London" in timezones
    assert "Europe/Paris" in timezones


@pytest.mark.asyncio
async def test_list_timezones_asia_region(calendar_server):
    """Test listing timezones filtered by Asia region."""
    server = calendar_server

    timezones = await server.list_timezones(region="Asia")

    assert isinstance(timezones, list)
    assert len(timezones) > 0
    # All should start with "Asia/"
    assert all(tz.startswith("Asia/") for tz in timezones)
    # Check for specific timezones
    assert "Asia/Tokyo" in timezones
    assert "Asia/Shanghai" in timezones
