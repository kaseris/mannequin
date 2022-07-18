import json
import os

from typing import List

with open('conf.json', 'r') as f:
    data = json.load(f)

PATTERN_DATABASE_DIR = data['pattern_db']
VALID_CATEGORIES = list(data['categories'])
CHOICES = data['pattern_available_choices']
EDITABLE_REGIONS = data['editable_regions']


def infer_pattern_category(path_to_pattern: str) -> str:
    for cat in VALID_CATEGORIES:
        if cat in path_to_pattern:
            return cat
    return None


def get_available_choices(cat: str) -> List[str]:
    return CHOICES[cat]


def select_region(pattern: str) -> List[str]:
    return EDITABLE_REGIONS[pattern]


if __name__ == '__main__':
    subdirs = os.listdir(PATTERN_DATABASE_DIR)
    retrieved_pattern = '/home/aboumpakis/Desktop/EKETA_python/Mannequin/shape context/python/database/dress/d1/6446'
    # retrieved_pattern = '/home/aboumpakis/Desktop/EKETA_python/Mannequin/shape context/python/database/blouse/b2/5456'
    cat = infer_pattern_category(retrieved_pattern)
    choices = get_available_choices(cat)
    print(f'Avaialable choices for {cat}: {choices}')
    regions = select_region(choices[3])
    print(f'you can edit the following regions: {regions}')
