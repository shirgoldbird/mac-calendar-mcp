# macOS Calendar MCP Server

This MCP server provides Claude Code with access to your macOS Calendar events (including synced Google Calendar events).

## Features

- ✅ Access all calendar events across all calendars
- ✅ Full event details including descriptions/notes
- ✅ Calendar name identification (shows which calendar each event belongs to)
- ✅ RSVP status tracking (Accepted, Declined, Tentative, Pending)
- ✅ Attendee information with their RSVP statuses
- ✅ Event locations and meeting URLs
- ✅ Organizer information
- ✅ All-day event detection
- ✅ Date range filtering
- ✅ Calendar-specific filtering

## Permissions

On first use, macOS will prompt you to grant Calendar access to Terminal. This is required for the server to work.

You can also manually manage permissions at:
**System Settings → Privacy & Security → Calendar**

## Available Tools

### 1. `get_calendar_events`

Fetch calendar events with full details.

**Parameters:**
- `start_date` (optional): Start date in YYYY-MM-DD format (default: today)
- `end_date` (optional): End date in YYYY-MM-DD format (default: start_date + days_ahead)
- `calendar_names` (optional): Array of calendar names to filter (default: all calendars)
- `days_ahead` (optional): Number of days to look ahead (default: 7)

**Example queries you can ask Claude:**
- "What's on my calendar today?"
- "Show me all meetings I've accepted this week"
- "What events do I have on the Team calendar?"
- "What meetings do I have tentative RSVP for?"
- "Show me my schedule for next Monday"
- "List all events with descriptions containing 'standup'"

### 2. `list_calendars`

List all available calendars.

**Example queries:**
- "What calendars do I have?"
- "List all my calendar sources"

## Use Cases

Now that this is set up, you can ask Claude to:

1. **Surface Context**: "Based on my calendar, what should I focus on today?"
2. **Determine Priorities**: "What are my most important meetings this week?"
3. **Find Conflicts**: "Do I have any scheduling conflicts?"
4. **RSVP Management**: "Show me all meetings I haven't responded to"
5. **Team Coordination**: "What Team meetings do I have?"
6. **Meeting Prep**: "What's the description for my next meeting?"
7. **Schedule Analysis**: "How much time am I spending in meetings this week?"

## Testing

You can test the server directly:
```bash
cd calendar-server
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
