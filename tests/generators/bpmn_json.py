import json
from typing import Dict
import random
import numpy as np
import pathlib
import time

MAX_CHILD = 5
MIN_CHILD = 2
IMPACTS_LEN = 3
MAX_TEMPERATURE = 4


def next_region(temperature):
    if temperature >= MAX_TEMPERATURE:
        return "task"

    probability = min(
        0.1 + (temperature / 100), 1.0
    )  # Probabilistic range: starts at 10% and grows with x

    if random.random() < probability:
        # Create a dictionary when the random chance is within the probability
        return "task"
    else:
        # Return None or some other indication when the probability doesn't match
        return np.random.choice(["choice", "parallel", "nature", "sequential"])


def next_region_id():

    def __inner():
        cur_rid = 1
        while True:
            yield cur_rid
            cur_rid += 1

    generator = __inner()
    return next(generator)


def generate_bpmn(depth=0) -> Dict:
    nr = next_region(depth)
    if nr == "task":
        task = {
            "id": next_region_id(),
            "type": "task",
            "impacts": np.random.randint(size=IMPACTS_LEN, high=13, low=1).tolist(),
            "duration": round(random.random() * 5, 1),
        }

        return task

    n_children = random.randint(MIN_CHILD, MAX_CHILD)
    region = {"id": next_region_id(), "type": nr, "children": [None] * n_children}
    if random.random() < 0.07:
        region["duration"] = round(random.random() * 5, 1)

    if nr == "nature":
        arr = np.random.rand(n_children)
        arr /= arr.sum()
        arr = np.round(arr, 2)
        arr[0] -= arr.sum() - 1
        region["distribution"] = arr.tolist()

    for i in range(n_children):
        child_region = generate_bpmn(depth + 1)
        region["children"][i] = child_region

    return region


if __name__ == "__main__":
    new_dir_name = f"generated_{time.time()}"
    dir_path = pathlib.Path(new_dir_name)
    if not dir_path.is_dir():
        dir_path.mkdir()

    n_files = 5
    for i in range(n_files):
        filename = f"{i}.json"
        with open(f"{new_dir_name}/{filename}", "w") as f:
            f.write(json.dumps(generate_bpmn()))
