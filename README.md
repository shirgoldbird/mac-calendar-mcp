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
