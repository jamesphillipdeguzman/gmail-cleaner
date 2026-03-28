from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle
import os
import json
from datetime import datetime, timezone

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CACHE_FILE = "cache.json"


# =========================
# AUTH
# =========================
def get_service():
    creds = None

    if os.path.exists("token.json"):
        with open("token.json", "rb") as token:
            creds = pickle.load(token)

    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open("token.json", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)


# =========================
# CACHE
# =========================
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


# =========================
# SCORING
# =========================
def score(text):
    text = text.lower()
    s = 0

    if any(k in text for k in ["security", "login", "otp"]):
        s += 6
    if any(k in text for k in ["bank", "payment", "invoice"]):
        s += 5
    if any(k in text for k in ["job", "hr", "interview"]):
        s += 4
    if any(k in text for k in ["newsletter", "unsubscribe"]):
        s -= 3
    if any(k in text for k in ["sale", "discount"]):
        s -= 2

    return s


# =========================
# FETCH NEW EMAILS
# =========================
def fetch_new_emails(service, cache):
    emails = []
    page_token = None

    while True:
        res = service.users().messages().list(
            userId="me",
            maxResults=100,
            pageToken=page_token,
            labelIds=["INBOX"],
            q="newer_than:30d"
        ).execute()

        msgs = res.get("messages", [])

        for m in msgs:
            if m["id"] in cache:
                continue

            msg = service.users().messages().get(
                userId="me",
                id=m["id"],
                format="metadata",
                metadataHeaders=["Subject"]
            ).execute()

            subject = ""
            for h in msg.get("payload", {}).get("headers", []):
                if h["name"] == "Subject":
                    subject = h["value"]

            email_data = {
                "id": m["id"],
                "subject": subject,
                "score": score(subject),
                "date": msg["internalDate"]
            }

            emails.append(email_data)
            cache[m["id"]] = email_data

        page_token = res.get("nextPageToken")
        if not page_token:
            break

    return emails


# =========================
# ANALYTICS
# =========================
def analyze(cache):
    emails = list(cache.values())

    high = sum(1 for e in emails if e["score"] >= 4)
    low = sum(1 for e in emails if e["score"] < 0)
    mid = len(emails) - high - low

    print("\n📊 INBOX HEALTH")
    print(f"Total cached: {len(emails)}")
    print(f"⭐ Important: {high}")
    print(f"📦 Medium: {mid}")
    print(f"🗑️ Low: {low}")

    return emails


# =========================
# FAST ARCHIVE (BATCH)
# =========================
def archive(service, emails):
    ids = [e["id"] for e in emails]

    for i in range(0, len(ids), 100):
        batch_ids = ids[i:i+100]

        service.users().messages().batchModify(
            userId="me",
            body={
                "ids": batch_ids,
                "removeLabelIds": ["INBOX"]
            }
        ).execute()


# =========================
# DELETE
# =========================
def delete(service, emails):
    for e in emails:
        service.users().messages().trash(
            userId="me",
            id=e["id"]
        ).execute()


# =========================
# MENU
# =========================
def menu(service, emails):
    to_delete = [e for e in emails if e["score"] <= -2]
    to_archive = [e for e in emails if -2 < e["score"] < 4]
    important = [e for e in emails if e["score"] >= 4]

    while True:
        print("\n===== MENU =====")
        print("1. Show important")
        print("2. Show delete candidates")
        print("3. Archive low priority")
        print("4. Delete low priority")
        print("5. View email details")
        print("6. Exit")

        c = input("Choice: ")

        if c == "1":
            for i, e in enumerate(important[:20]):
                print(f"{i}. ⭐ {e['subject']} ({e['score']})")

        elif c == "2":
            for i, e in enumerate(to_delete[:20]):
                print(f"{i}. 🗑️ {e['subject']} ({e['score']})")

        elif c == "3":
            confirm = input("Archive ALL low priority? (yes/no): ")
            if confirm.lower() == "yes":
                archive(service, to_archive)
                print("📦 Archived!")

        elif c == "4":
            print(f"\n⚠️ About to DELETE {len(to_delete)} emails")
            confirm = input("Type DELETE to confirm: ")

            if confirm == "DELETE":
                delete(service, to_delete)
                print("🗑️ Deleted!")
            else:
                print("❌ Cancelled")

        elif c == "5":
            idx = int(input("Enter index from list: "))
            if idx < len(emails):
                e = emails[idx]
                print("\n--- EMAIL ---")
                print("Subject:", e["subject"])
                print("Score:", e["score"])

        elif c == "6":
            break


# =========================
# MAIN
# =========================
def main():
    service = get_service()

    print("⚡ PRODUCTION MODE: Smart Gmail Scan")

    cache = load_cache()

    new_emails = fetch_new_emails(service, cache)

    print(f"📩 New emails processed: {len(new_emails)}")

    save_cache(cache)

    all_emails = analyze(cache)

    menu(service, all_emails)


if __name__ == "__main__":
    main()