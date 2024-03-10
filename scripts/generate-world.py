import asyncio
from pydantic import BaseModel, Field
from typing import List
from pipelines import task, Pipeline

class WorldConfig(BaseModel):
    name: str
    description: str
    geography: str
    climate: str
    inhabitants: List[str]

@task
async def get_world_prompt(world_type: str) -> str:
    # Generate a prompt based on the world type
    # You can customize this function to generate specific prompts for different world types
    return f"Create a {world_type} world with a unique name, description, geography, climate, and inhabitants."

@task
async def get_llm_request(prompt: str) -> str:
    # Simulate an LLM request and return the generated world JSON
    # Replace this with your actual LLM request implementation
    sample_world_json = '''
    {
        "name": "Ethereal Realm",
        "description": "A mystical world filled with enchanted forests and floating islands.",
        "geography": "Lush forests, soaring mountains, and vast oceans dotted with levitating landmasses.",
        "climate": "Temperate with occasional magical storms.",
        "inhabitants": ["Elves", "Fairies", "Wizards", "Talking Animals"]
    }
    '''
    return sample_world_json

@task
async def validate_world_json(world_json: str) -> WorldConfig:
    # Parse and validate the generated world JSON using Pydantic
    try:
        world_config = WorldConfig.parse_raw(world_json)
        return world_config
    except ValidationError as e:
        # Handle validation errors
        raise ValueError(f"Invalid world JSON: {e}")

# Define the world generation pipeline
generate_world = Pipeline(
    get_world_prompt >> get_llm_request >> validate_world_json
)

async def main():
    # Generate a world
    world_type = "Utopia"
    try:
        world = await generate_world(world_type)
        print(f"Generated World: {world}")
        # TODO: Save the generated world, handle errors, etc.
    except Exception as e:
        print(f"Error generating world: {e}")
        raise e

if __name__ == "__main__":
    asyncio.run(main())
