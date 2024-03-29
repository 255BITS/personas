import pytest
import asyncio
from pipelines import Pipeline, PipelineError, TaskExecutionError, task, set_output, get_output, OutputMismatchError

class Base:
    def __init__(self, content):
        self.content = content

class A(Base):
    content: str

class B(Base):
    content: str

class C(Base):
    content: str

@task
async def task_generate_a() -> A:
    return A(content="Generated A")

@task
async def task_generate_tuple():
    return (A(content="Generated A"), B(content="Generated B"))

@task
async def task_combine_tuple(a:A, b:B) -> C:
    return C(content=a.content + b.content)

@task
def task_sync_a() -> A:
    return A(content="Generated A")

@task
async def task_generate_b() -> B:
    return B(content="Generated B")

@task
async def task_override(override=None):
    return override

@task
async def task_convert_a(a: A) -> B:
    print("a", a, type(a))
    return B(content=a.content+" Convert B")

@task
async def task_convert_b(b: B) -> C:
    return C(content=b.content+" Convert C")

@task
async def task_chain_b(b: B) -> B:
    return B(content=b.content+" Convert B")

@task
async def task_combine_a_b(a: A, b: B) -> C:
    combined_content = f"{a.content} + {b.content}"
    return C(content=combined_content)

@task
async def task_fail() -> C:
    assert 1 == 2

@pytest.mark.asyncio
async def test_task():
    result = await task_generate_a(None)
    assert isinstance(result, A)

@pytest.mark.asyncio
async def test_sync_task():
    result = await task_sync_a(None)
    assert isinstance(result, A)

@pytest.mark.asyncio
async def test_task_group_sequential():
    result = await (task_generate_a >> task_convert_a)(None)
    assert isinstance(result, B)

@pytest.mark.asyncio
async def test_task_combine_tuple():
    result = await (task_generate_tuple >> task_combine_tuple)(None)
    assert isinstance(result, C)

@pytest.mark.asyncio
async def test_task_group_parallel():
    tg = task_generate_a | task_generate_b
    result = await tg(None)
    assert isinstance(result[0], A)
    assert isinstance(result[1], B)

@pytest.mark.asyncio
async def test_task_group_combined():
    tg = ((task_generate_a >> task_convert_a) | (task_generate_b >> task_chain_b))
    result = await tg(None)
    assert isinstance(result[0], B)
    assert isinstance(result[1], B)

@pytest.mark.asyncio
async def test_task_group_combined_flat():
    tg = (task_generate_a | task_generate_b) >> task_combine_a_b
    result = await tg(None)
    assert isinstance(result, C)

@pytest.mark.asyncio
async def test_pipeline_type_chaining():
    """Test that tasks are correctly chained based on type."""
    pipeline = Pipeline(task_generate_a >> task_convert_a)
    result = await pipeline()
    assert isinstance(result, B) and result.content == "Generated A Convert B", "Type-based chaining failed."

@pytest.mark.asyncio
async def test_pipeline_subgraphs():
    pipeline = Pipeline(task_generate_a, task_generate_b)
    result = await pipeline()
    assert isinstance(result[0], A) and isinstance(result[1], B)

@pytest.mark.asyncio
async def test_pipeline_fan_out():
    pipeline = Pipeline(task_generate_a >> set_output("a"), get_output("a") >> (task_convert_a | task_convert_a))
    result = await pipeline()
    assert isinstance(result[0], A) and isinstance(result[1][0], B) and isinstance(result[1][1], B)

@pytest.mark.asyncio
async def test_pipeline_parallel_execution():
    """Test handling of parallel tasks."""
    pipeline = Pipeline(task_generate_a >> task_convert_a >> task_convert_b)
    result = await pipeline()
    assert isinstance(result, C)

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
    with pytest.raises(TaskExecutionError):
        await pipeline()

@pytest.mark.asyncio
async def test_pipeline_failure_fan_out():
    """Test the pipeline's ability to handle mismatched fan-in/fan-out."""
    with pytest.raises(OutputMismatchError):
        Pipeline(task_generate_a >> set_output('typo'), get_output('a') >> task_convert_a)
