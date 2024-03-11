import asyncio
import inspect
import functools
from typing import Callable, TypeVar, Generic, Union, Awaitable, Dict, Any, List

# Credit to Claude 3 Opus 20240220 and ChatGPT
T = TypeVar('T')
R = TypeVar('R')

class Composable(Generic[T, R]):
    async def __call__(self, context, *args, **kwargs) -> R:
        raise NotImplementedError

    def __rshift__(self, other: 'Composable') -> 'Composable':
        raise NotImplementedError

    def __or__(self, other: 'Composable') -> 'Composable':
        raise NotImplementedError

class TaskGroup(Composable[T, R]):
    def __init__(self, tasks=None, parallel=False):
        self.tasks = tasks if tasks is not None else []
        self.parallel = parallel
        self.name = [t.name for t in tasks]

    async def execute_task(self, task, context, *args, **kwargs):
        if isinstance(task, GetOutput):
            return await context.get_output(task.name)
        elif isinstance(task, Task):
            return await task(*args, **kwargs)
        else:
            return await task(context, *args, **kwargs)

    async def __call__(self, context, *args, **kwargs):
        if self.parallel:
            # Use a comprehension with the execute_task method for parallel execution
            tasks_to_execute = [self.execute_task(task, context, *args, **kwargs) for task in self.tasks]
            results = await asyncio.gather(*tasks_to_execute)
            return results

        results = []
        for task in self.tasks:
            result = await self.execute_task(task, context, *args, **kwargs)
            results.append(result)
            if isinstance(task, TaskGroup) and task.parallel:
                args = result
            else:
                args = (result,)
        # For sequential tasks, return the last result if there is one
        return results[-1] if results else None

    def __rshift__(self, other: 'Composable') -> 'TaskGroup':
        return self.compose(other, False)

    def __or__(self, other: 'Composable') -> 'TaskGroup':
        return self.compose(other, True)

    def compose(self, other: 'Composable', parallel: bool) -> 'TaskGroup':
        return TaskGroup([self, other], parallel=parallel)

    def __repr__(self):
        mode = "Parallel" if self.parallel else "Sequential"
        tasks_repr = ', '.join(repr(task) for task in self.tasks)
        return f"{self.__class__.__name__}({mode}: [{tasks_repr}])"

class GraphNode(Composable[T, R]):
    def __rshift__(self, other: 'Composable') -> 'TaskGroup':
        if isinstance(other, TaskGroup):
            return TaskGroup([self, other.tasks], parallel=False)
        if isinstance(other, Composable):
            return TaskGroup([self, other], parallel=False)

    def __or__(self, other: 'Composable') -> 'TaskGroup':
        if isinstance(other, Task):
            return TaskGroup([self, other], parallel=True)
        return other.__or__(self)

class Task(GraphNode[T, R]):
    def __init__(self, func: Callable[..., Union[Awaitable[R], R]], name: str = None):
        self.func = func
        self.name = name or func.__name__

    async def __call__(self, *args, **kwargs) -> R:
        if inspect.iscoroutinefunction(self.func):
            return await self.func(*args, **kwargs)
        else:
            return self.func(*args, **kwargs)

class SetOutput(GraphNode[T, T]):
    def __init__(self, name: str):
        self.name = name

    async def __call__(self, context, value: T) -> T:
        await context.set_output(self.name, value)
        return value

class GetOutput(GraphNode[T, T]):
    def __init__(self, name: str):
        self.name = name

    async def __call__(self, context, *args, **kwargs) -> T:
        return None

def task(func: Callable[..., Awaitable[R]], name: str = None) -> Task[T, R]:
    return Task(func, name)

def set_output(name: str) -> SetOutput[T]:
    return SetOutput(name)

def get_output(name: str) -> GetOutput[T]:
    return GetOutput(name)
