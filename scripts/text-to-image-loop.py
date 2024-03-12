
from PIL import Image
import io
import base64
import requests
import json
import asyncio
from pydantic import BaseModel, Field
from typing import List
from pipelines import task, Pipeline, set_output, get_output
import torch
from transformers import AutoModelForCausalLM
from datetime import datetime
import random
import string


from datetime import datetime
import random
import string

from deepseek_vl.models import VLChatProcessor, MultiModalityCausalLM
from deepseek_vl.utils.io import load_pil_images

txt2imgurl = "http://localhost:7777/sdapi/v1/txt2img"


def random_fname():
    # Generate a random string of letters and digits
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    # Current timestamp for uniqueness
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    # Combine them to form a filename
    return f"images/{random_string}_{timestamp}.png"

def generate_image(prompt, negative_prompt, lora):
    seed = random.SystemRandom().randint(0, 2**32-1)
    url = txt2imgurl
    headers = {"Content-Type": "application/json"}
    prompt_ = prompt.replace("LORAVALUE",  "{:.14f}".format(lora))
    nprompt_ = negative_prompt.replace("LORAVALUE",  "{:.14f}".format(lora))
    uid = prompt_+"_"+negative_prompt+"_"+str(seed)+"_"+"{:.14f}".format(lora)

    data = {
        "seed": seed,
        "width": 1024,
        "height": 1024,
        "sampler_name": "Euler a",
        "prompt": prompt_,
        "negative_prompt": nprompt_,
        "cfg_scale": 1.0,
        "steps": 14
    }
    print(" calling: ", prompt_)
    print(url)

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        r = response.json()
        image = Image.open(io.BytesIO(base64.b64decode(r['images'][0].split(",",1)[0])))
        fname= random_fname()
        image.save(fname)
        return fname

    else:
        print(f"Request failed with status code {response.status_code}")
        return generate_image(prompt, negative_prompt, lora)

@task
async def generate_comparison(image, imageprompt, vlmquestion):
    A = image
    B = generate_image(imageprompt, "", 0)
    while True:
        r = get_vlm_request(vlmquestion, [A,B])
        if r.strip().startswith("A"):
            return A
        if r.strip().startswith("B"):
            return B
        print("Trying again...")

# specify the path to the model
model_path = "deepseek-ai/deepseek-vl-7b-chat"
vl_chat_processor: VLChatProcessor = VLChatProcessor.from_pretrained(model_path)
tokenizer = vl_chat_processor.tokenizer

vl_gpt: MultiModalityCausalLM = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
vl_gpt = vl_gpt.to(torch.bfloat16).cuda().eval()

def get_vlm_request(prompt: str, images) -> str:

    print("IMAGES: ", images)
    conversation = [
        {
            "role": "User",
            "content": "A.<image_placeholder> B.<image_placeholder>"+prompt,
            "images": images
        },
        {
            "role": "Assistant",
            "content": ""
        }
    ]

    # load images and prepare for inputs
    pil_images = load_pil_images(conversation)
    prepare_inputs = vl_chat_processor(
        conversations=conversation,
        images=pil_images,
        force_batchify=True
    ).to(vl_gpt.device)

    # run image encoder to get the image embeddings
    inputs_embeds = vl_gpt.prepare_inputs_embeds(**prepare_inputs)

    # run the model to get the response
    outputs = vl_gpt.language_model.generate(
        inputs_embeds=inputs_embeds,
        attention_mask=prepare_inputs.attention_mask,
        pad_token_id=tokenizer.eos_token_id,
        bos_token_id=tokenizer.bos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        max_new_tokens=512,
        do_sample=False,
        use_cache=True
    )

    answer = tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
    print(f"{prepare_inputs['sft_format'][0]}", answer)
    return answer


# Define the pipeline
pipeline = Pipeline(
    generate_comparison
)
#pipeline = (gen_image(name1) | gen_image(name2)) >> vlmChooseBest >> train_lora(name) >> eval_lora(name) >> add_to_personas()

async def main():
    # Execute the pipeline
    vlmquestion = "Which image is the darkest? Answer A or B only."
    imageprompt = "__sdprompt__"
    A = generate_image(imageprompt, "", 0)
    try:
        while True:
            A = await pipeline(A, imageprompt, vlmquestion)
            print("Found ", A)
    except Exception as e:
        print(f"Error generating world and personas: {e}")

if __name__ == "__main__":
    asyncio.run(main())
