import pathlib
import sys

import zstandard as zstd


def main():
    # The user must provide:
    # python decompress.py input.zst output.json
    if len(sys.argv) != 3:
        print("Usage: python decompress.py input_file output_file")
        print("Example: python decompress.py example.zst recovered.json")
        sys.exit(1)

    input_path = pathlib.Path(sys.argv[1])
    output_path = pathlib.Path(sys.argv[2])
    dictionary_path = pathlib.Path("dictionary.bin")

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}")
        sys.exit(1)

    if not dictionary_path.exists():
        print("Error: dictionary.bin not found.")
        print("Make sure you are inside the project folder.")
        sys.exit(1)

    # Load the trained dictionary into memory
    dictionary_bytes = dictionary_path.read_bytes()
    dictionary = zstd.ZstdCompressionDict(dictionary_bytes)

    # Create a decompressor that uses the dictionary
    decompressor = zstd.ZstdDecompressor(dict_data=dictionary)

    # Read the compressed file
    compressed_data = input_path.read_bytes()

    # Try to decompress it
    try:
        recovered_data = decompressor.decompress(compressed_data)
    except Exception as error:
        print("Decompression failed.")
        print(f"Error: {error}")
        sys.exit(1)

    # Save the recovered JSON
    output_path.write_bytes(recovered_data)

    print(f"Dictionary: {dictionary_path}")
    print(f"Compressed input: {input_path}")
    print(f"Recovered output: {output_path}")
    print(f"Compressed size: {len(compressed_data)} bytes")
    print(f"Recovered size: {len(recovered_data)} bytes")
    print("Decompression successful.")


if __name__ == "__main__":
    main()
