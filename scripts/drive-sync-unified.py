#!/usr/bin/env python3
"""Unified Drive Sync — Bidirectional sync with Google Docs ↔ Markdown conversion.

Syncs 01_ArnoldOS_Gemini and 02_ClawdBot folders with format conversion.
Google Docs on Drive ↔ Markdown locally for AI readability.

Usage:
  python3 drive-sync-unified.py pull              # Drive → Local
  python3 drive-sync-unified.py push              # Local → Drive
  python3 drive-sync-unified.py sync              # Bidirectional (pull then push)
  python3 drive-sync-unified.py status            # Show sync state
  python3 drive-sync-unified.py dry               # Dry run (show what would happen)
  python3 drive-sync-unified.py list-folders      # Show configured folder mappings
"""

import sys
import os
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io

# --- Config ---
TOKEN_FILE = os.path.expanduser("~/.config/clawd/google-tokens.json")
STATE_FILE = os.path.expanduser("~/.config/clawd/drive-sync-unified-state.json")
LOG_FILE = os.path.expanduser("~/clawd/logs/drive-sync-unified.log")

# Folder mappings: (drive_folder_id, local_path, sync_subdirs_recursively)
# These are the ROOT mappings - subdirectories are synced recursively
FOLDER_MAPPINGS = [
    # 01_ArnoldOS_Gemini
    ("1HuRZueJfRzWbUSFj8PwvSesNsNuHGtJE", "~/arnoldos/00_Inbox", True),
    ("1paymtPXeI7jICqVhY8Q0XAM2ty8Gk-r9", "~/arnoldos/Ministry", True),
    ("1EFKyIg9p16SaG8hW6p18BJXeKmY9ju7T", "~/arnoldos/Chapel", True),
    ("1HQlsU2eBO1h7SyKmer9yIqIqpmxu9E8p", "~/arnoldos/Trading", True),
    ("1BObDiyABWgXY5YAlz5wgppcQtoQ2eK2q", "~/arnoldos/Dev", True),
    ("1HTgm4axfUzLfcbTiGLm11hcstBvUYSWF", "~/arnoldos/Family", True),
    ("1wEAjj77hlFTYg-wVWpW3oDKlWe11xUw3", "~/arnoldos/Personal", True),
    ("1hMoewL3YKon5AnYaQBDaXLg52EUWrxVA", "~/arnoldos/Content", True),
    # Note: Images folder skipped (binary files)
    
    # 02_ClawdBot - using existing local paths
    ("1u3fujN4OFXUujOrEzjHEHAd6ReOPNBLI", "~/clawd/memory/context", True),
    ("1MPBBEytKJSSuKO1pSWKJTMMCpalf3-xv", "~/clawd/memory/todos", True),
    ("1X1DQbFF_2eR_jpS3cyqlI1OcgeD3cglP", "~/clawd/supervisor-project", True),
    # Skills handled by skills-sync-v2.py (has special logic) - skip here
    # ricks-projects - new
    ("1mLsMxY5rsTeE8J85VjQu2AIhVx-YqDYG", "~/clawd/ricks-projects", True),  
    ("19BpfbkZF8fTPuj9sjGi8TEDxHEHkWHJL", "~/clawd/inbox", True),  # 02_ClawdBot/01_Inbox
]

# File extensions to sync (others are skipped)
SYNC_EXTENSIONS = {'.md', '.txt', '.json', '.yaml', '.yml', '.py', '.sh', '.js'}

# Google Docs MIME type
GDOC_MIME = "application/vnd.google-apps.document"
GSHEET_MIME = "application/vnd.google-apps.spreadsheet"
GSLIDES_MIME = "application/vnd.google-apps.presentation"

# Skip patterns
SKIP_PATTERNS = [
    r'\.git/',
    r'__pycache__/',
    r'\.pyc$',
    r'node_modules/',
    r'\.DS_Store',
    r'\.swp$',
    r'~$',
]


def log(msg: str, level: str = "INFO"):
    """Log message to file and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def get_creds() -> Credentials:
    """Get and refresh Google credentials."""
    if not os.path.exists(TOKEN_FILE):
        log("ERROR: No token file. Run: python3 scripts/google-oauth.py auth", "ERROR")
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
            log(f"ERROR: Token refresh failed — {e}", "ERROR")
            sys.exit(1)

    return creds


def load_state() -> dict:
    """Load sync state from file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"files": {}, "folders": {}}


