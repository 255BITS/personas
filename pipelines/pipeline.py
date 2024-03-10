from .checkpoint_strategies import CheckpointStrategy
from .task import Composable, TaskGroup
import asyncio
from typing import Callable, TypeVar, Generic, Union, Awaitable, Dict, Any, List

class PipelineError(Exception):
    pass

class PipelineContext:
    def __init__(self):
        self.outputs = {}
        self.events = {}

    async def set_output(self, name, value):
        """Set the output value and notify any waiters."""
        self.outputs[name] = value
        event = self.events.get(name)
        if event and event.is_set() == False:
            event.set()

    async def get_output(self, name):
        """Get the output value if available, or wait for it to be set."""
        if name in self.outputs:
            return self.outputs[name]

        if name not in self.events:
            self.events[name] = asyncio.Event()

        await self.events[name].wait()
        return self.outputs[name]

class Pipeline:
    def __init__(self, *subgraphs: Composable, checkpoint_strategy: 'CheckpointStrategy' = None):
        self.subgraphs = subgraphs
        self.checkpoint_strategy = checkpoint_strategy
        self.context = PipelineContext()

    async def __call__(self, *args, **kwargs) -> List[Any]:
        outputs = []
        for subgraph in self.subgraphs:
            if isinstance(subgraph, TaskGroup):
                result = await subgraph(self.context, *args, **kwargs)
            else:
                result = await subgraph(*args, **kwargs)
            outputs.append(result)
            args = (result,)
        if len(outputs) == 1:
            return outputs[0]
        return outputs
