from typing import Dict, Any
import pickle

class PipelineError(Exception):
    pass

async def checkpoint(data: Dict[str, Any], checkpoint_path: str):
    with open(checkpoint_path, 'wb') as f:
        pickle.dump(data, f)

async def restore_from_checkpoint(checkpoint_path: str) -> Dict[str, Any]:
    with open(checkpoint_path, 'rb') as f:
        data = pickle.load(f)
    return data

async def pipeline(input_data: Dict[str, Any], checkpoint_path: str = None) -> Dict[str, Any]:
    if checkpoint_path:
        try:
            data = await restore_from_checkpoint(checkpoint_path)
            completed_steps = data.get('completed_steps', [])
        except FileNotFoundError:
            data = input_data
            completed_steps = []
    else:
        data = input_data
        completed_steps = []

    for coroutine in coroutines:
        if coroutine.__name__ not in completed_steps:
            try:
                data = await coroutine(data)
                completed_steps.append(coroutine.__name__)
                data['completed_steps'] = completed_steps
                await checkpoint(data, checkpoint_path)
            except PipelineError as e:
                # Log the error and re-raise the exception
                print(f"Error occurred in pipeline step: {coroutine.__name__}")
                print(f"Error message: {str(e)}")
                raise
        else:
            print(f"Skipping completed step: {coroutine.__name__}")

    return data


