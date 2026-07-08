"""
Incremental crawler: crawl hot songs for singers in list.txt,
auto-dedup, checkpoint, concurrent where safe, import to Django DB.

Usage: python crawl_hot_songs.py
Set env NETEASE_COOKIES for authenticated requests (faster, less rate-limiting).
"""
import os, sys, json, time, random, re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix Windows GBK console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django; django.setup()

import requests
from fake_useragent import UserAgent

ua = UserAgent()
# Try to load cookies from original crawler
_COOKIE_FILE = os.path.join(os.path.dirname(__file__), ".env")
_COOKIES = os.environ.get("NETEASE_COOKIES", "")
if not _COOKIES and os.path.exists(_COOKIE_FILE):
    with open(_COOKIE_FILE) as f:
        for line in f:
            if line.startswith("NETEASE_COOKIES="):
                _COOKIES = line.strip().split("=", 1)[1]
                break
COOKIES = _COOKIES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_FILE = os.path.join(BASE_DIR, "list.txt")
CHECKPOINT_FILE = os.path.join(BASE_DIR, "data", "crawl_checkpoint.json")
IMG_DIR = os.path.join(BASE_DIR, "data", "images")
os.makedirs(IMG_DIR, exist_ok=True)

# ── NetEase API ──

def _headers():
    h = {"User-Agent": ua.random, "Referer": "https://music.163.com/"}
    if COOKIES:
        h["Cookie"] = COOKIES
    return h

def fetch(url, max_retries=5):
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=_headers(), timeout=(5, 15))
            r.encoding = "UTF-8"
            return r.text
        except Exception as e:
            t = random.uniform(2, 6)
            print(f"  [retry {attempt+1}/{max_retries}] {str(e)[:80]}")
            time.sleep(t)
    raise Exception(f"Failed: {url}")

def fetch_image(url, max_retries=4):
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=_headers(), timeout=(5, 20))
            return r.content
        except Exception as e:
            time.sleep(random.uniform(1, 4))
    return None

# ── Checkpoint ──

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"done_singers": {}, "song_data": {}, "new_singers": {}, "imported_songs": []}

