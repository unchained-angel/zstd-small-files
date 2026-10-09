import pathlib
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
