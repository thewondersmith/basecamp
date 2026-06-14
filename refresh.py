import os, json, requests
from datetime import datetime

YOUTUBE_KEY   = os.environ["YOUTUBE_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

# ── REGULAR CHANNELS (activities API, 1 unit each) ────────────────────────
CHANNEL_IDS = [
    "UCsXVk37bltHxD1rDPwtNM8Q",  # Kurzgesagt
    "UCsooa4yRKGN_zEE8iknghZA",  # TED-Ed
    "UCY1kMZp36IQSyNx_9h4mpCg",  # Mark Rober
    "UC6107grRI4m0o2-emgoDnAA",  # SmarterEveryDay
    "UCHnyfMqiRRG1u-2MsSQLbXA",  # Veritasium
    "UCo8bcnLyZH8tBIH9V1mLgqQ",  # TheOdd1sOut
    "UCRFIPG2u1DxKLNuE3y2SjHA",  # SciShow Kids
    "UC6nSFpj9HTCZ5t-N3Rm3-HA",  # Vsauce
    "UCUHW94eEFW7hkUMVaZz4eDg",  # MinutePhysics
    "UCeiYXex_fwgYDonaTcSIk6w",  # MinuteEarth
    "UCBa659QWEk1AI4Tg--mrJ2A",  # Tom Scott
    "UCoookXUzPciGrEZEXmh4Jjg",  # Sesame Street
    "UCPlwvN0w4qFSP1FllALB92w",  # Numberblocks
    "UCfPyVJEBD7Di1YYjTdS2v8g",  # Homeschool Pop
    "UCH-_hzb2ILSCo9ftVSnrCIQ",  # Peekaboo Kidz
    "UC5XMF3Inoi8R9nSI8ChOsdQ",  # Art for Kids Hub
    "UC5uIZ2KOZZeQDQo_Gsi_qbQ",  # Cosmic Kids Yoga
    "UCXVCgDuD_QCkI7gTKU7-tpg",  # Nat Geo Kids
    "UCxEmDFo1yUbbxjEb9RjitVA",  # Wild Kratts
    "UC6USPnJ8bCWGnR9TuDLuaKA",  # Simple History
    "UCP-Ng5SXUEt0VE-TXqRdL6g",  # LEGO
    "UCddiUEpeqJcYeBxX1IVBKvQ",  # How To Cook That
    "UCekQr9znsk2vWxBo3YiLq2w",  # Epic Gardening
    "UCMOqf8ab-42UUQIdVoKwjlQ",  # Practical Engineering
    "UCAgIIvpEGwYe6YBxpq_GAhg",  # Design Squad Global
    "UCFpEwFz8VFMBEiBzIggUG8g",  # Royal Opera House
    "UC5uIZ2KOZZeQDQo_Gsi_qbQ",  # Cosmic Kids
]

# ── POP ARTISTS (search API, 100 units each) ─────────────────────────────
POP_ARTISTS = [
    "Taylor Swift",
    "Sabrina Carpenter",
    "Olivia Rodrigo",
    "Ariana Grande",
    "Dua Lipa",
    "Billie Eilish",
    "Katy Perry",
    "Meghan Trainor",
    "Ghost and Pals",  # Amygdala's Ragdoll etc
    "Brave Wilderness",
]


def fetch_channel_videos(channel_id):
    """Activities endpoint — 1 unit."""
    try:
        url = (
            f"https://www.googleapis.com/youtube/v3/activities"
            f"?part=snippet,contentDetails"
            f"&channelId={channel_id}"
            f"&maxResults=25"
            f"&type=upload"
            f"&key={YOUTUBE_KEY}"
        )
        r = requests.get(url, timeout=15)
        if not r.ok:
            print(f"    HTTP {r.status_code}")
            return []
        data = r.json()
        if "error" in data:
            print(f"    API error: {data['error'].get('message','')}")
            return []
        videos = []
        for item in data.get("items", []):
            vid = item.get("contentDetails", {}).get("upload", {}).get("videoId")
            snippet = item.get("snippet", {})
            title = snippet.get("title", "")
            channel = snippet.get("channelTitle", "")
            if not vid or not title:
                continue
            if is_short(title):
                continue
            videos.append({
                "id": vid,
                "title": title,
                "channel": channel,
                "thumb": f"https://img.youtube.com/vi/{vid}/mqdefault.jpg",
            })
        return videos
    except Exception as e:
        print(f"    error: {e}")
        return []


def fetch_artist_videos(artist_name):
    """Search endpoint — 100 units. Tags results as music=True."""
    is_music = artist_name != "Brave Wilderness"
    try:
        # Search for the artist's official videos
        query = f"{artist_name} official music video" if is_music else artist_name
        url = (
            f"https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet"
            f"&q={requests.utils.quote(query)}"
            f"&type=video"
            f"&order=viewCount"
            f"&maxResults=15"
            f"&key={YOUTUBE_KEY}"
        )
        r = requests.get(url, timeout=15)
        if not r.ok:
            print(f"    HTTP {r.status_code}")
            return []
        data = r.json()
        if "error" in data:
            print(f"    API error: {data['error'].get('message','')}")
            return []
        videos = []
        for item in data.get("items", []):
            vid = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})
            title = snippet.get("title", "")
            channel = snippet.get("channelTitle", "")
            if not vid or not title:
                continue
            if is_short(title):
                continue
            entry = {
                "id": vid,
                "title": title,
                "channel": channel,
                "thumb": f"https://img.youtube.com/vi/{vid}/mqdefault.jpg",
            }
            if is_music:
                entry["music"] = True
            videos.append(entry)
        return videos
    except Exception as e:
        print(f"    error: {e}")
        return []


