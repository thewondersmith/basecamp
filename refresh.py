import os, json, requests, xml.etree.ElementTree as ET
from datetime import datetime

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

CHANNELS = [
    # ── SCIENCE & CURIOSITY ───────────────────────────────────────────────
    ("UCsXVk37bltHxD1rDPwtNM8Q", "id"),   # Kurzgesagt
    ("UCsooa4yRKGN_zEE8iknghZA", "id"),   # TED-Ed
    ("UCY1kMZp36IQSyNx_9h4mpCg", "id"),   # Mark Rober
    ("UC6107grRI4m0o2-emgoDnAA", "id"),   # SmarterEveryDay
    ("UCHnyfMqiRRG1u-2MsSQLbXA", "id"),   # Veritasium
    ("UCo8bcnLyZH8tBIH9V1mLgqQ", "id"),   # TheOdd1sOut
    ("UCRFIPG2u1DxKLNuE3y2SjHA", "id"),   # SciShow Kids
    ("UC6nSFpj9HTCZ5t-N3Rm3-HA", "id"),   # Vsauce
    ("UCUHW94eEFW7hkUMVaZz4eDg", "id"),   # MinutePhysics
    ("UCeiYXex_fwgYDonaTcSIk6w", "id"),   # MinuteEarth
    ("UCBa659QWEk1AI4Tg--mrJ2A", "id"),   # Tom Scott

    # ── KIDS & EDUCATION ──────────────────────────────────────────────────
    ("UCoookXUzPciGrEZEXmh4Jjg", "id"),   # Sesame Street
    ("UCPlwvN0w4qFSP1FllALB92w", "id"),   # Numberblocks
    ("UCRFIPG2u1DxKLNuE3y2SjHA", "id"),   # SciShow Kids (also listed above - dedupe in practice)
    ("UCVHYGJpbpXCjuwd8AlKFEoQ", "id"),   # Crash Course Kids (channel ID)
    ("crashcoursekids",           "user"), # Crash Course Kids (legacy username fallback)
    ("UCfPyVJEBD7Di1YYjTdS2v8g", "id"),   # Homeschool Pop
    ("UCH-_hzb2ILSCo9ftVSnrCIQ", "id"),   # Peekaboo Kidz - Dr. Binocs

    # ── ART, YOGA & CREATIVITY ────────────────────────────────────────────
    ("UC5XMF3Inoi8R9nSI8ChOsdQ", "id"),   # Art for Kids Hub
    ("UC5uIZ2KOZZeQDQo_Gsi_qbQ", "id"),   # Cosmic Kids Yoga

    # ── NATURE & ANIMALS ─────────────────────────────────────────────────
    ("UCXVCgDuD_QCkI7gTKU7-tpg", "id"),   # Nat Geo Kids
    ("UCxEmDFo1yUbbxjEb9RjitVA", "id"),   # Wild Kratts
    ("UCBcRF18a7Qf58cCRy5xuWwQ", "id"),   # Brave Wilderness (Claude filters sting content)

    # ── HISTORY ───────────────────────────────────────────────────────────
    ("UC6USPnJ8bCWGnR9TuDLuaKA", "id"),   # Simple History
    ("UCH1dpzjCc2KHEiamdown3nA", "id"),   # Horrible Histories (BBC)

    # ── GEOGRAPHY ────────────────────────────────────────────────────────
    ("UCmmPgObSUPw1HL2lq6H5Ukg", "id"),   # Geography Now
    ("UCVIbTFvRn3cG79wf2gNZerg", "id"),   # Kids Learning Tube - geography songs

    # ── LEGO & BUILDING ──────────────────────────────────────────────────
    ("UCP-Ng5SXUEt0VE-TXqRdL6g", "id"),   # LEGO official

    # ── FOOD, FRUIT & PLANTS ─────────────────────────────────────────────
    ("UCddiUEpeqJcYeBxX1IVBKvQ", "id"),   # How To Cook That - food science & baking
    ("UCekQr9znsk2vWxBo3YiLq2w", "id"),   # Epic Gardening - growing fruit & veg
    ("UCJFp8uSYCjXOMnkUyb3CQ3Q", "id"),   # Kids Cook Monday

    # ── CODING & TECHNOLOGY ──────────────────────────────────────────────
    ("UCJXGnJCYp3sGEMZkxFnQnnA", "id"),   # Code.org
    ("UCVTyTA7-g9nopHeHbeuvpRA", "id"),   # Scratch (MIT)
]

# Deduplicate while preserving order
seen = set()
CHANNELS = [(cid, ctype) for cid, ctype in CHANNELS if not (cid in seen or seen.add(cid))]

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt":   "http://www.youtube.com/xml/schemas/2015",
}

def fetch_rss(channel_id, channel_type):
    if channel_type == "user":
        url = f"https://www.youtube.com/feeds/videos.xml?user={channel_id}"
    else:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            print(f"    HTTP {r.status_code}")
            return []
        root = ET.fromstring(r.content)
        channel_name = root.findtext("atom:title", namespaces=NS) or channel_id
        videos = []
        for entry in root.findall("atom:entry", NS):
            vid = entry.findtext("yt:videoId", namespaces=NS)
            title = entry.findtext("atom:title", namespaces=NS) or ""
            if not vid: continue
            if any(x in title.lower() for x in ["#shorts", "#short"]):
                continue
            videos.append({
                "id": vid,
                "title": title,
                "channel": channel_name,
                "thumb": f"https://img.youtube.com/vi/{vid}/mqdefault.jpg",
            })
        return videos
    except Exception as e:
        print(f"    error: {e}")
        return []

def filter_with_claude(videos):
    if not videos: return []
    approved = []
    for i in range(0, len(videos), 30):
        batch = videos[i:i+30]
        items = [{"i": j, "title": v["title"], "channel": v["channel"]} for j, v in enumerate(batch)]
        prompt = (
            "Filter YouTube videos for kids aged 7-9. Be reasonably permissive.\n"
            "APPROVE: science, nature, math, history, humor, animation, crafts, animals, space, "
            "experiments, geography, storytelling, funny skits, art, yoga, music, food, fruit, "
            "plants, gardening, cooking, coding, technology\n"
            "REJECT: scary/horror, real violence, crude sexual humor, political drama, "
            "toy hauls, dangerous challenges, rage content, adult gaming drama\n"
            f"Videos:\n{json.dumps(items)}\n"
            "Reply ONLY with JSON array like: [{\"i\":0,\"ok\":true}]. No other text."
        )
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY,
                         "anthropic-version": "2023-06-01"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 2000,
                      "messages": [{"role": "user", "content": prompt}]},
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
    print(f"Fetching RSS feeds for {len(CHANNELS)} channels...")
    all_videos = []
    for cid, ctype in CHANNELS:
        vids = fetch_rss(cid, ctype)
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
