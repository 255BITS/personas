from .pipeline import Pipeline, PipelineError
from .task import task, set_output, get_output
from .checkpoint_strategies import FileCheckpointStrategy
from .llm_methods import deserialize_llm_response_json
import asyncio
import functools

def async_partial(func, *partial_args, **partial_kwargs):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Merge kwargs with partial_kwargs, giving precedence to kwargs provided at call time
        combined_kwargs = {**partial_kwargs, **kwargs}
        if asyncio.iscoroutinefunction(func):
            # If func is a coroutine, await it with both args and kwargs
            return await func(*partial_args, *args, **combined_kwargs)
        else:
            # If func is not a coroutine, call it normally with both args and kwargs
            return func(*partial_args, *args, **combined_kwargs)
    return wrapper
