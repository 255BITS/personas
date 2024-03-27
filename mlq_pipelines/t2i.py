import random
import requests
import json
from PIL import Image
import io
import base64

def load_model(name, url=None):
    if url is None:
        with open("txt2img/sdwebui_config.json", 'r') as file:
            data = json.load(file)
        url = data["sd_webui_url"]
    url = url.replace("txt2img", "unload-checkpoint")
    opt = requests.get(url)
    opt_json = opt.json()
    opt_json['sd_model_checkpoint'] = name
    r = requests.post(url=f'{url}/sdapi/v1/options', json=opt_json)
    print("Load Model", r.json())
    assert r.json() == {}

def unload_checkpoint(url=None):
    if url is None:
        with open("txt2img/sdwebui_config.json", 'r') as file:
            data = json.load(file)
        url = data["sd_webui_url"]
    url = url.replace("txt2img", "unload-checkpoint")
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data={})
    print("checkpoint unloaded", response.json())

def reload_checkpoint(url=None):
    if url is None:
        with open("txt2img/sdwebui_config.json", 'r') as file:
            data = json.load(file)
        url = data["sd_webui_url"]
    url = url.replace("txt2img", "reload-checkpoint")
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data={})
    print("checkpoint loaded", response.json())


def text_to_image(p: str, np=""):
    @task
    async def generate_image_() -> str:
        return generate_image(p, np)
    return generate_image_

def generate_image(prompt, negative_prompt, config_file=None, fname=None):
    seed = random.SystemRandom().randint(0, 2**32-1)
    if config_file is None:
        with open("txt2img/sdwebui_config.json", 'r') as file:
            config_file = json.load(file)
    headers = {"Content-Type": "application/json"}
    data = dict(config_file)

    data["prompt"]=prompt
    data["negative_prompt"]=negative_prompt

    data["seed"]=seed
    url = data["sd_webui_url"]
    del data["sd_webui_url"]
    #print(" calling: ", prompt_)
    #print(url)

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        r = response.json()
        image = Image.open(io.BytesIO(base64.b64decode(r['images'][0].split(",",1)[0])))
        if fname is None:
            fname= random_fname()
        image.save(fname)
        return fname

    else:
        print(f"Request failed with status code {response.status_code}")
        return generate_image(prompt, negative_prompt, config_file, fname)
