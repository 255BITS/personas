from .checkpoint_strategies import CheckpointStrategy
from .task import Composable, TaskGroup
from .pipeline_context import PipelineContext
import asyncio
from typing import Callable, TypeVar, Generic, Union, Awaitable, Dict, Any, List

class PipelineError(Exception):
    pass

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
