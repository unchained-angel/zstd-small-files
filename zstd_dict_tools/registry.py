import json
import pathlib
import re
import tempfile
import os

class Registry:
    def __init__(self, path="registry.json"):
        self.path = pathlib.Path(path)
        self.data = {}
        self.load()

    def load(self):
        if self.path.exists():
            self.data = json.loads(self.path.read_text())

    def save(self):
        """Atomic write to prevent corruption on crash."""
        dir_name = self.path.parent or pathlib.Path(".")
        # 1. Create temp file in same directory
        fd, tmp_path = tempfile.mkstemp(dir=dir_name)
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(self.data, f, indent=2)
                f.write("\n")
            # 2. Atomic swap
            os.replace(tmp_path, self.path)
        except Exception:
            os.unlink(tmp_path) # Clean up on failure
            raise

    def get_filename(self, dict_id):
        return self.data.get(str(dict_id))

    def register(self, dict_id, filename):
        self.data[str(dict_id)] = filename
        self.save()

    def get_latest_file(self):
        if not self.data: return None
        def version_key(f):
            match = re.search(r"_v(\d+)\.bin$", f)
            return int(match.group(1)) if match else -1
        return sorted(self.data.values(), key=version_key)[-1]
        
    def get_latest_id(self):
        if not self.data: return None
        def version_key(item):
            match = re.search(r"_v(\d+)\.bin$", item[1])
            return int(match.group(1)) if match else -1
        return max(self.data.items(), key=version_key)[0]

    def has_id(self, dict_id):
        return str(dict_id) in self.data