def is_short(title):
    t = title.lower()
    return any(x in t for x in ["#shorts", "#short", "shorts"])


def filter_with_claude(videos):
    if not videos:
        return []
    approved = []
    for i in range(0, len(videos), 30):
        batch = videos[i:i+30]
        items = [{"i": j, "title": v["title"], "channel": v["channel"]}
                 for j, v in enumerate(batch)]
        prompt = (
            "Filter YouTube videos for kids aged 7-9. Be permissive but apply these rules:\n"
            "APPROVE: science, nature, math, history, humor, animation, crafts, animals, space, "
            "experiments, geography, storytelling, art, yoga, music videos, pop music, "
            "Taylor Swift, Sabrina Carpenter, Olivia Rodrigo, Ariana Grande, Katy Perry, "
            "Billie Eilish, Dua Lipa, Meghan Trainor, food, fruit, plants, gardening, "
            "cooking, coding, technology, engineering, ballet, dance, wildlife\n"
            "REJECT: religious content, Jesus, church, prayer, worship, scary/horror, "
            "real violence, sexual content, political drama, dangerous challenges, "
            "rage content, adult gaming, toy unboxing hauls\n"
            f"Videos:\n{json.dumps(items)}\n"
            "Reply ONLY with JSON array like: [{\"i\":0,\"ok\":true}]. No other text."
        )
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=60
            )
            text = r.json()["content"][0]["text"].replace("```json","").replace("```","").strip()
            results = json.loads(text)
            ok = {x["i"] for x in results if x.get("ok") is not False}
            approved.extend(batch[j] for j in range(len(batch)) if j in ok)
        except Exception as e:
            print(f"    claude error: {e}")
            approved.extend(batch)
    return approved


def main():
    print(f"Fetching {len(set(CHANNEL_IDS))} channels + {len(POP_ARTISTS)} artists...")
    all_videos = []

    seen_channels = set()
    for cid in CHANNEL_IDS:
        if cid in seen_channels:
            continue
        seen_channels.add(cid)
        vids = fetch_channel_videos(cid)
        name = vids[0]["channel"] if vids else cid
        print(f"  {name}: {len(vids)} videos")
        all_videos.extend(vids)

    print("--- Artists ---")
    for artist in POP_ARTISTS:
        vids = fetch_artist_videos(artist)
        print(f"  {artist}: {len(vids)} videos")
        all_videos.extend(vids)

    print(f"\nBefore filter: {len(all_videos)}")
    filtered = filter_with_claude(all_videos)
    print(f"After filter: {len(filtered)}")

    music_count = sum(1 for v in filtered if v.get("music"))
    print(f"Music videos: {music_count}")

    with open("videos.json", "w") as f:
        json.dump({
            "updated": datetime.utcnow().isoformat() + "Z",
            "count": len(filtered),
            "videos": filtered
        }, f)

    print(f"Done. Saved {len(filtered)} videos.")


if __name__ == "__main__":
    main()
