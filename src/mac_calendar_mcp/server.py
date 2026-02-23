#!/usr/bin/env python3
"""
macOS Calendar MCP Server
Provides access to Apple Calendar events synced from Google Calendar
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import pytz

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# PyObjC imports for EventKit
from Foundation import NSDate, NSPredicate
from EventKit import (
    EKEventStore,
    EKEntityTypeEvent,
    EKEntityTypeReminder,
    EKParticipantStatusAccepted,
    EKParticipantStatusDeclined,
    EKParticipantStatusTentative,
    EKParticipantStatusPending,
    EKParticipantStatusUnknown,
    EKEventAvailabilityBusy,
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

    def extract_meeting_url(self, event) -> Optional[str]:
        """Extract meeting URL from event URL field or notes"""
        # Try the URL field first
        url = event.URL()
        if url:
            return str(url)

        # Fallback: search notes for common meeting URLs
        notes = event.notes() or ""
        url_patterns = [
            r'https://[^\s]*zoom\.us/[^\s]*',
            r'https://[^\s]*meet\.google\.com/[^\s]*',
            r'https://[^\s]*teams\.microsoft\.com/[^\s]*',
            r'https://[^\s]*webex\.com/[^\s]*',
        ]

        for pattern in url_patterns:
            match = re.search(pattern, notes, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    async def get_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        calendar_names: Optional[List[str]] = None,
        days_ahead: int = 7,
        attendee_name_pattern: Optional[str] = None,
        attendee_status_filter: Optional[List[str]] = None,
        all_day_only: bool = False,
        busy_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Fetch calendar events

        Args:
            start_date: ISO format date string (YYYY-MM-DD) or None for today
            end_date: ISO format date string (YYYY-MM-DD) or None for start_date + days_ahead
            calendar_names: List of calendar names to filter, or None for all
            days_ahead: Number of days to look ahead if end_date not specified
            attendee_name_pattern: Filter events by attendee name/email substring (case-insensitive)
            attendee_status_filter: Filter events by attendee RSVP status (e.g., ["Accepted", "Tentative"])
            all_day_only: If True, only return all-day events
            busy_only: If True, only return events marked as busy
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
                # Get the current user's participation status and build attendee details
                attendees_raw = event.attendees()
                user_email = None
                user_status = "Organizer"  # Default if no attendees or user is organizer
                attendees_list = []

                if attendees_raw:
                    for attendee in attendees_raw:
                        # Build detailed attendee info
                        attendee_info = {
                            "name": str(attendee.name() or ""),
                            "email": str(attendee.emailAddress() or ""),
                            "status": self.get_rsvp_status(attendee),
                            "is_organizer": False,  # EventKit doesn't expose this easily
                            "is_current_user": bool(attendee.isCurrentUser()),
                        }
                        attendees_list.append(attendee_info)

                        # Track current user's status
                        if attendee.isCurrentUser():
                            user_email = attendee_info["email"]
                            user_status = attendee_info["status"]

                # Extract location and meeting URL
                location = event.location()
                location_str = str(location) if location else ""

                meeting_url = self.extract_meeting_url(event)

                # Format the event with all fields
                attendee_count = len(attendees_list)
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
                    "location": location_str,
                    "meeting_url": meeting_url,
                    "organizer": str(event.organizer().name() if event.organizer() else ""),
                    "user_rsvp_status": user_status,
                    "attendee_count": attendee_count,
                    "attendees": attendees_list,
                }
                result.append(event_dict)

            # Apply post-processing filters
            # Filter by all-day status
            if all_day_only:
                result = [e for e in result if e["all_day"]]

            # Filter by busy status
            if busy_only:
                # Re-fetch events to check availability status
                filtered_result = []
                for i, event in enumerate(events):
                    if i < len(result):  # Ensure indices match
                        try:
                            availability = event.availability()
                            if availability == EKEventAvailabilityBusy:
                                filtered_result.append(result[i])
                        except:
                            # If availability() fails, skip this filter for this event
                            filtered_result.append(result[i])
                result = filtered_result

            # Filter by attendee name pattern
            if attendee_name_pattern:
                pattern_lower = attendee_name_pattern.lower()
                result = [
                    e for e in result
                    if any(
                        pattern_lower in att["name"].lower() or
                        pattern_lower in att["email"].lower()
                        for att in e["attendees"]
                    )
                ]

            # Filter by attendee status
            if attendee_status_filter:
                result = [
                    e for e in result
                    if any(
                        att["status"] in attendee_status_filter
                        for att in e["attendees"]
                    )
                ]

            return result

        return await asyncio.to_thread(_get_events)

    async def get_reminders(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        calendar_names: Optional[List[str]] = None,
        include_completed: bool = False,
        days_ahead: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Fetch reminders

        Args:
            start_date: ISO format date string (YYYY-MM-DD) or None for today
            end_date: ISO format date string (YYYY-MM-DD) or None for start_date + days_ahead
            calendar_names: List of calendar names to filter, or None for all
            include_completed: Whether to include completed reminders
            days_ahead: Number of days to look ahead if end_date not specified
        """
        if not self.access_granted:
            await self.request_access()

        def _get_reminders():
            import threading

            # Parse dates (similar to events)
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                if end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0:
                    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                end_dt = start_dt + timedelta(days=days_ahead)
                end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Get calendars for reminders
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeReminder)

            # Filter calendars if specified
            if calendar_names:
                calendars = [c for c in calendars if c.title() in calendar_names]

            # Create predicate for reminders
            predicate = self.event_store.predicateForRemindersInCalendars_(calendars)

            # Fetch reminders using completion handler
            reminders = []
            done = threading.Event()

            def completion_handler(fetched_reminders):
                if fetched_reminders:
                    reminders.extend(fetched_reminders)
                done.set()

            self.event_store.fetchRemindersMatchingPredicate_completion_(
                predicate, completion_handler
            )

            # Wait for completion
            done.wait(timeout=30)

            # Filter and format reminders
            result = []
            for reminder in reminders:
                # Filter by completion status
                is_completed = bool(reminder.isCompleted())
                if not include_completed and is_completed:
                    continue

                # Filter by due date
                due_date = reminder.dueDateComponents()
                if due_date:
                    # Convert to datetime for comparison
                    try:
                        due_dt = datetime(
                            due_date.year(),
                            due_date.month(),
                            due_date.day(),
                            due_date.hour() if due_date.hour() != -1 else 0,
                            due_date.minute() if due_date.minute() != -1 else 0,
                            due_date.second() if due_date.second() != -1 else 0,
                        )
                        # Check if within date range
                        if due_dt < start_dt or due_dt > end_dt:
                            continue
                        due_date_str = due_dt.isoformat()
                    except:
                        due_date_str = None
                else:
                    # No due date - skip if filtering by date range
                    if start_date or end_date:
                        continue
                    due_date_str = None

                # Get completion date
                completion_date = reminder.completionDate()
                completion_date_str = None
                if completion_date:
                    completion_date_str = datetime.fromtimestamp(
                        completion_date.timeIntervalSince1970()
                    ).isoformat()

                # Get priority
                priority = reminder.priority()
                priority_map = {
                    0: "None",
                    1: "High",
                    5: "Medium",
                    9: "Low",
                }
                priority_str = priority_map.get(priority, "None")

                reminder_dict = {
                    "title": str(reminder.title() or ""),
                    "calendar": str(reminder.calendar().title() or ""),
                    "due_date_str": due_date_str,
                    "completion_date_str": completion_date_str,
                    "is_completed": is_completed,
                    "priority": priority_str,
                    "notes": str(reminder.notes() or ""),
                }
                result.append(reminder_dict)

            return result

        return await asyncio.to_thread(_get_reminders)

    async def search(
        self,
        query: str,
        search_events: bool = True,
        search_reminders: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search events and reminders by query string

        Args:
            query: Search query (case-insensitive substring match)
            search_events: Whether to search events
            search_reminders: Whether to search reminders
            start_date: ISO format date string (YYYY-MM-DD) or None for today
            end_date: ISO format date string (YYYY-MM-DD) or None for 30 days ahead
        """
        query_lower = query.lower()
        results = []

        # Set default date range (30 days)
        if not end_date and not start_date:
            days_ahead = 30
        else:
            days_ahead = 30

        # Search events
        if search_events:
            events = await self.get_events(
                start_date=start_date,
                end_date=end_date,
                days_ahead=days_ahead,
            )

            for event in events:
                # Search in title, notes, and location
                if (
                    query_lower in event["title"].lower()
                    or query_lower in event["notes"].lower()
                    or query_lower in event.get("location", "").lower()
                ):
                    event["type"] = "event"
                    results.append(event)

        # Search reminders
        if search_reminders:
            reminders = await self.get_reminders(
                start_date=start_date,
                end_date=end_date,
                days_ahead=days_ahead,
                include_completed=True,  # Include completed for search
            )

            for reminder in reminders:
                # Search in title and notes
                if (
                    query_lower in reminder["title"].lower()
                    or query_lower in reminder["notes"].lower()
                ):
                    reminder["type"] = "reminder"
                    results.append(reminder)

        return results

    async def get_today_summary(self) -> Dict[str, Any]:
        """
        Get today's events and reminders summary
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Get today's events
        events = await self.get_events(
            start_date=today,
            end_date=today,
        )

        # Get today's reminders (incomplete only)
        reminders = await self.get_reminders(
            start_date=today,
            end_date=today,
            include_completed=False,
        )

        return {
            "date": today,
            "events_count": len(events),
            "events": events,
            "reminders_count": len(reminders),
            "reminders": reminders,
        }

    async def get_current_time(self, timezone: str = "UTC") -> Dict[str, str]:
        """
        Get current time in specified timezone

        Args:
            timezone: Timezone name (e.g., "UTC", "America/New_York", "Europe/London")
        """
        try:
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)
            return {
                "timezone": timezone,
                "datetime": current_time.isoformat(),
                "timestamp": current_time.timestamp(),
            }
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")

    async def convert_time(
        self, datetime_str: str, from_timezone: str, to_timezone: str
    ) -> Dict[str, str]:
        """
        Convert datetime between timezones

        Args:
            datetime_str: ISO format datetime string
            from_timezone: Source timezone name
            to_timezone: Target timezone name
        """
        try:
            from_tz = pytz.timezone(from_timezone)
            to_tz = pytz.timezone(to_timezone)

            # Parse datetime
            dt = datetime.fromisoformat(datetime_str)

            # If naive, localize to from_timezone
            if dt.tzinfo is None:
                dt = from_tz.localize(dt)
            else:
                # If already aware, convert to from_timezone
                dt = dt.astimezone(from_tz)

            # Convert to target timezone
            dt_converted = dt.astimezone(to_tz)

            return {
                "from_timezone": from_timezone,
                "to_timezone": to_timezone,
                "original_datetime": dt.isoformat(),
                "converted_datetime": dt_converted.isoformat(),
            }
        except pytz.exceptions.UnknownTimeZoneError as e:
            raise ValueError(f"Unknown timezone: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid datetime string: {e}")

    async def list_timezones(self, region: Optional[str] = None) -> List[str]:
        """
        List available timezones

        Args:
            region: Optional region filter (e.g., "America", "Europe", "Asia")
        """
        all_timezones = pytz.all_timezones

        if region:
            # Filter by region prefix
            return [tz for tz in all_timezones if tz.startswith(region + "/")]
        else:
            return list(all_timezones)

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
- Attendees list with their RSVP statuses, names, and emails
- Organizer information
- Whether it's an all-day event
- Meeting URL if available

