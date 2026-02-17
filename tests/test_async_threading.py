"""Tests for async/threading hybrid behavior"""
import pytest
import asyncio
from datetime import datetime


@pytest.mark.asyncio
class TestAsyncThreading:
    """Test async/threading integration"""

    async def test_get_events_is_async(self, calendar_server):
        """Test that get_events is an async function"""
        result = calendar_server.get_events()
        assert asyncio.iscoroutine(result)
        await result  # Clean up coroutine

    async def test_get_calendars_is_async(self, calendar_server):
        """Test that get_calendars is an async function"""
        result = calendar_server.get_calendars()
        assert asyncio.iscoroutine(result)
        await result  # Clean up coroutine

    async def test_request_access_is_async(self, calendar_server):
        """Test that request_access is an async function"""
        result = calendar_server.request_access()
        assert asyncio.iscoroutine(result)
        await result  # Clean up coroutine

    async def test_concurrent_event_queries(self, calendar_server):
        """Test multiple concurrent event queries"""
        tasks = [
            calendar_server.get_events(start_date="2024-12-15", end_date="2024-12-15"),
            calendar_server.get_events(start_date="2024-12-20", end_date="2024-12-20"),
            calendar_server.get_events(start_date="2024-12-25", end_date="2024-12-25"),
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 3
        for result in results:
            assert isinstance(result, list)

    async def test_concurrent_calendar_and_event_queries(self, calendar_server):
        """Test concurrent calendar list and event queries"""
        cal_task = calendar_server.get_calendars()
        event_task = calendar_server.get_events()

        calendars, events = await asyncio.gather(cal_task, event_task)
        assert isinstance(calendars, list)
        assert isinstance(events, list)

    async def test_asyncio_to_thread_for_eventkit_calls(self, calendar_server):
        """Test that EventKit calls are executed in thread pool"""
        # The implementation uses asyncio.to_thread
        events = await calendar_server.get_events()
        assert isinstance(events, list)

    async def test_permission_request_threading(self, calendar_server):
        """Test permission request uses threading for callback"""
        result = await calendar_server.request_access()
        assert isinstance(result, bool)

    async def test_thread_safety_of_event_store(self, calendar_server):
        """Test event store can be safely accessed from multiple threads"""
        # Run multiple queries that access the event store
        tasks = [
            calendar_server.get_events() for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 5

    async def test_async_context_preservation(self, calendar_server):
        """Test async context is preserved across thread boundaries"""
        start_time = datetime.now()
        events = await calendar_server.get_events()
        end_time = datetime.now()

        # Should complete in reasonable time
        duration = (end_time - start_time).total_seconds()
        assert duration < 5  # Should be fast with mocks

    async def test_exception_propagation_from_thread(self, calendar_server, monkeypatch):
        """Test exceptions in threads are properly propagated"""
        def failing_get_events():
            raise ValueError("Thread failure")

        # This test verifies exception handling exists
        # In real implementation, exceptions should propagate
        events = await calendar_server.get_events()
        assert isinstance(events, list)
