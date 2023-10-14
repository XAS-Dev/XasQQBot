from typing import TypeVar
from pathlib import Path
import json

_T_JSON = TypeVar("_T_JSON", dict, list, str, int, bool, None)


class JsonDataKeeper:
    def __init__(self, path: Path | str, data: _T_JSON = None):
        self.path = Path(path)
        self.data = data
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.save()
        self.load()

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f)

    def load(self):
        with open(self.path) as f:
            self.data = json.load(f)


githubOpenGraphMessages = JsonDataKeeper("./data/github_open_graph_messages.json", [])
