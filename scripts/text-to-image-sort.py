
from PIL import Image
import io
import os
import shutil
import base64
import requests
import json
import asyncio
from vlm import *
from pydantic import BaseModel, Field
from typing import List
from pipelines import task, Pipeline, set_output, get_output
import torch
from transformers import AutoModelForCausalLM
from datetime import datetime
import string

import heapq
import time
import random
import glob

async def correct_insert_element(item, sorted_list):
    if not sorted_list:
        return [item]
    # Find a place for insertion
    insert_pos = await find_insertion_point(item, sorted_list)
    # Insert item tentatively
    sorted_list.insert(insert_pos, item)
    return sorted_list

async def find_insertion_point(item, sorted_list):
    # Binary search variant that accounts for potential comparison errors
    low, high = 0, len(sorted_list) - 1
    while low <= high:
        mid = (low + high) // 2
        result = await compare(item, sorted_list[mid])
        # Adjust binary search based on comparison, considering potential inaccuracies
        if result == 1:
            high = mid - 1
        else:
            low = mid + 1
    return low

async def sort_with_correction(buffer):
    sorted_list = []
    for item in buffer:
        sorted_list = await correct_insert_element(item, sorted_list)
    # Correction mechanism here
    sorted_list = await correction_pass(sorted_list)
    return sorted_list

async def correction_pass(sorted_list):
    # Implement a correction pass, potentially re-comparing elements
    # This could involve heuristic-based swaps or reinsertions
    return sorted_list

def choose_first_occurrence(s, opta, optb):
    # Find the index of A and B
    index_a = s.find(opta)
    index_b = s.find(optb)

    # Check if both A and B are found
    if index_a != -1 and index_b != -1:
        # Return the one that occurs first
        if index_a < index_b:
            return opta
        else:
            return optb
    elif index_a != -1:
        # Only A is found
        return opta
    elif index_b != -1:
        # Only B is found
        return optb
    else:
        # Neither A nor B is found
        return None

async def compare(a, b):
    question = open("txt2img/q.txt", "r").read().strip()
    vlmquestion = f"Q: <image> <image>\n{question}\nA: "
    rag = [a, b]
    random.shuffle(rag)
    while True:
        print("Call vlm", vlmquestion, rag)
        r = vlm_call(vlmquestion, ",".join(rag))
        print("choose focc", r)
        if choose_first_occurrence(r, "first", "second") == "first" or choose_first_occurrence(r, "1st", "2nd") == "1st":
            print("1")
            if a == rag[0]:
                return 1
            else:
                return -1
        if choose_first_occurrence(r, "first", "second") == "second" or choose_first_occurrence(r, "1st", "2nd") == "2nd":
            print("2")
            if a == rag[0]:
                return -1
            else:
                return 1
        print("Retrying ...")

@task
async def generate_comparison(imageprompt, np):
    return generate_image(imageprompt, np, 0)
pipeline = Pipeline(
        generate_comparison
        )

async def main():
    # Execute the pipeline
    random_dir = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    os.makedirs("images/"+random_dir, exist_ok=True)
    old = None
    i = 0
    buffer = []
    sorted_list = []
    num_elements = 128
    all_elements = []

    #unload_checkpoint()
    #load_model("XL/mario/toprated1.safetensors")
    reload_checkpoint()
    while i < num_elements:
        print(i)
        pattern = "txt2img/prompt-*"
        files_matching = glob.glob(pattern)

        # Choose a random file from the matched files
        random_file = random.choice(files_matching) if files_matching else None
        p = open(random_file, "r").read()
        np = open("txt2img/nprompt-a.txt", "r").read()
        #if i % 2 == 0:
        #    p = "blank black background"
        #    np = "people, interesting, colors"
        A = await pipeline(p, np)
        all_elements.append(A)
        i += 1
    unload_checkpoint()

    sorted_list = await sort_with_correction(all_elements)

    num_digits = len(str(num_elements - 1))

    for j, img in enumerate(sorted_list):
        dst = f"images/{random_dir}/{random_dir}_{j:0{num_digits}d}.png"
        print(dst)
        shutil.move(img, dst)

if __name__ == "__main__":
    asyncio.run(main())
