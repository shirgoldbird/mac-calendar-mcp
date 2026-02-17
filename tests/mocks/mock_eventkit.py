"""Mock PyObjC EventKit objects for testing without real calendar access."""

from datetime import datetime
from typing import Optional, List, Any


class MockNSDate:
    """Mock NSDate for testing."""

    def __init__(self, timestamp: float):
        self._timestamp = timestamp

    def timeIntervalSince1970(self) -> float:
        return self._timestamp

    @classmethod
    def dateWithTimeIntervalSince1970_(cls, timestamp: float):
        return cls(timestamp)


class MockEKParticipant:
    """Mock EKParticipant for testing."""

    def __init__(
        self,
        name: str,
        email: Optional[str] = None,
        status: int = 0,
        is_current_user: bool = False
    ):
        self._name = name
        self._email = email
        self._status = status
        self._is_current_user = is_current_user

    def name(self) -> str:
        return self._name

    def emailAddress(self) -> Optional[str]:
        return self._email

    def participantStatus(self) -> int:
        return self._status

    def isCurrentUser(self) -> bool:
        return self._is_current_user


class MockEKCalendar:
    """Mock EKCalendar for testing."""

    def __init__(
        self,
        title: str,
        cal_type: str = "Local",
        color: str = "#FF0000",
        source_title: str = "Local"
    ):
        self._title = title
        self._type = cal_type
        self._color = color
        self._source_title = source_title

    def title(self) -> str:
        return self._title

    def type(self) -> str:
        return self._type

    def color(self) -> str:
        return self._color

    def source(self):
        """Return mock source object."""
        class MockSource:
            def __init__(self, source_title):
                self._source_title = source_title
            def title(self):
                return self._source_title
        return MockSource(self._source_title)


class MockEKEvent:
    """Mock EKEvent for testing."""

    def __init__(
        self,
        title: str,
        start: datetime,
        end: datetime,
        calendar,
        notes: str = "",
        organizer_name: str = "",
        attendees: Optional[List] = None,
        is_all_day: bool = False
    ):
        self._title = title
        self._start = MockNSDate(start.timestamp())
        self._end = MockNSDate(end.timestamp())
        self._calendar = calendar
        self._notes = notes
        self._organizer_name = organizer_name
        self._attendees = attendees or []
        self._is_all_day = is_all_day

    def title(self) -> str:
        return self._title

    def startDate(self):
        return self._start

    def endDate(self):
        return self._end

    def calendar(self):
        return self._calendar

    def notes(self) -> str:
        return self._notes

    def organizer(self):
        """Return mock organizer object."""
        if not self._organizer_name:
            return None

        class MockOrganizer:
            def __init__(self, name: str):
                self._name = name
            def name(self) -> str:
                return self._name

        return MockOrganizer(self._organizer_name)

    def attendees(self):
        return self._attendees

    def isAllDay(self) -> bool:
        return self._is_all_day


class MockEKEventStore:
    """Mock EKEventStore for testing."""

    # Class-level authorization status for authorizationStatusForEntityType_
    _class_auth_status = None

    def __init__(self):
        self._calendars = []
        self._events = []
        self._authorized = False

    @classmethod
    def alloc(cls):
        """Mimic PyObjC alloc pattern."""
        return cls()

    def init(self):
        """Mimic PyObjC init pattern."""
        return self

    @classmethod
    def authorizationStatusForEntityType_(cls, entity_type):
        """Check authorization status (class method)."""
        if cls._class_auth_status is not None:
            return cls._class_auth_status
        return EKAuthorizationStatusNotDetermined

    def set_authorized(self, authorized: bool):
        """Set authorization status for testing."""
        self._authorized = authorized
        # Also set class-level status
        if authorized:
            MockEKEventStore._class_auth_status = EKAuthorizationStatusAuthorized
        else:
            MockEKEventStore._class_auth_status = EKAuthorizationStatusDenied

    def add_calendar(self, calendar):
        """Add a mock calendar."""
        self._calendars.append(calendar)

    def add_event(self, event):
        """Add a mock event."""
        self._events.append(event)

    def calendarsForEntityType_(self, entity_type: int):
        """Return mock calendars."""
        return self._calendars

    def predicateForEventsWithStartDate_endDate_calendars_(
        self,
        start_date,
        end_date,
        calendars
    ):
        """Return a mock predicate (just store the params)."""
        class MockPredicate:
            def __init__(self, start, end, cals):
                self.start = start
                self.end = end
                self.calendars = cals

        return MockPredicate(start_date, end_date, calendars)

    def eventsMatchingPredicate_(self, predicate):
        """Return events matching the predicate."""
        start_ts = predicate.start.timeIntervalSince1970()
        end_ts = predicate.end.timeIntervalSince1970()
        calendar_titles = {cal.title() for cal in predicate.calendars}

        # Filter events by date range and calendars
        matching = []
        for event in self._events:
            event_start = event.startDate().timeIntervalSince1970()
            event_end = event.endDate().timeIntervalSince1970()
            event_calendar = event.calendar().title()

            # Check if event overlaps with date range
            if event_start <= end_ts and event_end >= start_ts:
                # Check if calendar matches
                if event_calendar in calendar_titles:
                    matching.append(event)

        return matching

    def requestFullAccessToEventsWithCompletion_(self, completion_handler):
        """Mock permission request."""
        # Call completion handler immediately with authorized status
        completion_handler(self._authorized, None)


# Mock EventKit constants
EKEntityTypeEvent = 0
EKParticipantStatusUnknown = 0
EKParticipantStatusPending = 1
EKParticipantStatusAccepted = 2
EKParticipantStatusDeclined = 3
EKParticipantStatusTentative = 4
EKAuthorizationStatusNotDetermined = 0
EKAuthorizationStatusRestricted = 1
EKAuthorizationStatusDenied = 2
EKAuthorizationStatusAuthorized = 3
