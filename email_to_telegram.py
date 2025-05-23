import imaplib
import email
from email.header import decode_header
import os
import requests
from datetime import datetime
import pytz
import email.utils

# Configuration from environment
IMAP_SERVER = os.environ.get("IMAP_SERVER")
EMAIL_ACCOUNT = os.environ.get("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID")
TOPIC_ID = int(os.environ.get("TELEGRAM_TOPIC_ID", "0"))  # Your fixed topic id here


def send_to_telegram(subject, body, images, topic_id, sender_name, sender_email, timestamp_str):
    message_text = (
        f"📧 Subject: {subject}\n"
        f"👤 From: {sender_name} <{sender_email}>\n"
        f"🕒 Sent: {timestamp_str}\n\n"
        f"{body}"
    )
    print(f"[📤] Sending message to Telegram topic ID: {topic_id}")

    if images:
        # Send first image with caption (the message text)
        name, image = images[0]
        print(f"[🖼️] Uploading image with caption: {name}")
        photo_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': (name, image)}
        data = {
            "chat_id": GROUP_ID,
            "message_thread_id": topic_id,
            "caption": message_text
        }
        r = requests.post(photo_url, files=files, data=data)
        if not r.ok:
            raise Exception(f"[❌] Failed to send photo with caption: {r.text}")

        # Send remaining images without caption
        for name, image in images[1:]:
            print(f"[🖼️] Uploading image: {name}")
            files = {'photo': (name, image)}
            data = {
                "chat_id": GROUP_ID,
                "message_thread_id": topic_id,
            }
            r = requests.post(photo_url, files=files, data=data)
            if not r.ok:
                print(f"[⚠️] Failed to send image: {r.text}")

    else:
        # No images: send text message normally
        message_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        res = requests.post(message_url, data={
            "chat_id": GROUP_ID,
            "message_thread_id": topic_id,
            "text": message_text
        })

        if not res.ok:
            raise Exception(f"[❌] Failed to send message: {res.text}")



def parse_emails():
    print("[📬] Connecting to mailbox...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("inbox")

    result, data = mail.search(None, 'UNSEEN')
    email_ids = data[0].split()
    print(f"[📥] Found {len(email_ids)} unread emails")

    for eid in email_ids:
        print(f"\n[📧] Processing email ID: {eid.decode()}")
        _, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        subject = decode_header(msg["Subject"])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode(errors="ignore")

        sender_full = msg.get("From")
        sender_name, sender_email = email.utils.parseaddr(sender_full)
        print(f"[👤] From: {sender_name} <{sender_email}>")
        print(f"[📝] Subject: {subject}")

        # Parse date
        raw_date = msg.get("Date")
        try:
            email_datetime = email.utils.parsedate_to_datetime(raw_date)
            melbourne = pytz.timezone("Australia/Melbourne")
            email_datetime_mel = email_datetime.astimezone(melbourne)
            timestamp_str = email_datetime_mel.strftime("%Y-%m-%d %I:%M %p (%Z)")
        except Exception as e:
            print(f"[⚠️] Failed to parse date: {e}")
            timestamp_str = "Unknown"

        body = ""
        images = []

        for part in msg.walk():
            content_type = part.get_content_type()
            if part.get_content_maintype() == "multipart":
                continue
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode()
                except Exception as e:
                    print(f"[⚠️] Failed to decode body: {e}")
                    body = "[Unable to decode body]"
            elif "image" in content_type:
                filename = part.get_filename()
                img_data = part.get_payload(decode=True)
                images.append((filename or "image.jpg", img_data))

        try:
            if TOPIC_ID == 0:
                raise Exception("TELEGRAM_TOPIC_ID is not set or zero in .env")

            send_to_telegram(subject, body, images, TOPIC_ID, sender_name, sender_email, timestamp_str)

            # Mark as read only after success
            print(f"[✅] Marking email as read: {eid.decode()}")
            mail.store(eid, '+FLAGS', '\\Seen')

        except Exception as e:
            print(f"[❌] Failed to process email: {e}")

    mail.logout()
    print("\n[🔚] Done!")


if __name__ == "__main__":
    parse_emails()
