import json
from typing import Type, Tuple, Any, Union
import aiohttp
import asyncio
import os

async def post_message_to_anthropic(message: str, model: str = "claude-3-opus-20240229", system=None):
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', None)  # Ensure the ANTHROPIC_API_KEY is set in your environment variables
    if anthropic_api_key is None:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "max_tokens": 2048,
        "temperature": 0.8,
        "messages": [
            {"role": "user", "content": message}
        ]
    }
    if system:
        data["system"] = system

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                print("Request successful.")
                return await response.json()
            else:
                print(f"Request failed with status code: {response.status}")

# Adjusted function to support any model with **kwargs
async def deserialize_llm_response_json(model: Type[Any], response: str) -> Tuple[Union[Any, None], str]:
    """
    Deserializes a JSON string response into a specified model.

    Parameters:
    - model: Type[Any] - The model class to deserialize the response into. Must support **kwargs.
    - response: str - The JSON string response.

    Returns:
    - A tuple containing:
        - An instance of the model if deserialization is successful, or None if it fails.
        - An error message indicating the reason for failure or an empty string if successful.
    """
    try:
        data = json.loads(response)
    except json.JSONDecodeError as e:
        return None, f"Malformed JSON response: {e}"

    try:
        model_instance = model(**data)
        return model_instance, ''
    except Exception as e:  # Catching broadly since we don't know the specific exceptions models might raise
        return None, f"Error during model instantiation: {e}"
