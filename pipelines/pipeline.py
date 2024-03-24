from .task import Composable, TaskGroup, SetOutput, GetOutput, GraphNode, Task
from .pipeline_context import PipelineContext
import asyncio
from typing import Callable, TypeVar, Generic, Union, Awaitable, Dict, Any, List

class PipelineError(Exception):
    pass

class OutputMismatchError(Exception):
    pass

class Pipeline:
    def __init__(self, *subgraphs: Composable):
        self.subgraphs = subgraphs
        self.validate_pipeline()

    def validate_pipeline(self):
        self.validate_pipeline()

    def validate_pipeline(self):
        set_outputs = set()
        get_outputs = set()
        for subgraph in self.subgraphs:
            self.traverse_dag(subgraph, set_outputs, get_outputs)
        if len(get_outputs - set_outputs) > 0:
            raise OutputMismatchError(get_outputs - set_outputs)

    def traverse_dag(self, task, set_outputs, get_outputs):
        if isinstance(task, SetOutput):
            set_outputs.add(task.name)
        elif isinstance(task, GetOutput):
            get_outputs.add(task.name)
        elif isinstance(task, TaskGroup):
            for subtask in task.tasks:
                self.traverse_dag(subtask, set_outputs, get_outputs)

    async def __call__(self, *args, context: PipelineContext = None, **kwargs) -> List[Any]:
        if context is None:
            context = PipelineContext()
        outputs = []
        subgraphs_to_execute = [subgraph(context, *args, **kwargs) for subgraph in self.subgraphs]
        outputs = await asyncio.gather(*subgraphs_to_execute)
        if len(outputs) == 1:
            return outputs[0]
        return outputs
