"""
Task CRUD tools for TickTick MCP.

This module contains MCP tools for batch task operations.
All task operations support batch processing for improved efficiency.
"""

import logging
from typing import List, Dict, Any, Union
from datetime import datetime
from mcp.server.fastmcp import FastMCP

from ..config import ensure_client
from ..utils.formatters import format_task
from ..utils.timezone import normalize_iso_date
from ..utils.validators import validate_task_data, normalize_priority

# Set up logging
logger = logging.getLogger(__name__)


def register_task_tools(mcp: FastMCP):
    """Register all task-related MCP tools (batch operations only)."""
    
    @mcp.tool()
    async def create_tasks(tasks: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """
        Create one or more tasks in TickTick.
        
        Supports both single task and batch creation. For single task, you can pass
        a dictionary directly. For multiple tasks, pass a list of dictionaries.
        
        Args:
            tasks: Task dictionary or list of task dictionaries. Each task must contain:
                - title (required): Task Name
                - project_id (required): ID of the project for the task
                - content (optional): Task description
                - desc (optional): Description of checklist
                - start_date (optional): Start date in ISO format (YYYY-MM-DDTHH:mm:ss+0000)
                - due_date (optional): Due date in ISO format (YYYY-MM-DDTHH:mm:ss+0000)
                - priority (optional): Priority level - "none", "low", "medium", or "high" (case-insensitive)
                - is_all_day (optional): Whether this is an all-day task (boolean)
                - time_zone (optional): Time zone (e.g., "America/Los_Angeles")
                - reminders (optional): List of reminder triggers (e.g., ["TRIGGER:P0DT9H0M0S"])
                - repeat_flag (optional): Recurring rules (e.g., "RRULE:FREQ=DAILY;INTERVAL=1")
                - sort_order (optional): Sort order value (integer)
                - items (optional): List of subtask dictionaries
        
        Examples:
            # Single task
            {"title": "Buy milk", "project_id": "1234ABC", "priority": "medium"}
            
            # Multiple tasks
            [
                {"title": "Example A", "project_id": "1234ABC", "priority": "high", "is_all_day": True},
                {"title": "Example B", "project_id": "1234XYZ", "content": "Description", "due_date": "2025-07-19T10:00:00+0000"}
            ]
        """
        # Normalize input - convert single dict to list
        if isinstance(tasks, dict):
            task_list = [tasks]
            single_task = True
        elif isinstance(tasks, list):
            task_list = tasks
            single_task = False
        else:
            return "Invalid input. Tasks must be a dictionary or list of dictionaries."
        
        if not task_list:
            return "No tasks provided. Please provide at least one task to create."
        
        # Validate all tasks before creating any
        validation_errors = []
        for i, task_data in enumerate(task_list):
            if not isinstance(task_data, dict):
                validation_errors.append(f"Task {i + 1}: Must be a dictionary")
                continue
            
            error = validate_task_data(task_data, i)
            if error:
                validation_errors.append(error)
        
        if validation_errors:
            return "Validation errors found:\n" + "\n".join(validation_errors)
        
        # Create tasks one by one and collect results
        created_tasks = []
        failed_tasks = []
        
        try:
            ticktick = ensure_client()
            for i, task_data in enumerate(task_list):
                try:
                    # Extract task parameters with defaults
                    title = task_data['title']
                    project_id = task_data['project_id']
                    content = task_data.get('content')
                    desc = task_data.get('desc')
                    start_date = task_data.get('start_date')
                    due_date = task_data.get('due_date')
                    # Normalize priority from string to int
                    priority_raw = task_data.get('priority', 0)
                    priority = normalize_priority(priority_raw) if priority_raw else 0
                    is_all_day = task_data.get('is_all_day', False)
                    time_zone = task_data.get('time_zone')
                    reminders = task_data.get('reminders')
                    repeat_flag = task_data.get('repeat_flag')
                    sort_order = task_data.get('sort_order')
                    items = task_data.get('items')
                    
                    # Create the task
                    result = ticktick.create_task(
                        title=title,
                        project_id=project_id,
                        content=content,
                        desc=desc,
                        start_date=start_date,
                        due_date=due_date,
                        priority=priority,
                        is_all_day=is_all_day,
                        time_zone=time_zone,
                        reminders=reminders,
                        repeat_flag=repeat_flag,
                        sort_order=sort_order,
                        items=items
                    )
                    
                    if 'error' in result:
                        failed_tasks.append(f"Task {i + 1} ('{title}'): {result['error']}")
                    else:
                        created_tasks.append((i + 1, title, result))
                        
                except Exception as e:
                    failed_tasks.append(f"Task {i + 1} ('{task_data.get('title', 'Unknown')}'): {str(e)}")
            
            # Format the results
            if single_task:
                if created_tasks:
                    return f"Task created successfully:\n\n" + format_task(created_tasks[0][2])
                else:
                    return f"Failed to create task:\n{failed_tasks[0]}"
            else:
                result_message = f"Batch task creation completed.\n\n"
                result_message += f"Successfully created: {len(created_tasks)} tasks\n"
                result_message += f"Failed: {len(failed_tasks)} tasks\n\n"
                
                if created_tasks:
                    result_message += "✅ Successfully Created Tasks:\n"
                    for task_num, title, task_obj in created_tasks:
                        result_message += f"{task_num}. {title} (ID: {task_obj.get('id', 'Unknown')})\n"
                    result_message += "\n"
                
                if failed_tasks:
                    result_message += "❌ Failed Tasks:\n"
                    for error in failed_tasks:
                        result_message += f"{error}\n"
                
                return result_message
            
        except Exception as e:
            logger.error(f"Error in create_tasks: {e}")
            return f"Error during task creation: {str(e)}"

    @mcp.tool()
    async def update_tasks(tasks: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """
        Update one or more existing tasks in TickTick.
        
        Supports both single task and batch updates. For single task, you can pass
        a dictionary directly. For multiple tasks, pass a list of dictionaries.
        
        Args:
            tasks: Task dictionary or list of task dictionaries. Each task must contain:
                - task_id (required): ID of the task to update
                - project_id (required): ID of the project the task belongs to
                - title (optional): New task title
                - content (optional): New task description/content
                - desc (optional): New description of checklist
                - start_date (optional): New start date in ISO format (YYYY-MM-DDTHH:mm:ss+0000)
                - due_date (optional): New due date in ISO format (YYYY-MM-DDTHH:mm:ss+0000)
                - priority (optional): New priority level - "none", "low", "medium", or "high" (case-insensitive)
                - is_all_day (optional): Whether this is an all-day task
                - time_zone (optional): Time zone (e.g., "America/Los_Angeles")
                - reminders (optional): List of reminder triggers
                - repeat_flag (optional): Recurring rules
                - sort_order (optional): Sort order value
                - items (optional): List of subtask dictionaries
        
        Examples:
            # Single task
            {"task_id": "abc123", "project_id": "xyz789", "priority": "high"}
            
            # Multiple tasks
            [
                {"task_id": "abc123", "project_id": "xyz789", "priority": "high"},
                {"task_id": "def456", "project_id": "xyz789", "title": "New Title", "due_date": "2025-12-31T23:59:59+0000"}
            ]
        """
        # Normalize input - convert single dict to list
        if isinstance(tasks, dict):
            task_list = [tasks]
            single_task = True
        elif isinstance(tasks, list):
            task_list = tasks
            single_task = False
        else:
            return "Invalid input. Tasks must be a dictionary or list of dictionaries."
        
        if not task_list:
            return "No tasks provided. Please provide at least one task to update."
        
        # Validate all tasks have required fields
        validation_errors = []
        for i, task_data in enumerate(task_list):
            if not isinstance(task_data, dict):
                validation_errors.append(f"Task {i + 1}: Must be a dictionary")
                continue
            
            if 'task_id' not in task_data:
                validation_errors.append(f"Task {i + 1}: Missing required field 'task_id'")
            if 'project_id' not in task_data:
                validation_errors.append(f"Task {i + 1}: Missing required field 'project_id'")
            
            # Validate priority if provided
            from ..utils.validators import validate_priority
            priority = task_data.get('priority')
            if priority is not None:
                priority_error = validate_priority(priority, i)
                if priority_error:
                    validation_errors.append(priority_error)
            
            # Validate dates if provided
            for date_field in ['start_date', 'due_date']:
                date_str = task_data.get(date_field)
                if date_str:
                    try:
                        normalized_date = normalize_iso_date(date_str)
                        datetime.fromisoformat(normalized_date)
                    except ValueError:
                        validation_errors.append(f"Task {i + 1}: Invalid {date_field} format")
        
        if validation_errors:
            return "Validation errors found:\n" + "\n".join(validation_errors)
        
        # Update tasks one by one and collect results
        updated_tasks = []
        failed_tasks = []
        
        try:
            ticktick = ensure_client()
            for i, task_data in enumerate(task_list):
                try:
                    task_id = task_data['task_id']
                    project_id = task_data['project_id']
                    
                    # Normalize priority if provided
                    priority_raw = task_data.get('priority')
                    priority = normalize_priority(priority_raw) if priority_raw is not None else None
                    
                    # Update the task
                    result = ticktick.update_task(
                        task_id=task_id,
                        project_id=project_id,
                        title=task_data.get('title'),
                        content=task_data.get('content'),
                        desc=task_data.get('desc'),
                        start_date=task_data.get('start_date'),
                        due_date=task_data.get('due_date'),
                        priority=priority,
                        is_all_day=task_data.get('is_all_day'),
                        time_zone=task_data.get('time_zone'),
                        reminders=task_data.get('reminders'),
                        repeat_flag=task_data.get('repeat_flag'),
                        sort_order=task_data.get('sort_order'),
                        items=task_data.get('items')
                    )
                    
                    if 'error' in result:
                        failed_tasks.append(f"Task {i + 1} (ID: {task_id}): {result['error']}")
                    else:
                        updated_tasks.append((i + 1, task_id, result))
                        
                except Exception as e:
                    task_id = task_data.get('task_id', 'Unknown')
                    failed_tasks.append(f"Task {i + 1} (ID: {task_id}): {str(e)}")
            
            # Format the results
            if single_task:
                if updated_tasks:
                    return f"Task updated successfully:\n\n" + format_task(updated_tasks[0][2])
                else:
                    return f"Failed to update task:\n{failed_tasks[0]}"
            else:
                result_message = f"Batch task update completed.\n\n"
                result_message += f"Successfully updated: {len(updated_tasks)} tasks\n"
                result_message += f"Failed: {len(failed_tasks)} tasks\n\n"
                
                if updated_tasks:
                    result_message += "✅ Successfully Updated Tasks:\n"
                    for task_num, task_id, task_obj in updated_tasks:
                        result_message += f"{task_num}. {task_obj.get('title', 'Unknown')} (ID: {task_id})\n"
                    result_message += "\n"
                
                if failed_tasks:
                    result_message += "❌ Failed Tasks:\n"
                    for error in failed_tasks:
                        result_message += f"{error}\n"
                
                return result_message
            
        except Exception as e:
            logger.error(f"Error in update_tasks: {e}")
            return f"Error during task update: {str(e)}"

    @mcp.tool()
    async def complete_tasks(tasks: Union[Dict[str, str], List[Dict[str, str]]]) -> str:
        """
        Mark one or more tasks as complete.
        
        Supports both single task and batch completion. For single task, you can pass
        a dictionary directly. For multiple tasks, pass a list of dictionaries.
        
        Args:
            tasks: Task dictionary or list of task dictionaries. Each task must contain:
                - project_id (required): ID of the project
                - task_id (required): ID of the task
        
        Examples:
            # Single task
            {"project_id": "xyz789", "task_id": "abc123"}
            
            # Multiple tasks
            [
                {"project_id": "xyz789", "task_id": "abc123"},
                {"project_id": "xyz789", "task_id": "def456"},
                {"project_id": "abc123", "task_id": "ghi789"}
            ]
        """
        # Normalize input - convert single dict to list
        if isinstance(tasks, dict):
            task_list = [tasks]
            single_task = True
        elif isinstance(tasks, list):
            task_list = tasks
            single_task = False
        else:
            return "Invalid input. Tasks must be a dictionary or list of dictionaries."
        
        if not task_list:
            return "No tasks provided. Please provide at least one task to complete."
        
        # Validate all tasks have required fields
        validation_errors = []
        for i, task_data in enumerate(task_list):
            if not isinstance(task_data, dict):
                validation_errors.append(f"Task {i + 1}: Must be a dictionary")
                continue
            
            if 'task_id' not in task_data:
                validation_errors.append(f"Task {i + 1}: Missing required field 'task_id'")
            if 'project_id' not in task_data:
                validation_errors.append(f"Task {i + 1}: Missing required field 'project_id'")
        
        if validation_errors:
            return "Validation errors found:\n" + "\n".join(validation_errors)
        
        # Complete tasks one by one and collect results
        completed_tasks = []
        failed_tasks = []
        
        try:
            ticktick = ensure_client()
            for i, task_data in enumerate(task_list):
                try:
                    project_id = task_data['project_id']
                    task_id = task_data['task_id']
                    
                    result = ticktick.complete_task(project_id, task_id)
                    
                    if 'error' in result:
                        failed_tasks.append(f"Task {i + 1} (ID: {task_id}): {result['error']}")
                    else:
                        completed_tasks.append((i + 1, task_id))
                        
                except Exception as e:
                    task_id = task_data.get('task_id', 'Unknown')
                    failed_tasks.append(f"Task {i + 1} (ID: {task_id}): {str(e)}")
            
            # Format the results
            if single_task:
                if completed_tasks:
                    return f"Task {completed_tasks[0][1]} marked as complete."
                else:
                    return f"Failed to complete task:\n{failed_tasks[0]}"
            else:
                result_message = f"Batch task completion completed.\n\n"
                result_message += f"Successfully completed: {len(completed_tasks)} tasks\n"
                result_message += f"Failed: {len(failed_tasks)} tasks\n\n"
                
                if completed_tasks:
                    result_message += "✅ Successfully Completed Tasks:\n"
                    for task_num, task_id in completed_tasks:
                        result_message += f"{task_num}. Task ID: {task_id}\n"
                    result_message += "\n"
                
                if failed_tasks:
                    result_message += "❌ Failed Tasks:\n"
                    for error in failed_tasks:
                        result_message += f"{error}\n"
                
                return result_message
            
        except Exception as e:
            logger.error(f"Error in complete_tasks: {e}")
            return f"Error during task completion: {str(e)}"

    @mcp.tool()
    async def delete_tasks(tasks: Union[Dict[str, str], List[Dict[str, str]]]) -> str:
        """
        Delete one or more tasks.
        
        Supports both single task and batch deletion. For single task, you can pass
        a dictionary directly. For multiple tasks, pass a list of dictionaries.
        
        Args:
            tasks: Task dictionary or list of task dictionaries. Each task must contain:
                - project_id (required): ID of the project
                - task_id (required): ID of the task
        
        Examples:
            # Single task
            {"project_id": "xyz789", "task_id": "abc123"}
            
            # Multiple tasks
            [
                {"project_id": "xyz789", "task_id": "abc123"},
                {"project_id": "xyz789", "task_id": "def456"},
                {"project_id": "abc123", "task_id": "ghi789"}
            ]
        """
        # Normalize input - convert single dict to list
        if isinstance(tasks, dict):
            task_list = [tasks]
            single_task = True
        elif isinstance(tasks, list):
            task_list = tasks
            single_task = False
        else:
            return "Invalid input. Tasks must be a dictionary or list of dictionaries."
        
        if not task_list:
            return "No tasks provided. Please provide at least one task to delete."
        
        # Validate all tasks have required fields
        validation_errors = []
        for i, task_data in enumerate(task_list):
            if not isinstance(task_data, dict):
                validation_errors.append(f"Task {i + 1}: Must be a dictionary")
                continue
            
            if 'task_id' not in task_data:
                validation_errors.append(f"Task {i + 1}: Missing required field 'task_id'")
            if 'project_id' not in task_data:
                validation_errors.append(f"Task {i + 1}: Missing required field 'project_id'")
        
        if validation_errors:
            return "Validation errors found:\n" + "\n".join(validation_errors)
        
        # Delete tasks one by one and collect results
        deleted_tasks = []
        failed_tasks = []
        
        try:
            ticktick = ensure_client()
            for i, task_data in enumerate(task_list):
                try:
                    project_id = task_data['project_id']
                    task_id = task_data['task_id']
                    
                    result = ticktick.delete_task(project_id, task_id)
                    
                    if 'error' in result:
                        failed_tasks.append(f"Task {i + 1} (ID: {task_id}): {result['error']}")
                    else:
                        deleted_tasks.append((i + 1, task_id))
                        
                except Exception as e:
                    task_id = task_data.get('task_id', 'Unknown')
                    failed_tasks.append(f"Task {i + 1} (ID: {task_id}): {str(e)}")
            
            # Format the results
            if single_task:
                if deleted_tasks:
                    return f"Task {deleted_tasks[0][1]} deleted successfully."
                else:
                    return f"Failed to delete task:\n{failed_tasks[0]}"
            else:
                result_message = f"Batch task deletion completed.\n\n"
                result_message += f"Successfully deleted: {len(deleted_tasks)} tasks\n"
                result_message += f"Failed: {len(failed_tasks)} tasks\n\n"
                
                if deleted_tasks:
                    result_message += "✅ Successfully Deleted Tasks:\n"
                    for task_num, task_id in deleted_tasks:
                        result_message += f"{task_num}. Task ID: {task_id}\n"
                    result_message += "\n"
                
                if failed_tasks:
                    result_message += "❌ Failed Tasks:\n"
                    for error in failed_tasks:
                        result_message += f"{error}\n"
                
                return result_message
            
        except Exception as e:
            logger.error(f"Error in delete_tasks: {e}")
            return f"Error during task deletion: {str(e)}"

    @mcp.tool()
    async def create_subtasks(subtasks: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """
        Create one or more subtasks for parent tasks. For single subtask, you can pass
        a dictionary directly. For multiple subtasks, pass a list of dictionaries.
        
        Args:
            subtasks: Subtask dictionary or list of subtask dictionaries. Each subtask must contain:
                - subtask_title (required): Title of the subtask
                - parent_task_id (required): ID of the parent task
                - project_id (required): ID of the project (must be same for both parent and subtask)
                - content (optional): Content/description for the subtask
                - priority (optional): Priority level - "none", "low", "medium", or "high" (case-insensitive)
        
        Examples:
            # Single subtask
            {"subtask_title": "Subtask 1", "parent_task_id": "abc123", "project_id": "xyz789"}
            
            # Multiple subtasks
            [
                {"subtask_title": "Subtask 1", "parent_task_id": "abc123", "project_id": "xyz789", "priority": "medium"},
                {"subtask_title": "Subtask 2", "parent_task_id": "abc123", "project_id": "xyz789", "content": "Details"}
            ]
        """
        # Normalize input - convert single dict to list
        if isinstance(subtasks, dict):
            subtask_list = [subtasks]
            single_subtask = True
        elif isinstance(subtasks, list):
            subtask_list = subtasks
            single_subtask = False
        else:
            return "Invalid input. Subtasks must be a dictionary or list of dictionaries."
        
        if not subtask_list:
            return "No subtasks provided. Please provide at least one subtask to create."
        
        # Validate all subtasks have required fields
        validation_errors = []
        for i, subtask_data in enumerate(subtask_list):
            if not isinstance(subtask_data, dict):
                validation_errors.append(f"Subtask {i + 1}: Must be a dictionary")
                continue
            
            if 'subtask_title' not in subtask_data:
                validation_errors.append(f"Subtask {i + 1}: Missing required field 'subtask_title'")
            if 'parent_task_id' not in subtask_data:
                validation_errors.append(f"Subtask {i + 1}: Missing required field 'parent_task_id'")
            if 'project_id' not in subtask_data:
                validation_errors.append(f"Subtask {i + 1}: Missing required field 'project_id'")
            
            # Validate priority if provided
            priority = subtask_data.get('priority')
            if priority is not None:
                from ..utils.validators import validate_priority
                priority_error = validate_priority(priority, i)
                if priority_error:
                    # Change "Task" to "Subtask" in the error message
                    validation_errors.append(priority_error.replace("Task", "Subtask"))
        
        if validation_errors:
            return "Validation errors found:\n" + "\n".join(validation_errors)
        
        # Create subtasks one by one and collect results
        created_subtasks = []
        failed_subtasks = []
        
        try:
            ticktick = ensure_client()
            for i, subtask_data in enumerate(subtask_list):
                try:
                    subtask_title = subtask_data['subtask_title']
                    parent_task_id = subtask_data['parent_task_id']
                    project_id = subtask_data['project_id']
                    content = subtask_data.get('content')
                    # Normalize priority from string to int
                    priority_raw = subtask_data.get('priority', 0)
                    priority = normalize_priority(priority_raw) if priority_raw else 0
                    
                    result = ticktick.create_subtask(
                        subtask_title=subtask_title,
                        parent_task_id=parent_task_id,
                        project_id=project_id,
                        content=content,
                        priority=priority
                    )
                    
                    if 'error' in result:
                        failed_subtasks.append(f"Subtask {i + 1} ('{subtask_title}'): {result['error']}")
                    else:
                        created_subtasks.append((i + 1, subtask_title, result))
                        
                except Exception as e:
                    subtask_title = subtask_data.get('subtask_title', 'Unknown')
                    failed_subtasks.append(f"Subtask {i + 1} ('{subtask_title}'): {str(e)}")
            
            # Format the results
            if single_subtask:
                if created_subtasks:
                    return f"Subtask created successfully:\n\n" + format_task(created_subtasks[0][2])
                else:
                    return f"Failed to create subtask:\n{failed_subtasks[0]}"
            else:
                result_message = f"Batch subtask creation completed.\n\n"
                result_message += f"Successfully created: {len(created_subtasks)} subtasks\n"
                result_message += f"Failed: {len(failed_subtasks)} subtasks\n\n"
                
                if created_subtasks:
                    result_message += "✅ Successfully Created Subtasks:\n"
                    for subtask_num, subtask_title, subtask_obj in created_subtasks:
                        result_message += f"{subtask_num}. {subtask_title} (ID: {subtask_obj.get('id', 'Unknown')})\n"
                    result_message += "\n"
                
                if failed_subtasks:
                    result_message += "❌ Failed Subtasks:\n"
                    for error in failed_subtasks:
                        result_message += f"{error}\n"
                
                return result_message
            
        except Exception as e:
            logger.error(f"Error in create_subtasks: {e}")
            return f"Error during subtask creation: {str(e)}"
