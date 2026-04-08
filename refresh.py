import os, json, requests
from datetime import datetime

YOUTUBE_KEY = os.environ["YOUTUBE_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

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
    "UCVHYGJpbpXCjuwd8AlKFEoQ",  # Crash Course Kids
    "UCBa659QWEk1AI4Tg--mrJ2A",  # Tom Scott
    "UCoUP2cRFLtg-YzqMIfHsCMw",  # Sesame Street
    "UCo7GGJxnXCEDVNNBiBxyfiQ",  # LEGO
    "UCXo3JclsOkFKiPb6lJqI0dA",  # Nat Geo Kids
    "UC5XMF3Inoi8R9nSI8ChOsdQ",  # Art for Kids Hub
    "UCH1dpzjCc2KHEiamdown3nA",  # Horrible Histories
    "UC5uIZ2KOZZeQDQo_Gsi_qbQ",  # Cosmic Kids Yoga
    "UCPlwvN0_4FHSe5_AM93ZTAQ",  # Numberblocks
    "UCuaJzcsonQSlZnXVNHmTBOA",  # Wild Kratts
    "UCF9IOB2TExg3QIBupFtBDxg",  # Bedtime History
    "UCWX3yGbODI3oRUW_MBQyA6A",  # See U in History
    "UCbmNph6atAoGfqLoCL_duAg",  # Mr. DeMaio
    "UC8e-z-g23-TK0q_fNFRGSkg",  # Overly Sarcastic Productions
]

def fetch_channel_videos(channel_id):
    url = (
        f"https://www.googleapis.com/youtube/v3/search?part=snippet"
        f"&channelId={channel_id}&maxResults=50&order=date&type=video"
        f"&safeSearch=strict&videoDuration=medium&key={YOUTUBE_KEY}"
    )
    try:
        r = requests.get(url, timeout=10)
        print(f"    HTTP {r.status_code}")
        if r.status_code != 200:
            print(f"    ERROR: {r.text[:300]}")
            return []
        data = r.json()
        if "error" in data:
            print(f"    API ERROR: {data['error']}")
            return []
        videos = []
        for item in data.get("items", []):
            vid = item.get("id", {}).get("videoId")
            if not vid: continue
            title = item["snippet"].get("title", "")
            desc = item["snippet"].get("description", "")
            if any(x in (title + desc).lower() for x in ["#shorts", "#short"]):
                continue
            videos.append({
                "id": vid,
                "title": title,
                "channel": item["snippet"].get("channelTitle", ""),
                "thumb": f"https://img.youtube.com/vi/{vid}/mqdefault.jpg",
                "_desc": desc[:200]
            })
        return videos
    except Exception as e:
        print(f"    EXCEPTION: {e}")
        return []

def filter_with_claude(videos):
    if not videos: return []
    approved = []
    for i in range(0, len(videos), 30):
        batch = videos[i:i+30]
        items = [{"i": j, "title": v["title"], "desc": v["_desc"][:150], "channel": v["channel"]} for j, v in enumerate(batch)]
        prompt = (
            "Filter YouTube videos for kids aged 7-9. Be reasonably permissive.\n"
            "APPROVE: science, nature, math, history, humor, animation, crafts, animals, space, experiments, geography, storytelling, funny skits\n"
            "REJECT: scary/horror, real violence, crude sexual humor, political drama, toy hauls, dangerous challenges, rage content\n"
            f"Videos:\n{json.dumps(items)}\n"
            "Reply ONLY with JSON array like: [{\"i\":0,\"ok\":true}]. No other text."
        )
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 2000,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=60
            )
            text = r.json()["content"][0]["text"].replace("```json", "").replace("```", "").strip()
            results = json.loads(text)
            ok = {x["i"] for x in results if x.get("ok") is not False}
            approved.extend(batch[j] for j in range(len(batch)) if j in ok)
        except Exception as e:
            print(f"    claude filter error: {e}")
            approved.extend(batch)
    return approved

def main():
    print(f"API key starts with: {YOUTUBE_KEY[:8]}...")
    print(f"Fetching from {len(CHANNEL_IDS)} channels...\n")
    all_videos = []
    for cid in CHANNEL_IDS:
        print(f"  {cid}:")
        vids = fetch_channel_videos(cid)
        print(f"    {len(vids)} videos")
        all_videos.extend(vids)

    print(f"\nBefore filter: {len(all_videos)}")
    filtered = filter_with_claude(all_videos)
    print(f"After filter: {len(filtered)}")

    for v in filtered:
        v.pop("_desc", None)

    with open("videos.json", "w") as f:
        json.dump({
            "updated": datetime.utcnow().isoformat() + "Z",
            "count": len(filtered),
            "videos": filtered
        }, f)

    print(f"\nDone. Saved {len(filtered)} videos.")

if __name__ == "__main__":
    main()
