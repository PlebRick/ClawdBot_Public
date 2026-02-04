#!/usr/bin/env python3
"""Supervisor Project Sync v2 — Python-native with format conversion.

Bi-directional sync between ~/clawd/supervisor-project/ and 02_ClawdBot/supervisor-project
Handles .md ↔ Google Docs conversion automatically.

Usage:
  python3 supervisor-sync-v2.py pull     # Drive → Local (.md files)
  python3 supervisor-sync-v2.py push     # Local → Drive (Google Docs)
  python3 supervisor-sync-v2.py sync     # Bidirectional: pull then push
  python3 supervisor-sync-v2.py dry      # Show what sync would do
  python3 supervisor-sync-v2.py status   # Show sync state
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
LOG_FILE = os.path.expanduser("~/clawd/logs/supervisor-sync.log")
STATE_FILE = os.path.expanduser("~/.config/clawd/supervisor-sync-state.json")

SUPERVISOR_FOLDER_ID = "1X1DQbFF_2eR_jpS3cyqlI1OcgeD3cglP"
LOCAL_DIR = Path.home() / "clawd" / "supervisor-project"

# Subfolders to sync (Drive subfolder name → local subfolder name)
SUBFOLDERS = {
    "PRDs": "PRDs",
}


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


def normalize_content(content: str) -> str:
    """Normalize content for consistent hashing."""
    lines = content.rstrip().split('\n')
    normalized = '\n'.join(line.rstrip() for line in lines)
    return normalized + '\n'


def hash_content(content: str) -> str:
    return hashlib.md5(normalize_content(content).encode()).hexdigest()


class SupervisorSync:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.creds = get_creds()
        self.drive = build("drive", "v3", credentials=self.creds)
        self.state = load_state()
        self.folder_cache = {}
        
    def _get_folder_id(self, folder_name: str, parent_id: str) -> Optional[str]:
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
    
    def _create_folder(self, name: str, parent_id: str) -> str:
        """Create a folder in Drive."""
        metadata = {
            "name": name,
            "parents": [parent_id],
            "mimeType": "application/vnd.google-apps.folder"
        }
        folder = self.drive.files().create(body=metadata, fields="id").execute()
        return folder["id"]
    
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
        results = self.drive.files().list(q=q, fields="files(id, name)").execute()
        return results.get("files", [])
    
    def _sync_folder(self, drive_folder_id: str, local_dir: Path, direction: str, stats: dict):
        """Sync a single folder (pull or push)."""
        
        if direction == "pull":
            # Download all docs from Drive folder
            docs = self._list_docs_in_folder(drive_folder_id)
            
            for doc in docs:
                doc_name = doc["name"]
                local_file = local_dir / f"{doc_name}.md"
                local_rel = str(local_file.relative_to(LOCAL_DIR))
                
                try:
                    content = self._download_doc_as_text(doc["id"])
                    content_hash = hash_content(content)
                    
                    # Check if file exists and matches
                    if local_file.exists():
                        local_content = local_file.read_text()
                        if hash_content(local_content) == content_hash:
                            stats["skipped"] += 1
                            continue
                    
                    if self.dry_run:
                        log(f"  🔍 Would download: {doc_name} → {local_rel}")
                    else:
                        local_dir.mkdir(parents=True, exist_ok=True)
                        local_file.write_text(normalize_content(content))
                        self.state["files"][local_rel] = content_hash
                        log(f"  ✅ {doc_name} → {local_rel}")
                    
                    stats["transferred"] += 1
                    
                except Exception as e:
                    log(f"  ❌ Error: {doc_name} — {e}")
                    stats["errors"] += 1
        
        elif direction == "push":
            # Upload all .md files to Drive folder
            if not local_dir.exists():
                return
                
            for local_file in local_dir.glob("*.md"):
                doc_name = local_file.stem  # filename without .md
                local_rel = str(local_file.relative_to(LOCAL_DIR))
                
                try:
                    content = local_file.read_text()
                    content_hash = hash_content(content)
                    
                    # Check if unchanged
                    if self.state["files"].get(local_rel) == content_hash:
                        stats["skipped"] += 1
                        continue
                    
                    existing_id = self._get_doc_id(doc_name, drive_folder_id)
                    
                    if self.dry_run:
                        action = "update" if existing_id else "create"
                        log(f"  🔍 Would {action}: {local_rel} → {doc_name}")
                    else:
                        self._upload_text_as_doc(doc_name, content, drive_folder_id, existing_id)
                        self.state["files"][local_rel] = content_hash
                        log(f"  ✅ {local_rel} → {doc_name}")
                    
                    stats["transferred"] += 1
                    
                except Exception as e:
                    log(f"  ❌ Error: {local_rel} — {e}")
                    stats["errors"] += 1
    
    def pull(self):
        """Pull from Drive → Local."""
        log("Starting PULL: Drive → Local")
        stats = {"transferred": 0, "skipped": 0, "errors": 0}
        
        # Sync root folder
        log("  [root]")
        self._sync_folder(SUPERVISOR_FOLDER_ID, LOCAL_DIR, "pull", stats)
        
        # Sync subfolders
        for drive_subfolder, local_subfolder in SUBFOLDERS.items():
            subfolder_id = self._get_folder_id(drive_subfolder, SUPERVISOR_FOLDER_ID)
            if subfolder_id:
                log(f"  [{drive_subfolder}/]")
                local_subdir = LOCAL_DIR / local_subfolder
                self._sync_folder(subfolder_id, local_subdir, "pull", stats)
        
        if not self.dry_run:
            save_state(self.state)
        
        log(f"Pull complete: {stats['transferred']} downloaded, {stats['skipped']} unchanged, {stats['errors']} errors")
        return stats
    
    def push(self):
        """Push from Local → Drive."""
        log("Starting PUSH: Local → Drive")
        stats = {"transferred": 0, "skipped": 0, "errors": 0}
        
        # Sync root folder
        log("  [root]")
        self._sync_folder(SUPERVISOR_FOLDER_ID, LOCAL_DIR, "push", stats)
        
        # Sync subfolders
        for drive_subfolder, local_subfolder in SUBFOLDERS.items():
            local_subdir = LOCAL_DIR / local_subfolder
            if local_subdir.exists():
                subfolder_id = self._get_folder_id(drive_subfolder, SUPERVISOR_FOLDER_ID)
                if not subfolder_id:
                    # Create folder if it doesn't exist
                    if not self.dry_run:
                        subfolder_id = self._create_folder(drive_subfolder, SUPERVISOR_FOLDER_ID)
                        log(f"  📁 Created folder: {drive_subfolder}/")
                    else:
                        log(f"  🔍 Would create folder: {drive_subfolder}/")
                        continue
                
                log(f"  [{drive_subfolder}/]")
                self._sync_folder(subfolder_id, local_subdir, "push", stats)
        
        if not self.dry_run:
            save_state(self.state)
        
        log(f"Push complete: {stats['transferred']} uploaded, {stats['skipped']} unchanged, {stats['errors']} errors")
        return stats
    
    def sync(self):
        """Bidirectional sync: pull then push."""
        log("Starting BIDIRECTIONAL SYNC")
        pull_stats = self.pull()
        push_stats = self.push()
        log("Bidirectional sync complete")
        return {"pull": pull_stats, "push": push_stats}
    
    def status(self):
        print("Supervisor Project Sync v2")
        print("=" * 40)
        print(f"Drive folder: {SUPERVISOR_FOLDER_ID}")
        print(f"Local dir:    {LOCAL_DIR}")
        print(f"State file:   {STATE_FILE}")
        print(f"Log file:     {LOG_FILE}")
        print()
        
        local_count = len(list(LOCAL_DIR.glob("*.md")))
        for subfolder in SUBFOLDERS.values():
            subdir = LOCAL_DIR / subfolder
            if subdir.exists():
                local_count += len(list(subdir.glob("*.md")))
        
        print(f"Local .md files: {local_count}")
        print(f"State entries:   {len(self.state.get('files', {}))}")
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
        sync = SupervisorSync()
        sync.pull()
    elif cmd == "push":
        sync = SupervisorSync()
        sync.push()
    elif cmd == "sync":
        sync = SupervisorSync()
        sync.sync()
    elif cmd == "dry":
        print("🔍 DRY RUN — no changes will be made\n")
        sync = SupervisorSync(dry_run=True)
        sync.sync()
    elif cmd == "status":
        sync = SupervisorSync()
        sync.status()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
