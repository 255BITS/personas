from scripts.llava_util import run_llava
import re
from datetime import datetime
from pipelines import task, Pipeline, set_output, get_output
import random
import requests
import json
import io
import base64
import string
from PIL import Image

file_cache = {}

def load_file_and_return_random_line(file_path):
    global file_cache

    # If the file content is not in cache, load it
    if file_path not in file_cache:
        with open(file_path, 'r') as file:
            file_cache[file_path] = file.read().split('\n')

    # If the file content is empty or only contains '', return None
    if not file_cache[file_path] or file_cache[file_path] == ['']:
        return None

    # Return a random line
    line = random.choice(file_cache[file_path])

    return line

def wildcard_replace(s, directory):
    if directory is None:
        return s
    # Use a regular expression to find all occurrences of '__...__' in the string
    wildcards = re.findall(r'__(.*?)__', s)

    # Load a random line from the file corresponding to each wildcard
    replaced = [load_file_and_return_random_line(directory+"/"+w+".txt") for w in wildcards]

    # Create a dictionary mapping each wildcard to its replacement
    replacements = dict(zip(wildcards, replaced))

    # Replace each occurrence of '__...__' in the string with its corresponding replacement
    for wildcard, replacement in replacements.items():
        s = s.replace('__{}__'.format(wildcard), replacement)

    return s


def random_fname():
    # Generate a random string of letters and digits
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    # Current timestamp for uniqueness
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    # Combine them to form a filename
    return f"images/{random_string}_{timestamp}.png"

def generate_image(prompt, negative_prompt, lora):
    seed = random.SystemRandom().randint(0, 2**32-1)
    with open("sdwebui_config.json", 'r') as file:
        data = json.load(file)
    headers = {"Content-Type": "application/json"}
    prompt_ = prompt.replace("LORAVALUE",  "{:.14f}".format(lora))
    nprompt_ = negative_prompt.replace("LORAVALUE",  "{:.14f}".format(lora))
    uid = prompt_+"_"+negative_prompt+"_"+str(seed)+"_"+"{:.14f}".format(lora)

    data["prompt"]=prompt_
    data["negative_prompt"]=nprompt_

    data["seed"]=seed
    url = data["sd_webui_url"]
    del data["sd_webui_url"]
    #print(" calling: ", prompt_)
    #print(url)

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

def vlm_call(question, img):
    return run_llava("/ml2/trained/vllm/VILA/VILA-13b", "vicuna_v1", question, img)

#from deepseek_vl.models import VLChatProcessor, MultiModalityCausalLM
#from deepseek_vl.utils.io import load_pil_images
def filter_vlm(question: str, reverse=False):
    @task
    async def get_vlm_response_(img) -> str:
        if img is None:
            return None
        r = vlm_call(question, img)
        #r = get_vlm_request("<image_placeholder>"+question, [img])
        if reverse:
            if "Yes" in r:
                print("reverse fail", question)
                return None
            elif "No" in r:
                print("reverse pass", question)
                return img
            else:
                print("reverse cancel", question, r)
                return img
        else:
            if "Yes" in r:
                print("Pass", question)
                return img
            elif "No" in r:
                print("Fail", question)
                return None
            else:
                print("Retry Fail", question, r)
                return None
    return get_vlm_response_

def text_to_image(p: str, np=""):
    @task
    async def generate_image_() -> str:
        return generate_image(p, np, 0)
    return generate_image_
if False:
    # specify the path to the model
    model_path = "deepseek-ai/deepseek-vl-7b-chat"
    vl_chat_processor: VLChatProcessor = VLChatProcessor.from_pretrained(model_path)
    tokenizer = vl_chat_processor.tokenizer

    vl_gpt: MultiModalityCausalLM = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
    vl_gpt = vl_gpt.to(torch.bfloat16).cuda().eval()


