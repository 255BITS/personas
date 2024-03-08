import pytest
import asyncio
from pipeline import execute_pipeline, PipelineError  # Adjust import paths as necessary

# Mock tasks for testing purposes
async def task_a(data):
    data['result'] = (data.get('result', '') + ' A').strip()
    return data

async def task_b(data):
    data['result'] = (data.get('result', '') + ' B').strip()
    return data

async def task_concurrent(data, identifier):
    data['result'] = (data.get('result', '') + f' Concurrent{identifier}').strip()
    return data

async def task_failure(data):
    raise PipelineError("Simulated task failure")

@pytest.mark.asyncio
async def test_execute_single_task():
    """Test execution with a single task."""
    tasks = [task_a]
    result = await execute_pipeline(tasks, {})
    assert 'result' in result and result['result'] == 'A', "task_a should execute successfully."

@pytest.mark.asyncio
async def test_task_failure():
    """Test pipeline handling of a task failure."""
    tasks = [task_failure]
    with pytest.raises(PipelineError):
        await execute_pipeline(tasks, {})

@pytest.mark.asyncio
async def test_execute_sequential_tasks():
    """Test sequential execution of tasks."""
    tasks = [task_a, task_b]
    result = await execute_pipeline(tasks, {})
    assert 'result' in result and result['result'] == 'A B', "task_a and task_b should execute sequentially."

@pytest.mark.asyncio
async def test_execute_with_concurrency():
    """Test execution with concurrent tasks."""
    tasks = [task_a, [lambda data: task_concurrent(data, 1), lambda data: task_concurrent(data, 2)], task_b]
    result = await execute_pipeline(tasks, {})
    expected_results = ['A Concurrent1 Concurrent2 B', 'A Concurrent2 Concurrent1 B']
    assert 'result' in result and result['result'] in expected_results, "Concurrent tasks should execute and results should be in any order followed by task_b."

