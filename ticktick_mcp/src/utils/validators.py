"""
Validation and filtering utilities for TickTick MCP.

This module provides functions for validating task data, filtering tasks
by various criteria, and performing search operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from zoneinfo import ZoneInfo

from .timezone import normalize_iso_date, get_user_timezone_today, DEFAULT_TIMEZONE
from .formatters import format_task, format_project

# Set up logging
logger = logging.getLogger(__name__)

# Priority mapping constants
PRIORITY_MAP = {
    "none": 0,
    "low": 1,
    "medium": 3,
    "high": 5
}

# Reverse mapping for display purposes
PRIORITY_NAME_MAP = {
    0: "none",
    1: "low",
    3: "medium",
    5: "high"
}


def normalize_priority(priority: Union[str, int, None]) -> Optional[int]:
    """
    Convert priority from string to integer, with backward compatibility.
    
    Args:
        priority: Priority as string ("none", "low", "medium", "high") or int (0, 1, 3, 5)
    
    Returns:
        Integer priority value (0, 1, 3, 5) or None
    """
    if priority is None:
        return None
    
    if isinstance(priority, int):
        # Backward compatibility: accept integer directly
        if priority in [0, 1, 3, 5]:
            return priority
        return None
    
    if isinstance(priority, str):
        return PRIORITY_MAP.get(priority.lower())
    
    return None


def validate_priority(priority: Union[str, int, None], task_index: int) -> Optional[str]:
    """
    Validate priority value and return error message if invalid.
    
    Args:
        priority: Priority value to validate
        task_index: Task index for error messages
    
    Returns:
        Error message if invalid, None if valid
    """
    if priority is None:
        return None
    
    if isinstance(priority, int):
        if priority not in [0, 1, 3, 5]:
            return f"Task {task_index + 1}: Invalid priority {priority}. Must be 0, 1, 3, or 5"
        return None
    
    if isinstance(priority, str):
        if priority.lower() not in PRIORITY_MAP:
            valid_values = ", ".join([f'"{k}"' for k in PRIORITY_MAP.keys()])
            return f"Task {task_index + 1}: Invalid priority '{priority}'. Must be one of: {valid_values}"
        return None
    
    return f"Task {task_index + 1}: Priority must be a string or integer"


def is_task_due_today(task: Dict[str, Any]) -> bool:
    """Check if a task is due today."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    try:
        # 使用normalize_iso_date来处理各种日期格式
        normalized_date = normalize_iso_date(due_date)
        task_due_dt = datetime.fromisoformat(normalized_date)
        
        # 将任务截止时间转换为用户时区
        if DEFAULT_TIMEZONE and DEFAULT_TIMEZONE != "Local":
            try:
                user_tz = ZoneInfo(DEFAULT_TIMEZONE)
                task_due_local = task_due_dt.astimezone(user_tz)
            except Exception:
                # Fallback to local timezone
                task_due_local = task_due_dt.astimezone()
        else:
            task_due_local = task_due_dt.astimezone()
        
        task_due_date = task_due_local.date()
        today_date = get_user_timezone_today()
        return task_due_date == today_date
    except (ValueError, TypeError):
        return False


def is_task_overdue(task: Dict[str, Any]) -> bool:
    """Check if a task is overdue."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    try:
        # 使用normalize_iso_date来处理各种日期格式
        normalized_date = normalize_iso_date(due_date)
        task_due = datetime.fromisoformat(normalized_date)
        
        # 获取用户时区的当前时间进行比较
        if DEFAULT_TIMEZONE and DEFAULT_TIMEZONE != "Local":
            try:
                user_tz = ZoneInfo(DEFAULT_TIMEZONE)
                now_user_tz = datetime.now(user_tz)
                task_due_user_tz = task_due.astimezone(user_tz)
            except Exception:
                # Fallback to local timezone
                now_user_tz = datetime.now()
                task_due_user_tz = task_due.astimezone()
        else:
            now_user_tz = datetime.now()
            task_due_user_tz = task_due.astimezone()
        
        return task_due_user_tz < now_user_tz
    except (ValueError, TypeError):
        return False


def is_task_due_in_days(task: Dict[str, Any], days: int) -> bool:
    """Check if a task is due in exactly X days."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    try:
        # 使用normalize_iso_date来处理各种日期格式
        normalized_date = normalize_iso_date(due_date)
        task_due_dt = datetime.fromisoformat(normalized_date)
        
        # 将任务截止时间转换为用户时区
        if DEFAULT_TIMEZONE and DEFAULT_TIMEZONE != "Local":
            try:
                user_tz = ZoneInfo(DEFAULT_TIMEZONE)
                task_due_local = task_due_dt.astimezone(user_tz)
            except Exception:
                # Fallback to local timezone
                task_due_local = task_due_dt.astimezone()
        else:
            task_due_local = task_due_dt.astimezone()
        
        task_due_date = task_due_local.date()
        target_date = get_user_timezone_today() + timedelta(days=days)
        return task_due_date == target_date
    except (ValueError, TypeError):
        return False


