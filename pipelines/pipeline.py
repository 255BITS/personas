from .task import Composable, TaskGroup
from .pipeline_context import PipelineContext
import asyncio
from typing import Callable, TypeVar, Generic, Union, Awaitable, Dict, Any, List

class PipelineError(Exception):
    pass

class Pipeline:
    def __init__(self, *subgraphs: Composable, context: PipelineContext = None):
        self.subgraphs = subgraphs
        if context is None:
            self.context = PipelineContext()
        else:
            self.context = context

    async def __call__(self, *args, **kwargs) -> List[Any]:
        outputs = []
        subgraphs_to_execute = [subgraph(self.context, *args, **kwargs) for subgraph in self.subgraphs]
        outputs = await asyncio.gather(*subgraphs_to_execute)
        if len(outputs) == 1:
            return outputs[0]
        return outputs
