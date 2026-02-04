#!/usr/bin/env python3
"""Convert .md files in Voice-Profile to Google Docs, then delete originals."""

import os
import sys
import json
import time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

TOKEN_FILE = os.path.expanduser("~/.config/clawd/google-tokens.json")

def get_creds():
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"]
    )
    # Refresh if needed
    if creds.expired:
        creds.refresh(Request())
    return creds

creds = get_creds()
drive = build("drive", "v3", credentials=creds)

def find_folder(name, parent_id=None):
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    results = drive.files().list(q=q, fields="files(id, name)").execute()
    files = results.get("files", [])
    return files[0] if files else None

def get_md_files(folder_id, path=""):
    """Get all .md files recursively."""
    results = drive.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType)",
        pageSize=100
    ).execute()
    
    files = []
    for f in results.get("files", []):
        if f["mimeType"] == "application/vnd.google-apps.folder":
            files.extend(get_md_files(f["id"], f"{path}/{f['name']}"))
        elif f["name"].endswith(".md"):
            files.append({
                "id": f["id"],
                "name": f["name"],
                "parent_id": folder_id,
                "path": path
            })
    return files

def convert_file(file_info, dry_run=False):
    """Convert a single .md file to Google Doc."""
    file_id = file_info["id"]
    name = file_info["name"]
    parent_id = file_info["parent_id"]
    doc_name = name.rsplit(".md", 1)[0]  # Remove .md extension
    
    # Check if Doc already exists
    q = f"name='{doc_name}' and mimeType='application/vnd.google-apps.document' and '{parent_id}' in parents and trashed=false"
    existing = drive.files().list(q=q, fields="files(id)").execute().get("files", [])
    
    if existing:
        print(f"  ⏭️  {name} → Doc already exists, skipping")
        return "skipped"
    
    if dry_run:
        print(f"  🔍 {name} → would convert to '{doc_name}'")
        return "would_convert"
    
    try:
        # Download .md content
        content = drive.files().get_media(fileId=file_id).execute().decode("utf-8")
        
        # Create Google Doc with the content
        # Upload as text/plain, convert to Google Doc
        file_metadata = {
            "name": doc_name,
            "parents": [parent_id],
            "mimeType": "application/vnd.google-apps.document"
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(content.encode("utf-8")),
            mimetype="text/plain",
            resumable=True
        )
        
        new_doc = drive.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        
        # Delete original .md file
        drive.files().delete(fileId=file_id).execute()
        
        print(f"  ✅ {name} → {doc_name}")
        return "converted"
        
    except Exception as e:
        print(f"  ❌ {name} → ERROR: {e}")
        return "error"

def main():
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN - no changes will be made\n")
    
    # Navigate to Voice-Profile
    arnoldos = find_folder("01_ArnoldOS_Gemini")
    ministry = find_folder("Ministry", arnoldos["id"])
    voice_profile = find_folder("Voice-Profile", ministry["id"])
    
    print(f"📁 Voice-Profile folder: {voice_profile['id']}\n")
    
    # Get all .md files
    md_files = get_md_files(voice_profile["id"])
    print(f"Found {len(md_files)} .md files to convert\n")
    
    stats = {"converted": 0, "skipped": 0, "error": 0, "would_convert": 0}
    
    for f in sorted(md_files, key=lambda x: x["path"] + "/" + x["name"]):
        path_display = f["path"] or "(root)"
        if stats["converted"] + stats["skipped"] + stats["error"] == 0 or \
           md_files[md_files.index(f)-1]["path"] != f["path"]:
            print(f"\n📁 {path_display}")
        
        result = convert_file(f, dry_run)
        stats[result] += 1
        
        # Small delay to avoid rate limits
        if not dry_run:
            time.sleep(0.3)
    
    print(f"\n{'='*50}")
    print(f"📊 Results:")
    if dry_run:
        print(f"   Would convert: {stats['would_convert']}")
        print(f"   Would skip:    {stats['skipped']}")
    else:
        print(f"   Converted: {stats['converted']}")
        print(f"   Skipped:   {stats['skipped']}")
        print(f"   Errors:    {stats['error']}")

if __name__ == "__main__":
    main()
