# TickTick MCP Server | 滴答清单 MCP 服务器

[English](#english) | [中文](#中文)

---

`<a name="english"></a>`

## English

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for TickTick that enables interacting with your TickTick task management system directly through Claude and other MCP clients.

### ✨ Key Enhancements

This enhanced version builds upon the original [ticktick-mcp](https://github.com/jacepark12/ticktick-mcp) with significant improvements:

- 🚀 **Complete API Coverage** - Full support for TickTick's latest Open API with all available task parameters (reminders, repeat rules, subtasks, etc.)
- 📥 **Access** **Inbox** - ticktick-mcp can now access to tasks in inbox with special project ID `"inbox"`
- 🌍 **Timezone Fix** - Correctly handles task due dates across different timezones
- 📦 **Batch Operations** - All task and project operations (create, update, delete, complete) support both single and batch processing
- 🎯 **Simplified Tool Set**
- 🏗️ **Modular Architecture**

### Features

- 📋 View & Search all your TickTick projects and tasks
- ✏️ Create new projects, tasks, and subtasks through natural language
- 🔄 Update existing task details (title, content, dates, priority)
- 🗑️ Delete tasks and projects (single or batch)
- 🔌 Seamless integration with Claude Desktop and other LLM applications

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- TickTick account with API access
- TickTick API credentials (Client ID, Client Secret)

### Installation

1. **Clone this repository**:

   ```bash
   git clone https://github.com/Code-MonkeyZhang/ticktick-mcp-enhanced
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

### Authentication

#### TickTick

1. Register your application at the [TickTick Developer Center](https://developer.ticktick.com/manage)

   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. Run the authentication command:

   ```bash
   uv run -m ticktick_mcp.cli auth
   ```

3. Follow the prompts and authorize the application

The server handles token refresh automatically.

#### Dida365 (滴答清单)

For Dida365 users, add these environment variables to your `.env` file:

```env
TICKTICK_BASE_URL='https://api.dida365.com/open/v1'
TICKTICK_AUTH_URL='https://dida365.com/oauth/authorize'
TICKTICK_TOKEN_URL='https://dida365.com/oauth/token'
```

Then follow the same authentication steps.

### Use MCP in Claude Desktop and other LLM applicaitons

1. Install [Claude for Desktop](https://claude.ai/download)
2. Edit your Claude configuration file:

   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

3. Add the TickTick MCP server configuration:

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

### Available Tools

All 10 MCP tools in one place:

| Category     | Tool               | Description                                  | Key Parameters                                                                                                                                                                     |
| ------------ | ------------------ | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Projects** | `get_all_projects` | List all TickTick projects                   | None                                                                                                                                                                               |
|              | `get_project_info` | Get project details with all tasks           | `project_id` (use `"inbox"` for inbox)                                                                                                                                             |
|              | `create_project`   | Create a new project                         | `name`, `color`, `view_mode`                                                                                                                                                       |
|              | `delete_projects`  | Delete one or more projects                  | `projects` (ID or list of IDs)                                                                                                                                                     |
| **Tasks**    | `create_tasks`     | Create one or more tasks                     | `tasks` (dict or list of dicts)``Required: `title`, `project_id`Optional: `priority`, `due_date`, `content`, etc.                                                                  |
|              | `update_tasks`     | Update one or more tasks                     | `tasks` (dict or list of dicts)``Required: `task_id`, `project_id`Optional: `title`, `priority`, `due_date`, etc.                                                                  |
|              | `complete_tasks`   | Mark tasks as complete                       | `tasks` (dict or list of dicts)``Required: `project_id`, `task_id`                                                                                                                 |
|              | `delete_tasks`     | Delete one or more tasks                     | `tasks` (dict or list of dicts)``Required: `project_id`, `task_id`                                                                                                                 |
|              | `create_subtasks`  | Create one or more subtasks                  | `subtasks` (dict or list of dicts)``Required: `subtask_title`, `parent_task_id`, `project_id`                                                                                      |
| **Query**    | `query_tasks`      | Unified query with multi-dimensional filters | `task_id`, `project_id`, `priority` (`"high"`, `"medium"`, `"low"`, `"none"`), `date_filter` (`"today"`, `"tomorrow"`, `"overdue"`, `"next_7_days"`), `custom_days`, `search_term` |

### Example Usage

**Query Examples:**

```python
# All tasks
query_tasks()

# Inbox tasks
query_tasks(project_id="inbox")

# High priority tasks due today
query_tasks(priority="high", date_filter="today")

# Search for meetings
query_tasks(search_term="meeting")

# Specific task lookup
query_tasks(task_id="abc123", project_id="xyz789")
```

**Batch Operations:**

```python
# Create multiple tasks
create_tasks([
    {"title": "Task 1", "project_id": "inbox", "priority": "high"},
    {"title": "Task 2", "project_id": "work", "priority": "medium"}
])

# Update multiple tasks
update_tasks([
    {"task_id": "abc", "project_id": "123", "priority": "high"},
    {"task_id": "def", "project_id": "123", "title": "Updated"}
])

# Complete multiple tasks
complete_tasks([
    {"project_id": "inbox", "task_id": "abc"},
    {"project_id": "work", "task_id": "def"}
])
```

### Example Prompts

**General:**

- "Show me all my TickTick projects"
- "What's in my inbox?"
- "Create a task 'Buy groceries' with high priority"
- "Show me all high priority tasks due today"

**Batch Operations:**

- "Create these three tasks: 'Buy groceries', 'Call mom', and 'Finish report'"
- "Mark all overdue tasks as complete"
- "Delete all completed tasks from archive"

**Advanced Queries:**

- "Show me high priority tasks in my Work project"
- "Find all tasks with 'meeting' due this week"
- "What tasks are overdue in my inbox?"

### Project Structure

```
ticktick-mcp/
├── ticktick_mcp/
│   ├── src/
│   │   ├── server.py          # MCP server core (45 lines)
│   │   ├── config.py          # Configuration management
│   │   ├── ticktick_client.py # TickTick API client
│   │   ├── auth.py            # OAuth implementation
│   │   ├── tools/             # MCP tools (modular)
│   │   │   ├── project_tools.py
│   │   │   ├── task_tools.py
│   │   │   └── query_tools.py
│   │   └── utils/             # Utilities
│   │       ├── timezone.py
│   │       ├── formatters.py
│   │       └── validators.py
│   ├── cli.py                 # CLI interface
│   └── authenticate.py        # Auth utility
├── test/                      # Comprehensive tests
├── doc/
│   └── CUROR_MEMORY.md        # Development history
├── README.md
├── requirements.txt
└── setup.py
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### License

This project is licensed under the MIT License.

### Attribution

This project is inspired by and contains code derived from:

- [ticktick-mcp](https://github.com/jacepark12/ticktick-mcp) by Jaesung Park, licensed under MIT License
