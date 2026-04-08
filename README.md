# 🔭 Discovery Zone

Kid-safe YouTube for ages 7–9. AI-filtered. No algorithm. No Shorts. No slop.

---

## Deploy to GitHub Pages (5 minutes)

### Step 1 — Get a free YouTube API key
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (name it anything)
3. Go to **APIs & Services → Library**
4. Search for **YouTube Data API v3** and click **Enable**
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → API Key**
7. Copy the key — you'll enter it in the app

### Step 2 — Put the app on GitHub Pages
1. Go to [github.com](https://github.com) and sign in (create a free account if needed)
2. Click **New repository** (the green button)
3. Name it `discoveryzone` (or anything you want)
4. Leave it **Public**, click **Create repository**
5. Click **uploading an existing file**
6. Drag and drop `index.html` into the upload area
7. Click **Commit changes**

### Step 3 — Enable GitHub Pages
1. In your new repo, click **Settings**
2. Scroll down to **Pages** in the left sidebar
3. Under **Source**, select **Deploy from a branch**
4. Set branch to `main`, folder to `/ (root)`
5. Click **Save**
6. Wait ~60 seconds, then your app is live at:
   `https://YOUR-GITHUB-USERNAME.github.io/discoveryzone`

### Step 4 — Set it as the Silk browser homepage on the Kindle
1. Open **Silk browser** on the Kindle
2. Go to your GitHub Pages URL
3. Enter your YouTube API key when prompted (saved locally on the device)
4. Tap the **menu → Settings → Set as homepage**
5. Done — every time the kids open Silk, they're in Discovery Zone

---

## How it works

- Pulls recent videos from 12 curated quality channels
- Every video is scored by Claude AI before it appears — no manual review needed
- Search is filtered the same way — kids can search freely
- Videos play with `rel=0` so when a video ends, only same-channel suggestions appear
- API key is stored locally on the device (never sent anywhere except Google's API)

## Curated channels included
Kurzgesagt · TED-Ed · Mark Rober · SmarterEveryDay · Veritasium · TheOdd1sOut · SciShow Kids · Vsauce · MinutePhysics · MinuteEarth · Crash Course Kids · Tom Scott

## Costs
- YouTube Data API: **Free** (10,000 units/day — a family will use maybe 200/day)
- GitHub Pages: **Free**
- Claude API filtering: Handled automatically, no cost to you

---

## Want to add or remove channels?

Open `index.html` in any text editor, find the `CHANNELS` array near the top, and add or remove entries. Each entry needs the YouTube channel ID (find it at [commentpicker.com/youtube-channel-id.php](https://commentpicker.com/youtube-channel-id.php)).
