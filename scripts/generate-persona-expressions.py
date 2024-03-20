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
    print('<<', prompt)
    response_data = await post_message_to_anthropic(prompt)
    content = response_data['content'][0]['text']
    print("--", content)
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

emotion_sliders = {
    "happy": "44ba1d0d-6948-4676-8f3d-2df7d531a1ab",
    "laughing": "ecc7c41a-01f1-4afb-81fd-339ab9eea386"
}

personas = {
    "Dystopia_Lila Nakamura": "83d7fddf98434ed2985655a0a020b1bf",
    "Dystopia_Liam Hawkins": "af7979bd0ac846528a168717c7d4e9ac",
    "Neotopia_Zara Xander": "422cf62d05364ccdb3e880e40ca33127",
    "Neotopia_Aria Vance": "48e6a5095093445c85c1cdc80115d780",
    "Utopia_Lyra Solaris": "8ada7ba66f0c4971a715e9490d3f43a6",
    "Utopia_Zephyr": "60790fcbd82a4d86a4f0710be4ddaba5"
}
worlds = {
    "Utopia": "d57d772e39cd4dc09699743803ca3e51",
    "Neotopia": "895d89c8247d4cc0bbf94d078473e271",
    "Dystopia": "0d61620e4935416c9e53801e714f1b00"
}

# Define the pipeline
pipeline = Pipeline(
    load_world_and_persona >> set_output("persona"),
    get_output("persona") >> render_expressions >> save_expressions,
    get_output("persona") >> render_world >> save_world
)

async def main():
    try:
        # Loop through the personas dictionary
        for full_persona, persona_uuid in personas.items():
            # Split the key to extract the world name and persona name
            world_persona_split = full_persona.split("_")
            world_name = world_persona_split[0]
            persona_name = "_".join(world_persona_split[1:])  # In case persona names also contain underscores

            # Look up the world_uuid using the world name
            world_uuid = worlds.get(world_name)

            # Call the pipeline function with the required arguments
            pipeline(world_name, world_uuid, persona_name, persona_uuid)
        print(f"Generated Persona: {persona.name}")
    except Exception as e:
        print(f"Error generating world and personas: {e}")

if __name__ == "__main__":
    asyncio.run(main())
