import urllib.request
import pathlib
import time

def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers={'User-Agent': 'ZstdProject/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()

def fetch_many(urls, out_dir):
    out = pathlib.Path(out_dir)
    out.mkdir(exist_ok=True)
    saved = 0
    for url in urls:
        try:
            data = fetch(url)
            if len(data) < 10 * 1024:   # keep the under-10KB constraint
                (out / f"sample_{saved}.json").write_bytes(data)
                saved += 1
            time.sleep(0.1)             # be polite to the free API
        except Exception as e:
            print(f"  failed: {url} -> {e}")
    print(f"  saved {saved} files to {out}/")
    return saved

# TRAIN: posts + todos
train_urls = [f"https://jsonplaceholder.typicode.com/posts/{i}" for i in range(1, 51)] + \
             [f"https://jsonplaceholder.typicode.com/todos/{i}" for i in range(1, 51)]

# TEST (disjoint): comments + users + albums
test_urls  = [f"https://jsonplaceholder.typicode.com/comments/{i}" for i in range(1, 31)] + \
             [f"https://jsonplaceholder.typicode.com/users/{i}" for i in range(1, 11)] + \
             [f"https://jsonplaceholder.typicode.com/albums/{i}" for i in range(1, 21)]

print("Fetching TRAIN set (posts + todos)...")
fetch_many(train_urls, "samples_train")
print("Fetching TEST set (comments + users + albums)...")
fetch_many(test_urls, "samples_test")
