#!/usr/bin/env python3
"""Test script to verify calendar access"""

import asyncio
from server import CalendarServer


async def test_calendar():
    cal = CalendarServer()

    print("Requesting calendar access...")
    access = await cal.request_access()
    print(f"Access granted: {access}")

    if not access:
        print("\n⚠️  Calendar access denied!")
        print("You need to grant permission when prompted by macOS.")
        print("Or go to: System Settings > Privacy & Security > Calendar")
        return

    print("\n📅 Available Calendars:")
    calendars = await cal.get_calendars()
    for cal_info in calendars:
        print(f"  - {cal_info['title']} ({cal_info['source']})")

    print("\n📆 Events for the next 7 days:")
    events = await cal.get_events(days_ahead=7)

    if not events:
        print("  No events found")
    else:
        for event in events[:5]:  # Show first 5 events
            print(f"\n  Title: {event['title']}")
            print(f"  Calendar: {event['calendar']}")
            print(f"  When: {event['start_date_str']}")
            print(f"  RSVP Status: {event['user_rsvp_status']}")
            if event['notes']:
                print(f"  Description: {event['notes'][:100]}...")
            if event['location']:
                print(f"  Location: {event['location']}")


if __name__ == "__main__":
    asyncio.run(test_calendar())
