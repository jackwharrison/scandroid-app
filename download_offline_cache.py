import os
import json
from testies import get_all_submissions, get_photo_attachment  # Make sure this works
from config_loader import load_config
import requests

def download_cache():
    config = load_config()
    program_id = config["programId"]
    payment_id = config["PAYMENT_ID"]

    print(f"📥 Starting sync for Program ID {program_id}, Payment ID {payment_id}...")

    transactions = get_transactions(program_id, payment_id)

    if not transactions:
        print("⚠️ No transactions found.")
        return []

    submissions = get_all_submissions()

    cached_beneficiaries = []
    for tx in transactions:
        uuid = tx.get("registrationReferenceId")
        matching_submission = next((s for s in submissions if s["_uuid"] == uuid), None)
        if not matching_submission:
            continue

        data = {
            "uuid": uuid,
            "status": tx.get("status"),
            "fullName": tx.get("registrationName"),
            "phoneNumber": "",  # optionally fill
            "fields": {},       # add custom fields from display_config if needed
        }

        # ✅ Download photo
        photo_path = get_photo_attachment(uuid, save_dir="offline-cache/photos")
        if photo_path:
            data["photo"] = photo_path

        cached_beneficiaries.append(data)

    # Save final result
    if cached_beneficiaries:
        batch_name = f"offline-cache/payment-{payment_id}-batch"
        os.makedirs(batch_name, exist_ok=True)

        with open(os.path.join(batch_name, "beneficiaries.json"), "w", encoding="utf-8") as f:
            json.dump(cached_beneficiaries, f, ensure_ascii=False, indent=2)

        print(f"📦 {len(beneficiaries)} beneficiaries ready for offline validation.")
    else:
        print("⚠️ No matching beneficiaries found.")

    return cached_beneficiaries


def get_transactions(program_id, payment_id):
    config = load_config()
    token = login_and_get_token(config["username121"], config["password121"], config["url121"])
    url = f'{config["url121"]}/api/programs/{program_id}/payments/{payment_id}/transactions'
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"[!] Failed to get transactions: {response.status_code}")
        return []


def login_and_get_token(username, password, base_url):
    url = f"{base_url}/api/auth/login"
    response = requests.post(url, json={"username": username, "password": password})
    response.raise_for_status()
    return response.json()["access_token"]


if __name__ == "__main__":
    download_cache()
