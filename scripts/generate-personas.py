import asyncio
from pydantic import BaseModel, Field
from typing import List
from pipelines import task, Pipeline, set_output, get_output

class WorldConfig(BaseModel):
    name: str
    description: str
    geography: str
    climate: str
    inhabitants: List[str]

class PersonaConfig(BaseModel):
    name: str
    age: int
    background: str
    traits: List[str]
    goals: List[str]

@task
async def get_world_prompt(world_type: str) -> str:
    return f"Create a {world_type} world with a unique name, description, geography, climate, and inhabitants."

def get_persona_prompt(persona_name: str):
    @task
    async def get_persona_prompt_(world_config: WorldConfig) -> str:
        return f"Create a persona named {persona_name} who lives in the world of {world_config.name}. Include age, background, traits, and goals."
    return get_persona_prompt_

@task
async def get_llm_request(prompt: str) -> str:
    # Simulate an LLM request and return the generated JSON
    # Replace this with your actual LLM request implementation
    sample_json = '''
    {
        "name": "Ethereal Realm",
        "description": "A mystical world filled with enchanted forests and floating islands.",
        "geography": "Lush forests, soaring mountains, and vast oceans dotted with levitating landmasses.",
        "climate": "Temperate with occasional magical storms.",
        "inhabitants": ["Elves", "Fairies", "Wizards", "Talking Animals"],
        "age": 20,
        "background": "Persona background",
        "traits": ["active", "happy"],
        "goals": ["world domination"]
    }
    '''
    return sample_json

@task
def validate_world_json(world_json: str) -> WorldConfig:
    # Parse and validate the generated world JSON using Pydantic
    # Replace this with your actual validation logic
    return WorldConfig.parse_raw(world_json)

@task
def validate_persona_json(persona_json: str) -> PersonaConfig:
    # Parse and validate the generated persona JSON using Pydantic
    # Replace this with your actual validation logic
    return PersonaConfig.parse_raw(persona_json)

# Define the pipeline
pipeline = Pipeline(
    get_world_prompt
    >> get_llm_request
    >> validate_world_json
    >> set_output('world'),
    get_output('world') >> (
        (get_persona_prompt('Bob') >> get_llm_request >> validate_persona_json)
        | (get_persona_prompt('Alice') >> get_llm_request >> validate_persona_json)
        | (get_persona_prompt('Charlie') >> get_llm_request >> validate_persona_json)
    )
)

async def main():
    # Execute the pipeline
    world_type = "Fantasy"
    try:
        results = await pipeline(world_type)
        world = results[0]
        personas = results[1]

        print(f"Generated World: {world}")
        for persona in personas:
            print(f"Generated Persona: {persona}")
    except Exception as e:
        print(f"Error generating world and personas: {e}")

if __name__ == "__main__":
    asyncio.run(main())
