#!/usr/bin/env python3
"""
macOS Calendar MCP Server
Provides access to Apple Calendar events synced from Google Calendar
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# PyObjC imports for EventKit
from Foundation import NSDate, NSPredicate
from EventKit import (
    EKEventStore,
    EKEntityTypeEvent,
    EKParticipantStatusAccepted,
    EKParticipantStatusDeclined,
    EKParticipantStatusTentative,
    EKParticipantStatusPending,
    EKParticipantStatusUnknown,
)


class CalendarServer:
    def __init__(self):
        self.event_store = EKEventStore.alloc().init()
        self.access_granted = False

    async def request_access(self) -> bool:
        """Request access to calendar data"""
        def _request():
            import threading
            import time

            # Check current authorization status first
            from EventKit import EKAuthorizationStatusAuthorized, EKAuthorizationStatusNotDetermined
            status = EKEventStore.authorizationStatusForEntityType_(EKEntityTypeEvent)

            if status == EKAuthorizationStatusAuthorized:
                return True

            # Need to request access
            granted = [False]
            error = [None]
            done = threading.Event()

            def completion_handler(g, e):
                granted[0] = g
                error[0] = e
                done.set()

            self.event_store.requestFullAccessToEventsWithCompletion_(completion_handler)

            # Wait for the callback with timeout
            done.wait(timeout=30)  # 30 seconds for user to respond

            if error[0]:
                print(f"Error requesting calendar access: {error[0]}")

            return granted[0]

        self.access_granted = await asyncio.to_thread(_request)
        return self.access_granted

    def get_rsvp_status(self, participant) -> str:
        """Convert RSVP status to readable string"""
        if not participant:
            return "Unknown"

        status = participant.participantStatus()
        status_map = {
            EKParticipantStatusAccepted: "Accepted",
            EKParticipantStatusDeclined: "Declined",
            EKParticipantStatusTentative: "Tentative",
            EKParticipantStatusPending: "Pending",
            EKParticipantStatusUnknown: "Unknown",
        }
        return status_map.get(status, "Unknown")

    async def get_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        calendar_names: Optional[List[str]] = None,
        days_ahead: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Fetch calendar events

        Args:
            start_date: ISO format date string (YYYY-MM-DD) or None for today
            end_date: ISO format date string (YYYY-MM-DD) or None for start_date + days_ahead
            calendar_names: List of calendar names to filter, or None for all
            days_ahead: Number of days to look ahead if end_date not specified
        """
        if not self.access_granted:
            await self.request_access()

        def _get_events():
            # Parse dates
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                # If only date provided (no time), set to start of day
                if start_dt.hour == 0 and start_dt.minute == 0 and start_dt.second == 0:
                    start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                # If same date as start or only date provided, go to end of that day
                if end_dt.date() == start_dt.date() or (end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0):
                    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                end_dt = start_dt + timedelta(days=days_ahead)
                # Make sure we include the full last day
                end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Convert to NSDate
            start_ns = NSDate.dateWithTimeIntervalSince1970_(start_dt.timestamp())
            end_ns = NSDate.dateWithTimeIntervalSince1970_(end_dt.timestamp())

            # Get calendars
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)

            # Filter calendars if specified
            if calendar_names:
                calendars = [c for c in calendars if c.title() in calendar_names]

            # Create predicate and fetch events
            predicate = self.event_store.predicateForEventsWithStartDate_endDate_calendars_(
                start_ns, end_ns, calendars
            )

            events = self.event_store.eventsMatchingPredicate_(predicate)

            # Convert to dictionaries
            result = []
            for event in events:
                # Get the current user's participation status
                attendees = event.attendees()
                user_email = None
                user_status = "Organizer"  # Default if no attendees or user is organizer

                if attendees:
                    for attendee in attendees:
                        if attendee.isCurrentUser():
                            user_email = str(attendee.emailAddress() or "")
                            user_status = self.get_rsvp_status(attendee)
                            break

                # Format the event - minimal data + attendee count
                attendee_count = len(attendees) if attendees else 0
                event_dict = {
                    "title": str(event.title() or ""),
                    "calendar": str(event.calendar().title() or ""),
                    "start_date_str": datetime.fromtimestamp(
                        event.startDate().timeIntervalSince1970()
                    ).isoformat(),
                    "end_date_str": datetime.fromtimestamp(
                        event.endDate().timeIntervalSince1970()
                    ).isoformat(),
                    "all_day": bool(event.isAllDay()),
                    "notes": str(event.notes() or ""),
                    "organizer": str(event.organizer().name() if event.organizer() else ""),
                    "user_rsvp_status": user_status,
                    "attendee_count": attendee_count,
                }
                result.append(event_dict)

            return result

        return await asyncio.to_thread(_get_events)

    async def get_calendars(self) -> List[Dict[str, str]]:
        """Get list of available calendars"""
        if not self.access_granted:
            await self.request_access()

        def _get_calendars():
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
            return [
                {
                    "title": str(cal.title()),
                    "type": str(cal.type()),
                    "color": str(cal.color()),
                    "source": str(cal.source().title()),
                }
                for cal in calendars
            ]

        return await asyncio.to_thread(_get_calendars)


# Create the MCP server
app = Server("mac-calendar-mcp")
calendar = CalendarServer()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available calendar tools"""
    return [
        Tool(
            name="get_calendar_events",
            description="""Get calendar events with full details including:
- Event title, description/notes, location
- Calendar name (which calendar the event belongs to)
- Start and end times
- RSVP status (Accepted, Declined, Tentative, Pending)
- Attendees list with their RSVP statuses
- Organizer information
- Whether it's an all-day event
- Meeting URL if available

Perfect for understanding your schedule, priorities, and commitments.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format (default: today)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format (default: start_date + days_ahead)",
                    },
                    "calendar_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by specific calendar names (default: all calendars)",
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days to look ahead if end_date not specified (default: 7)",
                        "default": 7,
                    },
                },
            },
        ),
        Tool(
            name="list_calendars",
            description="List all available calendars with their names, types, and sources",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    if name == "get_calendar_events":
        events = await calendar.get_events(
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            calendar_names=arguments.get("calendar_names"),
            days_ahead=arguments.get("days_ahead", 7),
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(events, indent=2, default=str),
            )
        ]

    elif name == "list_calendars":
        calendars = await calendar.get_calendars()

        return [
            TextContent(
                type="text",
                text=json.dumps(calendars, indent=2, default=str),
            )
        ]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
