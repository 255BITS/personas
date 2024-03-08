import pytest
import asyncio
from pipelines import Pipeline, PipelineError, async_partial

# Mock tasks for testing purposes
async def task_a(data):
    data['result'] = (data.get('result', '') + ' A').strip()
    return data

async def task_b(data):
    data['result'] = (data.get('result', '') + ' B').strip()
    return data

async def task_concurrent(identifier, data):
    data['result'] = (data.get('result', '') + f' Concurrent{identifier}').strip()
    return data

async def task_failure(data):
    raise PipelineError("Simulated task failure")

@pytest.mark.asyncio
async def test_execute_single_task():
    """Test execution with a single task."""
    pipeline = Pipeline([task_a])  # Not specifying a checkpoint strategy for simplicity
    result = await pipeline({})
    assert 'result' in result and result['result'] == 'A', "task_a should execute successfully."

@pytest.mark.asyncio
async def test_task_failure():
    """Test pipeline handling of a task failure."""
    pipeline = Pipeline([task_failure])  # Pipeline with a task that fails
    with pytest.raises(PipelineError):
        await pipeline({})

@pytest.mark.asyncio
async def test_execute_sequential_tasks():
    """Test sequential execution of tasks."""
    pipeline = Pipeline([task_a, task_b])
    result = await pipeline({})
    assert 'result' in result and result['result'] == 'A B', "task_a and task_b should execute sequentially."

@pytest.mark.asyncio
async def test_execute_with_concurrency():
    """Test concurrency."""
    pipeline = Pipeline([task_a, [async_partial(task_concurrent, 1), async_partial(task_concurrent, 2)], task_b])
    result = await pipeline({})
    expected_result = 'A Concurrent1 Concurrent2 B'
    assert 'result' in result and result['result'] == expected_result, "Tasks including concurrent ones should execute in order."

