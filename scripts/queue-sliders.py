import asyncio
import pydantic
import os
import aiohttp
import re
import json
import shelve
from typing import List
from pipelines import task, Pipeline
from personas.llm_methods import post_message_to_anthropic

CACHE_FILENAME = "anthropic_cache2.db"

async def post_message_to_anthropic_cached(prompt, system=None):
    cache_filepath = os.path.abspath(CACHE_FILENAME)  # Get absolute path for reliability
    with shelve.open(cache_filepath) as cache:  # Open the cache as a database-like object
        if prompt in cache:
            return cache[prompt]
        else:
            response_data = await post_message_to_anthropic(prompt, system=system)  # Call the Anthropic API
            cache[prompt] = response_data
            return response_data


# Define the schema for your candidates
class Candidate(pydantic.BaseModel):
    positive: str
    negative: str

# **Tasks**
class PendingException(Exception):
    pass

@task
async def insert_samples(prompt):
    url = "https://sliders.ntcai.xyz/sliders/random_sliders"

    try:
        # Asynchronously send our ship to fetch the data
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Ensure our ship returned successfully
                if response.status != 200:
                    raise Exception(f"Failed to fetch data: HTTP Status {response.status}")

                # Unload our treasures
                data = await response.json()

                # Process the treasures into the desired format
                results = [
                    {
                        "positive": item["data"]["prompts"][0]["positive"],
                        "negative": item["data"]["prompts"][0].get("negative", "")
                    } for item in data
                ]

                # Replace "SAMPLES" in our prompt with the structured data
                modified_prompt = prompt.replace("SAMPLES", json.dumps(results))
                print('--', modified_prompt)
                return modified_prompt

    except aiohttp.ClientError as e:
        # Handle storms by raising an exception
        raise Exception(f"Network error occurred: {e}")


@task
async def check_api_metrics(prompt) -> str:
    """Queries the metrics endpoint and raises an exception if tasks are pending."""
    url = "https://sliders.ntcai.xyz/admin/metrics"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()  # Check for API success
                data = await response.json()
                if data["pending"] and "sliders-train" in data["pending"]:  # Check if 'pending' is not empty 
                    print("Pending tasks", data["pending"])
                    raise PendingException("API has pending tasks.")
                return prompt

        except aiohttp.ClientError as e:
            print(f"Error checking API metrics: {e}")
            raise  # Re-raise the exception 

@task  # Assuming you have a task framework like 'pipelines'
async def generate_candidates(prompt: str) -> str:  # Returns raw JSON strings
    """Queries the LLM for candidate solutions, tailored to your prompt."""
    system = "You are an AI artist AI. You work with text-to-image AIs like stable diffusion and bring brilliant ideas to life. Your main job right now is training LoRA 'sliders' using innovative positives and negatives."
    response_data = await post_message_to_anthropic(prompt, system=system) 
    content = response_data['content'][0]['text']
    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if json_match:
        json_string = json_match.group(1)
        return json_string
    else:
        print("--", content)
        raise LLMResponseInvalid()

@task
async def parse_candidates(raw_candidates: str) -> List[Candidate]:
    """Parses raw JSON strings into validated Candidate objects."""
    candidates_data = json.loads(raw_candidates)  # Load JSON into a list/dictionary structure
    parsed_candidates = []
    for candidate_data in candidates_data:  # Iterate over candidates in the list/dictionary
        try:
            candidate = Candidate(**candidate_data)  # Create Candidate object
            parsed_candidates.append(candidate)
        except pydantic.ValidationError as e:
            raise e

    return parsed_candidates

@task
async def filter_existing(*candidates: List[Candidate]) -> List[Candidate]:
    """Removes candidates that already exist in your storage."""
    filtered_candidates = []
    async with aiohttp.ClientSession() as session:
        for candidate in candidates:
            url = f"https://sliders.ntcai.xyz/sliders/search?positive={candidate.positive}&negative={candidate.negative}"

            try:
                async with session.get(url) as response:
                    if response.status == 404:
                        filtered_candidates.append(candidate)  # Keep if not found
                    # else: (Implicitly means it exists, so we discard it)

            except aiohttp.ClientError as e:
                print(f"Error checking candidate existence: {e}")
                # You might want to handle these errors differently

    return filtered_candidates

@task
async def queue_candidates(*candidates: List[Candidate]) -> None:
    """Adds candidates to the queue with API calls."""
    url = "https://sliders.ntcai.xyz/sliders/train"
    headers = {"Content-Type": "application/json"}

    async with aiohttp.ClientSession(headers=headers) as session:
        for candidate in candidates:
            payload = {
                "name": f"{candidate.negative}→{candidate.positive}", 
                "prompts": [
                    {
                        "target": "",
                        "positive": candidate.positive, 
                        "negative": candidate.negative,
                        "unconditional": "",
                        "neutral": "",
                        "action": "enhance",
                        "alpha": 1,
                        "rank": 4,
                        "attributes": "woman, man, bright, dim, cartoon, photo, anime" 
                    }
                ],
                "resolution": 512,
                "batch_size": 10,
                "steps": 600
            }

            try:
                print("Calling", url, json.dumps(payload))
                async with session.post(url, data=json.dumps(payload)) as response:
                    response.raise_for_status()  # Check for successful API response 
                    print(f"Candidate queued: {candidate}")

            except aiohttp.ClientError as e:
                print(f"Error queueing candidate: {candidate} - Error: {e}")

@task
async def log_prompt(prompt: str) -> str:
    print("--", prompt)
    return prompt
# **Pipeline Definition**
candidate_pipeline = Pipeline(
    check_api_metrics >> insert_samples >> log_prompt >> generate_candidates >> parse_candidates >> filter_existing >> queue_candidates
    #insert_samples >> generate_candidates >> log_prompt
)

# **Main Function**
async def main():
    your_initial_prompt = """
Create a list of 10 slider candidates. Each candidate will be trained and released as a stable diffusion slider LoRA - trained on only the clip embeddings of the negative and positive terms using a self-play game.

Here's some examples:

```json
SAMPLES
```

Make your candidates diverse and awesome. Good ideas are things like clothing, emotion, expression, style, or even persona descriptions of novel characters and places. Note that during training one of the following words are prepended to each training step: `woman, man, bright, dim, cartoon, photo, anime`.
Avoid themes that we already have - make the list unique, useful for artists, engaging, attention grabbing, and generally creative and interesting. Each of these suggestions will turn into a trained sliders LoRA.
Write the results in a JSON block wrapped with this markdown tag "```json". Have fun too, thanks in advance!
"""

    try:
        await candidate_pipeline(your_initial_prompt)
    except Exception as e:
        print(f"Error during candidate generation: {e}")

if __name__ == "__main__":
    asyncio.run(main())

