import aiohttp
import asyncio
import pydantic
import re
import os
from typing import List
from pipelines import task, Pipeline, set_output, get_output
from common import save_pydantic, load_pydantic_or_none, WorldConfig, ValidationError, schema_to_prompt, post_message_to_anthropic_cached, PersonaConfig
from personas.llm_methods import post_message_to_anthropic
from pathlib import Path

emotions = {
    "happy": "44ba1d0d-6948-4676-8f3d-2df7d531a1ab",
    "shocked": "ab7ade2b28b247e98223a90275d32da1"
}

personas = {
    #"Dystopia_Lila Nakamura": "83d7fddf98434ed2985655a0a020b1bf",
    #"Dystopia_Liam Hawkins": "af7979bd0ac846528a168717c7d4e9ac",
    "Neotopia_Zara Xander": "422cf62d05364ccdb3e880e40ca33127",
    "Neotopia_Aria Vance": "48e6a5095093445c85c1cdc80115d780",
    "Neotopia_Lyra Solaris": "8ada7ba66f0c4971a715e9490d3f43a6",
    "Utopia_Zephyr": "60790fcbd82a4d86a4f0710be4ddaba5",
    "Utopia_Lumina": "abd94c190be04c529f4eb5149dcc2607",
    "Dystopia_Liam Hawkins": "af7979bd0ac846528a168717c7d4e9ac"
}
worlds = {
    "Utopia": "d57d772e39cd4dc09699743803ca3e51",
    "Neotopia": "895d89c8247d4cc0bbf94d078473e271",
    "Dystopia": "0d61620e4935416c9e53801e714f1b00"
}

@task
async def load_world_and_persona(world_name, world_uuid, persona_name, persona_uuid):
    world = load_pydantic_or_none(WorldConfig, world_name+".json")
    assert world != None, f"world {world_name} not found"
    persona = load_pydantic_or_none(PersonaConfig, world_name + "_" + persona_name+".json")
    assert persona != None, f"persona {persona_name} not found"
    return (world, persona, world_uuid, persona_uuid)

async def generate_image(prompt, sliders, seed):
    url = "https://sliders.ntcai.xyz/sliders/api/image-generations"
    headers = {"Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "sliders": sliders,
        "options": {"seed": seed}
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                return await response.json()  # Decode JSON response
        except aiohttp.ClientError as e:
            print('e', e)
            # Log the exception e here if needed
            return None

async def fetch_image_details(uuid: str):
    url = f"https://sliders.ntcai.xyz/sliders/api/image-generations/{uuid}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                return await response.json()  # Decode JSON response
        except aiohttp.ClientError as e:
            # Log the exception e here if needed
            return None


async def wait_for_completion_and_fetch_details(uuid: str, retry_interval: int = 5):
    """Wait for the image generation to complete and then fetch the image details."""
    while True:
        image_details = await fetch_image_details(uuid)
        if image_details and image_details.get("status") == "completed":
            return image_details
        elif image_details and image_details.get("status") == "failed":
            print("Image generation failed.")
            return None
        else:
            # Wait before trying again
            await asyncio.sleep(retry_interval)

async def download_and_save_image(s3_key: str, i: int, j: int, persona_name: str, world_name: str):
    # URL to download the image from - replace this with the actual URL pattern if different
    image_url = f"https://mlqueue-imgen.s3.us-west-004.backblazeb2.com/{s3_key}"
    # Determine the file's destination path
    dirname = os.path.dirname(__file__)
    target_dir = Path(dirname) / ".."/"assets" / world_name / persona_name
    target_dir.mkdir(parents=True, exist_ok=True)  # Create the directory structure if it doesn't exist
    file_path = target_dir / f"happy_{i}_shocked_{j}.png"

    # Begin the download
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status == 200:
                # Write the image to a file
                with open(file_path, "wb") as f:
                    while True:  # Read the response in chunks
                        chunk = await response.content.read(1024)  # Adjust chunk size as needed
                        if not chunk:
                            break
                        f.write(chunk)
                print(f"Image saved to {file_path}")
            else:
                print("Failed to download the image.")


def check_if_image_exists(i: int, j: int, persona_name: str, world_name: str) -> bool:
    # Determine the file's expected path
    dirname = os.path.dirname(__file__)
    target_dir = Path(dirname) / ".." / "assets" / world_name / persona_name
    file_path = target_dir / f"happy_{i}_shocked_{j}.png"

    # Check if the file exists
    return file_path.exists()


async def process_coordinates(i, j, persona, world, emotions, persona_uuid, prompt, seed, semaphore):
	async with semaphore:

		if check_if_image_exists(i, j, persona.name, world.name):
			print("Skipping", i, j, persona.name, world.name)
			return
		sliders = [
			{"uuid": emotions["happy"], "strength": (i / 10) * 0.85},
			{"uuid": emotions["shocked"], "strength": (j / 10) * 0.7},
			{"uuid": persona_uuid, "strength": 0.8},
		]
		print("generate", world.name, persona.name, i, j)
		image_generation_response = await generate_image(prompt, sliders, seed)
		if image_generation_response:
			image_generation_uuid = image_generation_response.get("image_generation_uuid")
			if image_generation_uuid:
				image_details = await wait_for_completion_and_fetch_details(image_generation_uuid)
				if image_details and "image_s3_key" in image_details:
					await download_and_save_image(image_details["image_s3_key"], i, j, persona.name, world.name)
				else:
					print("Failed to fetch image details after completion.")
			else:
				print("Image generation didn't provide a UUID.")
		else:
			print("Failed to generate image.", image_generation_response)

@task
async def generate_expressions(world, persona, world_uuid, persona_uuid):
    prompt = "headshot photo"
    seed = 42

    semaphore = asyncio.Semaphore(5)  # Adjust the number as needed
    tasks = [process_coordinates(i, j, persona, world, emotions, persona_uuid, prompt, seed, semaphore)
             for i in range(10, -11, -1) for j in range(10, -11, -1)]
    await asyncio.gather(*tasks)


@task
async def render_world(*args):
    return None

# Define the pipeline
pipeline = Pipeline(
    load_world_and_persona >> ( generate_expressions | render_world )
)

async def main():
    # Loop through the personas dictionary
    for full_persona, persona_uuid in personas.items():
        # Split the key to extract the world name and persona name
        world_persona_split = full_persona.split("_")
        world_name = world_persona_split[0]
        persona_name = "_".join(world_persona_split[1:])  # In case persona names also contain underscores

        # Look up the world_uuid using the world name
        world_uuid = worlds.get(world_name)

        # Call the pipeline function with the required arguments
        await pipeline(world_name, world_uuid, persona_name, persona_uuid)

if __name__ == "__main__":
    asyncio.run(main())