def save_state(state: dict):
    """Save sync state to file."""
    Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def md5_hash(content: str) -> str:
    """Calculate MD5 hash of content."""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def normalize_content(content: str) -> str:
    """Normalize content for consistent hashing."""
    lines = content.rstrip().split('\n')
    normalized = '\n'.join(line.rstrip() for line in lines)
    return normalized + '\n'


def should_skip(path: str) -> bool:
    """Check if path should be skipped."""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, path):
            return True
    return False


def get_drive_service(creds):
    """Get Google Drive API service."""
    return build('drive', 'v3', credentials=creds)


def list_drive_folder(service, folder_id: str, recursive: bool = True) -> list:
    """List all files in a Drive folder, optionally recursively."""
    results = []
    
    query = f"'{folder_id}' in parents and trashed = false"
    response = service.files().list(
        q=query,
        fields="files(id,name,mimeType,modifiedTime,md5Checksum)",
        pageSize=1000,
    ).execute()
    
    files = response.get('files', [])
    
    for f in files:
        f['parent_id'] = folder_id
        
        # If it's a folder and we're recursive, descend
        if f['mimeType'] == 'application/vnd.google-apps.folder':
            if recursive:
                f['children'] = list_drive_folder(service, f['id'], recursive=True)
            results.append(f)
        else:
            results.append(f)
    
    return results


def flatten_drive_files(files: list, path_prefix: str = "") -> list:
    """Flatten recursive file list into flat list with paths."""
    result = []
    for f in files:
        current_path = f"{path_prefix}/{f['name']}" if path_prefix else f['name']
        
        if f['mimeType'] == 'application/vnd.google-apps.folder':
            # It's a folder - process children
            if 'children' in f:
                result.extend(flatten_drive_files(f['children'], current_path))
        else:
            f['rel_path'] = current_path
            result.append(f)
    
    return result


def mirror_folder_structure(service, drive_folder_id: str, local_path: Path):
    """Create local folder structure to match Drive, including empty folders."""
    local_path = Path(os.path.expanduser(str(local_path)))
    local_path.mkdir(parents=True, exist_ok=True)
    
    def get_subfolders_recursive(folder_id: str, path_prefix: str = ""):
        """Recursively get all subfolders."""
        folders = []
        query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        try:
            response = service.files().list(q=query, fields="files(id,name)", pageSize=1000).execute()
            for f in response.get('files', []):
                folder_path = f"{path_prefix}/{f['name']}" if path_prefix else f['name']
                folders.append(folder_path)
                folders.extend(get_subfolders_recursive(f['id'], folder_path))
        except Exception as e:
            log(f"Warning: Could not list subfolders: {e}", "WARN")
        return folders
    
    try:
        subfolders = get_subfolders_recursive(drive_folder_id)
        for folder_rel_path in subfolders:
            folder_path = local_path / folder_rel_path
            folder_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        log(f"Warning: Could not mirror folder structure: {e}", "WARN")



def download_gdoc_as_md(service, file_id: str) -> Optional[str]:
    """Download a Google Doc as plain text (markdown)."""
    try:
        response = service.files().export(
            fileId=file_id,
            mimeType='text/plain'
        ).execute()
        
        if isinstance(response, bytes):
            return response.decode('utf-8')
        return response
    except Exception as e:
        log(f"Error downloading doc {file_id}: {e}", "ERROR")
        return None


def download_file(service, file_id: str) -> Optional[bytes]:
    """Download a regular file from Drive."""
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read()
    except Exception as e:
        log(f"Error downloading file {file_id}: {e}", "ERROR")
        return None


