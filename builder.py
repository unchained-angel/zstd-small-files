import pathlib

# 1. The Registry Code
registry_code = '''import json
import pathlib
import re

class Registry:
    def __init__(self, path="registry.json"):
        self.path = pathlib.Path(path)
        self.data = {}
        self.load()

    def load(self):
        if self.path.exists():
            self.data = json.loads(self.path.read_text())

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2) + "\\n")

    def get_filename(self, dict_id):
        return self.data.get(str(dict_id))

    def register(self, dict_id, filename):
        self.data[str(dict_id)] = filename
        self.save()

    def get_latest_file(self):
        if not self.data: return None
        def version_key(f):
            match = re.search(r"_v(\\d+)\\.bin$", f)
            return int(match.group(1)) if match else -1
        return sorted(self.data.values(), key=version_key)[-1]
        
    def get_latest_id(self):
        if not self.data: return None
        def version_key(item):
            match = re.search(r"_v(\\d+)\\.bin$", item[1])
            return int(match.group(1)) if match else -1
        return max(self.data.items(), key=version_key)[0]

    def has_id(self, dict_id):
        return str(dict_id) in self.data
'''

# 2. The Compressor Code
compressor_code = '''import pathlib
import zstandard as zstd
from .registry import Registry

class Compressor:
    def __init__(self, registry_path="registry.json"):
        self.registry = Registry(registry_path)
        self._dict_cache = {}

    def _load_dict(self, dict_id):
        if dict_id not in self._dict_cache:
            filename = self.registry.get_filename(dict_id)
            if not filename:
                raise ValueError(f"Dictionary ID {dict_id} not found in registry.")
            self._dict_cache[dict_id] = zstd.ZstdCompressionDict(pathlib.Path(filename).read_bytes())
        return self._dict_cache[dict_id]

    def compress(self, data, level=3):
        """Compresses data using the latest dictionary in the registry."""
        dict_id = self.registry.get_latest_id()
        if not dict_id:
            raise RuntimeError("No dictionaries found in registry.")
            
        d = self._load_dict(dict_id)
        cctx = zstd.ZstdCompressor(level=level, dict_data=d)
        return cctx.compress(data)

    def decompress(self, data):
        """Decompresses data by reading the Dictionary ID from the zstd frame."""
        params = zstd.get_frame_parameters(data)
        dict_id = params.dict_id
        
        if dict_id == 0:
            # Vanilla fallback
            dctx = zstd.ZstdDecompressor()
        else:
            d = self._load_dict(dict_id)
            dctx = zstd.ZstdDecompressor(dict_data=d)
            
        return dctx.decompress(data)
'''

# 3. The Init Code
init_code = '''from .registry import Registry
from .compressor import Compressor

__all__ = ["Registry", "Compressor"]
'''

# Build the files
pathlib.Path("zstd_dict_tools/registry.py").write_text(registry_code)
pathlib.Path("zstd_dict_tools/compressor.py").write_text(compressor_code)
pathlib.Path("zstd_dict_tools/__init__.py").write_text(init_code)
print("Library files built successfully!")
