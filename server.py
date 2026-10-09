import json
import pathlib
import hashlib
import zstandard as zstd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

app = FastAPI()

reg_path = pathlib.Path("registry.json")
registry = json.loads(reg_path.read_text())

latest_dict_file = sorted(registry.values())[-1]
latest_dict_id = next((k for k, v in registry.items() if v == latest_dict_file), None)
print(f"Server starting with latest dictionary: {latest_dict_file} (ID: {latest_dict_id})")

dict_bytes = pathlib.Path(latest_dict_file).read_bytes()
dict_data = zstd.ZstdCompressionDict(dict_bytes)
cctx = zstd.ZstdCompressor(dict_data=dict_data)

@app.get("/api/data")
def get_mock_json():
    payload = {
        "users": [
            {"id": 1, "name": "Alice", "role": "admin", "status": "active"},
            {"id": 2, "name": "Bob", "role": "editor", "status": "active"},
            {"id": 3, "name": "Charlie", "role": "viewer", "status": "inactive"},
        ],
        "meta": {"page": 1, "total_pages": 10, "timestamp": "2026-10-02T12:00:00Z"},
    }
    json_bytes = json.dumps(payload).encode("utf-8")
    compressed_bytes = cctx.compress(json_bytes)
    return Response(
        content=compressed_bytes,
        media_type="application/zstd",
        headers={
            "X-Dictionary-ID": str(latest_dict_id),
            "X-Original-Size": str(len(json_bytes)),
            "X-Compressed-Size": str(len(compressed_bytes)),
        },
    )

@app.get("/dictionaries/{dict_id}")
def get_dictionary(dict_id: int, request: Request):
    dict_filename = registry.get(str(dict_id))
    if not dict_filename:
        raise HTTPException(status_code=404, detail="Dictionary ID not found")
    
    dict_path = pathlib.Path(dict_filename)
    if not dict_path.exists():
        raise HTTPException(status_code=404, detail="Dictionary file missing")
        
    raw_bytes = dict_path.read_bytes()
    
    # Generate a strong ETag based on the actual file content (SHA-256 hash)
    etag = f'"{hashlib.sha256(raw_bytes).hexdigest()}"'
    
    # If the client already has this exact file, tell them to use their cache
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304) # 304 Not Modified (0 bytes transferred!)
        
    return Response(
        content=raw_bytes,
        media_type="application/octet-stream",
        headers={
            # Tell clients to cache this for 1 year, and that it will never change
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": etag
        }
    )