def upload_md_as_gdoc(service, local_path: Path, folder_id: str, existing_id: Optional[str] = None) -> Optional[str]:
    """Upload a markdown file as a Google Doc."""
    try:
        content = local_path.read_text(encoding='utf-8')
        
        # File metadata
        name = local_path.stem  # Remove .md extension for Google Doc
        file_metadata = {
            'name': name,
            'mimeType': GDOC_MIME,
        }
        
        if existing_id:
            # Update existing
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype='text/plain',
                resumable=True
            )
            file = service.files().update(
                fileId=existing_id,
                media_body=media
            ).execute()
            return file.get('id')
        else:
            # Create new
            file_metadata['parents'] = [folder_id]
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype='text/plain',
                resumable=True
            )
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            return file.get('id')
            
    except Exception as e:
        log(f"Error uploading {local_path}: {e}", "ERROR")
        return None


def upload_file(service, local_path: Path, folder_id: str, existing_id: Optional[str] = None) -> Optional[str]:
    """Upload a regular file to Drive."""
    try:
        content = local_path.read_bytes()
        
        file_metadata = {
            'name': local_path.name,
        }
        
        # Guess MIME type
        ext = local_path.suffix.lower()
        mime_map = {
            '.json': 'application/json',
            '.txt': 'text/plain',
            '.py': 'text/x-python',
            '.sh': 'application/x-sh',
            '.yaml': 'text/yaml',
            '.yml': 'text/yaml',
            '.js': 'application/javascript',
        }
        mimetype = mime_map.get(ext, 'text/plain')
        
        if existing_id:
            media = MediaIoBaseUpload(
                io.BytesIO(content),
                mimetype=mimetype,
                resumable=True
            )
            file = service.files().update(
                fileId=existing_id,
                media_body=media
            ).execute()
            return file.get('id')
        else:
            file_metadata['parents'] = [folder_id]
            media = MediaIoBaseUpload(
                io.BytesIO(content),
                mimetype=mimetype,
                resumable=True
            )
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            return file.get('id')
            
    except Exception as e:
        log(f"Error uploading {local_path}: {e}", "ERROR")
        return None


def ensure_drive_folder(service, parent_id: str, folder_name: str) -> str:
    """Ensure a folder exists in Drive, create if needed. Returns folder ID."""
    # Check if exists - escape apostrophes in folder name for query
    safe_name = folder_name.replace("'", "\\'")
    query = f"'{parent_id}' in parents and name = '{safe_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    response = service.files().list(q=query, fields="files(id)").execute()
    files = response.get('files', [])
    
    if files:
        return files[0]['id']
    
    # Create
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')


def pull_folder(service, drive_folder_id: str, local_path: Path, state: dict, dry_run: bool = False) -> dict:
    """Pull files from Drive folder to local path."""
    stats = {"downloaded": 0, "skipped": 0, "errors": 0}
    
    local_path = Path(os.path.expanduser(str(local_path)))
    
    if not dry_run:
        local_path.mkdir(parents=True, exist_ok=True)
        # Mirror folder structure including empty folders
        mirror_folder_structure(service, drive_folder_id, local_path)
    
    # List Drive files
    drive_files = list_drive_folder(service, drive_folder_id, recursive=True)
    flat_files = flatten_drive_files(drive_files)
    
    for f in flat_files:
        rel_path = f['rel_path']
        file_id = f['id']
        mime = f['mimeType']
        
        if should_skip(rel_path):
            stats["skipped"] += 1
            continue
        
        # Determine local filename
        if mime == GDOC_MIME:
            # Google Doc -> .md
            local_file = local_path / (rel_path + ".md")
        elif mime in (GSHEET_MIME, GSLIDES_MIME):
            # Skip sheets/slides for now
            stats["skipped"] += 1
            continue
        else:
            local_file = local_path / rel_path
        
        # Check if we need to download
        state_key = f"{drive_folder_id}:{rel_path}"
        drive_modified = f.get('modifiedTime', '')
        
        if state_key in state.get('files', {}):
            if state['files'][state_key].get('drive_modified') == drive_modified:
                if local_file.exists():
                    stats["skipped"] += 1
                    continue
        
        # Download
        if dry_run:
            log(f"[DRY RUN] Would download: {rel_path} -> {local_file}")
            stats["downloaded"] += 1
            continue
        
        # Ensure parent directory exists
        local_file.parent.mkdir(parents=True, exist_ok=True)
        
        if mime == GDOC_MIME:
            content = download_gdoc_as_md(service, file_id)
            if content:
                # Atomic write
                tmp_file = local_file.with_suffix('.tmp')
                tmp_file.write_text(content, encoding='utf-8')
                tmp_file.rename(local_file)
                
                state.setdefault('files', {})[state_key] = {
                    'drive_id': file_id,
                    'drive_modified': drive_modified,
                    'local_hash': md5_hash(normalize_content(content)),
                    'synced_at': datetime.now().isoformat(),
                }
                log(f"Downloaded: {rel_path} -> {local_file}")
                stats["downloaded"] += 1
            else:
                stats["errors"] += 1
        else:
            content = download_file(service, file_id)
            if content:
                tmp_file = local_file.with_suffix('.tmp')
                tmp_file.write_bytes(content)
                tmp_file.rename(local_file)
                
                state.setdefault('files', {})[state_key] = {
                    'drive_id': file_id,
                    'drive_modified': drive_modified,
                    'local_hash': f.get('md5Checksum', ''),
                    'synced_at': datetime.now().isoformat(),
                }
                log(f"Downloaded: {rel_path} -> {local_file}")
                stats["downloaded"] += 1
            else:
                stats["errors"] += 1
    
    return stats