Supports filtering by:
- Attendee name or email (substring matching)
- Attendee RSVP status (Accepted, Declined, Tentative, Pending)
- All-day events only
- Busy events only

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
                    "attendee_name_pattern": {
                        "type": "string",
                        "description": "Filter events by attendee name or email (case-insensitive substring match)",
                    },
                    "attendee_status_filter": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter events by attendee RSVP status (e.g., ['Accepted', 'Tentative'])",
                    },
                    "all_day_only": {
                        "type": "boolean",
                        "description": "If true, only return all-day events (default: false)",
                        "default": False,
                    },
                    "busy_only": {
                        "type": "boolean",
                        "description": "If true, only return events marked as busy (default: false)",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="get_events",
            description="""Alias for get_calendar_events. Get calendar events with full details including:
- Event title, description/notes, location
- Calendar name (which calendar the event belongs to)
- Start and end times
- RSVP status (Accepted, Declined, Tentative, Pending)
- Attendees list with their RSVP statuses, names, and emails
- Organizer information
- Whether it's an all-day event
- Meeting URL if available

Supports filtering by:
- Attendee name or email (substring matching)
- Attendee RSVP status (Accepted, Declined, Tentative, Pending)
- All-day events only
- Busy events only

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
                    "attendee_name_pattern": {
                        "type": "string",
                        "description": "Filter events by attendee name or email (case-insensitive substring match)",
                    },
                    "attendee_status_filter": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter events by attendee RSVP status (e.g., ['Accepted', 'Tentative'])",
                    },
                    "all_day_only": {
                        "type": "boolean",
                        "description": "If true, only return all-day events (default: false)",
                        "default": False,
                    },
                    "busy_only": {
                        "type": "boolean",
                        "description": "If true, only return events marked as busy (default: false)",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="list_calendars",
            description="List all available calendars with their names, types, and sources",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_reminders",
            description="""Get reminders with full details including:
- Title and notes
- Calendar name
- Due date and completion date
- Completion status
- Priority level (High, Medium, Low, None)

Supports filtering by date range, calendar names, and completion status.""",
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
                    "include_completed": {
                        "type": "boolean",
                        "description": "Include completed reminders (default: false)",
                        "default": False,
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
            name="search",
            description="""Search across events and reminders by query string.
Searches in:
- Event titles, notes, and locations
- Reminder titles and notes

Case-insensitive substring matching. Returns both events and reminders with a 'type' field.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "search_events": {
                        "type": "boolean",
                        "description": "Search in events (default: true)",
                        "default": True,
                    },
                    "search_reminders": {
                        "type": "boolean",
                        "description": "Search in reminders (default: true)",
                        "default": True,
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format (default: today)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format (default: 30 days ahead)",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_today_summary",
            description="""Get a summary of today's events and reminders.
Returns:
- Date
- Count of events and reminders
- List of today's events
- List of today's incomplete reminders""",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_current_time",
            description="Get current time in a specific timezone",
            inputSchema={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone name (e.g., 'UTC', 'America/New_York', 'Europe/London'). Default: UTC",
                        "default": "UTC",
                    },
                },
            },
        ),
        Tool(
            name="convert_time",
            description="Convert datetime between timezones",
            inputSchema={
                "type": "object",
                "properties": {
                    "datetime_str": {
                        "type": "string",
                        "description": "ISO format datetime string to convert",
                    },
                    "from_timezone": {
                        "type": "string",
                        "description": "Source timezone name",
                    },
                    "to_timezone": {
                        "type": "string",
                        "description": "Target timezone name",
                    },
                },
                "required": ["datetime_str", "from_timezone", "to_timezone"],
            },
        ),
        Tool(
            name="list_timezones",
            description="List available timezones, optionally filtered by region",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Optional region filter (e.g., 'America', 'Europe', 'Asia')",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    if name == "get_calendar_events" or name == "get_events":
        events = await calendar.get_events(
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            calendar_names=arguments.get("calendar_names"),
            days_ahead=arguments.get("days_ahead", 7),
            attendee_name_pattern=arguments.get("attendee_name_pattern"),
            attendee_status_filter=arguments.get("attendee_status_filter"),
            all_day_only=arguments.get("all_day_only", False),
            busy_only=arguments.get("busy_only", False),
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

    elif name == "get_reminders":
        reminders = await calendar.get_reminders(
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            calendar_names=arguments.get("calendar_names"),
            include_completed=arguments.get("include_completed", False),
            days_ahead=arguments.get("days_ahead", 7),
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(reminders, indent=2, default=str),
            )
        ]

    elif name == "search":
        results = await calendar.search(
            query=arguments.get("query"),
            search_events=arguments.get("search_events", True),
            search_reminders=arguments.get("search_reminders", True),
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(results, indent=2, default=str),
            )
        ]

    elif name == "get_today_summary":
        summary = await calendar.get_today_summary()

        return [
            TextContent(
                type="text",
                text=json.dumps(summary, indent=2, default=str),
            )
        ]

    elif name == "get_current_time":
        result = await calendar.get_current_time(
            timezone=arguments.get("timezone", "UTC"),
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str),
            )
        ]

    elif name == "convert_time":
        result = await calendar.convert_time(
            datetime_str=arguments.get("datetime_str"),
            from_timezone=arguments.get("from_timezone"),
            to_timezone=arguments.get("to_timezone"),
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str),
            )
        ]

    elif name == "list_timezones":
        result = await calendar.list_timezones(
            region=arguments.get("region"),
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str),
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
