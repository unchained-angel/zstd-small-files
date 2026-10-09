import pathlib
import zstandard as zstd

LIMIT = 50


def load_dictionary(path):
    p = pathlib.Path(path)
    if not p.exists():
        raise SystemExit(f"Error: dictionary not found: {path}")
    return zstd.ZstdCompressionDict(p.read_bytes())


def make_compressor(dict_data=None):
    if dict_data is None:
        return zstd.ZstdCompressor(level=3)
    return zstd.ZstdCompressor(level=3, dict_data=dict_data)


def make_decompressor(dict_data=None):
    if dict_data is None:
        return zstd.ZstdDecompressor()
    return zstd.ZstdDecompressor(dict_data=dict_data)


def compress(data, dict_data=None):
    return make_compressor(dict_data).compress(data)


def decompress(comp, original_size, dict_data=None):
    # original_size helps if the frame does not store the content size.
    return make_decompressor(dict_data).decompress(
        comp,
        max_output_size=original_size + 1024
    )


def collect_files(directory, limit=LIMIT):
    p = pathlib.Path(directory)
    if not p.exists():
        return []

    files = []
    for f in sorted(p.iterdir()):
        if f.is_file():
            files.append(f)
            if len(files) == limit:
                break
    return files


def savings(original, compressed):
    if original == 0:
        return 0.0
    return (1 - compressed / original) * 100


def benchmark(name, files, dict_v1, dict_v2):
    print()
    print("=" * 60)
    print(name)
    print("=" * 60)

    totals = {
        "original": 0,
        "vanilla": 0,
        "v1": 0,
        "v2": 0,
    }

    for f in files:
        original = f.read_bytes()

        vanilla = compress(original, None)
        v1 = compress(original, dict_v1)
        v2 = compress(original, dict_v2)

        # Verify round-trip correctness
        assert decompress(vanilla, len(original), None) == original
        assert decompress(v1, len(original), dict_v1) == original
        assert decompress(v2, len(original), dict_v2) == original

        totals["original"] += len(original)
        totals["vanilla"] += len(vanilla)
        totals["v1"] += len(v1)
        totals["v2"] += len(v2)

    print(f"files: {len(files)}")
    print(f"original: {totals['original']} bytes")
    print(f"vanilla:  {totals['vanilla']} bytes "
          f"({savings(totals['original'], totals['vanilla']):.1f}% saved)")
    print(f"dict_v1:  {totals['v1']} bytes "
          f"({savings(totals['original'], totals['v1']):.1f}% saved)")
    print(f"dict_v2:  {totals['v2']} bytes "
          f"({savings(totals['original'], totals['v2']):.1f}% saved)")

    if totals["v1"] < totals["v2"]:
        print("Best dictionary for this dataset: dictionary_v1.bin")
    elif totals["v2"] < totals["v1"]:
        print("Best dictionary for this dataset: dictionary_v2.bin")
    else:
        print("dictionary_v1.bin and dictionary_v2.bin tied")


def main():
    dict_v1 = load_dictionary("dictionary_v1.bin")
    dict_v2 = load_dictionary("dictionary_v2.bin")

    old_files = collect_files("samples")
    new_files = collect_files("samples_v2")

    single_old = [pathlib.Path("example.json")]
    single_new = [pathlib.Path("example_v2.json")]

    benchmark("Old sample batch", old_files, dict_v1, dict_v2)
    benchmark("New sample batch", new_files, dict_v1, dict_v2)
    benchmark("Single old example", single_old, dict_v1, dict_v2)
    benchmark("Single new example", single_new, dict_v1, dict_v2)


if __name__ == "__main__":
    main()