def push_folder(service, drive_folder_id: str, local_path: Path, state: dict, dry_run: bool = False) -> dict:
    """Push local files to Drive folder."""
    stats = {"uploaded": 0, "skipped": 0, "errors": 0}
    
    local_path = Path(os.path.expanduser(str(local_path)))
    
    if not local_path.exists():
        log(f"Local path does not exist: {local_path}", "WARN")
        return stats
    
    # Build map of Drive files for lookup
    drive_files = list_drive_folder(service, drive_folder_id, recursive=True)
    flat_files = flatten_drive_files(drive_files)
    
    # Map: relative_path (without .md for gdocs) -> file info
    drive_map = {}
    for f in flat_files:
        drive_map[f['rel_path']] = f
    
    # Walk local directory
    for local_file in local_path.rglob('*'):
        if local_file.is_dir():
            continue
        
        rel_path = str(local_file.relative_to(local_path))
        
        if should_skip(rel_path):
            stats["skipped"] += 1
            continue
        
        # Check extension
        if local_file.suffix.lower() not in SYNC_EXTENSIONS:
            stats["skipped"] += 1
            continue
        
        state_key = f"{drive_folder_id}:{rel_path}"
        
        # Read local content
        try:
            if local_file.suffix.lower() in ('.json', '.yaml', '.yml', '.py', '.sh', '.js', '.txt'):
                content = local_file.read_text(encoding='utf-8')
                is_text = True
            elif local_file.suffix.lower() == '.md':
                content = local_file.read_text(encoding='utf-8')
                is_text = True
            else:
                content = local_file.read_bytes()
                is_text = False
        except Exception as e:
            log(f"Error reading {local_file}: {e}", "ERROR")
            stats["errors"] += 1
            continue
        
        # Calculate hash
        if is_text:
            local_hash = md5_hash(normalize_content(content))
        else:
            local_hash = hashlib.md5(content).hexdigest()
        
        # Check if changed
        if state_key in state.get('files', {}):
            if state['files'][state_key].get('local_hash') == local_hash:
                stats["skipped"] += 1
                continue
        
        # Determine Drive path
        if local_file.suffix.lower() == '.md':
            # .md -> Google Doc (without .md extension)
            drive_rel_path = rel_path[:-3]  # Remove .md
            upload_as_gdoc = True
        else:
            drive_rel_path = rel_path
            upload_as_gdoc = False
        
        # Find or create parent folder on Drive
        path_parts = Path(drive_rel_path).parts
        current_folder_id = drive_folder_id
        
        if len(path_parts) > 1:
            # Need to navigate/create folders
            for folder_name in path_parts[:-1]:
                if dry_run:
                    log(f"[DRY RUN] Would ensure folder: {folder_name}")
                else:
                    current_folder_id = ensure_drive_folder(service, current_folder_id, folder_name)
        
        # Check if file exists on Drive
        existing_id = None
        if drive_rel_path in drive_map:
            existing_id = drive_map[drive_rel_path]['id']
        
        if dry_run:
            action = "update" if existing_id else "create"
            log(f"[DRY RUN] Would {action}: {rel_path} -> Drive:{drive_rel_path}")
            stats["uploaded"] += 1
            continue
        
        # Upload
        if upload_as_gdoc:
            result_id = upload_md_as_gdoc(service, local_file, current_folder_id, existing_id)
        else:
            result_id = upload_file(service, local_file, current_folder_id, existing_id)
        
        if result_id:
            state.setdefault('files', {})[state_key] = {
                'drive_id': result_id,
                'local_hash': local_hash,
                'synced_at': datetime.now().isoformat(),
            }
            log(f"Uploaded: {rel_path} -> Drive:{drive_rel_path}")
            stats["uploaded"] += 1
        else:
            stats["errors"] += 1
    
    return stats


