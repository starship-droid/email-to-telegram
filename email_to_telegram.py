import imaplib
import email
from email.header import decode_header
import os
import requests
from datetime import datetime
import pytz
import email.utils
import mimetypes
import io
import traceback
import json
from dotenv import load_dotenv
load_dotenv()

# Configuration from environment
IMAP_SERVER = os.environ.get("IMAP_SERVER")
EMAIL_ACCOUNT = os.environ.get("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID")
TOPIC_ID = int(os.environ.get("TELEGRAM_TOPIC_ID", "0"))


def send_telegram_text(text, topic_id):
    """Sends a plain text message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    res = requests.post(url, data={
        "chat_id": GROUP_ID,
        "message_thread_id": topic_id,
        "text": text
    })
    if not res.ok:
        print(f"[❌] Failed to send Telegram text message: {res.text}")


def send_to_telegram(subject, body, attachments, topic_id, sender_name, sender_email, timestamp_str):
    header = (
        f"📧 Subject: {subject}\n"
        f"👤 From: {sender_name} <{sender_email}>\n"
        f"🕒 Sent: {timestamp_str}\n\n"
    )

    full_message = header + body

    def split_text(text, max_length=4096):
        parts = []
        while len(text) > max_length:
            split_point = text.rfind("\n", 0, max_length)
            if split_point == -1:
                split_point = max_length
            parts.append(text[:split_point])
            text = text[split_point:].lstrip()
        parts.append(text)
        return parts

    message_parts = split_text(full_message)

    for idx, msg_part in enumerate(message_parts):
        print(f"[📤] Sending text part {idx + 1}/{len(message_parts)}")
        send_telegram_text(msg_part, topic_id)

    if not attachments:
        return

    MAX_MEDIA_PER_GROUP = 10
    grouped_media_by_type = {"photo": [], "video": [], "document": []}
    files = {}

    for i, (filename, filedata) in enumerate(attachments):
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"

        maintype = mime_type.split("/")[0]

        if maintype == "image":
            media_type = "photo"
        elif maintype == "video":
            media_type = "video"
        else:
            media_type = "document"

        fieldname = f"attachment{i}"
        files[fieldname] = (filename, io.BytesIO(filedata))

        media_item = {
            "type": media_type,
            "media": f"attach://{fieldname}"
        }
        if len(grouped_media_by_type[media_type]) == 0:
            media_item["caption"] = ""  # optional caption on first file

        grouped_media_by_type[media_type].append((media_item, fieldname))

    for media_type, items in grouped_media_by_type.items():
        if not items:
            continue

        print(f"[📎] Sending {len(items)} '{media_type}' attachments in media groups")

        # Send in chunks of MAX_MEDIA_PER_GROUP
        for i in range(0, len(items), MAX_MEDIA_PER_GROUP):
            chunk = items[i:i + MAX_MEDIA_PER_GROUP]
            chunk_media = [item[0] for item in chunk]
            chunk_file_keys = [item[1] for item in chunk]
            chunk_files = {k: files[k] for k in chunk_file_keys}

            print(f"[📎] Sending media group {i // MAX_MEDIA_PER_GROUP + 1} with {len(chunk)} items")
            send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMediaGroup"
            payload = {
                "chat_id": GROUP_ID,
                "message_thread_id": topic_id,
                "media": json.dumps(chunk_media)
            }

            response = requests.post(send_url, data=payload, files=chunk_files)
            if not response.ok:
                error_text = (
                    f"⚠️ Failed to send media group ({media_type}): {response.text}"
                )
                print(f"[⚠️] {error_text}")
                send_telegram_text(error_text, topic_id)
            else:
                print(f"[✅] Media group {i // MAX_MEDIA_PER_GROUP + 1} sent successfully")



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
        try:
            _, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode(errors="ignore")

            sender_full = msg.get("From")
            sender_name, sender_email = email.utils.parseaddr(sender_full)
            print(f"[👤] From: {sender_name} <{sender_email}>")
            print(f"[📝] Subject: {subject}")

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
            attachments = []

            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition") or "")

                if part.get_content_maintype() == "multipart":
                    continue

                is_attachment = (
                    "attachment" in content_disposition.lower()
                    or "inline" in content_disposition.lower()
                    or part.get_filename()
                )

                if content_type == "text/plain" and not is_attachment:
                    try:
                        body = part.get_payload(decode=True).decode()
                    except Exception as e:
                        print(f"[⚠️] Failed to decode body: {e}")
                        body = "[Unable to decode body]"
                elif is_attachment:
                    filename = part.get_filename() or "file"
                    filedata = part.get_payload(decode=True)
                    attachments.append((filename, filedata))

            if TOPIC_ID == 0:
                raise Exception("TELEGRAM_TOPIC_ID is not set or zero in .env")

            send_to_telegram(subject, body, attachments, TOPIC_ID, sender_name, sender_email, timestamp_str)

            print(f"[✅] Marking email as read: {eid.decode()}")
            mail.store(eid, '+FLAGS', '\\Seen')

        except Exception as e:
            error_message = (
                f"❌ *Failed to process email ID {eid.decode()}*\n"
                f"📝 Subject: {subject if 'subject' in locals() else 'Unknown'}\n"
                f"💥 Error: {str(e)}\n"
                f"🧵 Check logs for full traceback."
            )
            print("[❌] Exception:", traceback.format_exc())
            send_telegram_text(error_message, TOPIC_ID)

    mail.logout()
    print("\n[🔚] Done!")


if __name__ == "__main__":
    parse_emails()
