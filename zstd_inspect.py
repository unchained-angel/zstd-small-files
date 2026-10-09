import sys
import pathlib
import zstandard as zstd

def main():
    if len(sys.argv) != 2:
        print("Usage: python inspect.py file.zst")
        sys.exit(1)

    file_path = pathlib.Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"Error: {file_path} not found.")
        sys.exit(1)

    # Read the raw compressed bytes
    data = file_path.read_bytes()

    # Ask zstd to read the frame header parameters
    params = zstd.get_frame_parameters(data)

    print(f"File: {file_path}")
    print(f"Window size: {params.window_size} bytes")
    print(f"Dictionary ID: {params.dict_id}")

    if params.dict_id == 0:
        print("-> This file was compressed WITHOUT a dictionary (Vanilla zstd).")
    else:
        print(f"-> This file REQUIRES dictionary ID: {params.dict_id}")

if __name__ == "__main__":
    main()
