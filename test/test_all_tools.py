#!/usr/bin/env python3
"""
综合测试所有 TickTick MCP 工具
测试当前所有10个工具的功能，包括批量操作
"""

import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ticktick_mcp.src.ticktick_client import TickTickClient
from ticktick_mcp.src.config import initialize_client, ensure_client

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
        self.data = {}
    
    def record_pass(self, test_name):
        self.passed.append(test_name)
        print(f"   {GREEN}✓{RESET} {test_name}")
    
    def record_fail(self, test_name, error):
        self.failed.append((test_name, error))
        print(f"   {RED}✗{RESET} {test_name}: {error}")
    
    def record_skip(self, test_name, reason):
        self.skipped.append((test_name, reason))
        print(f"   {YELLOW}⊘{RESET} {test_name}: {reason}")
    
    def set_data(self, key, value):
        self.data[key] = value
    
    def get_data(self, key):
        return self.data.get(key)
    
    def print_summary(self):
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        print(f"\n{BOLD}{'=' * 60}{RESET}")
        print(f"{BOLD}测试总结{RESET}")
        print(f"{'=' * 60}")
        print(f"{GREEN}通过: {len(self.passed)}{RESET}")
        print(f"{RED}失败: {len(self.failed)}{RESET}")
        print(f"{YELLOW}跳过: {len(self.skipped)}{RESET}")
        print(f"总计: {total}")
        print(f"{'=' * 60}\n")
        
        if self.failed:
            print(f"{RED}{BOLD}失败的测试:{RESET}")
            for test_name, error in self.failed:
                print(f"  {RED}✗{RESET} {test_name}: {error}")
            print()


def print_section(title):
    """Print a section header"""
    print(f"\n{BLUE}{BOLD}{'=' * 60}{RESET}")
    print(f"{BLUE}{BOLD}{title}{RESET}")
    print(f"{BLUE}{BOLD}{'=' * 60}{RESET}\n")


# ==================== 项目管理工具测试 ====================

def test_get_all_projects(client: TickTickClient, results: TestResults):
    """测试：获取所有项目"""
    try:
        projects = client.get_all_projects()
        
        if 'error' in projects:
            results.record_fail("get_all_projects", projects['error'])
            return
        
        if isinstance(projects, list):
            results.record_pass(f"获取所有项目 (共 {len(projects)} 个)")
            # 保存第一个项目ID用于后续测试
            if projects:
                results.set_data('existing_project_id', projects[0]['id'])
        else:
            results.record_fail("get_all_projects", "返回格式错误")
    except Exception as e:
        results.record_fail("get_all_projects", str(e))


def test_create_project(client: TickTickClient, results: TestResults):
    """测试：创建项目"""
    try:
        project_name = f"[测试项目] {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        project = client.create_project(
            name=project_name,
            color="#FF6B6B",
            view_mode="list"
        )
        
        if 'error' in project:
            results.record_fail("create_project", project['error'])
            return
        
        if project.get('name') == project_name:
            results.record_pass(f"创建项目 '{project_name}'")
            results.set_data('test_project_id', project['id'])
            results.set_data('test_project_name', project_name)
        else:
            results.record_fail("create_project", "项目信息不匹配")
    except Exception as e:
        results.record_fail("create_project", str(e))


def test_get_project_info(client: TickTickClient, results: TestResults):
    """测试：获取项目完整信息"""
    try:
        project_id = results.get_data('test_project_id')
        if not project_id:
            results.record_skip("get_project_info", "没有可用的项目ID")
            return
        
        project_data = client.get_project_with_data(project_id)
        
        if 'error' in project_data:
            results.record_fail("get_project_info", project_data['error'])
            return
        
        project = project_data.get('project', {})
        tasks = project_data.get('tasks', [])
        
        if project.get('id') == project_id:
            results.record_pass(f"获取项目信息 (项目+{len(tasks)}个任务)")
        else:
            results.record_fail("get_project_info", "项目ID不匹配")
    except Exception as e:
        results.record_fail("get_project_info", str(e))


def test_delete_projects_single(client: TickTickClient, results: TestResults):
    """测试：删除单个项目"""
    try:
        # 创建一个临时项目用于删除
        temp_project = client.create_project(
            name=f"[临时删除测试] {datetime.now().strftime('%H%M%S')}"
        )
        
        if 'error' in temp_project:
            results.record_fail("delete_projects (单个)", f"创建临时项目失败: {temp_project['error']}")
            return
        
        temp_project_id = temp_project['id']
        
        # 删除项目
        result = client.delete_project(temp_project_id)
        
        if 'error' in result:
            results.record_fail("delete_projects (单个)", result['error'])
        else:
            results.record_pass("删除单个项目")
    except Exception as e:
        results.record_fail("delete_projects (单个)", str(e))


