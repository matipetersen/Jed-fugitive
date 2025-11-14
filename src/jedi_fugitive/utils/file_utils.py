import pickle
from typing import Any

def save_to_file(obj: Any, path: str):
    with open(path, "wb") as f:
        pickle.dump(obj, f)

def load_from_file(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)