📧 Gmail Cleaner

A Python-based Gmail automation tool that connects to the Gmail API and intelligently organizes your inbox by scoring emails, archiving low-priority messages, and safely managing unwanted emails.

🚀 Features
🔐 Secure Gmail OAuth authentication
📩 Fetch and analyze inbox emails
🧠 Rule-based email scoring system
📦 Auto-archive low priority emails
🗑️ Move unwanted emails to Trash safely
📊 Inbox health analytics
⏱️ Execution time tracking
💾 Local caching system
⚙️ How It Works
Connects to Gmail API using OAuth2
Fetches emails from the inbox
Scores emails based on rules:
Security / OTP → High priority
Bank / Invoice → Important
Job / HR → Medium priority
Newsletters / Ads → Low priority
Categorizes emails:
⭐ Important
📦 Medium priority
🗑️ Low priority
Actions available:
View emails
Archive emails
Move to Trash
Permanently delete (manual confirmation)
🛠️ Tech Stack
Python 3
Google Gmail API
OAuth2 Authentication
JSON (cache storage)
Pickle (token storage)
📦 Installation
Clone the repository
Install dependencies
🔑 Google API Setup
Go to Google Cloud Console
Enable Gmail API
Create OAuth credentials
Download credentials.json
Place it in the project root
▶️ Run the Program
🔐 First Run
A Google login window will open
Click Allow access
token.json will be generated automatically
⚠️ Safety
Emails are NOT deleted by default
Default behavior moves emails to Trash
Permanent deletion requires confirmation
📊 Sample Output
🧠 Future Improvements
AI-based spam detection
GUI version
Scheduled auto-cleaning
Machine learning classification
📄 License

MIT License

👨‍💻 Author

Built with Python + Gmail API for smart inbox management
