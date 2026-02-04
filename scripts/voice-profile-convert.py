#!/usr/bin/env python3
"""Convert raw .md files in Drive Voice-Profile to Google Docs.

One-time migration script. For each .md file:
1. Download content
2. Create Google Doc with same name (minus .md)
3. Optionally delete original .md

Usage:
  python3 voice-profile-convert.py list       # Show files to convert
  python3 voice-profile-convert.py convert    # Do the conversion
  python3 voice-profile-convert.py cleanup    # Delete raw .md files after conversion
"""

import sys
import os
import json
import requests

sys.path.insert(0, os.path.dirname(__file__))
from arnoldos import get_creds

MIME_GDOC = "application/vnd.google-apps.document"
MIME_MD = "text/markdown"
MIME_PLAIN = "text/plain"

# Voice-Profile folder structure
VOICE_PROFILE_ROOT = "01_ArnoldOS_Gemini/Ministry/Voice-Profile"
SUBFOLDERS = ["core", "reference", "sermon-archive", "calibration-sessions"]


def get_folder_id(creds, path):
    """Get folder ID by path (e.g., '01_ArnoldOS_Gemini/Ministry/Voice-Profile/core')"""
    parts = path.split("/")
    parent_id = "root"
    
    for part in parts:
        url = "https://www.googleapis.com/drive/v3/files"
        params = {
            "q": f"'{parent_id}' in parents and name='{part}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            "fields": "files(id,name)",
        }
        r = requests.get(url, headers={"Authorization": f"Bearer {creds.token}"}, params=params, timeout=15)
        r.raise_for_status()
        files = r.json().get("files", [])
        if not files:
            return None
        parent_id = files[0]["id"]
    
    return parent_id


def list_files(creds, folder_id):
    """List all files in a folder."""
    url = "https://www.googleapis.com/drive/v3/files"
    params = {
        "q": f"'{folder_id}' in parents and trashed=false",
        "fields": "files(id,name,mimeType,modifiedTime)",
        "pageSize": "200",
    }
    r = requests.get(url, headers={"Authorization": f"Bearer {creds.token}"}, params=params, timeout=15)
    r.raise_for_status()
    return r.json().get("files", [])


def download_file(creds, file_id):
    """Download file content."""
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
    params = {"alt": "media"}
    r = requests.get(url, headers={"Authorization": f"Bearer {creds.token}"}, params=params, timeout=30)
    r.raise_for_status()
    return r.text


def create_google_doc(creds, folder_id, name, content):
    """Create a Google Doc with given content."""
    metadata = {
        "name": name,
        "parents": [folder_id],
        "mimeType": MIME_GDOC,
    }
    
    boundary = "----VoiceProfileConvert"
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
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        data=body.encode("utf-8"),
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def delete_file(creds, file_id):
    """Delete a file."""
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
    r = requests.delete(url, headers={"Authorization": f"Bearer {creds.token}"}, timeout=15)
    r.raise_for_status()


def cmd_list(creds):
    """List all .md files that need conversion."""
    print("Files to convert:\n")
    total = 0
    
    for subfolder in SUBFOLDERS:
        path = f"{VOICE_PROFILE_ROOT}/{subfolder}"
        folder_id = get_folder_id(creds, path)
        if not folder_id:
            print(f"  {subfolder}/: folder not found")
            continue
        
        files = list_files(creds, folder_id)
        md_files = [f for f in files if f["name"].endswith(".md")]
        docs = [f for f in files if f["mimeType"] == MIME_GDOC]
        
        print(f"  {subfolder}/:")
        print(f"    Raw .md files: {len(md_files)}")
        print(f"    Google Docs:   {len(docs)}")
        
        for f in md_files:
            doc_name = f["name"][:-3]  # strip .md
            has_doc = any(d["name"] == doc_name for d in docs)
            status = "✓ has Doc" if has_doc else "⚠ needs conversion"
            print(f"      {f['name']} → {status}")
        
        total += len([f for f in md_files if not any(d["name"] == f["name"][:-3] for d in docs)])
    
    print(f"\nTotal needing conversion: {total}")


def cmd_convert(creds):
    """Convert all .md files to Google Docs."""
    print("Converting .md files to Google Docs...\n")
    converted = 0
    skipped = 0
    
    for subfolder in SUBFOLDERS:
        path = f"{VOICE_PROFILE_ROOT}/{subfolder}"
        folder_id = get_folder_id(creds, path)
        if not folder_id:
            continue
        
        files = list_files(creds, folder_id)
        md_files = [f for f in files if f["name"].endswith(".md")]
        docs = [f for f in files if f["mimeType"] == MIME_GDOC]
        
        for f in md_files:
            doc_name = f["name"][:-3]
            
            # Skip if Doc already exists
            if any(d["name"] == doc_name for d in docs):
                print(f"  ⏭ {subfolder}/{f['name']} — Doc exists, skipping")
                skipped += 1
                continue
            
            # Download and convert
            print(f"  📄 {subfolder}/{f['name']} → {doc_name}")
            content = download_file(creds, f["id"])
            create_google_doc(creds, folder_id, doc_name, content)
            converted += 1
    
    print(f"\nConverted: {converted}, Skipped: {skipped}")


def cmd_cleanup(creds):
    """Delete raw .md files (only if Google Doc exists)."""
    print("Cleaning up raw .md files...\n")
    deleted = 0
    
    for subfolder in SUBFOLDERS:
        path = f"{VOICE_PROFILE_ROOT}/{subfolder}"
        folder_id = get_folder_id(creds, path)
        if not folder_id:
            continue
        
        files = list_files(creds, folder_id)
        md_files = [f for f in files if f["name"].endswith(".md")]
        docs = [f for f in files if f["mimeType"] == MIME_GDOC]
        
        for f in md_files:
            doc_name = f["name"][:-3]
            
            # Only delete if Doc exists
            if any(d["name"] == doc_name for d in docs):
                print(f"  🗑 {subfolder}/{f['name']}")
                delete_file(creds, f["id"])
                deleted += 1
            else:
                print(f"  ⚠ {subfolder}/{f['name']} — no Doc, keeping")
    
    print(f"\nDeleted: {deleted}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    creds = get_creds()
    
    if cmd == "list":
        cmd_list(creds)
    elif cmd == "convert":
        cmd_convert(creds)
    elif cmd == "cleanup":
        cmd_cleanup(creds)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
