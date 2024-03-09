from .checkpoint_strategies import CheckpointStrategy
from .task import Composable, SetOutput, GetOutput
import asyncio
from typing import Callable, TypeVar, Generic, Union, Awaitable, Dict, Any, List

class PipelineError(Exception):
    pass

class Pipeline:
    def __init__(self, *tasks: Composable, parallel: bool = False, checkpoint_strategy: 'CheckpointStrategy' = None):
        self.tasks = list(tasks)
        self.parallel = parallel
        self.checkpoint_strategy = checkpoint_strategy
        self.outputs = {}

    async def __call__(self, *args, **kwargs) -> List[Any]:
        checkpoint_identifier = f"pipeline_{id(self)}"
        checkpoint = await self.load_checkpoint(checkpoint_identifier)
        if checkpoint:
            start_index = checkpoint['task_index']
            args = checkpoint['args']
            kwargs = checkpoint['kwargs']
            self.outputs = checkpoint['outputs']
        else:
            start_index = 0

        outputs = []
        for i in range(start_index, len(self.tasks)):
            task = self.tasks[i]
            print("Tasks", len(self.tasks), task)
            if isinstance(task, SetOutput):
                self.outputs[task.name] = args[0]
            elif isinstance(task, GetOutput):
                args = (self.outputs[task.name],)
            else:
                if self.parallel:
                    result = await asyncio.gather(task(*args, **kwargs))
                else:
                    result = await task(*args, **kwargs)
                print("Found", result)
                outputs.append(result)
                args = (result,)
            await self.save_checkpoint(checkpoint_identifier, i + 1, args, kwargs, self.outputs)
        if len(outputs) == 1:
            return outputs[0]
        return outputs

    async def save_checkpoint(self, checkpoint_identifier: str, task_index: int, args: tuple, kwargs: dict, outputs: dict):
        if self.checkpoint_strategy:
            checkpoint_data = {
                'task_index': task_index,
                'args': args,
                'kwargs': kwargs,
                'outputs': outputs
            }
            await self.checkpoint_strategy.save_checkpoint(checkpoint_identifier, checkpoint_data)

    async def load_checkpoint(self, checkpoint_identifier: str) -> Dict[str, Any]:
        if self.checkpoint_strategy:
            return await self.checkpoint_strategy.load_checkpoint(checkpoint_identifier)
        return None
