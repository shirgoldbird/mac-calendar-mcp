#!/usr/bin/env python3
"""Test script to verify calendar access and new features"""

import asyncio
from datetime import datetime
from mac_calendar_mcp.server import CalendarServer


async def test_calendar():
    cal = CalendarServer()

    print("🚀 Testing mac-calendar-mcp v0.2.0")
    print("=" * 60)

    print("\nRequesting calendar access...")
    access = await cal.request_access()
    print(f"Access granted: {access}")

    if not access:
        print("\n⚠️  Calendar access denied!")
        print("You need to grant permission when prompted by macOS.")
        print("Or go to: System Settings > Privacy & Security > Calendar")
        return

    # Test 1: List Calendars
    print("\n" + "=" * 60)
    print("📅 Available Calendars:")
    calendars = await cal.get_calendars()
    for cal_info in calendars:
        print(f"  - {cal_info['title']} ({cal_info['source']})")

    # Test 2: Basic Events
    print("\n" + "=" * 60)
    print("📆 Events for the next 7 days:")
    events = await cal.get_events(days_ahead=7)

    if not events:
        print("  No events found")
    else:
        for event in events[:3]:  # Show first 3 events
            print(f"\n  📌 {event['title']}")
            print(f"     Calendar: {event['calendar']}")
            print(f"     When: {event['start_date_str']}")
            print(f"     RSVP: {event['user_rsvp_status']}")
            if event.get('location'):
                print(f"     📍 Location: {event['location']}")
            if event.get('meeting_url'):
                print(f"     🔗 Meeting URL: {event['meeting_url']}")
            if event.get('attendees'):
                print(f"     👥 Attendees: {len(event['attendees'])} people")

    # Test 3: Today's Summary
    print("\n" + "=" * 60)
    print("📋 Today's Summary:")
    summary = await cal.get_today_summary()
    print(f"  Events: {summary['events_count']}")
    print(f"  Reminders: {summary['reminders_count']}")

    # Test 4: Reminders
    print("\n" + "=" * 60)
    print("✅ Incomplete Reminders (next 7 days):")
    reminders = await cal.get_reminders(days_ahead=7, include_completed=False)

    if not reminders:
        print("  No reminders found")
    else:
        for reminder in reminders[:3]:
            priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢", "None": "⚪"}.get(reminder['priority'], "⚪")
            print(f"\n  {priority_emoji} {reminder['title']}")
            print(f"     Due: {reminder['due_date_str']}")
            print(f"     Priority: {reminder['priority']}")

    # Test 5: Search
    print("\n" + "=" * 60)
    print("🔍 Search Demo (searching for 'meeting'):")
    search_results = await cal.search(query="meeting", search_events=True, search_reminders=False)
    print(f"  Found {len(search_results)} results")
    for result in search_results[:2]:
        print(f"  - {result['title']} ({result['type']})")

    # Test 6: Timezone Utils
    print("\n" + "=" * 60)
    print("🌍 Timezone Utilities:")
    current_utc = await cal.get_current_time(timezone="UTC")
    print(f"  Current UTC time: {current_utc['datetime']}")

    current_ny = await cal.get_current_time(timezone="America/New_York")
    print(f"  Current NY time: {current_ny['datetime']}")

    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("\nTry these features in Claude Code:")
    print('  - "Find all events where [name] accepted"')
    print('  - "Show me high priority reminders"')
    print('  - "Search my calendar for [keyword]"')
    print('  - "What time is it in Tokyo?"')


if __name__ == "__main__":
    asyncio.run(test_calendar())
