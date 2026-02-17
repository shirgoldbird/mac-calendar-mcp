"""Parity tests to verify feature compatibility for Node.js migration"""
import pytest
import json
from pathlib import Path


@pytest.mark.asyncio
class TestParity:
    """Test parity scenarios for migration verification"""

    @pytest.fixture
    def parity_scenarios(self):
        """Load parity scenarios from JSON"""
        scenarios_path = Path(__file__).parent / "fixtures" / "parity_scenarios.json"
        with open(scenarios_path) as f:
            data = json.load(f)
        return data['scenarios']

    async def test_scenario_001_basic_event_retrieval(self, calendar_server, parity_scenarios):
        """Test basic event retrieval with date range"""
        scenario = next(s for s in parity_scenarios if s['id'] == 'scenario_001')
        events = await calendar_server.get_events(**scenario['arguments'])

        assert isinstance(events, list)
        if events:
            for field in scenario['expected_fields']:
                assert field in events[0]

    async def test_scenario_003_filter_single_calendar(self, calendar_server, parity_scenarios):
        """Test filtering by single calendar"""
        scenario = next(s for s in parity_scenarios if s['id'] == 'scenario_003')
        events = await calendar_server.get_events(**scenario['arguments'])

        for event in events:
            assert event['calendar'] == scenario['expected_calendar']

    async def test_scenario_006_single_day_query(self, calendar_server, parity_scenarios):
        """Test single day query"""
        scenario = next(s for s in parity_scenarios if s['id'] == 'scenario_006')
        events = await calendar_server.get_events(**scenario['arguments'])

        assert isinstance(events, list)

    async def test_scenario_008_list_calendars(self, calendar_server, parity_scenarios):
        """Test listing all calendars"""
        scenario = next(s for s in parity_scenarios if s['id'] == 'scenario_008')
        calendars = await calendar_server.get_calendars()

        assert isinstance(calendars, list)
        if calendars:
            for field in scenario['expected_fields']:
                assert field in calendars[0]

    async def test_scenario_010_organizer_fallback(self, calendar_server, parity_scenarios):
        """Test organizer fallback for events with no attendees"""
        scenario = next(s for s in parity_scenarios if s['id'] == 'scenario_010')
        events = await calendar_server.get_events(**scenario['arguments'])

        # Find event with no attendees
        for event in events:
            if event['attendee_count'] == 0:
                assert event['user_rsvp_status'] == "Organizer"

    async def test_scenario_011_all_day_events(self, calendar_server, parity_scenarios):
        """Test all-day event detection"""
        scenario = next(s for s in parity_scenarios if s['id'] == 'scenario_011')
        events = await calendar_server.get_events(**scenario['arguments'])

        # Should find at least one all-day event
        assert any(event['all_day'] for event in events)

    async def test_scenario_015_empty_calendar_filter(self, calendar_server, parity_scenarios):
        """Test empty calendar filter behavior (Python treats as no filter)"""
        scenario = next(s for s in parity_scenarios if s['id'] == 'scenario_015')
        events = await calendar_server.get_events(**scenario['arguments'])

        # Python implementation treats empty list as "no filter" - document this for Node.js parity
        assert isinstance(events, list)

    async def test_scenario_016_nonexistent_calendar(self, calendar_server, parity_scenarios):
        """Test nonexistent calendar filter returns no events"""
        scenario = next(s for s in parity_scenarios if s['id'] == 'scenario_016')
        events = await calendar_server.get_events(**scenario['arguments'])

        assert len(events) == 0

    async def test_scenario_017_no_events_date_range(self, calendar_server, parity_scenarios):
        """Test date range with no events"""
        scenario = next(s for s in parity_scenarios if s['id'] == 'scenario_017')
        events = await calendar_server.get_events(**scenario['arguments'])

        assert len(events) == 0

    async def test_all_scenarios_execute_without_error(self, calendar_server, parity_scenarios):
        """Test that all scenarios can be executed without errors"""
        from mac_calendar_mcp.server import call_tool

        for scenario in parity_scenarios:
            tool = scenario['tool']
            args = scenario['arguments']

            # Should execute without raising exceptions
            result = await call_tool(tool, args)
            assert isinstance(result, list)
