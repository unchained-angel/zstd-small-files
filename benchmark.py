import json
import random
import zstandard as zstd
import pathlib

# ─── Configuration ───────────────────────────────────────────────
NUM_TEST_FILES = 100
COMPRESSION_LEVEL = 3
MAX_FILE_SIZE = 10 * 1024  # Only test files under 10 KB

# ─── Generate fresh test data ────────────────────────────────────
def generate_test_sample():
    """Generate a new small JSON API response (different from training)."""
    return json.dumps({
        "request_id": f"test_{random.randint(10000, 99999)}",
        "timestamp": "2026-09-19T14:30:00Z",
        "status": random.choice(["success", "pending", "failed", "timeout"]),
        "user": {
            "id": random.randint(1, 10000),
            "role": random.choice(["admin", "user", "guest", "moderator"]),
            "email_verified": random.choice([True, False])
        },
        "payload": {
            "items": [
                {
                    "sku": f"PROD-{random.randint(100, 999)}",
                    "qty": random.randint(1, 20),
                    "price": round(random.uniform(1.0, 500.0), 2)
                }
                for _ in range(random.randint(1, 5))
            ],
            "currency": random.choice(["USD", "EUR", "GBP"])
        }
    }).encode("utf-8")

print(f"Generating {NUM_TEST_FILES} fresh test files...")
test_files = []
for i in range(NUM_TEST_FILES):
    data = generate_test_sample()
    if len(data) < MAX_FILE_SIZE:
        test_files.append(data)

print(f"Kept {len(test_files)} files under {MAX_FILE_SIZE} bytes")

# ─── Load dictionary ─────────────────────────────────────────────
dict_path = pathlib.Path("dictionary.bin")
dict_data = zstd.ZstdCompressionDict(dict_path.read_bytes())

# ─── Set up compressors ──────────────────────────────────────────
vanilla_compressor = zstd.ZstdCompressor(level=COMPRESSION_LEVEL)
dict_compressor = zstd.ZstdCompressor(level=COMPRESSION_LEVEL, dict_data=dict_data)

vanilla_decompressor = zstd.ZstdDecompressor()
dict_decompressor = zstd.ZstdDecompressor(dict_data=dict_data)

# ─── Run benchmark ───────────────────────────────────────────────
total_original = 0
total_vanilla = 0
total_dict = 0

print("\nRunning benchmark...")
print("-" * 60)

for i, original in enumerate(test_files):
    # Compress with vanilla zstd
    compressed_vanilla = vanilla_compressor.compress(original)

    # Compress with dictionary zstd
    compressed_dict = dict_compressor.compress(original)

    # Verify decompression
    assert vanilla_decompressor.decompress(compressed_vanilla) == original
    assert dict_decompressor.decompress(compressed_dict) == original

    total_original += len(original)
    total_vanilla += len(compressed_vanilla)
    total_dict += len(compressed_dict)

# ─── Report results ──────────────────────────────────────────────
vanilla_ratio = total_original / total_vanilla
dict_ratio = total_original / total_dict
improvement = ((total_vanilla - total_dict) / total_vanilla) * 100

print(f"\n{'Metric':<35} {'Vanilla zstd':<15} {'Dictionary zstd':<15}")
print("-" * 65)
print(f"{'Total original size (bytes)':<35} {total_original:<15} {total_original:<15}")
print(f"{'Total compressed size (bytes)':<35} {total_vanilla:<15} {total_dict:<15}")
print(f"{'Compression ratio':<35} {vanilla_ratio:<15.2f} {dict_ratio:<15.2f}")
print(f"{'Space saved vs original (%)':<35} {(1 - total_vanilla/total_original)*100:<15.1f} {(1 - total_dict/total_original)*100:<15.1f}")
print("-" * 65)
print(f"\nDictionary zstd is {improvement:.1f}% smaller than vanilla zstd")
print(f"Average file size: {total_original // len(test_files)} bytes")
