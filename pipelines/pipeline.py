from typing import Dict, Any
from .checkpoint_strategies import CheckpointStrategy
import asyncio
import pickle

class PipelineError(Exception):
    pass

class Pipeline:
    def __init__(self, coroutines, checkpoint_strategy=None):
        self.coroutines = coroutines
        self.checkpoint_strategy = checkpoint_strategy

    async def __call__(self, initial_data: Dict[str, Any], identifier: str = None) -> Dict[str, Any]:
        data = initial_data
        completed_steps = data.get('completed_steps', [])

        for step in self.coroutines:
            # Check if the step is a list (indicating concurrent execution)
            if isinstance(step, list):
                concurrent_tasks = [coroutine(data) for coroutine in step]
                results = await asyncio.gather(*concurrent_tasks)
                # Assuming you want to merge results - adjust according to your needs
                for result in results:
                    data.update(result)
            else:
                if step.__name__ not in completed_steps:
                    try:
                        data = await step(data)
                        completed_steps.append(step.__name__)
                        data['completed_steps'] = completed_steps
                        if self.checkpoint_strategy and identifier:
                            await self.checkpoint_strategy.save(data, identifier)
                    except PipelineError as e:
                        print(f"Error occurred in pipeline step: {step.__name__}")
                        print(f"Error message: {str(e)}")
                        raise
                else:
                    print(f"Skipping completed step: {step.__name__}")

        return data
