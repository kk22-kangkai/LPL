import os
import email
from email.parser import BytesParser
from email.policy import default
from datetime import datetime
import re

def parse_received_headers(headers):
    received = headers.get_all("Received", [])
    parsed = []

    for entry in received:
        # 提取时间戳
        match = re.search(r';\s*(.+)', entry)
        timestamp = match.group(1).strip() if match else "N/A"
        parsed.append({
            "hop": entry.split("\n")[0][:80] + ("..." if len(entry) > 80 else ""),
            "timestamp": timestamp
        })

    return parsed

def parse_eml_file(path):
    with open(path, 'rb') as f:
        msg = BytesParser(policy=default).parse(f)

    subject = msg.get('Subject', '')
    date = msg.get('Date', '')
    sender = msg.get('From', '')
    recipient = msg.get('To', '')
    received = parse_received_headers(msg)

    return {
        "file": os.path.basename(path),
        "subject": subject,
        "from": sender,
        "to": recipient,
        "date": date,
        "received_chain": received[::-1]  # 倒序，最早的在前
    }

def scan_eml_directory(folder):
    for root, _, files in os.walk(folder):
        for name in files:
            if name.endswith('.eml'):
                path = os.path.join(root, name)
                data = parse_eml_file(path)

                print(f"\n📩 文件: {data['file']}")
                print(f" 主题: {data['subject']}")
                print(f" 发件人: {data['from']}")
                print(f" 收件人: {data['to']}")
                print(f" 邮件头时间: {data['date']}")
                print(" ✉️ 传输路径:")
                for i, hop in enumerate(data['received_chain'], 1):
                    print(f"  [{i}] {hop['timestamp']} — {hop['hop']}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python parse_eml_flow.py <文件夹路径>")
        sys.exit(1)

    folder_path = sys.argv[1]
    scan_eml_directory("C:/Users/circu/Desktop/Login verification - acq")
