import os, json, requests
from datetime import datetime

YOUTUBE_KEY = os.environ["YOUTUBE_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

# 1 unit per channel via activities endpoint (vs 100 units for search)
# 41 channels = ~41 units per night, well within 10,000 daily quota
CHANNEL_IDS = [
    # Science & curiosity
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

    # Kids & education
    "UCoookXUzPciGrEZEXmh4Jjg",  # Sesame Street
    "UCPlwvN0w4qFSP1FllALB92w",  # Numberblocks
    "UCVHYGJpbpXCjuwd8AlKFEoQ",  # Crash Course Kids
    "UCfPyVJEBD7Di1YYjTdS2v8g",  # Homeschool Pop
    "UCH-_hzb2ILSCo9ftVSnrCIQ",  # Peekaboo Kidz

    # Art, yoga & creativity
    "UC5XMF3Inoi8R9nSI8ChOsdQ",  # Art for Kids Hub
    "UC5uIZ2KOZZeQDQo_Gsi_qbQ",  # Cosmic Kids Yoga

    # Nature & animals
    "UCXVCgDuD_QCkI7gTKU7-tpg",  # Nat Geo Kids
    "UCxEmDFo1yUbbxjEb9RjitVA",  # Wild Kratts
    "UCBcRF18a7Qf58cCRy5xuWwQ",  # Brave Wilderness

    # History
    "UC6USPnJ8bCWGnR9TuDLuaKA",  # Simple History
    "UCH1dpzjCc2KHEiamdown3nA",  # Horrible Histories

    # Geography
    "UCmmPgObSUPw1HL2lq6H5Ukg",  # Geography Now
    "UCVIbTFvRn3cG79wf2gNZerg",  # Kids Learning Tube

    # LEGO & building
    "UCP-Ng5SXUEt0VE-TXqRdL6g",  # LEGO official

    # Food, fruit & plants
    "UCddiUEpeqJcYeBxX1IVBKvQ",  # How To Cook That
    "UCekQr9znsk2vWxBo3YiLq2w",  # Epic Gardening
    "UCJFp8uSYCjXOMnkUyb3CQ3Q",  # Kids Cook Monday

    # Coding & technology
    "UCJXGnJCYp3sGEMZkxFnQnnA",  # Code.org
    "UCVTyTA7-g9nopHeHbeuvpRA",  # Scratch (MIT)

    # Engineering
    "UCMOqf8ab-42UUQIdVoKwjlQ",  # Practical Engineering
    "UCAgIIvpEGwYe6YBxpq_GAhg",  # Design Squad Global (PBS)

    # Ballet & dance
    "UCFpEwFz8VFMBEiBzIggUG8g",  # Royal Opera House
    "UCwhP9hNbqPtCdLXIy3UBEHA",  # GoNoodle
    "UCkqWFBSPNGS0Ys-ok5vFaYA",  # Just Dance Kids
]

def fetch_channel_videos(channel_id):
    """
    Uses the activities endpoint - costs only 1 unit per channel.
    Gets the 25 most recent uploads.
    """
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
            print(f"    HTTP {r.status_code}: {r.text[:100]}")
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
            # Skip Shorts by title
            if any(x in title.lower() for x in ["#shorts", "#short"]):
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


def filter_with_claude(videos):
    if not videos:
        return []
    approved = []
    for i in range(0, len(videos), 30):
        batch = videos[i:i+30]
        items = [{"i": j, "title": v["title"], "channel": v["channel"]} for j, v in enumerate(batch)]
        prompt = (
            "Filter YouTube videos for kids aged 7-9. Be reasonably permissive.\n"
            "APPROVE: science, nature, math, history, humor, animation, crafts, animals, space, "
            "experiments, geography, storytelling, funny skits, art, yoga, music, food, fruit, "
            "plants, gardening, cooking, coding, technology, engineering, ballet, dance\n"
            "REJECT: scary/horror, real violence, crude sexual humor, political drama, "
            "toy hauls, dangerous challenges, rage content, adult gaming drama\n"
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
            text = r.json()["content"][0]["text"].replace("```json", "").replace("```", "").strip()
            results = json.loads(text)
            ok = {x["i"] for x in results if x.get("ok") is not False}
            approved.extend(batch[j] for j in range(len(batch)) if j in ok)
        except Exception as e:
            print(f"    claude error: {e}")
            approved.extend(batch)
    return approved


def main():
    print(f"Fetching from {len(CHANNEL_IDS)} channels via activities API (~{len(CHANNEL_IDS)} quota units)...")
    all_videos = []
    for cid in CHANNEL_IDS:
        vids = fetch_channel_videos(cid)
        name = vids[0]["channel"] if vids else cid
        print(f"  {name}: {len(vids)} videos")
        all_videos.extend(vids)

    print(f"\nBefore filter: {len(all_videos)}")
    filtered = filter_with_claude(all_videos)
    print(f"After filter: {len(filtered)}")

    with open("videos.json", "w") as f:
        json.dump({
            "updated": datetime.utcnow().isoformat() + "Z",
            "count": len(filtered),
            "videos": filtered
        }, f)

    print(f"\nDone. Saved {len(filtered)} videos.")


if __name__ == "__main__":
    main()
