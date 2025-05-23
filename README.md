# Email to Telegram Bot

Automatically forwards unread emails from your inbox to a Telegram group topic. Runs every 10 minutes via GitHub Actions.

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   📧 IMAP   │───▶│  🐍 Python   │───▶│  📱 Telegram    │
│   Server    │    │    Script    │    │     Group       │
└─────────────┘    └──────────────┘    └─────────────────┘
```

## ✨ Features

- Forwards email subject, sender info, and timestamp
- Sends email body as message text
- Uploads email attachments as images
- Marks emails as read after successful forwarding
- Runs automatically every 10 minutes

## 🚀 Setup Guide

### Step 1: Fork Repository
```bash
# Fork this repository on GitHub
# Then clone your fork
git clone https://github.com/starship-droid/email-to-telegram.git
```

### Step 2: Get Email IMAP Details
```
📧 Email Provider Settings:
├── Gmail: imap.gmail.com (port 993)
├── Outlook: outlook.office365.com (port 993)
├── Yahoo: imap.mail.yahoo.com (port 993)
└── Custom: Check your provider's documentation
```

**Note:** For Gmail, use an App Password instead of your regular password.

### Step 3: Create Telegram Bot
```
🤖 Telegram Bot Setup:
1. Message @BotFather on Telegram
2. Send /newbot
3. Choose bot name and username
4. Save the bot token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)
```

### Step 4: Get Telegram Group Details
```
📱 Group Setup:
1. Add your bot to the target Telegram group
2. Make bot an admin (to post in topics)
3. Get Group ID:
   • Add @userinfobot to your group
   • Bot will show the group ID (negative number)
4. Get Topic ID:
   • Right-click on topic → Copy Link
   • Extract number from URL: t.me/c/123456789/TOPIC_ID
```

### Step 5: Configure GitHub Secrets
Go to your forked repository → Settings → Secrets and variables → Actions

Add these secrets:
```
🔐 Required Secrets:
├── EMAIL_ACCOUNT        → your-email@example.com
├── EMAIL_PASSWORD       → your-email-password-or-app-password
├── IMAP_SERVER         → imap.gmail.com
├── TELEGRAM_BOT_TOKEN  → 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
├── TELEGRAM_GROUP_ID   → -1001234567890
└── TELEGRAM_TOPIC_ID   → 123
```

### Step 6: Deploy
```
🚀 Deployment:
1. Go to Actions tab in your repository
2. Click "Email to Telegram Bot" workflow
3. Click "Run workflow" → "Run workflow"
4. Bot will now run every 10 minutes automatically
```

## 📊 Status Indicators

```
✅ Success: Email forwarded and marked as read
❌ Error:   Check Actions logs for details
⚠️  Warning: Partial failure (some images may not send)
```

## 🔧 Customization

To change the schedule, edit `.github/workflows/email_to_telegram.yml`:
```yaml
schedule:
  - cron: '*/5 * * * *'   # Every 5 minutes
  - cron: '0 * * * *'     # Every hour
  - cron: '0 9 * * *'     # Daily at 9 AM
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot not posting | Check if bot is admin in group |
| Wrong topic | Verify TELEGRAM_TOPIC_ID from topic URL |
| Email auth failed | Use app password for Gmail/Outlook |
| No emails found | Check IMAP server settings |

## 📝 Message Format

```
📧 Subject: Your Email Subject
👤 From: Sender Name <sender@email.com>
🕒 Sent: 2024-01-15 2:30 PM (AEDT)

Email body content here...
```

Images are sent as separate messages after the text content.