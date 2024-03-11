from .task import Composable, TaskGroup
from .pipeline_context import PipelineContext
import asyncio
from typing import Callable, TypeVar, Generic, Union, Awaitable, Dict, Any, List

class PipelineError(Exception):
    pass

class Pipeline:
    def __init__(self, *subgraphs: Composable):
        self.subgraphs = subgraphs

    async def __call__(self, *args, context: PipelineContext = None, **kwargs) -> List[Any]:
        if context is None:
            context = PipelineContext()
        outputs = []
        subgraphs_to_execute = [subgraph(context, *args, **kwargs) for subgraph in self.subgraphs]
        outputs = await asyncio.gather(*subgraphs_to_execute)
        if len(outputs) == 1:
            return outputs[0]
        return outputs
