import pathlib
import sys
import zstandard as zstd


def main():
    # Usage:
    # python compress.py input.json output.zst
    # python compress.py input.json output.zst dictionary_v1.bin
    # python compress.py input.json output.zst dictionary_v2.bin

    if len(sys.argv) not in (3, 4):
        print("Usage: python compress.py input_file output_file [dictionary_file]")
        print("Example: python compress.py example.json example.zst dictionary_v1.bin")
        sys.exit(1)

    input_path = pathlib.Path(sys.argv[1])
    output_path = pathlib.Path(sys.argv[2])

    # If no dictionary is provided, default to version 1.
    if len(sys.argv) == 4:
        dictionary_path = pathlib.Path(sys.argv[3])
    else:
        dictionary_path = pathlib.Path("dictionary_v1.bin")

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}")
        sys.exit(1)

    if not dictionary_path.exists():
        print(f"Error: dictionary file not found: {dictionary_path}")
        print("Make sure you are inside the project folder and the dictionary exists.")
        sys.exit(1)

    # Load the chosen dictionary
    dictionary_bytes = dictionary_path.read_bytes()
    dictionary = zstd.ZstdCompressionDict(dictionary_bytes)

    # Create compressor using that dictionary
    compressor = zstd.ZstdCompressor(level=3, dict_data=dictionary)

    # Read original data
    original_data = input_path.read_bytes()

    # Compress
    compressed_data = compressor.compress(original_data)

    # Save compressed output
    output_path.write_bytes(compressed_data)

    # Read back the frame header so we can show the Dictionary ID
    params = zstd.get_frame_parameters(compressed_data)

    print(f"Dictionary file: {dictionary_path}")
    print(f"Dictionary ID written into frame: {params.dict_id}")
    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print(f"Original size: {len(original_data)} bytes")
    print(f"Compressed size: {len(compressed_data)} bytes")

    if len(compressed_data) < len(original_data):
        saved = (1 - len(compressed_data) / len(original_data)) * 100
        print(f"Space saved: {saved:.1f}%")
    else:
        print("Compressed file is not smaller than original.")


if __name__ == "__main__":
    main()
