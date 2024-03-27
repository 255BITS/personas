
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
import os
import sys
from shutil import move
from PIL import Image

def identity(x):
    @task
    async def identity_():
        return x
    return identity_

async def filter(filename):
    """
    Placeholder filter function.
    Implement your filtering logic here.
    Returns None if the image fails the filter criteria.
    Returns anything else (not None) if the image passes the filter criteria.
    """
    try:
        questions = open("txt2img/qs.txt", "r").read().strip().split("\n")
        pipeline = Pipeline(
                reduce(lambda x, y: x >> filter_vlm(y), questions, identity(filename))
        )

        A = await pipeline()
        return A
    except Exception as e:
        print(traceback.format_exc())

        print(f"Error generating world and personas: {e}")
        return None

async def process_images(directory):
    unload_checkpoint()
    # Paths for 'pass' and 'fail' subdirectories
    pass_dir = os.path.join(directory, 'pass')
    fail_dir = os.path.join(directory, 'fail')

    # Create 'pass' and 'fail' directories if they don't exist
    if not os.path.exists(pass_dir):
        os.makedirs(pass_dir)
    if not os.path.exists(fail_dir):
        os.makedirs(fail_dir)

    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            filepath = os.path.join(directory, filename)
            try:
                if await filter(filepath) is None:
                    print("F MOVE", filepath, os.path.join(fail_dir, filename))
                    # Move to 'fail' directory if filter returns None
                    move(filepath, os.path.join(fail_dir, filename))
                else:
                    print("P MOVE", filepath, os.path.join(pass_dir, filename))
                    # Move to 'pass' directory otherwise
                    move(filepath, os.path.join(pass_dir, filename))
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory>")
        sys.exit(1)
    asyncio.run(process_images(sys.argv[1]))

