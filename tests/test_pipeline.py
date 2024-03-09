import pytest
import asyncio
from pipelines import Pipeline, PipelineError, async_partial, task, set_output

from typing import NamedTuple

# Define mock types for testing purposes
class A(NamedTuple):
    content: str

class B(NamedTuple):
    content: str

class C(NamedTuple):
    content: str

@task
async def task_generate_a() -> A:
    return A(content="Generated A")

@task
async def task_generate_b() -> B:
    return B(content="Generated B")

@task
async def task_convert_a(a: A) -> B:
    return B(content=a.content+" Convert B")

@task
async def task_chain_b(b: B) -> B:
    return B(content=b.content+" Convert B")

@task
async def task_combine_a_b(a: A, b: B) -> C:
    combined_content = f"{a.content} + {b.content}"
    return C(content=combined_content)

@task
async def task_fail() -> C:
    raise PipelineError("Simulated task failure")

@pytest.mark.asyncio
async def test_task():
    result = await task_generate_a()
    assert isinstance(result, A)

@pytest.mark.asyncio
async def test_task_group_sequential():
    result = await (task_generate_a >> task_convert_a)()
    assert isinstance(result, B)

@pytest.mark.asyncio
async def test_task_group_parallel():
    tg = task_generate_a | task_generate_b
    result = await tg()
    print("--", tg, result)
    assert isinstance(result[0], A)
    assert isinstance(result[1], B)

@pytest.mark.asyncio
async def test_task_group_combined():
    tg = ((task_generate_a >> task_convert_a) | (task_generate_b >> task_chain_b)) 
    print('--', tg)
    result = await tg()
    assert isinstance(result[0], B)
    assert isinstance(result[1], B)

@pytest.mark.asyncio
async def test_pipeline_type_chaining():
    """Test that tasks are correctly chained based on type."""
    pipeline = Pipeline(task_generate_a >> task_convert_a)
    result = await pipeline()
    assert isinstance(result, B) and result.content == "Generated A Convert B", "Type-based chaining failed."

@pytest.mark.asyncio
async def test_pipeline_parallel_execution():
    """Test handling of parallel tasks."""
    pipeline = Pipeline(task_generate_a >> task_convert_a >> task_combine_a_b)
    result = await pipeline()
    assert isinstance(result, C) and "Generated A" in result.content and "Convert B" in result.content, "Parallel execution or combination failed."

@pytest.mark.asyncio
async def test_pipeline_transitioning_types():
    """Test transitioning between task types through the pipeline."""
    pipeline = Pipeline((task_generate_a | task_generate_b) >> task_combine_a_b)
    result = await pipeline()
    assert isinstance(result, C), "Transitioning between types failed."

@pytest.mark.asyncio
async def test_pipeline_failure_handling():
    """Test the pipeline's ability to handle task failures."""
    pipeline = Pipeline(task_fail)
    with pytest.raises(Exception, match="Simulated task failure"):
        await pipeline()