def cmd_pull(dry_run: bool = False):
    """Pull all folders from Drive."""
    creds = get_creds()
    service = get_drive_service(creds)
    state = load_state()
    
    total_stats = {"downloaded": 0, "skipped": 0, "errors": 0}
    
    for drive_id, local_path, recursive in FOLDER_MAPPINGS:
        if "placeholder" in drive_id:
            log(f"Skipping placeholder mapping: {local_path}", "WARN")
            continue
            
        log(f"Pulling: {local_path}")
        stats = pull_folder(service, drive_id, Path(local_path), state, dry_run)
        
        for k, v in stats.items():
            total_stats[k] += v
    
    if not dry_run:
        save_state(state)
    
    log(f"Pull complete: {total_stats['downloaded']} downloaded, {total_stats['skipped']} skipped, {total_stats['errors']} errors")
    return total_stats


def cmd_push(dry_run: bool = False):
    """Push all local folders to Drive."""
    creds = get_creds()
    service = get_drive_service(creds)
    state = load_state()
    
    total_stats = {"uploaded": 0, "skipped": 0, "errors": 0}
    
    for drive_id, local_path, recursive in FOLDER_MAPPINGS:
        if "placeholder" in drive_id:
            log(f"Skipping placeholder mapping: {local_path}", "WARN")
            continue
            
        log(f"Pushing: {local_path}")
        stats = push_folder(service, drive_id, Path(local_path), state, dry_run)
        
        for k, v in stats.items():
            total_stats[k] += v
    
    if not dry_run:
        save_state(state)
    
    log(f"Push complete: {total_stats['uploaded']} uploaded, {total_stats['skipped']} skipped, {total_stats['errors']} errors")
    return total_stats


def cmd_sync(dry_run: bool = False):
    """Bidirectional sync: pull then push."""
    log("Starting bidirectional sync...")
    pull_stats = cmd_pull(dry_run)
    push_stats = cmd_push(dry_run)
    log("Sync complete.")
    return {"pull": pull_stats, "push": push_stats}


def cmd_status():
    """Show sync status."""
    state = load_state()
    
    print(f"State file: {STATE_FILE}")
    print(f"Total tracked files: {len(state.get('files', {}))}")
    print()
    
    # Group by folder
    by_folder = {}
    for key in state.get('files', {}).keys():
        folder_id = key.split(':')[0]
        by_folder[folder_id] = by_folder.get(folder_id, 0) + 1
    
    print("Files per folder:")
    for drive_id, local_path, _ in FOLDER_MAPPINGS:
        count = by_folder.get(drive_id, 0)
        print(f"  {local_path}: {count} files")


def cmd_list_folders():
    """List configured folder mappings."""
    print("Configured folder mappings:")
    print()
    for drive_id, local_path, recursive in FOLDER_MAPPINGS:
        status = "✓" if "placeholder" not in drive_id else "⚠ placeholder"
        rec = "recursive" if recursive else "top-level only"
        print(f"  {status} {local_path}")
        print(f"      Drive ID: {drive_id}")
        print(f"      Mode: {rec}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "pull":
        cmd_pull()
    elif cmd == "push":
        cmd_push()
    elif cmd == "sync":
        cmd_sync()
    elif cmd == "dry":
        cmd_sync(dry_run=True)
    elif cmd == "status":
        cmd_status()
    elif cmd == "list-folders":
        cmd_list_folders()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
