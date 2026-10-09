import urllib.request
import pathlib
import time

OUT_DIR = pathlib.Path("samples_real")
OUT_DIR.mkdir(exist_ok=True)

# Gather a mix of real public API endpoints
urls = [
    f"https://jsonplaceholder.typicode.com/posts/{i}" for i in range(1, 30)
] + [
    f"https://jsonplaceholder.typicode.com/comments?postId={i}" for i in range(1, 15)
] + [
    f"https://jsonplaceholder.typicode.com/users/{i}" for i in range(1, 11)
] + [
    f"https://jsonplaceholder.typicode.com/todos/{i}" for i in range(1, 30)
]

print(f"Fetching {len(urls)} real API responses from the internet...")

saved_count = 0
for i, url in enumerate(urls):
    try:
        # Add a User-Agent so servers don't block our Python script
        req = urllib.request.Request(url, headers={'User-Agent': 'ZstdProject/1.0'})
        
        with urllib.request.urlopen(req) as response:
            data = response.read()
            
        # Our project constraint: only keep files under 10 KB
        if len(data) < 10 * 1024:
            filename = OUT_DIR / f"real_api_{saved_count}.json"
            filename.write_bytes(data)
            saved_count += 1
            
        # Be polite to the free API
        time.sleep(0.1)
        
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")

print(f"Done! Saved {saved_count} real API samples to {OUT_DIR}/")
