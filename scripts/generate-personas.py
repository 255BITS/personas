import asyncio
import pydantic
import re
from typing import List
from pipelines import task, Pipeline, set_output, get_output
from common import save_pydantic, load_pydantic_or_none, WorldConfig, ValidationError, schema_to_prompt, post_message_to_anthropic_cached, PersonaConfig
from personas.llm_methods import post_message_to_anthropic

@task
async def load_world(world_name: str) -> WorldConfig:
    world = load_pydantic_or_none(WorldConfig, world_name+".json")
    return world

@task
async def create_persona_json(world: WorldConfig) -> str:
    schema_desc = schema_to_prompt(PersonaConfig)
    prompt = f"Generate a persona for a `personas` chat project. Characters will come from this world: ```\n{world}\n```\n\nThe resulting persona should have the following attributes:\n```\n{schema_desc}\n```\n\nWrite your resulting Persona in json. Be sure to wrap it in \"```json\" markdown tag. Don't use the name Zephyr or Aria."
    response_data = await post_message_to_anthropic(prompt)
    content = response_data['content'][0]['text']
    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if json_match:
        json_string = json_match.group(1)
        return json_string
    else:
        raise LLMResponseInvalid()

@task
def validate_persona_json(persona_json: str) -> PersonaConfig:
    # Parse and validate the generated persona JSON using Pydantic
    # Replace this with your actual validation logic
    return PersonaConfig.parse_raw(persona_json)

# Define the pipeline
pipeline = Pipeline(
    load_world >> create_persona_json >> validate_persona_json
)

async def main():
    # Execute the pipeline
    world_types = ["Utopia", "Neotopia", "Dystopia"]
    try:
        for world_type in world_types:
            for i in range(2):
                persona = await pipeline(world_type)
                save_pydantic(persona, f"{world_type}_{persona.name}.json")

        print(f"Generated Persona: {persona.name}")
    except Exception as e:
        print(f"Error generating world and personas: {e}")

if __name__ == "__main__":
    asyncio.run(main())
