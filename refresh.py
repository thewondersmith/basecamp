import os, json, requests
from datetime import datetime

YOUTUBE_KEY = os.environ["YOUTUBE_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

CHANNEL_HANDLES = [
    "kurzgesagt", "TEDed", "MarkRober", "SmarterEveryDay", "veritasium",
    "theodd1sout", "SciShowKids", "vsauce", "minutephysics", "MinuteEarth",
    "CrashCourseKids", "TomScottGo", "SesameStreet", "LEGO", "NatGeoKids",
    "ArtforKidsHub", "HorribleHistories", "CosmicKidsYoga", "Numberblocks", "WildKratts",
    "BedtimeHistory", "SeeUinHistory", "MrDeMaio", "OverlySarcasticProductions",
]

def resolve_handle(handle):
    try:
        r = requests.get(f"https://www.googleapis.com/youtube/v3/channels?part=id&forHandle={handle}&key={YOUTUBE_KEY}", timeout=10)
        items = r.json().get("items", [])
        return items[0]["id"] if items else None
    except: return None

def fetch_channel_videos(channel_id):
    try:
        r = requests.get(
            f"https://www.googleapis.com/youtube/v3/search?part=snippet"
            f"&channelId={channel_id}&maxResults=50&order=date&type=video"
            f"&safeSearch=strict&videoDuration=medium&key={YOUTUBE_KEY}", timeout=10)
        videos = []
        for item in r.json().get("items", []):
            vid = item.get("id", {}).get("videoId")
            if not vid: continue
            title = item["snippet"].get("title", "")
            desc = item["snippet"].get("description", "")
            if any(x in (title + desc).lower() for x in ["#shorts", "#short"]): continue
            videos.append({
                "id": vid,
                "title": title,
                "channel": item["snippet"].get("channelTitle", ""),
                "thumb": f"https://img.youtube.com/vi/{vid}/mqdefault.jpg",
                "_desc": desc[:200]
            })
        return videos
    except: return []

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
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]},
                timeout=30
            )
            text = r.json()["content"][0]["text"].replace("```json", "").replace("```", "").strip()
            results = json.loads(text)
            ok = {x["i"] for x in results if x.get("ok") is not False}
            approved.extend(batch[j] for j in range(len(batch)) if j in ok)
        except:
            approved.extend(batch)  # fail open
    return approved

def main():
    print("Resolving handles...")
    channel_ids = []
    for h in CHANNEL_HANDLES:
        cid = resolve_handle(h)
        print(f"  {h} -> {cid or 'NOT FOUND'}")
        if cid: channel_ids.append(cid)

    print(f"\nFetching from {len(channel_ids)} channels...")
    all_videos = []
    for cid in channel_ids:
        vids = fetch_channel_videos(cid)
        print(f"  {cid}: {len(vids)} videos")
        all_videos.extend(vids)

    print(f"\nBefore filter: {len(all_videos)}")
    filtered = filter_with_claude(all_videos)
    print(f"After filter: {len(filtered)}")

    for v in filtered:
        v.pop("_desc", None)

    with open("videos.json", "w") as f:
        json.dump({"updated": datetime.utcnow().isoformat() + "Z", "count": len(filtered), "videos": filtered}, f)

    print(f"Saved {len(filtered)} videos.")

if __name__ == "__main__":
    main()
