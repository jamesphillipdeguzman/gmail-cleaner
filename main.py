import os
import json
import time
import logging
import shutil

from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# =========================
# LOAD ENV
# =========================
load_dotenv()

# =========================
# CONFIG
# =========================
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

CONFIG = {
    "credentials_file": os.getenv("GOOGLE_CREDENTIALS", "credentials.json"),
    "token_file": os.getenv("GOOGLE_TOKEN", "token.json"),
    "cache_file": os.getenv("CACHE_FILE", "cache.json"),
    "query": os.getenv("QUERY", "newer_than:30d"),
    "max_results": int(os.getenv("MAX_RESULTS", 100)),
    "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
}

# =========================
# SAFETY: DRY RUN MODE
# =========================
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=getattr(logging, CONFIG["log_level"], logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

logger.info(f"🧪 DRY RUN MODE: {DRY_RUN}")


# =========================
# CLEANUP (SAFE)
# =========================
def cleanup_environment():
    logger.info("🧹 Running startup cleanup...")

    paths = ["dist", "build", "main.spec"]

    for path in paths:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                logger.info(f"Removed folder: {path}")
            elif os.path.isfile(path):
                os.remove(path)
                logger.info(f"Removed file: {path}")
        except Exception as e:
            logger.warning(f"Could not remove {path}: {e}")

# =========================
# AUTH
# =========================
def get_service():
    creds = None
    token_file = CONFIG["token_file"]

    # =========================
    # LOAD TOKEN
    # =========================
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        except Exception:
            logger.warning("⚠️ Corrupted token. Deleting...")
            os.remove(token_file)
            creds = None

    # =========================
    # REFRESH TOKEN
    # =========================
    if creds and creds.expired and creds.refresh_token:
        try:
            logger.info("🔄 Refreshing token...")
            creds.refresh(Request())
        except Exception:
            logger.warning("⚠️ Token refresh failed. Deleting...")
            os.remove(token_file)
            creds = None

    # =========================
    # NEW AUTH
    # =========================
    if not creds or not creds.valid:
        logger.info("🔐 Authenticating new session...")
        flow = InstalledAppFlow.from_client_secrets_file(
            CONFIG["credentials_file"], SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

# =========================
# CACHE
# =========================
def load_cache():
    if os.path.exists(CONFIG["cache_file"]):
        with open(CONFIG["cache_file"], "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CONFIG["cache_file"], "w") as f:
        json.dump(cache, f, indent=2)

# =========================
# RETRY WRAPPER
# =========================
def execute_with_retry(request, retries=3):
    for i in range(retries):
        try:
            return request.execute()
        except HttpError as e:
            status = getattr(e, "status_code", None)

            # ❌ Don't retry permission errors
            if status == 403:
                logger.error("❌ Permission error (likely bad token/scopes)")
                raise e

            logger.warning(f"Retry {i+1}/{retries} - {e}")
            time.sleep(2 ** i)

    raise Exception("Max retries exceeded")

# =========================
# SCORING
# =========================
import re

def score(text):
    text = (text or "").lower()
    s = 0

    rules = {
        6: ["security", "otp", "login"],
        5: ["bank", "payment", "invoice"],
        4: ["job", "interview", "hr"],
        -3: ["unsubscribe", "newsletter"],
        -2: ["sale", "discount", "promo"]
    }

    for weight, keywords in rules.items():
        for k in keywords:
            if re.search(rf"\b{k}\b", text):
                s += weight

    return s

# =========================
# FETCH EMAILS
# =========================
def fetch_new_emails(service, cache):
    emails = []
    page_token = None

    while True:
        res = execute_with_retry(
            service.users().messages().list(
                userId="me",
                maxResults=CONFIG["max_results"],
                pageToken=page_token,
                labelIds=["INBOX"],
                q=CONFIG["query"]
            )
        )

        msgs = res.get("messages", [])

        for m in msgs:
            if m["id"] in cache:
                continue

            msg = execute_with_retry(
                service.users().messages().get(
                    userId="me",
                    id=m["id"],
                    format="metadata",
                    metadataHeaders=["Subject"]
                )
            )

            headers = msg.get("payload", {}).get("headers", [])
            subject = next(
                (h["value"] for h in headers if h["name"] == "Subject"),
                "(No Subject)"
            )

            email_data = {
                "id": m["id"],
                "subject": subject,
                "score": score(subject),
                "date": int(msg.get("internalDate", "0"))
            }

            cache[m["id"]] = email_data
            emails.append(email_data)

        page_token = res.get("nextPageToken")
        if not page_token:
            break

    return emails

# =========================
# ANALYTICS
# =========================
def analyze(cache):
    emails = list(cache.values())

    important = [e for e in emails if e["score"] >= 4]
    delete = [e for e in emails if e["score"] <= -2]
    archive = [e for e in emails if -2 < e["score"] < 4]

    logger.info(f"📊 Total: {len(emails)}")
    logger.info(f"⭐ Important: {len(important)}")
    logger.info(f"📦 Archive: {len(archive)}")
    logger.info(f"🗑️ Delete: {len(delete)}")

    return important, archive, delete

# =========================
# ACTIONS
# =========================
def batch_modify(service, ids, add=None, remove=None):
    if not ids:
        return

    body = {"ids": ids}
    if add:
        body["addLabelIds"] = add
    if remove:
        body["removeLabelIds"] = remove

    execute_with_retry(
        service.users().messages().batchModify(userId="me", body=body)
    )

def batch_delete(service, ids, cache=None):
    if not ids:
        return

    if DRY_RUN:
        logger.info(f"[DRY RUN] Would permanently delete {len(ids)} emails")
        for i in ids[:10]:
            logger.info(f"[DRY RUN] delete id={i}")
        return

    execute_with_retry(
        service.users().messages().batchDelete(
            userId="me",
            body={"ids": ids}
        )
    )

    # remove from cache
    if cache:
        for i in ids:
            cache.pop(i, None)
# =========================
# MENU
# =========================
def menu(service, important, archive_list, delete_list, cache):
    while True:
        print("\n===== MENU =====")
        print("1. Show important")
        print("2. Show delete candidates")
        print("3. Archive low priority")
        print("4. Move to TRASH")
        print("5. Permanent delete")
        print("6. Exit")

        choice = input("Choice: ").strip()

        if choice == "1":
            for i, e in enumerate(important[:20]):
                print(f"{i}. ⭐ {e['subject']} ({e['score']})")

        elif choice == "2":
            for i, e in enumerate(delete_list[:20]):
                print(f"{i}. 🗑️ {e['subject']} ({e['score']})")

        elif choice == "3":
            if input("Confirm archive? ").strip().lower() in ["yes", "y"]:
                batch_modify(service,
                    [e["id"] for e in archive_list],
                    remove=["INBOX"]
                )

        elif choice == "4":
            if input("Confirm trash? ").strip().lower() in ["yes", "y"]:

                for e in delete_list:

                    if DRY_RUN:
                        logger.info(f"[DRY RUN] Would trash: {e['subject']} ({e['id']})")
                        continue

                    execute_with_retry(
                        service.users().messages().trash(
                            userId="me",
                            id=e["id"]
                        )
                    )
        elif choice == "5":
            confirm = input("Type DELETE: ")
            if confirm == "DELETE":
                batch_delete(service,
                    [e["id"] for e in delete_list],cache=cache
                )

        elif choice == "6":
            break

# =========================
# MAIN
# =========================
def main():
    start = time.time()
    logger.info("🚀 Starting Gmail Cleaner...")

    cleanup_environment()

    service = get_service()
    cache = load_cache()

    new_emails = fetch_new_emails(service, cache)
    logger.info(f"📩 New emails fetched: {len(new_emails)}")

    save_cache(cache)

    important, archive_list, delete_list = analyze(cache)

    menu(service, important, archive_list, delete_list, cache=cache)

    logger.info(f"✅ Done in {time.time() - start:.2f}s")

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()