#!/usr/bin/env python3
"""Sync supervisor-project/ Markdown files to Google Drive as Google Docs.

Usage: python3 sync-supervisor-drive.py <local_dir> <drive_folder_id>

For each .md file in local_dir:
  - If a Google Doc with the same name (minus .md) exists in the Drive folder → update it
  - If not → create it
  
Files are uploaded as plain text (text/plain) and converted to Google Docs via Drive API.
"""

import sys, os, json, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from arnoldos import get_creds, api_get

import requests

MIME_GDOC = "application/vnd.google-apps.document"


def list_drive_files(creds, folder_id):
    """List all files in a Drive folder."""
    result = api_get(creds, "https://www.googleapis.com/drive/v3/files", {
        "q": f"'{folder_id}' in parents and trashed=false",
        "fields": "files(id,name,mimeType)",
        "spaces": "drive",
        "pageSize": "100"
    })
    return result.get("files", [])


def upload_new(creds, folder_id, name, content):
    """Create a new Google Doc from text content."""
    metadata = {
        "name": name,
        "parents": [folder_id],
        "mimeType": MIME_GDOC
    }
    
    # Multipart upload with conversion
    import io
    boundary = "----SupervisorSync"
    body = (
        f"--{boundary}\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/plain; charset=UTF-8\r\n\r\n"
        f"{content}\r\n"
        f"--{boundary}--"
    )
    
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        headers={
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": f"multipart/related; boundary={boundary}"
        },
        data=body.encode("utf-8"),
        timeout=30
    )
    r.raise_for_status()
    return r.json()


def update_existing(creds, file_id, folder_id, name, content):
    """Update a Google Doc by deleting and recreating (media PATCH doesn't work on converted Docs)."""
    # Delete existing
    r = requests.delete(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        headers={"Authorization": f"Bearer {creds.token}"},
        timeout=15
    )
    r.raise_for_status()
    
    # Recreate
    return upload_new(creds, folder_id, name, content)


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <local_dir> <drive_folder_id>")
        sys.exit(1)
    
    local_dir = sys.argv[1]
    folder_id = sys.argv[2]
    
    creds = get_creds()
    
    # Get existing Drive files
    drive_files = list_drive_files(creds, folder_id)
    drive_map = {f["name"]: f["id"] for f in drive_files}
    
    # Process each .md file
    md_files = sorted(f for f in os.listdir(local_dir) if f.endswith(".md"))
    
    created = 0
    updated = 0
    
    for filename in md_files:
        filepath = os.path.join(local_dir, filename)
        doc_name = filename[:-3]  # strip .md
        
        with open(filepath, "r") as f:
            content = f.read()
        
        if doc_name in drive_map:
            update_existing(creds, drive_map[doc_name], folder_id, doc_name, content)
            print(f"  ✅ Updated: {doc_name}")
            updated += 1
        else:
            upload_new(creds, folder_id, doc_name, content)
            print(f"  📄 Created: {doc_name}")
            created += 1
    
    print(f"\nSync complete: {created} created, {updated} updated, {len(md_files)} total files")


if __name__ == "__main__":
    main()