def test_delete_projects_batch(client: TickTickClient, results: TestResults):
    """测试：批量删除项目"""
    try:
        # 创建多个临时项目用于删除
        temp_projects = []
        for i in range(3):
            project = client.create_project(
                name=f"[批量删除测试{i+1}] {datetime.now().strftime('%H%M%S')}"
            )
            if 'error' not in project:
                temp_projects.append(project['id'])
        
        if len(temp_projects) < 2:
            results.record_skip("delete_projects (批量)", "无法创建足够的临时项目")
            return
        
        # 批量删除
        deleted_count = 0
        for project_id in temp_projects:
            result = client.delete_project(project_id)
            if 'error' not in result:
                deleted_count += 1
        
        if deleted_count == len(temp_projects):
            results.record_pass(f"批量删除 {deleted_count} 个项目")
        else:
            results.record_fail("delete_projects (批量)", f"只成功删除 {deleted_count}/{len(temp_projects)} 个")
    except Exception as e:
        results.record_fail("delete_projects (批量)", str(e))


# ==================== 任务管理工具测试 ====================

def test_create_tasks_single(client: TickTickClient, results: TestResults):
    """测试：创建单个任务"""
    try:
        project_id = results.get_data('test_project_id')
        if not project_id:
            results.record_skip("create_tasks (单个)", "没有可用的项目ID")
            return
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT12:00:00+0000')
        
        task = client.create_task(
            title="[测试任务] 单个任务创建测试",
            project_id=project_id,
            content="这是一个测试任务",
            due_date=tomorrow,
            priority="medium"
        )
        
        if 'error' in task:
            results.record_fail("create_tasks (单个)", task['error'])
            return
        
        if task.get('title'):
            results.record_pass("创建单个任务")
            results.set_data('test_task_id', task['id'])
        else:
            results.record_fail("create_tasks (单个)", "任务信息不完整")
    except Exception as e:
        results.record_fail("create_tasks (单个)", str(e))


def test_create_tasks_batch(client: TickTickClient, results: TestResults):
    """测试：批量创建任务"""
    try:
        project_id = results.get_data('test_project_id')
        if not project_id:
            results.record_skip("create_tasks (批量)", "没有可用的项目ID")
            return
        
        # 批量创建3个任务
        task_ids = []
        for i in range(3):
            task = client.create_task(
                title=f"[批量测试] 任务 {i+1}",
                project_id=project_id,
                priority="low"
            )
            if 'error' not in task:
                task_ids.append(task['id'])
        
        if len(task_ids) == 3:
            results.record_pass(f"批量创建 {len(task_ids)} 个任务")
            results.set_data('batch_task_ids', task_ids)
        else:
            results.record_fail("create_tasks (批量)", f"只成功创建 {len(task_ids)}/3 个")
    except Exception as e:
        results.record_fail("create_tasks (批量)", str(e))


def test_update_tasks(client: TickTickClient, results: TestResults):
    """测试：更新任务"""
    try:
        task_id = results.get_data('test_task_id')
        project_id = results.get_data('test_project_id')
        
        if not task_id or not project_id:
            results.record_skip("update_tasks", "没有可用的任务ID")
            return
        
        task = client.update_task(
            task_id=task_id,
            project_id=project_id,
            title="[测试任务] 已更新",
            priority="high"
        )
        
        if 'error' in task:
            results.record_fail("update_tasks", task['error'])
            return
        
        if task.get('priority') == 5:  # API 返回的仍是数字
            results.record_pass("更新任务 (优先级改为高)")
        else:
            results.record_fail("update_tasks", "任务更新未生效")
    except Exception as e:
        results.record_fail("update_tasks", str(e))


def test_create_subtasks(client: TickTickClient, results: TestResults):
    """测试：创建子任务"""
    try:
        task_id = results.get_data('test_task_id')
        project_id = results.get_data('test_project_id')
        
        if not task_id or not project_id:
            results.record_skip("create_subtasks", "没有可用的任务ID")
            return
        
        subtask = client.create_subtask(
            subtask_title="[测试子任务] 子任务1",
            parent_task_id=task_id,
            project_id=project_id,
            priority="medium"
        )
        
        if 'error' in subtask:
            results.record_fail("create_subtasks", subtask['error'])
            return
        
        if subtask.get('title'):
            results.record_pass("创建子任务")
            results.set_data('test_subtask_id', subtask['id'])
        else:
            results.record_fail("create_subtasks", "子任务信息不完整")
    except Exception as e:
        results.record_fail("create_subtasks", str(e))


def test_complete_tasks(client: TickTickClient, results: TestResults):
    """测试：完成任务"""
    try:
        batch_task_ids = results.get_data('batch_task_ids')
        project_id = results.get_data('test_project_id')
        
        if not batch_task_ids or not project_id:
            results.record_skip("complete_tasks", "没有可用的任务ID")
            return
        
        # 完成第一个批量任务
        task_id = batch_task_ids[0]
        result = client.complete_task(project_id, task_id)
        
        if 'error' in result:
            results.record_fail("complete_tasks", result['error'])
        else:
            results.record_pass("完成任务")
    except Exception as e:
        results.record_fail("complete_tasks", str(e))


