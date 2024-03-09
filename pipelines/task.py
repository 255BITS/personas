import asyncio
from typing import Callable, TypeVar, Generic, Union, Awaitable, Dict, Any, List

# Credit to Claude 3 Opus 20240220 and ChatGPT
T = TypeVar('T')
R = TypeVar('R')

class Composable(Generic[T, R]):
    async def __call__(self, *args, **kwargs) -> R:
        raise NotImplementedError

    def __rshift__(self, other: 'Composable') -> 'Composable':
        raise NotImplementedError

    def __or__(self, other: 'Composable') -> 'Composable':
        raise NotImplementedError

class TaskGroup(Composable[T, R]):
    def __init__(self, tasks=None, parallel=False):
        self.tasks = tasks if tasks is not None else []
        self.parallel = parallel

    async def __call__(self, *args, **kwargs):
        if self.parallel:
            results = await asyncio.gather(*[task(*args, **kwargs) for task in self.tasks])
            return results

        results = []
        for task in self.tasks:
            result = await task(*args, **kwargs)
            results.append(result)
            args = (result,)
        return results[-1]

    def __rshift__(self, other: 'Composable') -> 'TaskGroup':
        return self.compose(other, False)

    def __or__(self, other: 'Composable') -> 'TaskGroup':
        return self.compose(other, True)

    def compose(self, other: 'Composable', parallel: bool) -> 'TaskGroup':
        if isinstance(other, TaskGroup):
            return TaskGroup([self, other], parallel=parallel)
        return TaskGroup(self.tasks + [other], parallel=parallel)

    def __repr__(self):
        mode = "Parallel" if self.parallel else "Sequential"
        tasks_repr = ', '.join(repr(task) for task in self.tasks)
        return f"{self.__class__.__name__}({mode}: [{tasks_repr}])"

class Task(Composable[T, R]):
    def __init__(self, func: Callable[..., Awaitable[R]], name: str = None):
        self.func = func
        self.name = name or func.__name__

    async def __call__(self, *args, **kwargs) -> R:
        return await self.func(*args, **kwargs)

    def __rshift__(self, other: 'Composable') -> 'TaskGroup':
        if isinstance(other, Task):
            return TaskGroup([self, other], parallel=False)
        return other.__rshift__(self)

    def __or__(self, other: 'Composable') -> 'TaskGroup':
        if isinstance(other, Task):
            return TaskGroup([self, other], parallel=True)
        return other.__or__(self)

class SetOutput(Composable[T, T]):
    def __init__(self, name: str):
        self.name = name

    async def __call__(self, value: T) -> T:
        return value

class GetOutput(Composable[T, T]):
    def __init__(self, name: str):
        self.name = name

    async def __call__(self, *args, **kwargs) -> T:
        return None  # Placeholder, will be replaced by the actual output value in the pipeline

def task(func: Callable[..., Awaitable[R]], name: str = None) -> Task[T, R]:
    return Task(func, name)

def set_output(name: str) -> SetOutput[T]:
    return SetOutput(name)

def get_output(name: str) -> GetOutput[T]:
    return GetOutput(name)
