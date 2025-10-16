# TickTick MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for TickTick that enables interacting with your TickTick task management system directly through Claude and other MCP clients.

## Features

- 📋 View all your TickTick projects and tasks
- ✏️ Create new projects and tasks through natural language
- 🔄 Update existing task details (title, content, dates, priority)
- ✅ Mark tasks as complete
- 🗑️ Delete tasks and projects
- 🔄 Full integration with TickTick's open API
- 🔌 Seamless integration with Claude and other MCP clients

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- TickTick account with API access
- TickTick API credentials (Client ID, Client Secret, Access Token)

## Installation

1. **Clone this repository**:

   ```bash
   git clone https://github.com/jacepark12/ticktick-mcp.git
   cd ticktick-mcp
   ```

2. **Install with uv**:

   ```bash
   # Install uv if you don't have it already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create a virtual environment
   uv venv

   # Activate the virtual environment
   # On macOS/Linux:
   source .venv/bin/activate
   # On Windows:
   .venv\Scripts\activate

   # Install the package
   uv pip install -e .
   ```

3. **Authenticate with TickTick**:

   ```bash
   # Run the authentication flow
   uv run -m ticktick_mcp.cli auth
   ```

   This will:

   - Ask for your TickTick Client ID and Client Secret
   - Open a browser window for you to log in to TickTick
   - Automatically save your access tokens to a `.env` file

4. **Test your configuration**:
   ```bash
   uv run test_server.py
   ```
   This will verify that your TickTick credentials are working correctly.

## Authentication with TickTick

This server uses OAuth2 to authenticate with TickTick. The setup process is straightforward:

