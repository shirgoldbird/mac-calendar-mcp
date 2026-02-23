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


class MockEKDateComponents:
    """Mock NSDateComponents for testing."""

    def __init__(self, year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0):
        self._year = year
        self._month = month
        self._day = day
        self._hour = hour
        self._minute = minute
        self._second = second

    def year(self) -> int:
        return self._year

    def month(self) -> int:
        return self._month

    def day(self) -> int:
        return self._day

    def hour(self) -> int:
        return self._hour

    def minute(self) -> int:
        return self._minute

    def second(self) -> int:
        return self._second


class MockEKReminder:
    """Mock EKReminder for testing."""

    def __init__(
        self,
        title: str,
        calendar,
        due_date_components: Optional[MockEKDateComponents] = None,
        is_completed: bool = False,
        completion_date: Optional[datetime] = None,
        priority: int = 0,
        notes: str = "",
    ):
        self._title = title
        self._calendar = calendar
        self._due_date_components = due_date_components
        self._is_completed = is_completed
        self._completion_date = (
            MockNSDate(completion_date.timestamp()) if completion_date else None
        )
        self._priority = priority
        self._notes = notes

    def title(self) -> str:
        return self._title

    def calendar(self):
        return self._calendar

    def dueDateComponents(self):
        return self._due_date_components

    def isCompleted(self) -> bool:
        return self._is_completed

    def completionDate(self):
        return self._completion_date

    def priority(self) -> int:
        return self._priority

    def notes(self) -> str:
        return self._notes


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
        is_all_day: bool = False,
        location: str = "",
        url: Optional[str] = None,
        availability: int = 0  # 0 = busy by default
    ):
        self._title = title
        self._start = MockNSDate(start.timestamp())
        self._end = MockNSDate(end.timestamp())
        self._calendar = calendar
        self._notes = notes
        self._organizer_name = organizer_name
        self._attendees = attendees or []
        self._is_all_day = is_all_day
        self._location = location
        self._url = url
        self._availability = availability

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

    def location(self) -> Optional[str]:
        return self._location if self._location else None

    def URL(self) -> Optional[str]:
        return self._url

    def availability(self) -> int:
        return self._availability


class MockEKEventStore:
    """Mock EKEventStore for testing."""

    # Class-level authorization status for authorizationStatusForEntityType_
    _class_auth_status = None

    def __init__(self):
        self._calendars = []
        self._events = []
        self._reminders = []
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

    def add_reminder(self, reminder):
        """Add a mock reminder."""
        self._reminders.append(reminder)

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

    def predicateForRemindersInCalendars_(self, calendars):
        """Return a mock predicate for reminders."""
        class MockReminderPredicate:
            def __init__(self, cals):
                self.calendars = cals

        return MockReminderPredicate(calendars)

    def fetchRemindersMatchingPredicate_completion_(self, predicate, completion_handler):
        """Fetch reminders matching predicate."""
        calendar_titles = {cal.title() for cal in predicate.calendars}

        # Filter reminders by calendar
        matching = []
        for reminder in self._reminders:
            reminder_calendar = reminder.calendar().title()
            if reminder_calendar in calendar_titles:
                matching.append(reminder)

        # Call completion handler immediately
        completion_handler(matching)


# Mock EventKit constants
EKEntityTypeEvent = 0
EKEntityTypeReminder = 1
EKParticipantStatusUnknown = 0
EKParticipantStatusPending = 1
EKParticipantStatusAccepted = 2
EKParticipantStatusDeclined = 3
EKParticipantStatusTentative = 4
EKAuthorizationStatusNotDetermined = 0
EKAuthorizationStatusRestricted = 1
EKAuthorizationStatusDenied = 2
EKAuthorizationStatusAuthorized = 3
EKEventAvailabilityBusy = 0
EKEventAvailabilityFree = 1
EKReminderPriorityNone = 0
EKReminderPriorityHigh = 1
EKReminderPriorityMedium = 5
EKReminderPriorityLow = 9