def safe_print(*args, **kwargs):
    """Print without crashing on Windows GBK encoding."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        print(*(str(a).encode('ascii', errors='replace').decode('ascii') for a in args), **kwargs)

def save_checkpoint(cp):
    tmp = CHECKPOINT_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cp, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CHECKPOINT_FILE)

# ── DB helpers ──

_EXISTING_SONG_NIDS = None
_EXISTING_SINGER_NIDS = None

def get_existing_song_nids():
    global _EXISTING_SONG_NIDS
    if _EXISTING_SONG_NIDS is None:
        from web.models import Song
        _EXISTING_SONG_NIDS = set()
        for s in Song.objects.only("source_url").iterator():
            m = re.search(r"id=(\d+)", s.source_url)
            if m:
                _EXISTING_SONG_NIDS.add(int(m.group(1)))
    return _EXISTING_SONG_NIDS

def get_existing_singer_map():
    """Returns {netease_id: django_id} for all existing singers."""
    global _EXISTING_SINGER_NIDS
    if _EXISTING_SINGER_NIDS is None:
        from web.models import Singer
        _EXISTING_SINGER_NIDS = {}
        for s in Singer.objects.only("source_url", "id").iterator():
            m = re.search(r"id=(\d+)", s.source_url)
            if m:
                _EXISTING_SINGER_NIDS[int(m.group(1))] = s.id
    return _EXISTING_SINGER_NIDS

# ── Main crawl logic ──

def main():
    from web.models import Singer, Song
    from django.db.models import Max

    cp = load_checkpoint()
    existing_songs = get_existing_song_nids()
    existing_singers = get_existing_singer_map()

    print(f"DB: {len(existing_songs)} songs, {len(existing_singers)} singers")
    print(f"Checkpoint: {len(cp['done_singers'])} singers done, {len(cp['song_data'])} songs queued")

    # Read target singers
    with open(LIST_FILE, "r") as f:
        target_ids = [line.strip() for line in f if line.strip()]
    print(f"Target: {len(target_ids)} singers from list.txt\n")

    # ── Phase 1: Collect hot songs per singer ──
    for sid_str in target_ids:
        if sid_str in cp["done_singers"]:
            continue
        sid = int(sid_str)
        name, songs = _crawl_singer(sid)
        if songs is None:
            continue
        for s in songs:
            snid = s["id"]
            if snid not in existing_songs and str(snid) not in cp["song_data"]:
                cp["song_data"][str(snid)] = {
                    "name": s["name"],
                    "artists": [(a["id"], a["name"]) for a in s.get("artists", [])],
                    "pic": s.get("album", {}).get("picUrl", ""),
                }
        cp["done_singers"][sid_str] = True
        save_checkpoint(cp)

    if not cp["song_data"]:
        print("No new songs found!")
        return

    print(f"\nTotal new songs: {len(cp['song_data'])}")

    # ── Phase 2: Collect new singer IDs ──
    new_singer_ids = set()
    for snid, info in cp["song_data"].items():
        for a_nid, a_name in info.get("artists", []):
            if a_nid not in existing_singers and str(a_nid) not in cp["new_singers"]:
                new_singer_ids.add(a_nid)

    print(f"New singers: {len(new_singer_ids)}")

    # ── Phase 3: Concurrent singer info ──
    if new_singer_ids:
        singer_info_list = list(new_singer_ids)
        singer_info_list.sort()
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(_crawl_singer_info, nid): nid for nid in singer_info_list}
            for f in as_completed(futures):
                nid = futures[f]
                try:
                    info = f.result()
                    if info:
                        cp["new_singers"][str(nid)] = info
                except Exception as e:
                    print(f"  Singer {nid} failed: {e}")
                save_checkpoint(cp)

    # ── Phase 4: Import singers ──
    max_sid = Singer.objects.aggregate(m=Max("id"))["m"] or 0
    singer_map = {}  # netease_id -> django_id
    for nid_str, info in cp["new_singers"].items():
        nid = int(nid_str)
        if nid in existing_singers:
            singer_map[nid] = existing_singers[nid]
            continue
        max_sid += 1
        Singer.objects.create(
            id=max_sid, name=info["name"], image_url="",
            desc=info.get("desc", ""), source_url=info["source_url"],
        )
        singer_map[nid] = max_sid
        _download_image(info.get("image_url"), f"singer{max_sid}.jpg")
        print(f"  Singer {max_sid}: {info['name']}")
    save_checkpoint(cp)

    # ── Phase 5: Concurrent lyrics + create songs ──
    max_gid = Song.objects.aggregate(m=Max("id"))["m"] or 0
    full_singer_map = {**existing_singers, **singer_map}

    # Split song_data into batches for concurrent lyrics
    song_items = list(cp["song_data"].items())
    # Remove already-imported
    imported_set = set(cp.get("imported_songs", []))
    song_items = [(k, v) for k, v in song_items if k not in imported_set]

    def process_song(item):
        snid_str, info = item
        snid = int(snid_str)
        lyrics = _crawl_lyric(snid)
        # Map artists
        artist_ids = []
        for a_nid, a_name in info.get("artists", []):
            if a_nid in full_singer_map:
                artist_ids.append(full_singer_map[a_nid])
        return snid_str, info, lyrics, artist_ids

    BATCH = 5  # concurrent lyrics requests
    imported = 0
    for i in range(0, len(song_items), BATCH):
        batch = song_items[i:i+BATCH]
        with ThreadPoolExecutor(max_workers=BATCH) as pool:
            futures = [pool.submit(process_song, item) for item in batch]
            for f in as_completed(futures):
                try:
                    snid_str, info, lyrics, artist_ids = f.result()
                except Exception as e:
                    print(f"  Song process failed: {e}")
                    continue

                max_gid += 1
                song = Song.objects.create(
                    id=max_gid, name=info["name"], image_url="",
                    source_url=f"https://music.163.com/#/song?id={snid_str}",
                    lyrics=lyrics,
                )
                if artist_ids:
                    song.singers.set(artist_ids)
                _download_image(info.get("pic"), f"song{max_gid}.jpg")
                cp["imported_songs"].append(snid_str)
                imported += 1

                if imported % 20 == 0:
                    print(f"  Songs: {imported}/{len(song_items)}")
                    save_checkpoint(cp)

        save_checkpoint(cp)

    # Cleanup
    cp["song_data"] = {}
    cp["imported_songs"] = []
    save_checkpoint(cp)

    print(f"\nDone! {len(cp['done_singers'])} singers processed. DB now has:")
    print(f"  Songs: {Song.objects.count()}, Singers: {Singer.objects.count()}")

# ── Single API calls ──

def _crawl_singer(netease_id):
    try:
        data = json.loads(fetch(f"https://music.163.com/api/artist/{netease_id}"))
        time.sleep(random.uniform(0.2, 0.5))
        name = data.get("artist", {}).get("name", f"Unknown-{netease_id}")
        songs = data.get("hotSongs", [])
        print(f"  {name}: {len(songs)} hot songs")
        return name, songs
    except Exception as e:
        print(f"  ERROR singer {netease_id}: {e}")
        return None, None

def _crawl_lyric(netease_id):
    try:
        url = f"https://music.163.com/api/song/lyric?id={netease_id}&lv=-1&kv=-1&tv=-1"
        data = json.loads(fetch(url))
        time.sleep(random.uniform(0.15, 0.35))
        lrc = data.get("lrc")
        if lrc and lrc.get("lyric"):
            lines = re.split(r"\[\d+:\d+\.\d+\]", lrc["lyric"])
            lines = [l.strip() for l in lines if l.strip()]
            return "\n".join(lines) if lines else "纯音乐，请欣赏"
    except Exception:
        pass
    return "纯音乐，请欣赏"

def _crawl_singer_info(netease_id):
    try:
        url = f"https://music.163.com/api/artist/{netease_id}"
        data = json.loads(fetch(url))
        time.sleep(random.uniform(0.15, 0.35))
        artist = data.get("artist", {})
        intro_url = f"https://music.163.com/api/artist/introduction?id={netease_id}"
        intro_data = json.loads(fetch(intro_url))
        time.sleep(random.uniform(0.15, 0.35))
        return {
            "name": artist.get("name", f"Singer-{netease_id}"),
            "image_url": artist.get("picUrl", ""),
            "source_url": f"https://music.163.com/#/artist/desc?id={netease_id}",
            "desc": intro_data.get("briefDesc", ""),
        }
    except Exception as e:
        print(f"    Singer info {netease_id}: {e}")
        return None

def _download_image(url, filename):
    if not url:
        return
    path = os.path.join(IMG_DIR, filename)
    if os.path.exists(path):
        return
    try:
        data = fetch_image(url)
        if data:
            with open(path, "wb") as f:
                f.write(data)
    except Exception:
        pass

if __name__ == "__main__":
    main()
