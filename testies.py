import os
import json
import requests

# Load config
with open("system_config.json") as f:
    config = json.load(f)

TOKEN = config["KOBO_TOKEN"]
ASSET_ID = config["ASSET_ID"]
KOBO_BASE = "https://kobo.ifrc.org"

HEADERS = {
    "Authorization": f"Token {TOKEN}"
}

SAVE_DIR = "photos"

def download_photos():
    url = f"{KOBO_BASE}/api/v2/assets/{ASSET_ID}/data.json"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"[!] Failed to fetch submissions: {response.status_code}")
        return

    data = response.json()
    submissions = data.get("results", [])
    print(f"📥 Found {len(submissions)} submissions")

    for sub in submissions:
        uuid = sub.get("_uuid")
        attachments = sub.get("_attachments", [])

        if not attachments:
            print(f"🚫 No photo for UUID {uuid}")
            continue

        for attach in attachments:
            media_file = attach["filename"]
            download_url = f"{KOBO_BASE}/media/original?media_file={media_file}"

            ext = os.path.splitext(media_file)[1]
            filename = f"photo{ext}"
            folder = os.path.join(SAVE_DIR, uuid)
            os.makedirs(folder, exist_ok=True)
            save_path = os.path.join(folder, filename)

            res = requests.get(download_url, headers=HEADERS)
            if res.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(res.content)
                print(f"✅ Saved photo for {uuid} -> {save_path}")
            else:
                print(f"❌ Failed to download photo for {uuid}: {res.status_code}")
                print(f"URL: {download_url}")

if __name__ == "__main__":
    download_photos()
