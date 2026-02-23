# macOS Calendar MCP Server

This MCP server provides Claude Code with access to your macOS Calendar events (including synced Google Calendar events).

## Installation

### Prerequisites

- macOS (required for EventKit framework)
- Python 3.8 or higher
- Claude Code CLI

### Option 1: Install from PyPI (Recommended)

The easiest way to install:

```bash
source ~/.zshrc && pip install mac-calendar-mcp
```

Then configure Claude Code by adding to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "calendar": {
      "command": "uvx",
      "args": ["mac-calendar-mcp"]
    }
  }
}
```

Or use Python directly:

```json
{
  "mcpServers": {
    "calendar": {
      "command": "python",
      "args": ["-m", "mac_calendar_mcp.server"]
    }
  }
}
```

### Option 2: Install from Source

For development or if you want to modify the code:

```bash
git clone https://github.com/yourusername/mac-calendar-mcp.git
cd mac-calendar-mcp
source ~/.zshrc && pip install -e .
```

Then configure Claude Code at `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "calendar": {
      "command": "python",
      "args": [
        "/Users/YOUR_USERNAME/PATH_TO_FOLDER/mac-calendar-mcp/src/mac_calendar_mcp/server.py"
      ]
    }
  }
}
```

**Important**: Use the full absolute path to the server.py file.

### Grant Calendar Permissions

On first use, macOS will prompt you to grant Calendar access. Click **Allow** when prompted.

You can verify or change permissions later at:
**System Settings → Privacy & Security → Calendar**

### Restart Claude Code

After adding the server configuration, restart Claude Code for the changes to take effect.

### Verify Installation

Check the MCP server list in Claude Code:
```bash
claude mcp list
```

Or test the server directly (if installed from source):

```bash
cd mac-calendar-mcp
source ~/.zshrc && python test.py
```

## Features

### Events
- ✅ Access all calendar events across all calendars
- ✅ Full event details including descriptions/notes
- ✅ Calendar name identification (shows which calendar each event belongs to)
- ✅ RSVP status tracking (Accepted, Declined, Tentative, Pending)
- ✅ Detailed attendee information with names, emails, and RSVP statuses
- ✅ Event locations and meeting URLs (Zoom, Google Meet, Teams)
- ✅ Organizer information
- ✅ All-day event detection
- ✅ Date range filtering
- ✅ Calendar-specific filtering
- ✅ **NEW**: Filter events by attendee name or email
- ✅ **NEW**: Filter events by attendee RSVP status
- ✅ **NEW**: Filter for all-day events only
- ✅ **NEW**: Filter for busy events only

### Reminders
- ✅ **NEW**: Access reminders with due dates
- ✅ **NEW**: Priority levels (High, Medium, Low, None)
- ✅ **NEW**: Completion status tracking
- ✅ **NEW**: Filter by completion status
- ✅ **NEW**: Reminder notes and details

### Search & Organization
- ✅ **NEW**: Search across events and reminders
- ✅ **NEW**: Today's schedule summary
- ✅ **NEW**: Full-text search in titles, notes, and locations

### Timezone Support
- ✅ **NEW**: Get current time in any timezone
- ✅ **NEW**: Convert times between timezones
- ✅ **NEW**: List available timezones by region

## Available Tools

### 1. `get_calendar_events` / `get_events`

Fetch calendar events with full details including attendee filtering.

**Parameters:**
- `start_date` (optional): Start date in YYYY-MM-DD format (default: today)
- `end_date` (optional): End date in YYYY-MM-DD format (default: start_date + days_ahead)
- `calendar_names` (optional): Array of calendar names to filter (default: all calendars)
- `days_ahead` (optional): Number of days to look ahead (default: 7)
- `attendee_name_pattern` (optional): Filter by attendee name or email (case-insensitive)
- `attendee_status_filter` (optional): Filter by RSVP status (e.g., ["Accepted", "Tentative"])
- `all_day_only` (optional): Only return all-day events (default: false)
- `busy_only` (optional): Only return busy events (default: false)

**Example queries you can ask Claude:**
- "What's on my calendar today?"
- "Show me all meetings I've accepted this week"
- "Find all events where Shir accepted the invitation"
- "What meetings does alice@company.com have tentative?"
- "Show me my schedule for next Monday"
- "What all-day events do I have this month?"

### 2. `get_reminders`

Fetch reminders with due dates, priorities, and completion status.

**Parameters:**
- `start_date` (optional): Start date in YYYY-MM-DD format (default: today)
- `end_date` (optional): End date in YYYY-MM-DD format (default: start_date + days_ahead)
- `calendar_names` (optional): Array of calendar names to filter (default: all calendars)
- `include_completed` (optional): Include completed reminders (default: false)
- `days_ahead` (optional): Number of days to look ahead (default: 7)

**Example queries:**
- "What reminders do I have due today?"
- "Show me all high priority reminders"
- "What incomplete tasks do I have this week?"
- "List all completed reminders from yesterday"

### 3. `search`

Search across events and reminders by keyword.

**Parameters:**
- `query` (required): Search query string
- `search_events` (optional): Search in events (default: true)
- `search_reminders` (optional): Search in reminders (default: true)
- `start_date` (optional): Start date filter (default: today)
- `end_date` (optional): End date filter (default: 30 days ahead)

**Example queries:**
- "Search my calendar for 'standup'"
- "Find all events mentioning 'project deadline'"
- "Search for reminders about 'groceries'"

### 4. `get_today_summary`

Get a summary of today's events and incomplete reminders.

**Parameters:** None

**Example queries:**
- "What's my schedule today?"
- "Give me a summary of today"
- "What do I have on today?"

### 5. `list_calendars`

List all available calendars.

**Example queries:**
- "What calendars do I have?"
- "List all my calendar sources"

### 6. `get_current_time`

Get current time in a specific timezone.

**Parameters:**
- `timezone` (optional): Timezone name (default: "UTC")

**Example queries:**
- "What time is it in Tokyo?"
- "Get current time in London"
- "What's the time in America/New_York?"

### 7. `convert_time`

Convert datetime between timezones.

**Parameters:**
- `datetime_str` (required): ISO format datetime string
- `from_timezone` (required): Source timezone name
- `to_timezone` (required): Target timezone name

**Example queries:**
- "Convert 2024-03-15T14:00:00 from UTC to PST"
- "What time is 9am London time in New York?"

### 8. `list_timezones`

List available timezones, optionally filtered by region.

**Parameters:**
- `region` (optional): Region filter (e.g., "America", "Europe", "Asia")

**Example queries:**
- "List all timezones"
- "Show me timezones in Europe"
- "What timezones are available in Asia?"

## Use Cases

Now that this is set up, you can ask Claude to:

### Calendar Management
1. **Daily Overview**: "Give me a summary of today's schedule"
2. **Meeting Prep**: "What's the meeting URL and description for my next meeting?"
3. **Schedule Analysis**: "How much time am I spending in meetings this week?"
4. **Find Conflicts**: "Do I have any scheduling conflicts?"

### Attendee Tracking (NEW)
5. **Filter by Person**: "Find all events where Shir accepted the invitation"
6. **RSVP Analysis**: "Show me all meetings where Alice has tentative status"
7. **Team Coordination**: "What meetings does the engineering team have this week?"
8. **Response Tracking**: "Show me all meetings I haven't responded to"

### Task Management (NEW)
9. **Reminder Overview**: "What incomplete tasks do I have?"
10. **Priority Focus**: "Show me all high priority reminders"
11. **Task Planning**: "What reminders are due this week?"

### Search & Discovery (NEW)
12. **Content Search**: "Search my calendar for 'project deadline'"
13. **Meeting Lookup**: "Find all events about the new feature"
14. **Reminder Search**: "Search for reminders about 'presentation'"

### Timezone Coordination (NEW)
15. **Global Teams**: "What time is it in Tokyo right now?"
16. **Time Conversion**: "Convert 2pm London time to New York time"
17. **Meeting Scheduling**: "If I schedule a meeting at 10am PST, what time is that in Paris?"

## Testing

You can test the server directly (if installed from source):
```bash
cd mac-calendar-mcp
source ~/.zshrc && python test.py
```

## Troubleshooting

If the server isn't working:

1. **Check permissions**: System Settings → Privacy & Security → Calendar
2. **Verify server status**: `claude mcp list`
3. **Test directly**: Run the test script above
4. **Restart Claude Code**: Sometimes needed after adding new servers

## Technical Details

- Built with PyObjC and EventKit framework
- Uses macOS native Calendar.app data
- Syncs automatically with Google Calendar (if configured in Calendar.app)
- No Google API credentials needed
- No GCP project required
