import os
import sys
import shutil
import asyncio
from PIL import Image
from .vlm import *
import random
import string
import glob

async def correct_insert_element(item, sorted_list, question):
    if not sorted_list:
        return [item]
    # Find a place for insertion
    insert_pos = await find_insertion_point(item, sorted_list, question)
    # Insert item tentatively
    sorted_list.insert(insert_pos, item)
    return sorted_list

async def find_insertion_point(item, sorted_list, question):
    # Binary search variant that accounts for potential comparison errors
    low, high = 0, len(sorted_list) - 1
    while low <= high:
        mid = (low + high) // 2
        result = await compare(item, sorted_list[mid], question)
        # Adjust binary search based on comparison, considering potential inaccuracies
        if result == 1:
            high = mid - 1
        else:
            low = mid + 1
    return low

async def sort_with_correction(buffer, question=None):
    sorted_list = []
    for item in buffer:
        sorted_list = await correct_insert_element(item, sorted_list, question)
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

async def compare(a, b, question=None):
    if question is None:
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


async def sort_images(indir, outdir, question=None):
    # Execute the pipeline
    os.makedirs(outdir, exist_ok=True)
    all_elements = []
    filenames = os.listdir(indir)
    for filename in filenames:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            filepath = os.path.join(indir, filename)
            all_elements.append(filepath)
    #unload_checkpoint()
    sorted_list = await sort_with_correction(all_elements, question)
    print("Found files", indir, len(all_elements))
    num_digits = len(str(len(sorted_list) - 1))
    for j, img in enumerate(sorted_list):
        filename = img.split("/")[-1].split(".")[0]
        dst = f"{outdir}/{j:0{num_digits}d}_{filename}.png"
        print(dst)
        shutil.move(img, dst)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sort_image_directory.py <directory>")
        sys.exit(1)
    asyncio.run(sort_images(sys.argv[1]))
