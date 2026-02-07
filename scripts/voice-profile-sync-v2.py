#!/usr/bin/env python3
"""Voice Profile Sync v2 — Python-native with format conversion.

Replaces rclone-based voice-profile-sync.sh with direct Drive API access.
Handles .md ↔ Google Docs conversion automatically.

Usage:
  python3 voice-profile-sync-v2.py pull     # Drive → Local (.md files)
  python3 voice-profile-sync-v2.py push     # Local → Drive (Google Docs)
  python3 voice-profile-sync-v2.py sync     # Bidirectional: pull then push
  python3 voice-profile-sync-v2.py dry      # Show what sync would do
  python3 voice-profile-sync-v2.py status   # Show sync state
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
LOG_FILE = os.path.expanduser("~/clawd/logs/voice-sync.log")
STATE_FILE = os.path.expanduser("~/.config/clawd/voice-sync-state.json")

VOICE_PROFILE_FOLDER_ID = "1J-sl9LqLKHosR5mDsSh3d9yF7_7eg4U3"

# Mapping: Drive path → local path (with optional rename)
FILE_MAP = {
    "core/ricks-voice-profile": "memory/context/ricks-voice-profile.md",
    "core/voice-profile-training": "memory/training/voice-profile.md",
    "core/ricks-theological-framework": "memory/context/ricks-theological-framework.md",
    "core/ricks-bio": "memory/context/ricks-bio.md",
    "core/ai-voice-calibration": "memory/training/ai-voice-calibration.md",
    "core/user-profile": "memory/context/user.md",
    "reference/voice-card": "skills/sermon-writer/references/voice-card.md",
    "reference/voice-phrases": "skills/sermon-writer/references/voice-phrases.md",
    "reference/theological-positions": "memory/context/theological-positions.md",
    "reference/recurring-themes": "memory/context/recurring-themes.md",
    "reference/sermon-structure-templates": "memory/training/sermon-structure-templates.md",
}

DIR_MAP = {
    "sermon-archive": "memory/training/sermon-archive",
    "calibration-sessions": "memory/training/calibration-sessions",
}

CLAWD_ROOT = Path.home() / "clawd"


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
    return {"files": {}}  # Single hash per file path


def save_state(state: dict):
    Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def normalize_content(content: str) -> str:
    """Normalize content for consistent hashing (strip trailing whitespace per line, ensure single trailing newline)."""
    lines = content.rstrip().split('\n')
    normalized = '\n'.join(line.rstrip() for line in lines)
    return normalized + '\n'


def hash_content(content: str) -> str:
    """Generate hash of normalized content."""
    return hashlib.md5(normalize_content(content).encode()).hexdigest()


class VoiceProfileSync:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.creds = get_creds()
        self.drive = build("drive", "v3", credentials=self.creds)
        self.state = load_state()
        self.folder_cache = {}
        
    def _get_folder_id(self, folder_name: str, parent_id: str = VOICE_PROFILE_FOLDER_ID) -> Optional[str]:
        cache_key = f"{parent_id}/{folder_name}"
        if cache_key in self.folder_cache:
            return self.folder_cache[cache_key]
            
        q = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.drive.files().list(q=q, fields="files(id)").execute()
        files = results.get("files", [])
        
        if files:
            self.folder_cache[cache_key] = files[0]["id"]
            return files[0]["id"]
        return None
    
    def _get_doc_id(self, name: str, parent_id: str) -> Optional[str]:
        q = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false"
        results = self.drive.files().list(q=q, fields="files(id)").execute()
        files = results.get("files", [])
        return files[0]["id"] if files else None
    
    def _download_doc_as_text(self, file_id: str) -> str:
        content = self.drive.files().export(fileId=file_id, mimeType="text/plain").execute()
        return content.decode("utf-8")
    
    def _upload_text_as_doc(self, name: str, content: str, parent_id: str, existing_id: Optional[str] = None):
        media = MediaIoBaseUpload(
            io.BytesIO(content.encode("utf-8")),
            mimetype="text/plain",
            resumable=True
        )
        
        if existing_id:
            self.drive.files().update(fileId=existing_id, media_body=media).execute()
        else:
            metadata = {
                "name": name,
                "parents": [parent_id],
                "mimeType": "application/vnd.google-apps.document"
            }
            self.drive.files().create(body=metadata, media_body=media, fields="id").execute()
    
    def _list_docs_in_folder(self, folder_id: str) -> list:
        q = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false"
        results = self.drive.files().list(q=q, fields="files(id, name, modifiedTime)").execute()
        return results.get("files", [])
    
    def pull(self):
        """Pull from Drive → Local (Google Docs → .md files)."""
        log("Starting PULL: Drive → Local")
        stats = {"downloaded": 0, "skipped": 0, "errors": 0}
        
        # Pull individual mapped files
        for drive_path, local_rel in FILE_MAP.items():
            try:
                parts = drive_path.split("/")
                if len(parts) == 2:
                    folder_name, doc_name = parts
                    folder_id = self._get_folder_id(folder_name)
                else:
                    doc_name = parts[0]
                    folder_id = VOICE_PROFILE_FOLDER_ID
                
                if not folder_id:
                    log(f"  ⚠️ Folder not found for {drive_path}")
                    stats["errors"] += 1
                    continue
                
                doc_id = self._get_doc_id(doc_name, folder_id)
                if not doc_id:
                    log(f"  ⚠️ Doc not found: {drive_path}")
                    stats["errors"] += 1
                    continue
                
                content = self._download_doc_as_text(doc_id)
                content_hash = hash_content(content)
                local_path = CLAWD_ROOT / local_rel
                
                # Check if file exists and matches
                if local_path.exists():
                    local_content = local_path.read_text()
                    if hash_content(local_content) == content_hash:
                        stats["skipped"] += 1
                        continue
                
                if self.dry_run:
                    log(f"  🔍 Would download: {drive_path} → {local_rel}")
                else:
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    local_path.write_text(normalize_content(content))
                    self.state["files"][local_rel] = content_hash
                    log(f"  ✅ {drive_path} → {local_rel}")
                
                stats["downloaded"] += 1
                
            except Exception as e:
                log(f"  ❌ Error pulling {drive_path}: {e}")
                stats["errors"] += 1
        
        # Pull directory mappings
        for drive_dir, local_dir_rel in DIR_MAP.items():
            try:
                folder_id = self._get_folder_id(drive_dir)
                if not folder_id:
                    log(f"  ⚠️ Directory not found: {drive_dir}")
                    continue
                
                docs = self._list_docs_in_folder(folder_id)
                local_dir = CLAWD_ROOT / local_dir_rel
                
                for doc in docs:
                    doc_name = doc["name"]
                    local_file = local_dir / f"{doc_name}.md"
                    local_rel = f"{local_dir_rel}/{doc_name}.md"
                    
                    content = self._download_doc_as_text(doc["id"])
                    content_hash = hash_content(content)
                    
                    # Check if file exists and matches
                    if local_file.exists():
                        local_content = local_file.read_text()
                        if hash_content(local_content) == content_hash:
                            stats["skipped"] += 1
                            continue
                    
                    if self.dry_run:
                        log(f"  🔍 Would download: {drive_dir}/{doc_name} → {local_rel}")
                    else:
                        local_dir.mkdir(parents=True, exist_ok=True)
                        local_file.write_text(normalize_content(content))
                        self.state["files"][local_rel] = content_hash
                        log(f"  ✅ {drive_dir}/{doc_name} → {local_rel}")
                    
                    stats["downloaded"] += 1
                    
            except Exception as e:
                log(f"  ❌ Error pulling directory {drive_dir}: {e}")
                stats["errors"] += 1
        
        if not self.dry_run:
            save_state(self.state)
        
        log(f"Pull complete: {stats['downloaded']} downloaded, {stats['skipped']} unchanged, {stats['errors']} errors")
        return stats
    
    def push(self):
        """Push from Local → Drive (.md files → Google Docs)."""
        log("Starting PUSH: Local → Drive")
        stats = {"uploaded": 0, "skipped": 0, "errors": 0}
        
        # Push individual mapped files
        for drive_path, local_rel in FILE_MAP.items():
            try:
                local_path = CLAWD_ROOT / local_rel
                if not local_path.exists():
                    log(f"  ⚠️ Local file missing: {local_rel}")
                    stats["errors"] += 1
                    continue
                
                content = local_path.read_text()
                content_hash = hash_content(content)
                
                # Check if unchanged from last sync
                if self.state["files"].get(local_rel) == content_hash:
                    stats["skipped"] += 1
                    continue
                
                parts = drive_path.split("/")
                if len(parts) == 2:
                    folder_name, doc_name = parts
                    folder_id = self._get_folder_id(folder_name)
                else:
                    doc_name = parts[0]
                    folder_id = VOICE_PROFILE_FOLDER_ID
                
                if not folder_id:
                    log(f"  ⚠️ Folder not found for {drive_path}")
                    stats["errors"] += 1
                    continue
                
                existing_id = self._get_doc_id(doc_name, folder_id)
                
                if self.dry_run:
                    action = "update" if existing_id else "create"
                    log(f"  🔍 Would {action}: {local_rel} → {drive_path}")
                else:
                    self._upload_text_as_doc(doc_name, content, folder_id, existing_id)
                    self.state["files"][local_rel] = content_hash
                    log(f"  ✅ {local_rel} → {drive_path}")
                
                stats["uploaded"] += 1
                
            except Exception as e:
                log(f"  ❌ Error pushing {local_rel}: {e}")
                stats["errors"] += 1
        
        # Push directory mappings
        for drive_dir, local_dir_rel in DIR_MAP.items():
            try:
                local_dir = CLAWD_ROOT / local_dir_rel
                if not local_dir.exists():
                    log(f"  ⚠️ Local directory missing: {local_dir_rel}")
                    continue
                
                folder_id = self._get_folder_id(drive_dir)
                if not folder_id:
                    log(f"  ⚠️ Drive folder not found: {drive_dir}")
                    continue
                
                for local_file in local_dir.glob("*.md"):
                    doc_name = local_file.stem
                    local_rel = f"{local_dir_rel}/{local_file.name}"
                    content = local_file.read_text()
                    content_hash = hash_content(content)
                    
                    if self.state["files"].get(local_rel) == content_hash:
                        stats["skipped"] += 1
                        continue
                    
                    existing_id = self._get_doc_id(doc_name, folder_id)
                    
                    if self.dry_run:
                        action = "update" if existing_id else "create"
                        log(f"  🔍 Would {action}: {local_rel} → {drive_dir}/{doc_name}")
                    else:
                        self._upload_text_as_doc(doc_name, content, folder_id, existing_id)
                        self.state["files"][local_rel] = content_hash
                        log(f"  ✅ {local_rel} → {drive_dir}/{doc_name}")
                    
                    stats["uploaded"] += 1
                    
            except Exception as e:
                log(f"  ❌ Error pushing directory {local_dir_rel}: {e}")
                stats["errors"] += 1
        
        if not self.dry_run:
            save_state(self.state)
        
        log(f"Push complete: {stats['uploaded']} uploaded, {stats['skipped']} unchanged, {stats['errors']} errors")
        return stats
    
    def sync(self):
        """Bidirectional sync: pull then push."""
        log("Starting BIDIRECTIONAL SYNC")
        pull_stats = self.pull()
        push_stats = self.push()
        log("Bidirectional sync complete")
        return {"pull": pull_stats, "push": push_stats}
    
    def status(self):
        print(f"Voice Profile Sync v2")
        print(f"=" * 40)
        print(f"Drive folder: {VOICE_PROFILE_FOLDER_ID}")
        print(f"Local root:   {CLAWD_ROOT}")
        print(f"State file:   {STATE_FILE}")
        print(f"Log file:     {LOG_FILE}")
        print()
        
        local_count = 0
        for local_rel in FILE_MAP.values():
            if (CLAWD_ROOT / local_rel).exists():
                local_count += 1
        for local_dir_rel in DIR_MAP.values():
            local_dir = CLAWD_ROOT / local_dir_rel
            if local_dir.exists():
                local_count += len(list(local_dir.glob("*.md")))
        
        print(f"Local .md files tracked: {local_count}")
        print(f"State entries:           {len(self.state.get('files', {}))}")
        print()
        
        print("Last sync activity:")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE) as f:
                lines = f.readlines()[-5:]
                for line in lines:
                    print(f"  {line.rstrip()}")
        else:
            print("  (no log yet)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "pull":
        sync = VoiceProfileSync()
        sync.pull()
    elif cmd == "push":
        sync = VoiceProfileSync()
        sync.push()
    elif cmd == "sync":
        sync = VoiceProfileSync()
        sync.sync()
    elif cmd == "dry":
        print("🔍 DRY RUN — no changes will be made\n")
        sync = VoiceProfileSync(dry_run=True)
        sync.sync()
    elif cmd == "status":
        sync = VoiceProfileSync()
        sync.status()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
