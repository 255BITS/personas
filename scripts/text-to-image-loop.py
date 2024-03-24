
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

async def correct_insert_element(item, sorted_list, top_k):
    if not sorted_list:
        return [item]
    # Find a place for insertion
    insert_pos = await find_insertion_point(item, sorted_list)
    # Insert item tentatively
    sorted_list.insert(insert_pos, item)
    # If list is longer than top_k, remove the least element
    #if len(sorted_list) > top_k:
    #    sorted_list.pop()
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

async def sort_with_correction(buffer, top_k):
    sorted_list = []
    for item in buffer:
        sorted_list = await correct_insert_element(item, sorted_list, top_k)
    # Correction mechanism here
    sorted_list = await correction_pass(sorted_list)
    return sorted_list[:top_k], sorted_list[top_k:]

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

async def compare(a,b):
    vlmquestion = "Q:\nIMG1: <image>\nIMG2: <image>\nLook at IMG1 then look at IMG2. Which image is darker?\nA:\n"
    while True:
        print("Call vlm", vlmquestion, a, b)
        r = vlm_call(vlmquestion, ",".join([a,b]))
        print(r)
        if choose_first_occurrence(r, "IMG1", "IMG2")=="IMG1":
            print("1")
            return 1
        if choose_first_occurrence(r, "IMG1", "IMG2") == "IMG2":
            print("2")
            return -1
        print("Retrying ...")

@task
async def generate_comparison(imageprompt, np):
    return generate_image(imageprompt, np, 0)
pipeline = Pipeline(
        generate_comparison
        )

async def main():
    # Execute the pipeline
    p = open("prompt-a.txt", "r").read()
    np = open("nprompt-a.txt", "r").read()
    random_dir = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    os.makedirs("images/"+random_dir, exist_ok=True)
    old = None
    i = 0
    buffer = []
    sorted_list = []
    num_elements = 30
    top_k = 5
    all_elements = []

    while i < num_elements:
        print(i)
        p = open("prompt-a.txt", "r").read()
        np = open("nprompt-a.txt", "r").read()
        A = await pipeline(p, np)
        all_elements.append(A)
        i += 1

    sorted_list, rest = await sort_with_correction(all_elements, top_k)

    for j, img in enumerate(sorted_list):
        dst = "images/"+random_dir+"/topk_sorted_"+str(j)+".png"
        shutil.move(img, dst)
        print(dst)


    for j, img in enumerate(rest):
        dst = "images/"+random_dir+"/not_topk_unsorted_"+str(j)+".png"
        shutil.move(img, dst)
        print(dst)


if __name__ == "__main__":
    asyncio.run(main())
