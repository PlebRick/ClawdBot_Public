#!/usr/bin/env python3
"""Memory Sync v2 — Python-native with format conversion.

Selective sync of ~/clawd/memory/context/ and ~/clawd/memory/todos/ 
to 02_ClawdBot/01_Memory/daily/context/ and .../todos/

Excludes: training/, daily logs, cache/, logs/

Usage:
  python3 memory-sync-v2.py pull     # Drive → Local (.md files)
  python3 memory-sync-v2.py push     # Local → Drive (Google Docs)
  python3 memory-sync-v2.py sync     # Bidirectional: pull then push
  python3 memory-sync-v2.py dry      # Show what sync would do
  python3 memory-sync-v2.py status   # Show sync state
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
LOG_FILE = os.path.expanduser("~/clawd/logs/memory-sync.log")
STATE_FILE = os.path.expanduser("~/.config/clawd/memory-sync-state.json")

# Drive folder IDs (inside 02_ClawdBot/01_Memory/daily/)
CONTEXT_FOLDER_ID = "1u3fujN4OFXUujOrEzjHEHAd6ReOPNBLI"
TODOS_FOLDER_ID = "1MPBBEytKJSSuKO1pSWKJTMMCpalf3-xv"

LOCAL_ROOT = Path.home() / "clawd" / "memory"

# Folders to sync: Drive folder ID → local subfolder
SYNC_FOLDERS = {
    CONTEXT_FOLDER_ID: "context",
    TODOS_FOLDER_ID: "todos",
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
    lines = content.rstrip().split('\n')
    normalized = '\n'.join(line.rstrip() for line in lines)
    return normalized + '\n'


def hash_content(content: str) -> str:
    return hashlib.md5(normalize_content(content).encode()).hexdigest()


class MemorySync:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.creds = get_creds()
        self.drive = build("drive", "v3", credentials=self.creds)
        self.state = load_state()
        
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
        results = self.drive.files().list(q=q, fields="files(id, name)", pageSize=200).execute()
        return results.get("files", [])
    
    def pull(self):
        """Pull from Drive → Local."""
        log("Starting PULL: Drive → Local")
        stats = {"transferred": 0, "skipped": 0, "errors": 0}
        
        for folder_id, local_subdir in SYNC_FOLDERS.items():
            log(f"  [{local_subdir}/]")
            local_dir = LOCAL_ROOT / local_subdir
            docs = self._list_docs_in_folder(folder_id)
            
            for doc in docs:
                doc_name = doc["name"]
                local_file = local_dir / f"{doc_name}.md"
                local_rel = f"{local_subdir}/{doc_name}.md"
                
                try:
                    content = self._download_doc_as_text(doc["id"])
                    content_hash = hash_content(content)
                    
                    if local_file.exists():
                        local_content = local_file.read_text()
                        if hash_content(local_content) == content_hash:
                            stats["skipped"] += 1
                            continue
                    
                    if self.dry_run:
                        log(f"    🔍 Would download: {doc_name} → {local_rel}")
                    else:
                        local_dir.mkdir(parents=True, exist_ok=True)
                        local_file.write_text(normalize_content(content))
                        self.state["files"][local_rel] = content_hash
                        log(f"    ✅ {doc_name} → {local_rel}")
                    
                    stats["transferred"] += 1
                    
                except Exception as e:
                    log(f"    ❌ {doc_name}: {e}")
                    stats["errors"] += 1
        
        if not self.dry_run:
            save_state(self.state)
        
        log(f"Pull complete: {stats['transferred']} downloaded, {stats['skipped']} unchanged, {stats['errors']} errors")
        return stats
    
    def push(self):
        """Push from Local → Drive."""
        log("Starting PUSH: Local → Drive")
        stats = {"transferred": 0, "skipped": 0, "errors": 0}
        
        for folder_id, local_subdir in SYNC_FOLDERS.items():
            log(f"  [{local_subdir}/]")
            local_dir = LOCAL_ROOT / local_subdir
            
            if not local_dir.exists():
                continue
            
            for local_file in local_dir.glob("*.md"):
                doc_name = local_file.stem
                local_rel = f"{local_subdir}/{local_file.name}"
                
                try:
                    content = local_file.read_text()
                    content_hash = hash_content(content)
                    
                    if self.state["files"].get(local_rel) == content_hash:
                        stats["skipped"] += 1
                        continue
                    
                    existing_id = self._get_doc_id(doc_name, folder_id)
                    
                    if self.dry_run:
                        action = "update" if existing_id else "create"
                        log(f"    🔍 Would {action}: {local_rel} → {doc_name}")
                    else:
                        self._upload_text_as_doc(doc_name, content, folder_id, existing_id)
                        self.state["files"][local_rel] = content_hash
                        log(f"    ✅ {local_rel} → {doc_name}")
                    
                    stats["transferred"] += 1
                    
                except Exception as e:
                    log(f"    ❌ {local_rel}: {e}")
                    stats["errors"] += 1
        
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
        print("Memory Sync v2 (context + todos only)")
        print("=" * 40)
        print(f"Drive context/: {CONTEXT_FOLDER_ID}")
        print(f"Drive todos/:   {TODOS_FOLDER_ID}")
        print(f"Local root:     {LOCAL_ROOT}")
        print(f"State file:     {STATE_FILE}")
        print(f"Log file:       {LOG_FILE}")
        print()
        
        local_count = 0
        for subdir in SYNC_FOLDERS.values():
            local_dir = LOCAL_ROOT / subdir
            if local_dir.exists():
                local_count += len(list(local_dir.glob("*.md")))
        
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
        sync = MemorySync()
        sync.pull()
    elif cmd == "push":
        sync = MemorySync()
        sync.push()
    elif cmd == "sync":
        sync = MemorySync()
        sync.sync()
    elif cmd == "dry":
        print("🔍 DRY RUN — no changes will be made\n")
        sync = MemorySync(dry_run=True)
        sync.sync()
    elif cmd == "status":
        sync = MemorySync()
        sync.status()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
