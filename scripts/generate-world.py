from pipelines import task, Pipeline
import pydantic
from typing import Dict, List
import json
import re
import os
import asyncio
from common import save_pydantic, WorldConfig, ValidationError, schema_to_prompt, post_message_to_anthropic_cached

@task
async def get_world_prompt(world_type: str) -> str:
    # Generate a prompt based on the world type
    # You can customize this function to generate specific prompts for different world types
    return f"Create a {world_type} world with a unique name, description, geography, climate, and inhabitants."

@task
async def get_llm_request(world_type: str) -> str:
    schema_desc = schema_to_prompt(WorldConfig)
    prompt = f"Generate an interesting world for a `personas` project. Characters will come from this world which should be {world_type}. It should have the following attributes:\n```{schema_desc}```\n\nWrite your results in json. Be sure to wrap it in \"```json\" markdown tag."
    response_data = await post_message_to_anthropic_cached(prompt)
    content = response_data['content'][0]['text']
    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if json_match:
        json_string = json_match.group(1)
        return json_string
    else:
        print("--", content)
        raise LLMResponseInvalid()

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
    world_types = ["Utopia", "Dystopian", "Neotopia"]
    for world_type in world_types:
        try:
            world = await generate_world(world_type)
            save_pydantic(world, f"{world_type}.json")
            print(f"Generated World: {world}")
            # TODO: Save the generated world, handle errors, etc.
        except Exception as e:
            print(f"Error generating world: {e}")
            raise e

if __name__ == "__main__":
    asyncio.run(main())