def test_delete_tasks(client: TickTickClient, results: TestResults):
    """测试：删除任务"""
    try:
        batch_task_ids = results.get_data('batch_task_ids')
        project_id = results.get_data('test_project_id')
        
        if not batch_task_ids or not project_id:
            results.record_skip("delete_tasks", "没有可用的任务ID")
            return
        
        # 删除第二个批量任务
        if len(batch_task_ids) >= 2:
            task_id = batch_task_ids[1]
            result = client.delete_task(project_id, task_id)
            
            if 'error' in result:
                results.record_fail("delete_tasks", result['error'])
            else:
                results.record_pass("删除任务")
        else:
            results.record_skip("delete_tasks", "没有足够的任务")
    except Exception as e:
        results.record_fail("delete_tasks", str(e))


# ==================== 查询工具测试 ====================

def test_query_tasks_all(client: TickTickClient, results: TestResults):
    """测试：查询所有任务"""
    try:
        projects = client.get_all_projects()
        if 'error' in projects or not projects:
            results.record_skip("query_tasks (全部)", "无法获取项目列表")
            return
        
        # 获取第一个项目的任务
        project_id = projects[0]['id']
        project_data = client.get_project_with_data(project_id)
        
        if 'error' in project_data:
            results.record_fail("query_tasks (全部)", project_data['error'])
            return
        
        tasks = project_data.get('tasks', [])
        results.record_pass(f"查询所有任务 (找到 {len(tasks)} 个)")
    except Exception as e:
        results.record_fail("query_tasks (全部)", str(e))


def test_query_tasks_by_priority(client: TickTickClient, results: TestResults):
    """测试：按优先级查询"""
    try:
        project_id = results.get_data('test_project_id')
        if not project_id:
            results.record_skip("query_tasks (优先级)", "没有可用的项目ID")
            return
        
        project_data = client.get_project_with_data(project_id)
        if 'error' in project_data:
            results.record_fail("query_tasks (优先级)", project_data['error'])
            return
        
        tasks = project_data.get('tasks', [])
        high_priority_tasks = [t for t in tasks if t.get('priority', 0) == 5]
        
        results.record_pass(f"按优先级查询 (找到 {len(high_priority_tasks)} 个高优先级任务)")
    except Exception as e:
        results.record_fail("query_tasks (优先级)", str(e))


def test_query_tasks_by_project(client: TickTickClient, results: TestResults):
    """测试：按项目查询"""
    try:
        project_id = results.get_data('test_project_id')
        if not project_id:
            results.record_skip("query_tasks (项目)", "没有可用的项目ID")
            return
        
        project_data = client.get_project_with_data(project_id)
        
        if 'error' in project_data:
            results.record_fail("query_tasks (项目)", project_data['error'])
            return
        
        tasks = project_data.get('tasks', [])
        results.record_pass(f"按项目查询 (找到 {len(tasks)} 个任务)")
    except Exception as e:
        results.record_fail("query_tasks (项目)", str(e))


# ==================== 清理测试数据 ====================

def cleanup_test_data(client: TickTickClient, results: TestResults):
    """清理测试数据"""
    print_section("清理测试数据")
    
    try:
        project_id = results.get_data('test_project_id')
        if project_id:
            # 先删除项目中的所有任务
            project_data = client.get_project_with_data(project_id)
            if 'error' not in project_data:
                tasks = project_data.get('tasks', [])
                deleted_count = 0
                for task in tasks:
                    result = client.delete_task(project_id, task['id'])
                    if 'error' not in result:
                        deleted_count += 1
                print(f"   清理了 {deleted_count} 个测试任务")
            
            # 删除测试项目
            result = client.delete_project(project_id)
            if 'error' not in result:
                print(f"   {GREEN}✓{RESET} 删除测试项目")
            else:
                print(f"   {RED}✗{RESET} 删除测试项目失败: {result['error']}")
    except Exception as e:
        print(f"   {RED}✗{RESET} 清理失败: {str(e)}")


# ==================== 主测试流程 ====================

def main():
    """运行所有测试"""
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}TickTick MCP 工具综合测试{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")
    
    # 初始化客户端
    if not initialize_client():
        print(f"{RED}❌ 无法初始化 TickTick 客户端{RESET}")
        print("请确保已运行: uv run -m ticktick_mcp.cli auth")
        return 1
    
    client = ensure_client()
    results = TestResults()
    
    # 1. 项目管理工具测试
    print_section("1. 项目管理工具测试 (4个工具)")
    test_get_all_projects(client, results)
    test_create_project(client, results)
    test_get_project_info(client, results)
    test_delete_projects_single(client, results)
    test_delete_projects_batch(client, results)
    
    # 2. 任务管理工具测试
    print_section("2. 任务管理工具测试 (5个工具)")
    test_create_tasks_single(client, results)
    test_create_tasks_batch(client, results)
    test_update_tasks(client, results)
    test_create_subtasks(client, results)
    test_complete_tasks(client, results)
    test_delete_tasks(client, results)
    
    # 3. 查询工具测试
    print_section("3. 查询工具测试 (1个工具)")
    test_query_tasks_all(client, results)
    test_query_tasks_by_priority(client, results)
    test_query_tasks_by_project(client, results)
    
    # 4. 清理测试数据
    cleanup_test_data(client, results)
    
    # 打印测试总结
    results.print_summary()
    
    # 返回状态码
    return 0 if len(results.failed) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

