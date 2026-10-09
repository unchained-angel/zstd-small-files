import json
import pathlib
import sys

import zstandard as zstd


REGISTRY_PATH = pathlib.Path("registry.json")


def load_registry():
    if not REGISTRY_PATH.exists():
        return {}

    text = REGISTRY_PATH.read_text()
    return json.loads(text)


def main():
    # Expected:
    # python smart_decompress.py input.zst output.json
    if len(sys.argv) != 3:
        print("Usage: python smart_decompress.py input_file output_file")
        print("Example: python smart_decompress.py example.zst recovered_smart.json")
        sys.exit(1)

    input_path = pathlib.Path(sys.argv[1])
    output_path = pathlib.Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}")
        sys.exit(1)

    compressed_data = input_path.read_bytes()

    # Read the zstd frame header
    params = zstd.get_frame_parameters(compressed_data)
    dictionary_id = params.dict_id

    print(f"Input file: {input_path}")
    print(f"Dictionary ID from frame: {dictionary_id}")

    if dictionary_id == 0:
        # Vanilla zstd fallback
        print("No dictionary required. Using vanilla zstd decompression.")
        decompressor = zstd.ZstdDecompressor()
        dictionary_source = "none"
    else:
        # Dictionary lookup
        registry = load_registry()

        dictionary_file = registry.get(str(dictionary_id))

        if dictionary_file is None:
            print(f"Error: No dictionary registered for ID {dictionary_id}")
            print("Add it to registry.json, for example:")
            print(f'{{"{dictionary_id}": "dictionary.bin"}}')
            sys.exit(1)

        dictionary_path = pathlib.Path(dictionary_file)

        if not dictionary_path.exists():
            print(f"Error: dictionary file not found: {dictionary_path}")
            sys.exit(1)

        dictionary_bytes = dictionary_path.read_bytes()
        dictionary = zstd.ZstdCompressionDict(dictionary_bytes)

        print(f"Using dictionary file: {dictionary_path}")
        decompressor = zstd.ZstdDecompressor(dict_data=dictionary)
        dictionary_source = str(dictionary_path)

    # Decompress
    try:
        recovered_data = decompressor.decompress(compressed_data)
    except Exception as error:
        print("Decompression failed.")
        print(f"Error: {error}")
        sys.exit(1)

    output_path.write_bytes(recovered_data)

    print(f"Recovered output: {output_path}")
    print(f"Compressed size: {len(compressed_data)} bytes")
    print(f"Recovered size: {len(recovered_data)} bytes")
    print(f"Dictionary used: {dictionary_source}")
    print("Decompression successful.")


if __name__ == "__main__":
    main()
