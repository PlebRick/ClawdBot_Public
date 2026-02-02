#!/usr/bin/env python3
"""Sync ~/Projects/ to Google Drive 'ricks-projects' folder.

Mirrors the folder structure recursively. Uploads .md files as Google Docs,
other text files as-is. Skips .git, node_modules, __pycache__, .trash.

Usage: python3 sync-projects-drive.py <local_projects_dir> <drive_folder_id>
"""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from arnoldos import get_creds, api_get

import requests

MIME_GDOC = "application/vnd.google-apps.document"
MIME_FOLDER = "application/vnd.google-apps.folder"

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".trash", ".venv"}
SYNC_EXTENSIONS = {".md", ".txt", ".json", ".js", ".py", ".sh", ".csv"}


def list_drive_files(creds, folder_id):
    result = api_get(creds, "https://www.googleapis.com/drive/v3/files", {
        "q": f"'{folder_id}' in parents and trashed=false",
        "fields": "files(id,name,mimeType)",
        "spaces": "drive",
        "pageSize": "200"
    })
    return result.get("files", [])


def find_or_create_folder(creds, parent_id, name):
    """Find existing subfolder or create it."""
    files = list_drive_files(creds, parent_id)
    for f in files:
        if f["name"] == name and f["mimeType"] == MIME_FOLDER:
            return f["id"]
    # Create
    metadata = {"name": name, "parents": [parent_id], "mimeType": MIME_FOLDER}
    resp = requests.post(
        "https://www.googleapis.com/drive/v3/files",
        headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
        json=metadata
    )
    resp.raise_for_status()
    folder_id = resp.json()["id"]
    print(f"  📁 Created folder: {name}")
    return folder_id


def _create_file(creds, folder_id, name, content_bytes, as_gdoc=False):
    """Create a file on Drive via multipart upload."""
    metadata = {"name": name, "parents": [folder_id]}
    if as_gdoc:
        metadata["mimeType"] = MIME_GDOC
    boundary = "----ProjectsSync"
    body = (
        f"--{boundary}\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/plain; charset=UTF-8\r\n\r\n"
    ).encode("utf-8") + content_bytes + f"\r\n--{boundary}--".encode("utf-8")
    resp = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        headers={
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": f"multipart/related; boundary={boundary}"
        },
        data=body, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def upload_or_update(creds, folder_id, name, content, as_gdoc=False):
    """Upload a new file or update existing one."""
    files = list_drive_files(creds, folder_id)
    
    # For .md files uploaded as Google Docs, the Drive name has no extension
    drive_name = name[:-3] if as_gdoc and name.endswith(".md") else name
    
    existing = None
    for f in files:
        if f["name"] == drive_name:
            existing = f
            break

    content_bytes = content.encode("utf-8") if isinstance(content, str) else content
    upload_mime = "text/plain"

    if existing:
        # Delete and recreate (media PATCH doesn't work on converted Google Docs)
        requests.delete(
            f"https://www.googleapis.com/drive/v3/files/{existing['id']}",
            headers={"Authorization": f"Bearer {creds.token}"},
            timeout=15
        ).raise_for_status()
        _create_file(creds, folder_id, drive_name, content_bytes, as_gdoc)
        print(f"  ✏️  Updated: {drive_name}")
    else:
        _create_file(creds, folder_id, drive_name, content_bytes, as_gdoc)
        print(f"  ✅ Created: {drive_name}")


def sync_directory(creds, local_dir, drive_folder_id, depth=0):
    """Recursively sync a local directory to Drive."""
    entries = sorted(os.listdir(local_dir))
    
    for entry in entries:
        full_path = os.path.join(local_dir, entry)
        
        if entry in SKIP_DIRS or entry.startswith("."):
            continue
        
        if os.path.isdir(full_path):
            subfolder_id = find_or_create_folder(creds, drive_folder_id, entry)
            sync_directory(creds, full_path, subfolder_id, depth + 1)
        
        elif os.path.isfile(full_path):
            _, ext = os.path.splitext(entry)
            if ext not in SYNC_EXTENSIONS:
                continue
            
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except (UnicodeDecodeError, PermissionError):
                continue
            
            as_gdoc = ext == ".md"
            upload_or_update(creds, drive_folder_id, entry, content, as_gdoc=as_gdoc)


def main():
    if len(sys.argv) < 3:
        print("Usage: sync-projects-drive.py <local_dir> <drive_parent_id> [--name <subfolder>]")
        sys.exit(1)
    
    local_dir = sys.argv[1]
    drive_parent_id = sys.argv[2]
    
    # Optional --name flag to sync into a named subfolder
    project_name = None
    if "--name" in sys.argv:
        idx = sys.argv.index("--name")
        if idx + 1 < len(sys.argv):
            project_name = sys.argv[idx + 1]
    
    if not os.path.isdir(local_dir):
        print(f"Error: {local_dir} is not a directory")
        sys.exit(1)
    
    creds = get_creds()
    
    # If --name given, find or create that subfolder first
    if project_name:
        drive_folder_id = find_or_create_folder(creds, drive_parent_id, project_name)
    else:
        drive_folder_id = drive_parent_id
    
    print(f"Syncing {local_dir} → Drive ({project_name or 'root'})...")
    sync_directory(creds, local_dir, drive_folder_id)
    print("Done!")


if __name__ == "__main__":
    main()
