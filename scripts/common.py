from pydantic import BaseModel
from typing import TypeVar, Type, Optional, Dict, List
import shelve
import pydantic
import json
import os
from personas.llm_methods import post_message_to_anthropic

# Defining a generic Pydantic type for our functions
T = TypeVar('T', bound=BaseModel)

def get_asset_path(filename: str) -> str:
    """
    Constructs a path to the assets directory relative to the current working directory.

    Parameters:
        filename: The filename to append to the assets path.

    Returns:
        The full path to the file within the assets directory.
    """
    dirname = os.path.dirname(os.path.abspath(__file__))
    assets_path = os.path.join(dirname, '..', 'assets')
    # Ensure the assets directory exists
    os.makedirs(assets_path, exist_ok=True)
    return os.path.join(assets_path, filename)

def save_pydantic(obj: T, filename: str) -> None:
    """
    Serializes a Pydantic object to JSON and saves it to a file in the ../assets directory.
    
    Parameters:
        obj: The Pydantic object to serialize.
        filename: The filename where the JSON will be saved.
    """
    full_path = get_asset_path(filename)
    if os.path.exists(full_path):
        return save_pydantic(obj, filename+'-2')
    with open(full_path, 'w') as file:
        file.write(obj.json())

def load_pydantic_or_none(obj_type: Type[T], filename: str) -> Optional[T]:
    """
    Attempts to load a Pydantic object from a JSON file in the ../assets directory. Uses Pydantic V2 compatible method.
    
    Parameters:
        obj_type: The Pydantic model class to deserialize to.
        filename: The filename from which to load the JSON.
        
    Returns:
        The deserialized Pydantic object, or None if it cannot be loaded.
    """
    full_path = get_asset_path(filename)
    print("Looking for", full_path)
    try:
        with open(full_path, 'r') as file:
            return obj_type.parse_raw(file.read())
    except (FileNotFoundError, json.JSONDecodeError):
        return None

CACHE_FILENAME = "anthropic_cache.db"

async def post_message_to_anthropic_cached(prompt, temperature=0.5, system=None):
    cache_filepath = os.path.abspath(CACHE_FILENAME)  # Get absolute path for reliability
    with shelve.open(cache_filepath) as cache:  # Open the cache as a database-like object
        if prompt in cache:
            return cache[prompt]
        else:
            response_data = await post_message_to_anthropic(prompt,temperature=temperature, system=system)  # Call the Anthropic API
            cache[prompt] = response_data
            return response_data

def schema_to_prompt(schema: pydantic.BaseModel) -> str:
    """Converts a Pydantic schema into a formatted prompt, including examples if available.

    Args:
        schema: The Pydantic schema to convert.

    Returns:
        A string representing the formatted prompt with optional examples.
    """
    return pydantic.TypeAdapter(schema).json_schema()

class WorldConfig(pydantic.BaseModel):
    name: str
    description: str
    geography: str
    climate: str
    inhabitants: List[Dict[str, str]] = pydantic.Field(..., example=[{"Rebels": "The Rebels are a loose coalition..."}])
    stable_diffusion_prompt: str

class PersonaConfig(pydantic.BaseModel):
    name: str
    background: str
    short_description: str
    chat_prompt: str = pydantic.Field(..., description="The chat prompt that is sent to an LLM. Usually includes instructions and background information on the character and world.")
    stable_diffusion_prompt: str = pydantic.Field(..., description="An SDXL prompt that will generate an image for the character. Do not include action, expression, clothing, or location. These will be added later.", example="Sofia from Australia, medium shoulder-length ginger parted in the side with blond streaks, brown eyes, curved nose, thick lips, dimples, perfect teeth, teasing look, freckles")

class ValidationError(Exception):
    pass

