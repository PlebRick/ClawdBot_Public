#!/usr/bin/env python3
"""Skills Sync v2 — Python-native with format conversion.

Bi-directional sync between ~/clawd/skills/ and 02_ClawdBot/Skills/
Syncs SKILL.md files and references/ folders for each skill.

Usage:
  python3 skills-sync-v2.py pull     # Drive → Local (.md files)
  python3 skills-sync-v2.py push     # Local → Drive (Google Docs)
  python3 skills-sync-v2.py sync     # Bidirectional: pull then push
  python3 skills-sync-v2.py dry      # Show what sync would do
  python3 skills-sync-v2.py status   # Show sync state
"""

import sys
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# --- Config ---
TOKEN_FILE = os.path.expanduser("~/.config/clawd/google-tokens.json")
LOG_FILE = os.path.expanduser("~/clawd/logs/skills-sync.log")
STATE_FILE = os.path.expanduser("~/.config/clawd/skills-sync-state.json")

SKILLS_FOLDER_ID = "130M4qPxuzJZoUCBMb035vE4eblGC12e-"
LOCAL_DIR = Path.home() / "clawd" / "skills"

# Skills to sync (skill folder names)
SKILLS_TO_SYNC = ["arnoldos", "bible-brainstorm", "liturgy", "sermon-writer", "web-scout", "youtube-transcript"]


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def get_creds() -> Credentials:
    if not os.path.exists(TOKEN_FILE):
        log("ERROR: No token file. Run: python3 google-oauth.py auth")
        sys.exit(1)

    with open(TOKEN_FILE) as f:
        t = json.load(f)

    creds = Credentials(
        token=t["token"],
        refresh_token=t["refresh_token"],
        token_uri=t["token_uri"],
        client_id=t["client_id"],
        client_secret=t["client_secret"],
        scopes=t.get("scopes"),
    )

    if creds.expired or not creds.valid:
        try:
            creds.refresh(Request())
            t["token"] = creds.token
            with open(TOKEN_FILE, "w") as f:
                json.dump(t, f, indent=2)
        except Exception as e:
            log(f"ERROR: Token refresh failed — {e}")
            sys.exit(1)

    return creds


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"files": {}}


def save_state(state: dict):
    Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def get_or_create_folder(service, parent_id: str, name: str) -> str:
    """Get folder ID, create if doesn't exist."""
    results = service.files().list(
        q=f"'{parent_id}' in parents and name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)"
    ).execute()
    
    if results.get('files'):
        return results['files'][0]['id']
    
    # Create folder
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=metadata, fields='id').execute()
    log(f"  📁 Created folder: {name}")
    return folder.get('id')


def list_drive_files(service, folder_id: str) -> dict:
    """List all files in a Drive folder."""
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType, modifiedTime)"
    ).execute()
    return {f['name']: f for f in results.get('files', [])}


def push_md_to_drive(service, local_path: Path, folder_id: str, existing_files: dict):
    """Upload .md file to Drive as Google Doc."""
    name = local_path.stem  # Remove .md extension
    content = local_path.read_text(encoding='utf-8')
    
    media = MediaIoBaseUpload(
        io.BytesIO(content.encode('utf-8')),
        mimetype='text/plain',
        resumable=True
    )
    
    if name in existing_files:
        # Update existing
        file_id = existing_files[name]['id']
        service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        log(f"  ✏️  Updated: {name}")
    else:
        # Create new
        metadata = {
            'name': name,
            'parents': [folder_id],
            'mimeType': 'application/vnd.google-apps.document'
        }
        service.files().create(
            body=metadata,
            media_body=media
        ).execute()
        log(f"  ✅ Created: {name}")


def pull_doc_to_local(service, file_info: dict, local_path: Path):
    """Download Google Doc as .md file."""
    content = service.files().export(
        fileId=file_info['id'],
        mimeType='text/plain'
    ).execute()
    
    local_path.write_bytes(content)
    log(f"  ⬇️  Downloaded: {local_path.name}")


def sync_skill(service, skill_name: str, state: dict, dry_run: bool = False):
    """Sync a single skill folder."""
    log(f"Syncing skill: {skill_name}")
    
    local_skill_dir = LOCAL_DIR / skill_name
    if not local_skill_dir.exists():
        log(f"  ⚠️  Local skill folder not found: {skill_name}")
        return
    
    # Get or create skill folder on Drive
    skill_folder_id = get_or_create_folder(service, SKILLS_FOLDER_ID, skill_name)
    
    # Sync SKILL.md
    skill_md = local_skill_dir / "SKILL.md"
    if skill_md.exists():
        drive_files = list_drive_files(service, skill_folder_id)
        if not dry_run:
            push_md_to_drive(service, skill_md, skill_folder_id, drive_files)
        else:
            log(f"  [DRY] Would sync: SKILL.md")
    
    # Sync references/ folder if exists
    refs_dir = local_skill_dir / "references"
    if refs_dir.exists() and refs_dir.is_dir():
        refs_folder_id = get_or_create_folder(service, skill_folder_id, "references")
        drive_ref_files = list_drive_files(service, refs_folder_id)
        
        for md_file in refs_dir.glob("*.md"):
            if not dry_run:
                push_md_to_drive(service, md_file, refs_folder_id, drive_ref_files)
            else:
                log(f"  [DRY] Would sync: references/{md_file.name}")


def cmd_push(service, state: dict, dry_run: bool = False):
    """Push local skills to Drive."""
    log("=== PUSH: Local → Drive ===")
    for skill in SKILLS_TO_SYNC:
        sync_skill(service, skill, state, dry_run)
    if not dry_run:
        save_state(state)
    log("Push complete.")


def cmd_status(service, state: dict):
    """Show current sync status."""
    log("=== STATUS ===")
    
    # Check Drive folder
    drive_files = list_drive_files(service, SKILLS_FOLDER_ID)
    log(f"Drive Skills folder: {len(drive_files)} items")
    for name, info in sorted(drive_files.items()):
        log(f"  {name}")
    
    log(f"\nLocal skills: {len(SKILLS_TO_SYNC)}")
    for skill in SKILLS_TO_SYNC:
        skill_dir = LOCAL_DIR / skill
        skill_md = skill_dir / "SKILL.md"
        refs_count = len(list((skill_dir / "references").glob("*.md"))) if (skill_dir / "references").exists() else 0
        status = "✅" if skill_md.exists() else "❌"
        log(f"  {status} {skill} (SKILL.md + {refs_count} refs)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    
    creds = get_creds()
    service = build('drive', 'v3', credentials=creds)
    state = load_state()
    
    if cmd == "push":
        cmd_push(service, state)
    elif cmd == "pull":
        log("Pull not yet implemented — skills are primarily local-authored")
    elif cmd == "sync":
        cmd_push(service, state)  # For now, sync = push (skills are local-first)
    elif cmd == "dry":
        cmd_push(service, state, dry_run=True)
    elif cmd == "status":
        cmd_status(service, state)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
