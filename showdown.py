import pathlib
import zstandard as zstd
import brotli
import time

samples = [p.read_bytes() for p in pathlib.Path('samples_real').iterdir() if p.is_file()]
orig = sum(len(s) for s in samples)

print(f"Benchmarking {len(samples)} REAL files ({orig} bytes total)...\n")
print(f"{'Algorithm':<20} | {'Size':>8} | {'Savings':>8} | {'Time':>8}")
print("-" * 55)

def bench(name, compress_func):
    start = time.time()
    total_size = 0
    for s in samples:
        total_size += len(compress_func(s))
    elapsed = time.time() - start
    sav = (1 - total_size/orig)*100
    print(f"{name:<20} | {total_size:>6} b | {sav:>6.1f}% | {elapsed:.4f}s")

# 1. Zstd Vanilla
c_zstd = zstd.ZstdCompressor(level=3)
bench("Zstd Vanilla (L3)", c_zstd.compress)

# 2. Zstd Dictionary v5
d5 = zstd.ZstdCompressionDict(pathlib.Path('dictionary_v5.bin').read_bytes())
c_zstd_dict = zstd.ZstdCompressor(level=3, dict_data=d5)
bench("Zstd Dict v5 (L3)", c_zstd_dict.compress)

# 3. Brotli Vanilla (Quality 4 - standard for dynamic APIs)
bench("Brotli Vanilla (Q4)", lambda s: brotli.compress(s, quality=4))

# 4. Brotli Vanilla (Quality 11 - maximum compression, very slow)
bench("Brotli Vanilla (Q11)", lambda s: brotli.compress(s, quality=11))

print("-" * 55)