def task_matches_search(task: Dict[str, Any], search_term: str) -> bool:
    """Check if a task matches the search term (case-insensitive)."""
    search_term = search_term.lower()
    
    # Search in title
    title = task.get('title', '').lower()
    if search_term in title:
        return True
    
    # Search in content
    content = task.get('content', '').lower()
    if search_term in content:
        return True
    
    # Search in subtasks
    items = task.get('items', [])
    for item in items:
        item_title = item.get('title', '').lower()
        if search_term in item_title:
            return True
    
    return False


def validate_task_data(task_data: Dict[str, Any], task_index: int) -> Optional[str]:
    """
    Validate a single task's data for batch creation.
    
    Returns:
        None if valid, error message string if invalid
    """
    # Check required fields
    if 'title' not in task_data or not task_data['title']:
        return f"Task {task_index + 1}: 'title' is required and cannot be empty"
    
    if 'project_id' not in task_data or not task_data['project_id']:
        return f"Task {task_index + 1}: 'project_id' is required and cannot be empty"
    
    # Validate priority if provided
    priority = task_data.get('priority')
    priority_error = validate_priority(priority, task_index)
    if priority_error:
        return priority_error
    
    # Validate dates if provided
    for date_field in ['start_date', 'due_date']:
        date_str = task_data.get(date_field)
        if date_str:
            try:
                # Try to parse the date to validate it
                normalized_date = normalize_iso_date(date_str)
                datetime.fromisoformat(normalized_date)
            except ValueError:
                return f"Task {task_index + 1}: Invalid {date_field} format '{date_str}'. Use ISO format: YYYY-MM-DDTHH:mm:ss or with timezone"
    
    # Validate is_all_day if provided
    is_all_day = task_data.get('is_all_day')
    if is_all_day is not None and not isinstance(is_all_day, bool):
        return f"Task {task_index + 1}: 'is_all_day' must be a boolean (true/false)"
    
    # Validate reminders if provided
    reminders = task_data.get('reminders')
    if reminders is not None and not isinstance(reminders, list):
        return f"Task {task_index + 1}: 'reminders' must be a list"
    
    # Validate items (subtasks) if provided
    items = task_data.get('items')
    if items is not None and not isinstance(items, list):
        return f"Task {task_index + 1}: 'items' must be a list"
    
    # Validate sort_order if provided
    sort_order = task_data.get('sort_order')
    if sort_order is not None and not isinstance(sort_order, int):
        return f"Task {task_index + 1}: 'sort_order' must be an integer"
    
    return None


def get_project_tasks_by_filter(projects: List[Dict], filter_func: Callable, filter_name: str, ticktick_client) -> str:
    """
    Helper function to filter tasks across all projects AND Inbox.
    
    Args:
        projects: List of project dictionaries
        filter_func: Function that takes a task and returns True if it matches the filter
        filter_name: Name of the filter for output formatting
        ticktick_client: TickTick client instance for API calls
    
    Returns:
        Formatted string of filtered tasks
    """
    if not projects:
        return "No projects found."
    
    result = f"Found {len(projects)} projects + Inbox:\n\n"
    
    # Regular projects
    for i, project in enumerate(projects, 1):
        if project.get('closed'):
            continue
            
        project_id = project.get('id', 'No ID')
        project_data = ticktick_client.get_project_with_data(project_id)
        tasks = project_data.get('tasks', [])
        
        if not tasks:
            result += f"Project {i}:\n{format_project(project)}"
            result += f"With 0 tasks that are to be '{filter_name}' in this project :\n\n\n"
            continue
        
        # Filter tasks using the provided function
        filtered_tasks = [(t, task) for t, task in enumerate(tasks, 1) if filter_func(task)]
        
        result += f"Project {i}:\n{format_project(project)}"
        result += f"With {len(filtered_tasks)} tasks that are to be '{filter_name}' in this project :\n"
        
        for t, task in filtered_tasks:
            result += f"Task {t}:\n{format_task(task)}\n"
        
        result += "\n\n"
    
    # Inbox
    try:
        inbox_data = ticktick_client.get_project_with_data("inbox")
        if 'error' not in inbox_data:
            inbox_project = inbox_data.get('project', {}) or {'name': 'Inbox'}
            inbox_tasks = inbox_data.get('tasks', []) or []
            
            filtered_inbox_tasks = [(t, task) for t, task in enumerate(inbox_tasks, 1) if filter_func(task)]
            
            result += "Inbox:\n"
            result += f"Name: {inbox_project.get('name', 'Inbox')}\n"
            result += "ID: inbox\n"
            result += f"With {len(filtered_inbox_tasks)} tasks that are to be '{filter_name}' in this project :\n"
            
            for t, task in filtered_inbox_tasks:
                result += f"Task {t}:\n{format_task(task)}\n"
            
            result += "\n"
        else:
            result += f"Inbox: Error fetching inbox: {inbox_data['error']}\n"
    except Exception as e:
        logger.warning(f"Could not fetch inbox tasks: {e}")
        result += f"Inbox: Could not fetch (error: {str(e)})\n"
    
    return result