1. Register your application at the [TickTick Developer Center](https://developer.ticktick.com/manage)

   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. Run the authentication command:

   ```bash
   uv run -m ticktick_mcp.cli auth
   ```

3. Follow the prompts to enter your Client ID and Client Secret

4. A browser window will open for you to authorize the application with your TickTick account

5. After authorizing, you'll be redirected back to the application, and your access tokens will be automatically saved to the `.env` file

The server handles token refresh automatically, so you won't need to reauthenticate unless you revoke access or delete your `.env` file.

## Authentication with Dida365

[滴答清单 - Dida365](https://dida365.com/home) is China version of TickTick, and the authentication process is similar to TickTick. Follow these steps to set up Dida365 authentication:

1. Register your application at the [Dida365 Developer Center](https://developer.dida365.com/manage)

   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. Add environment variables to your `.env` file:

   ```env
   TICKTICK_BASE_URL='https://api.dida365.com/open/v1'
   TICKTICK_AUTH_URL='https://dida365.com/oauth/authorize'
   TICKTICK_TOKEN_URL='https://dida365.com/oauth/token'
   ```

3. Follow the same authentication steps as for TickTick

## Usage with Claude for Desktop

1. Install [Claude for Desktop](https://claude.ai/download)
2. Edit your Claude for Desktop configuration file:

   **macOS**:

   ```bash
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   **Windows**:

   ```bash
   notepad %APPDATA%\Claude\claude_desktop_config.json
   ```

3. Add the TickTick MCP server configuration, using absolute paths:

   ```json
   {
     "mcpServers": {
       "ticktick": {
         "command": "<absolute path to uv>",
         "args": [
           "run",
           "--directory",
           "<absolute path to ticktick-mcp directory>",
           "-m",
           "ticktick_mcp.cli",
           "run"
         ]
       }
     }
   }
   ```

4. Restart Claude for Desktop

Once connected, you'll see the TickTick MCP server tools available in Claude, indicated by the 🔨 (tools) icon.

## Available MCP Tools

### Project Management Tools

| Tool               | Description                                               | Parameters                                         |
| ------------------ | --------------------------------------------------------- | -------------------------------------------------- |
| `get_all_projects` | List all your TickTick projects                           | None                                               |
| `get_project_info` | Get comprehensive project information including all tasks | `project_id` (use "inbox" for inbox)               |
| `create_project`   | Create a new project                                      | `name`, `color` (optional), `view_mode` (optional) |
| `delete_projects`  | Delete one or more projects                               | `projects` (project ID string or list)             |

> **Note**: `get_project_info` provides a complete view with both project details and all tasks in one call. For filtered task queries, use `query_tasks(project_id="...")` instead.

### Task Management Tools (Batch Operations)

All task operations support both **single task** and **batch processing**. You can pass either a single dictionary or a list of dictionaries.

| Tool              | Description                        | Single Task Example                                                        | Batch Example                                                           |
| ----------------- | ---------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `create_tasks`    | Create one or more tasks           | `{"title": "Buy milk", "project_id": "123"}`                               | `[{"title": "Task 1", "project_id": "123"}, {"title": "Task 2", ...}]`  |
| `update_tasks`    | Update one or more tasks           | `{"task_id": "abc", "project_id": "123", "priority": 5}`                   | `[{"task_id": "abc", "project_id": "123", "priority": 5}, ...]`         |
| `complete_tasks`  | Mark one or more tasks as complete | `{"project_id": "123", "task_id": "abc"}`                                  | `[{"project_id": "123", "task_id": "abc"}, {"project_id": "123", ...}]` |
| `delete_tasks`    | Delete one or more tasks           | `{"project_id": "123", "task_id": "abc"}`                                  | `[{"project_id": "123", "task_id": "abc"}, ...]`                        |
| `create_subtasks` | Create one or more subtasks        | `{"subtask_title": "Sub 1", "parent_task_id": "abc", "project_id": "123"}` | `[{"subtask_title": "Sub 1", "parent_task_id": "abc", ...}, ...]`       |

## Task-specific MCP Tools

### Unified Query Tool

| Tool          | Description                                       | Parameters                                                                                                                                                                                                                                                                           |
| ------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `query_tasks` | Unified task query with multi-dimensional filters | `task_id` (optional), `date_filter` (optional), `custom_days` (optional), `priority` (optional), `search_term` (optional), `project_id` (optional), `include_all_projects` (default: True)                                                                                           |
|               | **Supports flexible filtering and combinations:** | - Direct lookup: Use `task_id` + `project_id` for efficient single task retrieval<br>- Date filters: "today", "tomorrow", "overdue", "next_7_days", "custom"<br>- Priority: 0 (None), 1 (Low), 3 (Medium), 5 (High)<br>- Search by keyword<br>- Limit to specific project or "inbox" |

**Examples:**

```python
query_tasks()                                         # All tasks
query_tasks(task_id="abc123", project_id="xyz789")    # Get specific task (direct lookup)
query_tasks(task_id="abc123")                         # Find task by ID across all projects
query_tasks(project_id="inbox")                       # All inbox tasks
query_tasks(project_id="xyz789")                      # All tasks in a project
query_tasks(date_filter="today")                      # Tasks due today
query_tasks(priority=5)                               # High priority tasks
query_tasks(date_filter="today", priority=5)          # High priority tasks due today
query_tasks(search_term="meeting")                    # Tasks with "meeting"
query_tasks(project_id="inbox", priority=5)           # High priority inbox tasks
query_tasks(date_filter="overdue", priority=5)        # High priority overdue tasks
```

## Example Prompts for Claude

Here are some example prompts to use with Claude after connecting the TickTick MCP server:

### General

- "Show me all my TickTick projects"
- "Show me everything about my Work project" (uses `get_project_info`)
- "What's in my inbox?" (uses `get_project_info` with inbox)
- "Create a new task called 'Finish MCP server documentation' in my work project with high priority"
- "Mark the task 'Buy groceries' as complete"
- "Create a new project called 'Vacation Planning' with a blue color"
- "When is my next deadline in TickTick?"

### Batch Operations

All task operations now support batch processing:

- "Create these three tasks: 'Buy groceries', 'Call mom', and 'Finish report' in my inbox"
- "Mark these five tasks as complete: [list of task IDs]"
- "Delete all tasks with 'old' in the title from my archive project"
- "Update the priority of all tasks due today to high priority"
- "Create 10 subtasks for this project plan"

### Task Filtering Queries

With the unified `query_tasks` tool, you can combine multiple filters:

- "What tasks do I have due today?"
- "Show me everything that's overdue"
- "Show me all tasks due this week"
- "Show me high priority tasks due today"
- "Find tasks with 'meeting' that are due tomorrow"
- "Show me all high priority tasks"
- "What tasks in my inbox are due this week?"
- "Search for 'project alpha' in high priority tasks"

## Testing

The project includes comprehensive tests to verify functionality:

```bash
# Run comprehensive test for all 10 tools (recommended)
python test/test_all_tools.py

# Run batch operations tests (for all batch task tools)
python test/test_batch_operations.py

# Run API functionality tests
python test/test_api_functions.py

# Run query tools tests (for the unified date query tool)
python test/test_query_tools.py

# Run refactoring validation tests
python test/test_refactor_validation.py
```

### Test Coverage

The `test_all_tools.py` script provides comprehensive testing for all current tools:

**Project Management Tools (4 tools)**:

- ✅ `get_all_projects` - List all projects
- ✅ `get_project_info` - Get project info with tasks
- ✅ `create_project` - Create new project
- ✅ `delete_projects` - Delete single/batch projects

**Task Management Tools (5 tools)**:

- ✅ `create_tasks` - Create single/batch tasks
- ✅ `update_tasks` - Update single/batch tasks
- ✅ `complete_tasks` - Complete single/batch tasks
- ✅ `delete_tasks` - Delete single/batch tasks
- ✅ `create_subtasks` - Create single/batch subtasks

**Query Tools (1 tool)**:

- ✅ `query_tasks` - Unified query with filters

## Development

### Project Structure

```
ticktick-mcp/
├── .env.template          # Template for environment variables
├── README.md              # Project documentation
├── requirements.txt       # Project dependencies
├── setup.py               # Package setup file
├── test_server.py         # Test script for server configuration
└── ticktick_mcp/          # Main package
    ├── __init__.py        # Package initialization
    ├── authenticate.py    # OAuth authentication utility
    ├── cli.py             # Command-line interface
    └── src/               # Source code
        ├── __init__.py    # Module initialization
        ├── auth.py        # OAuth authentication implementation
        ├── server.py      # MCP server implementation
        └── ticktick_client.py  # TickTick API client
```

### Authentication Flow

The project implements a complete OAuth 2.0 flow for TickTick:

1. **Initial Setup**: User provides their TickTick API Client ID and Secret
2. **Browser Authorization**: User is redirected to TickTick to grant access
3. **Token Reception**: A local server receives the OAuth callback with the authorization code
4. **Token Exchange**: The code is exchanged for access and refresh tokens
5. **Token Storage**: Tokens are securely stored in the local `.env` file
6. **Token Refresh**: The client automatically refreshes the access token when it expires

This simplifies the user experience by handling the entire OAuth flow programmatically.

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
