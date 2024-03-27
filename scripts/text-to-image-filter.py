
from PIL import Image
import io
import traceback
import os
import shutil
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
from scripts.vlm import *
from functools import reduce
import random
import string

async def main():
    unload_checkpoint()
    random_dir = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    os.makedirs("images/"+random_dir, exist_ok=True)
    old = None
    i = 0
    try:
        while True:
            p = open("prompt-a.txt", "r").read()
            np = open("nprompt-a.txt", "r").read()
            questions = open("qs.txt", "r").read().strip().split("\n")
            pipeline = Pipeline(
                    reduce(lambda x, y: x >> filter_vlm(y), questions, text_to_image(p, np))
            )

            #A = await pipeline(A, imageprompt, vlmquestion)
            A = await pipeline()
            if A is not None and old != A:
                print("Found ", A)
                old = A
                i+=1
                shutil.copy(A, "images/"+random_dir+"/"+random_dir+"_"+str(i)+".png")
    except Exception as e:
        print(traceback.format_exc())

        print(f"Error generating world and personas: {e}")

if __name__ == "__main__":
    asyncio.run(main())
