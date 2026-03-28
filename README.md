# 📧 Gmail Cleaner

A Python-based Gmail automation tool that connects to the Gmail API and intelligently organizes your inbox by scoring emails, archiving low-priority messages, and safely managing unwanted emails.

---

## 🚀 Features

- 🔐 Secure Gmail OAuth authentication  
- 📩 Fetch and analyze inbox emails  
- 🧠 Rule-based email scoring system  
- 📦 Auto-archive low priority emails  
- 🗑️ Move unwanted emails to Trash safely  
- 📊 Inbox health analytics  
- ⏱️ Execution time tracking  
- 💾 Local caching system  

---

## ⚙️ How It Works

- Connects to Gmail API using OAuth2  
- Fetches emails from the inbox  
- Scores emails using rule-based logic:

  - Security / OTP → High priority  
  - Bank / Invoice → Important  
  - Job / HR → Medium priority  
  - Newsletters / Ads → Low priority  

- Categorizes emails into:
  - ⭐ Important  
  - 📦 Medium priority  
  - 🗑️ Low priority  

- User actions:
  - View emails  
  - Archive emails  
  - Move to Trash  
  - Permanently delete (manual confirmation required)  

---

## 🛠️ Tech Stack

- Python 3  
- Google Gmail API  
- Google OAuth2  
- JSON (cache storage)  
- Pickle (token storage)  

---

## 📦 Installation

### Clone the repository

```bash
git clone https://github.com/your-username/gmail-cleaner.git
cd gmail-cleaner
```

### Install dependencies

```bash
pip install google-auth-oauthlib google-api-python-client
```

---

## 🔑 Google API Setup

1. Go to Google Cloud Console  
2. Enable Gmail API  
3. Create OAuth credentials  
4. Download `credentials.json`  
5. Place it in the project root folder  

---

## ▶️ Run the Program

```bash
python main.py
```

---

## 🔐 First Run

- A Google login window will open  
- Click **Allow access**  
- A `token.json` file will be created automatically  

---

## ⚠️ Safety Notes

- Emails are NOT deleted automatically  
- Default action moves emails to Trash  
- Permanent deletion requires explicit confirmation  

---

## 📊 Sample Output

```text
INBOX HEALTH REPORT
--------------------
Total emails: 120
Important: 25
Medium priority: 70
Low priority: 25
```

---

## 🧠 Future Improvements

- AI-based spam detection  
- GUI desktop app version  
- Scheduled automatic cleanup  
- Machine learning classification system  

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

James De Guzman  
Built with Python + Gmail API for smart inbox automation.
