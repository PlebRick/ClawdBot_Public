#!/usr/bin/env python3
"""ArnoldOS Integration — Phase 2 Supervised Writes

Provides read access and supervised write access to Rick's Google Workspace:
- Calendars (all 7 domains)
- Tasks (00_Inbox, parsed by domain tag)
- Drive (01_ArnoldOS_Gemini folder structure)
- Conflict detection across calendars

Usage:
  python3 arnoldos.py today          # Today's events across all calendars
  python3 arnoldos.py week           # This week's events
  python3 arnoldos.py tasks          # All incomplete tasks grouped by domain
  python3 arnoldos.py conflicts      # Check today for scheduling conflicts
  python3 arnoldos.py conflicts-week # Check this week for conflicts
  python3 arnoldos.py drive-inbox    # List files in Drive 00_Inbox
  python3 arnoldos.py brief          # Full morning brief output
  python3 arnoldos.py calendars      # List all calendar names/IDs
  python3 arnoldos.py preaching-schedule          # Upcoming preaching events with prep status
  python3 arnoldos.py preaching-schedule --date 2026-02-15  # Specific date
  python3 arnoldos.py drive-read <file_id>        # Read a Drive file's content
  python3 arnoldos.py drive-read --folder Ministry/Brainstorm --prefix 2026-02-15
  python3 arnoldos.py complete-task "Task title"  # Mark a task as completed
  python3 arnoldos.py create-event <domain> <summary> <start> <end>  # Create calendar event
  python3 arnoldos.py update-event <domain> <event_id> [--summary ...] [--description ...]  # Update event
  python3 arnoldos.py create-task <title> [--notes ...] [--due YYYY-MM-DD]  # Create a task
  python3 arnoldos.py drive-upload <folder_key> <filename> <local_path>     # Upload file to Drive
  python3 arnoldos.py quick <text> [--domain DOMAIN]                         # Quick task with auto-domain
  python3 arnoldos.py quick-event <text> [--domain DOMAIN]                   # Quick event with auto-domain
"""

import sys
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- Config ---
TOKEN_FILE = os.path.expanduser("~/.config/clawd/google-tokens.json")
CST = timezone(timedelta(hours=-6))

CALENDARS = {
    "Chapel": "7aa8b91af856516199da961dab75b4ced0e5264a02e9f8dd106616e482dc748c@group.calendar.google.com",
    "Ministry": "9d3bd07ab2b73e9fd173e830ef38d1f83f2bbebec83bca67e5bcc785e608c78f@group.calendar.google.com",
    "Trading": "f6414f2c7ccd2096ad1d3e011adfe81f9193f4ba5a87e167afa01577673cdee7@group.calendar.google.com",
    "Dev": "87df929a3c6df9a7bac7b9709cd4424c60b7d220e146cad600e76b9bbaf7d889@group.calendar.google.com",
    "Family": "5b11a8091bd38b9eb0c06b0f47efab2c365d046a4051992b36c21013b5a89e81@group.calendar.google.com",
    "Personal": "chaplaincen@gmail.com",
    "US Holidays": "en.usa#holiday@group.v.calendar.google.com",
}

# Priority order for display (Chapel/Ministry first per ArnoldOS spec)
PRIORITY_ORDER = ["Chapel", "Ministry", "Trading", "Dev", "Family", "Personal"]
# US Holidays excluded — public calendar requires different API access; not critical for brief

TASK_LIST_ID = "MDMzMjg1NzQ3NzM4Mjc0MjQwMzk6MDow"

DRIVE_FOLDERS = {
    "Root": "12aczo3TPXamKkKQQc2iunPUqvfoBJovG",
    "00_Inbox": "1HuRZueJfRzWbUSFj8PwvSesNsNuHGtJE",
    "Ministry": "1paymtPXeI7jICqVhY8Q0XAM2ty8Gk-r9",
    "Chapel": "1EFKyIg9p16SaG8hW6p18BJXeKmY9ju7T",
    "Trading": "1HQlsU2eBO1h7SyKmer9yIqIqpmxu9E8p",
    "Dev": "1BObDiyABWgXY5YAlz5wgppcQtoQ2eK2q",
    "Family": "1HTgm4axfUzLfcbTiGLm11hcstBvUYSWF",
    "Personal": "1wEAjj77hlFTYg-wVWpW3oDKlWe11xUw3",
    "Content Creation": "1hMoewL3YKon5AnYaQBDaXLg52EUWrxVA",
}

DRIVE_SUBFOLDERS = {
    "Ministry/Brainstorm": "1bJtLGjfyKYs4QJ4HLacjsOxiu6Jlb29U",
    "Ministry/Sermons": "1-c2ywTDT_dsEqsJA0SUbMV34dRFIr_wG",
}

# Tag patterns for task parsing
TAG_PATTERN = re.compile(r'^[\[\(](MINISTRY|CHAPEL|TRADING|DEV|FAMILY|PERSONAL|CONTENT|INBOX)[\]\)]', re.IGNORECASE)


# --- Auth ---
def get_creds() -> Credentials:
    """Load and refresh Google OAuth credentials."""
    if not os.path.exists(TOKEN_FILE):
        print("ERROR: No token file found. Run: python3 google-oauth.py auth")
        print("RE-AUTH NEEDED: Google OAuth tokens not found at", TOKEN_FILE)
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
            print(f"RE-AUTH NEEDED: Token refresh failed — {e}")
            print("Run: python3 ~/clawd/scripts/google-oauth.py auth")
            sys.exit(1)

    return creds


def api_get(creds: Credentials, url: str, params: dict = None) -> Optional[dict]:
    """Make an authenticated GET request. Returns None on failure (graceful degradation)."""
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {creds.token}"}, params=params, timeout=15)
        if r.status_code == 401:
            # Try one refresh
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE) as f:
                    t = json.load(f)
                t["token"] = creds.token
                with open(TOKEN_FILE, "w") as f:
                    json.dump(t, f, indent=2)
                r = requests.get(url, headers={"Authorization": f"Bearer {creds.token}"}, params=params, timeout=15)
            except Exception:
                pass
        if r.status_code != 200:
            print(f"  ⚠️ API error ({r.status_code}) for {url.split('/')[-1]}")
            return None
        return r.json()
    except requests.RequestException as e:
        print(f"  ⚠️ Network error: {e}")
        return None


def api_patch(creds: Credentials, url: str, body: dict) -> Optional[dict]:
    """Make an authenticated PATCH request. Returns None on failure."""
    try:
        headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
        r = requests.patch(url, headers=headers, json=body, timeout=15)
        if r.status_code == 401:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE) as f:
                    t = json.load(f)
                t["token"] = creds.token
                with open(TOKEN_FILE, "w") as f:
                    json.dump(t, f, indent=2)
                headers["Authorization"] = f"Bearer {creds.token}"
                r = requests.patch(url, headers=headers, json=body, timeout=15)
            except Exception:
                pass
        if r.status_code != 200:
            print(f"  ⚠️ API error ({r.status_code}) for PATCH {url.split('/')[-1]}")
            return None
        return r.json()
    except requests.RequestException as e:
        print(f"  ⚠️ Network error: {e}")
        return None

def api_post(creds: Credentials, url: str, body: dict) -> Optional[dict]:
    """Make an authenticated POST request. Returns None on failure."""
    try:
        headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
        r = requests.post(url, headers=headers, json=body, timeout=15)
        if r.status_code == 401:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE) as f:
                    t = json.load(f)
                t["token"] = creds.token
                with open(TOKEN_FILE, "w") as f:
                    json.dump(t, f, indent=2)
                headers["Authorization"] = f"Bearer {creds.token}"
                r = requests.post(url, headers=headers, json=body, timeout=15)
            except Exception:
                pass
        if r.status_code not in (200, 201):
            print(f"  ⚠️ API error ({r.status_code}) for POST {url.split('/')[-1]}: {r.text[:200]}")
            return None
        return r.json()
    except requests.RequestException as e:
        print(f"  ⚠️ Network error: {e}")
        return None




# --- Calendar ---
def get_events(creds, calendar_id: str, time_min: str, time_max: str) -> list:
    """Get events from a specific calendar in a time range."""
    data = api_get(creds, f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events", {
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": 50,
    })
    if data is None:
        return []
    return data.get("items", [])


def get_all_events(creds, time_min: str, time_max: str) -> dict:
    """Get events from all calendars, keyed by domain name."""
    results = {}
    for name in PRIORITY_ORDER:
        cal_id = CALENDARS[name]
        events = get_events(creds, cal_id, time_min, time_max)
        if events:
            results[name] = events
    return results


def format_event_time(event: dict) -> str:
    """Extract a human-readable time from an event."""
    start = event.get("start", {})
    dt_str = start.get("dateTime")
    if dt_str:
        # Parse and format to HH:MM AM/PM
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%-I:%M %p")
        except Exception:
            return dt_str
    # All-day event
    return "All Day"


def get_time_range_today():
    """Return (time_min, time_max) for today in CST."""
    now = datetime.now(CST)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def get_time_range_week():
    """Return (time_min, time_max) for the next 7 days in CST."""
    now = datetime.now(CST)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return start.isoformat(), end.isoformat()


# --- Conflict Detection ---
def detect_conflicts(all_events: dict) -> list:
    """Find overlapping events across different calendars."""
    # Flatten all events with their domain
    flat = []
    for domain, events in all_events.items():
        if domain == "US Holidays":
            continue
        for e in events:
            start = e.get("start", {})
            end_t = e.get("end", {})
            dt_start = start.get("dateTime")
            dt_end = end_t.get("dateTime")
            if dt_start and dt_end:
                flat.append({
                    "domain": domain,
                    "summary": e.get("summary", "(no title)"),
                    "start": datetime.fromisoformat(dt_start),
                    "end": datetime.fromisoformat(dt_end),
                })

    # Check all pairs for overlap
    conflicts = []
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            a, b = flat[i], flat[j]
            if a["domain"] == b["domain"]:
                continue
            if a["start"] < b["end"] and b["start"] < a["end"]:
                conflicts.append((a, b))

    return conflicts


# --- Tasks ---
def get_tasks(creds, status: str = "needsAction") -> list:
    """Get tasks from 00_Inbox list."""
    data = api_get(creds, f"https://www.googleapis.com/tasks/v1/lists/{TASK_LIST_ID}/tasks", {
        "showCompleted": "false" if status == "needsAction" else "true",
        "maxResults": 100,
    })
    if data is None:
        return []
    return data.get("items", [])


def parse_task_tag(title: str) -> tuple:
    """Extract domain tag from task title. Returns (tag, clean_title)."""
    match = TAG_PATTERN.match(title.strip())
    if match:
        tag = match.group(1).upper()
        clean = title[match.end():].strip()
        return tag, clean
    return "INBOX", title.strip()


def get_tasks_by_domain(creds) -> dict:
    """Get all incomplete tasks grouped by domain tag."""
    tasks = get_tasks(creds)
    grouped = {}
    for t in tasks:
        title = t.get("title", "")
        if not title.strip():
            continue
        tag, clean = parse_task_tag(title)
        if tag not in grouped:
            grouped[tag] = []
        grouped[tag].append({
            "title": clean,
            "raw": title,
            "due": t.get("due"),
            "notes": t.get("notes", ""),
            "id": t.get("id"),
        })
    return grouped


def complete_task(creds, search_title: str) -> bool:
    """Mark a task as completed by searching for it by title (case-insensitive partial match)."""
    tasks = get_tasks(creds)
    search_lower = search_title.lower().strip()

    matches = []
    for t in tasks:
        title = t.get("title", "")
        if not title.strip():
            continue
        # Match against both raw title and clean (tag-stripped) title
        _, clean = parse_task_tag(title)
        if search_lower in title.lower() or search_lower in clean.lower():
            matches.append(t)

    if len(matches) == 0:
        print(f"❌ No task found matching: \"{search_title}\"")
        return False

    if len(matches) > 1:
        print(f"⚠️ Multiple tasks match \"{search_title}\":")
        for i, m in enumerate(matches, 1):
            print(f"  {i}. {m.get('title', '')}")
        print("Be more specific.")
        return False

    task = matches[0]
    task_id = task["id"]
    task_title = task.get("title", "")

    result = api_patch(
        creds,
        f"https://www.googleapis.com/tasks/v1/lists/{TASK_LIST_ID}/tasks/{task_id}",
        {"status": "completed"}
    )

    if result:
        print(f"✅ Completed: {task_title}")
        return True
    else:
        print(f"❌ Failed to complete: {task_title}")
        return False


# --- Drive ---
def list_drive_folder(creds, folder_id: str) -> list:
    """List files in a Drive folder."""
    data = api_get(creds, "https://www.googleapis.com/drive/v3/files", {
        "q": f"'{folder_id}' in parents and trashed = false",
        "fields": "files(id,name,mimeType,modifiedTime)",
        "orderBy": "modifiedTime desc",
        "pageSize": 20,
    })
    if data is None:
        return []
    return data.get("files", [])



# --- Sermon Pipeline ---
PREACHING_CALENDARS = ["Chapel", "Ministry"]

def get_time_range_days(days: int = 30):
    """Return (time_min, time_max) for the next N days in CST."""
    now = datetime.now(CST)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=days)
    return start.isoformat(), end.isoformat()


def find_preaching_events(creds, days: int = 30) -> list:
    """Find all events with PREACHING: in description from Chapel + Ministry calendars."""
    t_min, t_max = get_time_range_days(days)
    results = []
    for cal_name in PREACHING_CALENDARS:
        cal_id = CALENDARS[cal_name]
        events = get_events(creds, cal_id, t_min, t_max)
        for ev in events:
            desc = ev.get("description", "")
            if desc.strip().startswith("PREACHING:"):
                passage = desc.strip().split("PREACHING:", 1)[1].strip().split("\n")[0].strip()
                start_dt = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date", "")
                try:
                    event_date = datetime.fromisoformat(start_dt).strftime("%Y-%m-%d")
                except Exception:
                    event_date = start_dt[:10] if len(start_dt) >= 10 else start_dt
                results.append({
                    "calendar": cal_name,
                    "calendar_id": cal_id,
                    "event_id": ev.get("id"),
                    "summary": ev.get("summary", ""),
                    "date": event_date,
                    "start": start_dt,
                    "passage": passage,
                    "description": desc.strip(),
                    "location": ev.get("location", ""),
                })
    # Sort by date
    results.sort(key=lambda x: x["date"])
    return results


def check_drive_sermon_files(creds, date_prefix: str) -> dict:
    """Check for existing brainstorm/sermon files matching a date prefix."""
    found = {"brainstorm": None, "draft": None, "final": None}
    brainstorm_id = DRIVE_SUBFOLDERS["Ministry/Brainstorm"]
    if brainstorm_id:
        files = list_drive_folder(creds, brainstorm_id)
        for f in files:
            if f["name"].startswith(date_prefix):
                found["brainstorm"] = {"id": f["id"], "name": f["name"]}
                break

    sermons_id = DRIVE_SUBFOLDERS.get("Ministry/Sermons")
    if sermons_id:
        files = list_drive_folder(creds, sermons_id)
        for f in files:
            if f["name"].startswith(date_prefix):
                if "final" in f["name"].lower():
                    found["final"] = {"id": f["id"], "name": f["name"]}
                elif "draft" in f["name"].lower():
                    found["draft"] = {"id": f["id"], "name": f["name"]}
    return found


def preaching_schedule(creds, days: int = 30, target_date: str = None) -> dict:
    """Get preaching schedule with file status. Optionally filter to a specific date."""
    events = find_preaching_events(creds, days=max(days, 90) if target_date else days)
    schedule = []
    for ev in events:
        if target_date and ev["date"] != target_date:
            continue
        files = check_drive_sermon_files(creds, ev["date"])
        status = "not_started"
        if files["final"]:
            status = "final"
        elif files["draft"]:
            status = "draft"
        elif files["brainstorm"]:
            status = "brainstorm"
        schedule.append({
            **ev,
            "files": files,
            "status": status,
        })
    return {"command": "preaching-schedule", "count": len(schedule), "schedule": schedule}


def drive_read_file(creds, file_id: str) -> dict:
    """Read content from a Google Drive file. Supports Docs and docx."""
    # First get file metadata
    meta = api_get(creds, f"https://www.googleapis.com/drive/v3/files/{file_id}",
                   {"fields": "id,name,mimeType"})
    if not meta:
        return {"command": "drive-read", "success": False, "error": "File not found or inaccessible"}

    mime = meta.get("mimeType", "")
    name = meta.get("name", "")

    # For Google Docs, export as plain text
    if mime == "application/vnd.google-apps.document":
        try:
            r = requests.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}/export",
                headers={"Authorization": f"Bearer {creds.token}"},
                params={"mimeType": "text/plain"},
                timeout=30
            )
            if r.status_code == 200:
                return {"command": "drive-read", "success": True, "name": name,
                        "mimeType": mime, "content": r.text}
            else:
                return {"command": "drive-read", "success": False,
                        "error": f"Export failed: {r.status_code}"}
        except Exception as e:
            return {"command": "drive-read", "success": False, "error": str(e)}

    # For docx files, download and extract text
    if "wordprocessingml" in mime or name.endswith(".docx"):
        try:
            r = requests.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                headers={"Authorization": f"Bearer {creds.token}"},
                params={"alt": "media"},
                timeout=30
            )
            if r.status_code == 200:
                import io
                import zipfile
                from xml.etree import ElementTree
                # Extract text from docx
                zf = zipfile.ZipFile(io.BytesIO(r.content))
                xml_content = zf.read("word/document.xml")
                tree = ElementTree.fromstring(xml_content)
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                paragraphs = []
                for p in tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                    texts = [t.text for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if t.text]
                    if texts:
                        paragraphs.append("".join(texts))
                return {"command": "drive-read", "success": True, "name": name,
                        "mimeType": mime, "content": "\n\n".join(paragraphs)}
            else:
                return {"command": "drive-read", "success": False,
                        "error": f"Download failed: {r.status_code}"}
        except Exception as e:
            return {"command": "drive-read", "success": False, "error": str(e)}

    # For text/markdown files
    if mime.startswith("text/") or name.endswith(".md") or name.endswith(".txt"):
        try:
            r = requests.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                headers={"Authorization": f"Bearer {creds.token}"},
                params={"alt": "media"},
                timeout=30
            )
            if r.status_code == 200:
                return {"command": "drive-read", "success": True, "name": name,
                        "mimeType": mime, "content": r.text}
            else:
                return {"command": "drive-read", "success": False,
                        "error": f"Download failed: {r.status_code}"}
        except Exception as e:
            return {"command": "drive-read", "success": False, "error": str(e)}

    return {"command": "drive-read", "success": False,
            "error": f"Unsupported file type: {mime} ({name})"}


def drive_find_and_read(creds, folder_key: str, filename_prefix: str) -> dict:
    """Find a file by prefix in a known folder and read it."""
    folder_id = DRIVE_SUBFOLDERS.get(folder_key) or DRIVE_FOLDERS.get(folder_key)
    if not folder_id:
        return {"command": "drive-read", "success": False, "error": f"Unknown folder: {folder_key}"}
    files = list_drive_folder(creds, folder_id)
    for f in files:
        if f["name"].startswith(filename_prefix):
            return drive_read_file(creds, f["id"])
    return {"command": "drive-read", "success": False,
            "error": f"No file matching '{filename_prefix}*' in {folder_key}"}



def drive_upload_file(creds, folder_key: str, filename: str, content_bytes: bytes, 
                      mime_type: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document") -> dict:
    """Upload a file to a Drive folder.
    
    Args:
        folder_key: Folder key from DRIVE_FOLDERS or DRIVE_SUBFOLDERS (e.g., "Ministry/Brainstorm")
        filename: Name for the file (e.g., "2026-02-15-romans-8.docx")
        content_bytes: File content as bytes
        mime_type: MIME type of the file
    
    Returns:
        dict with success status and file details or error
    """
    folder_id = DRIVE_SUBFOLDERS.get(folder_key) or DRIVE_FOLDERS.get(folder_key)
    if not folder_id:
        return {"command": "drive-upload", "success": False,
                "error": f"Unknown folder: {folder_key}. Valid: {list(DRIVE_FOLDERS.keys()) + list(DRIVE_SUBFOLDERS.keys())}"}
    
    # Multipart upload
    import io
    boundary = "===BOUNDARY==="
    
    metadata = json.dumps({
        "name": filename,
        "parents": [folder_id]
    })
    
    body = (
        f"--{boundary}\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{metadata}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode('utf-8') + content_bytes + f"\r\n--{boundary}--".encode('utf-8')
    
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": f"multipart/related; boundary={boundary}"
    }
    
    try:
        r = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers=headers,
            data=body,
            timeout=30
        )
        if r.status_code in (200, 201):
            result = r.json()
            return {
                "command": "drive-upload",
                "success": True,
                "file": {
                    "id": result.get("id"),
                    "name": result.get("name"),
                    "folder": folder_key,
                    "webViewLink": f"https://drive.google.com/file/d/{result.get('id')}/view"
                }
            }
        else:
            return {"command": "drive-upload", "success": False,
                    "error": f"API error ({r.status_code}): {r.text[:200]}"}
    except Exception as e:
        return {"command": "drive-upload", "success": False,
                "error": f"Upload failed: {e}"}


def drive_upload_text(creds, folder_key: str, filename: str, text_content: str) -> dict:
    """Upload a text file to Drive (convenience wrapper).
    
    Args:
        folder_key: Folder key from DRIVE_FOLDERS or DRIVE_SUBFOLDERS
        filename: Name for the file
        text_content: Text content to upload
    
    Returns:
        dict with success status and file details or error
    """
    return drive_upload_file(creds, folder_key, filename, text_content.encode('utf-8'), "text/plain")


# --- Output Formatters ---
def print_today():
    creds = get_creds()
    t_min, t_max = get_time_range_today()
    now = datetime.now(CST)
    print(f"📅 Calendar — {now.strftime('%A, %B %-d, %Y')}")
    print()

    all_events = get_all_events(creds, t_min, t_max)
    if not all_events:
        print("  No events today.")
        return all_events

    for domain in PRIORITY_ORDER:
        if domain in all_events:
            events = all_events[domain]
            print(f"  **{domain}**")
            for e in events:
                time_str = format_event_time(e)
                summary = e.get("summary", "(no title)")
                print(f"    {time_str} — {summary}")
            print()

    return all_events


def print_week():
    creds = get_creds()
    t_min, t_max = get_time_range_week()
    now = datetime.now(CST)
    end = now + timedelta(days=7)
    print(f"📅 Week View — {now.strftime('%b %-d')} to {end.strftime('%b %-d, %Y')}")
    print()

    all_events = get_all_events(creds, t_min, t_max)
    if not all_events:
        print("  No events this week.")
        return all_events

    # Group by date
    by_date = {}
    for domain, events in all_events.items():
        for e in events:
            start = e.get("start", {})
            dt_str = start.get("dateTime", start.get("date", ""))
            try:
                dt = datetime.fromisoformat(dt_str)
                date_key = dt.strftime("%A, %b %-d")
            except Exception:
                date_key = dt_str
            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append((domain, e))

    for date_key in sorted(by_date.keys(), key=lambda d: d):
        print(f"  **{date_key}**")
        for domain, e in by_date[date_key]:
            time_str = format_event_time(e)
            summary = e.get("summary", "(no title)")
            print(f"    [{domain}] {time_str} — {summary}")
        print()

    return all_events


def print_tasks():
    creds = get_creds()
    grouped = get_tasks_by_domain(creds)
    total = sum(len(v) for v in grouped.values())
    print(f"✅ Tasks — {total} open items in 00_Inbox")
    print()

    if not grouped:
        print("  No open tasks.")
        return

    # Display in domain priority order
    domain_order = ["CHAPEL", "MINISTRY", "TRADING", "DEV", "FAMILY", "PERSONAL", "CONTENT", "INBOX"]
    for tag in domain_order:
        if tag in grouped:
            tasks = grouped[tag]
            print(f"  **{tag}** ({len(tasks)})")
            for t in tasks:
                due = f" (due {t['due'][:10]})" if t.get("due") else ""
                print(f"    • {t['title']}{due}")
            print()

    # Any tags not in the standard list
    for tag in grouped:
        if tag not in domain_order:
            tasks = grouped[tag]
            print(f"  **{tag}** ({len(tasks)})")
            for t in tasks:
                print(f"    • {t['title']}")
            print()


def print_conflicts(all_events=None):
    creds = get_creds()
    if all_events is None:
        t_min, t_max = get_time_range_today()
        all_events = get_all_events(creds, t_min, t_max)

    conflicts = detect_conflicts(all_events)
    if not conflicts:
        print("  ✅ No scheduling conflicts detected.")
    else:
        print(f"  ⚠️ {len(conflicts)} conflict(s) detected:")
        for a, b in conflicts:
            print(f"    ⚠️ {a['domain']}: {a['summary']} ({a['start'].strftime('%-I:%M %p')}–{a['end'].strftime('%-I:%M %p')})")
            print(f"       ↔ {b['domain']}: {b['summary']} ({b['start'].strftime('%-I:%M %p')}–{b['end'].strftime('%-I:%M %p')})")
        print()


def print_drive_inbox():
    creds = get_creds()
    files = list_drive_folder(creds, DRIVE_FOLDERS["00_Inbox"])
    print(f"📁 Drive Inbox — 01_ArnoldOS_Gemini/00_Inbox")
    print()
    if not files:
        print("  Empty — nothing to file.")
    else:
        print(f"  {len(files)} item(s):")
        for f in files:
            mod = f.get("modifiedTime", "")[:10]
            print(f"    • {f['name']} ({mod})")


def print_brief():
    """Full morning brief — ArnoldOS section."""
    print("=" * 50)
    print("🖥️  ArnoldOS — Daily Brief")
    print("=" * 50)
    print()

    # Calendar
    try:
        all_events = print_today()
    except Exception as e:
        print(f"  ⚠️ Calendar failed: {e}")
        all_events = {}
    print()

    # Conflicts
    try:
        print_conflicts(all_events)
    except Exception as e:
        print(f"  ⚠️ Conflict detection failed: {e}")
    print()

    # Tasks
    try:
        print_tasks()
    except Exception as e:
        print(f"  ⚠️ Tasks failed: {e}")
    print()

    # Drive inbox
    try:
        print_drive_inbox()
    except Exception as e:
        print(f"  ⚠️ Drive inbox failed: {e}")


def print_calendars():
    """List all calendar names and IDs."""
    for name in PRIORITY_ORDER:
        print(f"  {name}: {CALENDARS[name]}")


# --- JSON Output Helpers ---

def json_output(data: dict):
    """Print JSON to stdout and exit."""
    print(json.dumps(data, indent=2, default=str))
    sys.exit(0)


def tasks_json(creds) -> dict:
    """Return tasks data as a structured dict."""
    grouped = get_tasks_by_domain(creds)
    total = sum(len(v) for v in grouped.values())
    return {
        "command": "tasks",
        "total": total,
        "domains": grouped,
    }


def events_json(creds, time_min: str, time_max: str) -> dict:
    """Return calendar events as a structured dict, keyed by domain."""
    all_events = get_all_events(creds, time_min, time_max)
    result = {}
    for domain, events in all_events.items():
        result[domain] = []
        for e in events:
            start = e.get("start", {})
            end = e.get("end", {})
            dt_start = start.get("dateTime", start.get("date", ""))
            dt_end = end.get("dateTime", end.get("date", ""))
            all_day = "dateTime" not in start
            result[domain].append({
                "id": e.get("id", ""),
                "summary": e.get("summary", "(no title)"),
                "start": dt_start,
                "end": dt_end,
                "startFormatted": format_event_time(e),
                "allDay": all_day,
                "location": e.get("location", ""),
                "description": e.get("description", ""),
            })
    return result


def complete_task_json(creds, search_title: str) -> dict:
    """Complete a task and return structured result."""
    tasks = get_tasks(creds)
    search_lower = search_title.lower().strip()

    matches = []
    for t in tasks:
        title = t.get("title", "")
        if not title.strip():
            continue
        _, clean = parse_task_tag(title)
        if search_lower in title.lower() or search_lower in clean.lower():
            matches.append(t)

    if len(matches) == 0:
        return {"command": "complete-task", "success": False,
                "error": f"No task found matching: \"{search_title}\"", "matches": []}

    if len(matches) > 1:
        return {"command": "complete-task", "success": False,
                "error": f"Multiple tasks match \"{search_title}\"",
                "matches": [{"id": m["id"], "title": m.get("title", "")} for m in matches]}

    task = matches[0]
    result = api_patch(
        creds,
        f"https://www.googleapis.com/tasks/v1/lists/{TASK_LIST_ID}/tasks/{task['id']}",
        {"status": "completed"}
    )
    if result:
        return {"command": "complete-task", "success": True,
                "task": {"id": task["id"], "title": task.get("title", "")}}
    else:
        return {"command": "complete-task", "success": False,
                "error": f"API call failed for: {task.get('title', '')}",
                "task": {"id": task["id"], "title": task.get("title", "")}}



def create_task(creds, title: str, notes: str = None, due: str = None) -> dict:
    """Create a new task in 00_Inbox.
    
    Args:
        title: Task title (should include [DOMAIN] tag, e.g., "[MINISTRY] Sermon prep")
        notes: Optional notes/description
        due: Optional due date in YYYY-MM-DD format
    
    Returns:
        dict with success status and task details or error
    """
    task_body = {"title": title}
    
    if notes:
        task_body["notes"] = notes
    if due:
        # Tasks API expects RFC 3339 date format
        task_body["due"] = f"{due}T00:00:00.000Z"
    
    url = f"https://www.googleapis.com/tasks/v1/lists/{TASK_LIST_ID}/tasks"
    result = api_post(creds, url, task_body)
    
    if result:
        return {
            "command": "create-task",
            "success": True,
            "task": {
                "id": result.get("id"),
                "title": result.get("title"),
                "notes": result.get("notes"),
                "due": result.get("due"),
                "status": result.get("status")
            }
        }
    else:
        return {"command": "create-task", "success": False, 
                "error": "API call failed to create task"}



# --- Quick Capture ---

DOMAIN_KEYWORDS = {
    "CHAPEL": [
        "ucg", "passover", "chapel", "prison", "chaplain", "systematic theology",
        "sys theo", "unleavened", "feast", "sabbath", "holy day", "atonement",
        "tabernacles", "trumpets", "pentecost", "incarcerated", "correctional"
    ],
    "MINISTRY": [
        "sermon", "preach", "st. peter", "st peter", "stone church", "brainstorm",
        "manuscript", "liturgy", "congregation", "pastor", "ministry", "homily",
        "exegesis", "hermeneutic", "expository", "devotional", "bible study"
    ],
    "TRADING": [
        "bitcoin", "btc", "crypto", "tsla", "tesla", "stock", "market", "portfolio",
        "trade", "invest", "etf", "chart", "technical analysis", "ta", "dca",
        "bull", "bear", "position", "hodl", "exchange", "coinbase", "glassnode"
    ],
    "DEV": [
        "code", "deploy", "dashboard", "api", "bug", "feature", "github", "git",
        "script", "python", "clawdbot", "clawd", "server", "debug", "refactor",
        "pr", "merge", "branch", "test", "sacred", "btctx"
    ],
    "FAMILY": [
        "groceries", "grocery", "kids", "household", "doctor", "appointment",
        "dentist", "school", "family", "home", "repair", "maintenance", "chore",
        "errand", "pickup", "drop off", "wife", "husband", "son", "daughter"
    ],
    "CONTENT": [
        "youtube", "video", "record", "edit", "upload", "thumbnail", "channel",
        "subscriber", "content", "film", "camera", "audio", "podcast"
    ],
    "PERSONAL": [
        "workout", "gym", "exercise", "health", "read", "book", "personal",
        "hobby", "vacation", "travel", "birthday", "anniversary"
    ]
}

# Words that should never match (too generic)
STOPWORDS = {"the", "a", "an", "to", "for", "and", "or", "on", "in", "at", "by", "with", "about"}


def infer_domain(text: str) -> tuple:
    """Infer domain from text using keyword matching.
    
    Returns:
        tuple: (domain, confidence, matched_keywords)
        - domain: Best matching domain or None if ambiguous
        - confidence: "high" (1 match), "medium" (multiple same domain), "low" (multiple domains), "none"
        - matched_keywords: list of keywords that matched
    """
    text_lower = text.lower()
    matches = {}  # domain -> list of matched keywords
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        matched = []
        for kw in keywords:
            if kw in text_lower:
                matched.append(kw)
        if matched:
            matches[domain] = matched
    
    if not matches:
        return (None, "none", [])
    
    if len(matches) == 1:
        domain = list(matches.keys())[0]
        keywords = matches[domain]
        confidence = "high" if len(keywords) >= 1 else "medium"
        return (domain, confidence, keywords)
    
    # Multiple domains matched — pick the one with most keyword matches
    sorted_matches = sorted(matches.items(), key=lambda x: len(x[1]), reverse=True)
    top_domain, top_keywords = sorted_matches[0]
    second_domain, second_keywords = sorted_matches[1]
    
    # If clear winner (2+ more matches), use it with medium confidence
    if len(top_keywords) >= len(second_keywords) + 2:
        return (top_domain, "medium", top_keywords)
    
    # Too close to call
    return (None, "low", list(matches.keys()))


def parse_date_from_text(text: str) -> tuple:
    """Extract date from natural language text.
    
    Returns:
        tuple: (date_str or None, cleaned_text)
        - date_str: YYYY-MM-DD format or None
        - cleaned_text: text with date phrase removed
    """
    import re
    from datetime import datetime, timedelta
    
    text_lower = text.lower()
    today = datetime.now(CST)
    date_found = None
    phrase_to_remove = ""
    
    # Month name + day: "March 31", "Feb 15", "january 1st"
    month_pattern = r'\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?\b'
    match = re.search(month_pattern, text_lower)
    if match:
        month_str, day_str = match.groups()
        month_map = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
            'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9,
            'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }
        month = month_map.get(month_str)
        day = int(day_str)
        year = today.year
        try:
            candidate = datetime(year, month, day, tzinfo=CST)
            if candidate.date() < today.date():
                candidate = datetime(year + 1, month, day, tzinfo=CST)
            date_found = candidate.strftime("%Y-%m-%d")
            phrase_to_remove = match.group(0)
        except ValueError:
            pass
    
    # Day of week: "thursday", "friday", etc.
    if not date_found:
        days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day_name in enumerate(days_of_week):
            if re.search(r'\b' + day_name + r'\b', text_lower):
                days_ahead = i - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                date_found = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                phrase_to_remove = day_name
                break
    
    # Relative: "tomorrow", "today", "next week"
    if not date_found:
        if re.search(r'\btomorrow\b', text_lower):
            date_found = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            phrase_to_remove = "tomorrow"
        elif re.search(r'\btoday\b', text_lower):
            date_found = today.strftime("%Y-%m-%d")
            phrase_to_remove = "today"
        elif re.search(r'\bnext week\b', text_lower):
            date_found = (today + timedelta(days=7)).strftime("%Y-%m-%d")
            phrase_to_remove = "next week"
    
    # Clean up text - remove date phrase
    cleaned = text
    if phrase_to_remove:
        cleaned = re.sub(re.escape(phrase_to_remove), '', text, flags=re.IGNORECASE).strip()
        # Clean up dangling prepositions
        cleaned = re.sub(r'\s+(by|on|for|due|before)\s*$', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'^(by|on|for|due|before)\s+', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return (date_found, cleaned)




def quick_capture(creds, text: str, force_domain: str = None) -> dict:
    """Parse natural language and create a task with inferred domain.
    
    Args:
        text: Natural language input like "UCG Passover reminder March 31"
        force_domain: Override domain inference (optional)
    
    Returns:
        dict with success status, created task, and inference details
    """
    # Parse date first
    due_date, cleaned_text = parse_date_from_text(text)
    
    # Infer domain
    if force_domain:
        domain = force_domain.upper()
        confidence = "forced"
        matched = []
    else:
        domain, confidence, matched = infer_domain(text)
    
    # Handle low/no confidence
    if confidence in ("none", "low"):
        if confidence == "none":
            return {
                "command": "quick",
                "success": False,
                "error": "Could not determine domain. Please specify: --domain CHAPEL|MINISTRY|TRADING|DEV|FAMILY|CONTENT|PERSONAL",
                "parsed": {
                    "text": cleaned_text,
                    "due": due_date,
                    "domain_candidates": matched if matched else ["PERSONAL (default)"]
                }
            }
        else:  # low confidence - multiple domains matched
            return {
                "command": "quick",
                "success": False,
                "error": f"Ambiguous domain. Matched: {', '.join(matched)}. Please specify: --domain <DOMAIN>",
                "parsed": {
                    "text": cleaned_text,
                    "due": due_date,
                    "domain_candidates": matched
                }
            }
    
    # Build task title
    title = f"[{domain}] {cleaned_text}"
    
    # Create the task
    result = create_task(creds, title, notes=None, due=due_date)
    
    if result["success"]:
        return {
            "command": "quick",
            "success": True,
            "task": result["task"],
            "inference": {
                "domain": domain,
                "confidence": confidence,
                "matched_keywords": matched,
                "parsed_date": due_date,
                "original_text": text
            }
        }
    else:
        return {
            "command": "quick",
            "success": False,
            "error": result.get("error", "Failed to create task"),
            "inference": {
                "domain": domain,
                "confidence": confidence,
                "matched_keywords": matched
            }
        }



def parse_time_from_text(text: str) -> tuple:
    """Extract time from natural language text.
    
    Returns:
        tuple: (start_time, end_time, cleaned_text)
        - Times in HH:MM format (24hr) or None
        - Default duration: 1 hour if only start given
    """
    import re
    
    text_lower = text.lower()
    start_time = None
    end_time = None
    phrase_to_remove = ""
    
    # Pattern: "2pm", "2:30pm", "14:00", "2 pm"
    time_pattern = r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b'
    matches = list(re.finditer(time_pattern, text_lower))
    
    if matches:
        # First match is start time
        m = matches[0]
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)
        
        if ampm == 'pm' and hour < 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0
        elif not ampm and hour < 8:  # Assume PM for times like "2" without am/pm
            hour += 12
            
        start_time = f"{hour:02d}:{minute:02d}"
        phrase_to_remove = m.group(0)
        
        # If second time match, that's end time
        if len(matches) > 1:
            m2 = matches[1]
            hour2 = int(m2.group(1))
            minute2 = int(m2.group(2)) if m2.group(2) else 0
            ampm2 = m2.group(3)
            
            if ampm2 == 'pm' and hour2 < 12:
                hour2 += 12
            elif ampm2 == 'am' and hour2 == 12:
                hour2 = 0
            elif not ampm2 and hour2 < 8:
                hour2 += 12
                
            end_time = f"{hour2:02d}:{minute2:02d}"
            phrase_to_remove = text_lower[m.start():m2.end()]
        else:
            # Default 1 hour duration
            end_hour = hour + 1
            end_time = f"{end_hour:02d}:{minute:02d}"
    
    # Clean text
    cleaned = text
    if phrase_to_remove:
        cleaned = re.sub(re.escape(phrase_to_remove), '', text, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'\s+(at|from|@)\s*$', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'^(at|from|@)\s+', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return (start_time, end_time, cleaned)


def quick_event(creds, text: str, force_domain: str = None) -> dict:
    """Parse natural language and create a calendar event with inferred domain.
    
    Args:
        text: Natural language input like "meeting with John Thursday 2pm"
        force_domain: Override domain inference (optional)
    
    Returns:
        dict with success status, created event, and inference details
    """
    # Parse date first
    due_date, text_after_date = parse_date_from_text(text)
    
    # Parse time
    start_time, end_time, cleaned_text = parse_time_from_text(text_after_date)
    
    # If no time found, can't create event
    if not start_time:
        return {
            "command": "quick-event",
            "success": False,
            "error": "No time found. Include a time like '2pm' or '14:00'. For tasks without time, use 'quick' instead.",
            "parsed": {
                "text": cleaned_text,
                "date": due_date
            }
        }
    
    # If no date, default to today
    if not due_date:
        from datetime import datetime
        due_date = datetime.now(CST).strftime("%Y-%m-%d")
    
    # Infer domain
    if force_domain:
        domain = force_domain.upper()
        confidence = "forced"
        matched = []
    else:
        domain, confidence, matched = infer_domain(text)
    
    # Handle low/no confidence - default to PERSONAL for events
    if confidence in ("none", "low"):
        if confidence == "none":
            domain = "PERSONAL"
            confidence = "default"
            matched = []
        else:  # low - multiple matched, pick first or default
            domain = matched[0] if matched else "PERSONAL"
            confidence = "low-picked"
    
    # Build datetime strings
    start_dt = f"{due_date}T{start_time}:00"
    end_dt = f"{due_date}T{end_time}:00"
    
    # Map domain to calendar (CONTENT uses Personal calendar)
    # Calendar keys are title case: Chapel, Ministry, Trading, Dev, Family, Personal
    cal_domain = domain.title() if domain != "CONTENT" else "Personal"
    
    # Create the event
    result = create_calendar_event(creds, cal_domain, cleaned_text, start_dt, end_dt)
    
    if result["success"]:
        return {
            "command": "quick-event",
            "success": True,
            "event": result["event"],
            "inference": {
                "domain": domain,
                "calendar": cal_domain,
                "confidence": confidence,
                "matched_keywords": matched,
                "parsed_date": due_date,
                "parsed_time": f"{start_time}-{end_time}",
                "original_text": text
            }
        }
    else:
        return {
            "command": "quick-event",
            "success": False,
            "error": result.get("error", "Failed to create event"),
            "inference": {
                "domain": domain,
                "confidence": confidence,
                "matched_keywords": matched
            }
        }


def create_calendar_event(creds, domain: str, summary: str, start: str, end: str, 
                          description: str = None, location: str = None) -> dict:
    """Create a calendar event.
    
    Args:
        domain: Calendar domain (Chapel, Ministry, Trading, Dev, Family, Personal)
        summary: Event title
        start: Start time in ISO format (YYYY-MM-DDTHH:MM:SS) or date (YYYY-MM-DD for all-day)
        end: End time in ISO format or date
        description: Optional event description
        location: Optional location
    
    Returns:
        dict with success status and event details or error
    """
    if domain not in CALENDARS:
        return {"command": "create-event", "success": False, 
                "error": f"Unknown domain: {domain}. Valid: {', '.join(CALENDARS.keys())}"}
    
    calendar_id = CALENDARS[domain]
    
    # Determine if all-day event (date only) or timed event (datetime)
    is_all_day = len(start) == 10  # YYYY-MM-DD format
    
    event_body = {"summary": summary}
    
    if is_all_day:
        event_body["start"] = {"date": start}
        event_body["end"] = {"date": end}
    else:
        # Ensure timezone
        if not start.endswith('Z') and '+' not in start and '-' not in start[-6:]:
            start = start + "-06:00"  # CST
        if not end.endswith('Z') and '+' not in end and '-' not in end[-6:]:
            end = end + "-06:00"  # CST
        event_body["start"] = {"dateTime": start, "timeZone": "America/Chicago"}
        event_body["end"] = {"dateTime": end, "timeZone": "America/Chicago"}
    
    if description:
        event_body["description"] = description
    if location:
        event_body["location"] = location
    
    url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
    result = api_post(creds, url, event_body)
    
    if result:
        return {
            "command": "create-event",
            "success": True,
            "event": {
                "id": result.get("id"),
                "summary": result.get("summary"),
                "start": result.get("start"),
                "end": result.get("end"),
                "htmlLink": result.get("htmlLink"),
                "domain": domain
            }
        }
    else:
        return {"command": "create-event", "success": False, 
                "error": f"API call failed for calendar: {domain}"}


def update_calendar_event(creds, domain: str, event_id: str, 
                          summary: str = None, start: str = None, end: str = None,
                          description: str = None, location: str = None) -> dict:
    """Update an existing calendar event.
    
    Args:
        domain: Calendar domain
        event_id: The event ID to update
        summary: New title (optional)
        start: New start time (optional)
        end: New end time (optional)
        description: New description (optional)
        location: New location (optional)
    
    Returns:
        dict with success status and updated event details or error
    """
    if domain not in CALENDARS:
        return {"command": "update-event", "success": False,
                "error": f"Unknown domain: {domain}. Valid: {', '.join(CALENDARS.keys())}"}
    
    calendar_id = CALENDARS[domain]
    
    # First, get the existing event
    url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}"
    existing = api_get(creds, url)
    if not existing:
        return {"command": "update-event", "success": False,
                "error": f"Event not found: {event_id}"}
    
    # Build update body with only provided fields
    update_body = {}
    if summary is not None:
        update_body["summary"] = summary
    if description is not None:
        update_body["description"] = description
    if location is not None:
        update_body["location"] = location
    if start is not None:
        is_all_day = len(start) == 10
        if is_all_day:
            update_body["start"] = {"date": start}
        else:
            if not start.endswith('Z') and '+' not in start and '-' not in start[-6:]:
                start = start + "-06:00"
            update_body["start"] = {"dateTime": start, "timeZone": "America/Chicago"}
    if end is not None:
        is_all_day = len(end) == 10
        if is_all_day:
            update_body["end"] = {"date": end}
        else:
            if not end.endswith('Z') and '+' not in end and '-' not in end[-6:]:
                end = end + "-06:00"
            update_body["end"] = {"dateTime": end, "timeZone": "America/Chicago"}
    
    if not update_body:
        return {"command": "update-event", "success": False,
                "error": "No fields to update"}
    
    result = api_patch(creds, url, update_body)
    
    if result:
        return {
            "command": "update-event",
            "success": True,
            "event": {
                "id": result.get("id"),
                "summary": result.get("summary"),
                "start": result.get("start"),
                "end": result.get("end"),
                "htmlLink": result.get("htmlLink"),
                "domain": domain
            }
        }
    else:
        return {"command": "update-event", "success": False,
                "error": f"API call failed updating event: {event_id}"}


# --- CLI ---
if __name__ == "__main__":
    # Parse --json flag
    args = sys.argv[1:]
    use_json = "--json" in args
    if use_json:
        args.remove("--json")

    cmd = args[0] if args else "brief"

    if cmd == "today":
        if use_json:
            creds = get_creds()
            t_min, t_max = get_time_range_today()
            now = datetime.now(CST)
            data = events_json(creds, t_min, t_max)
            json_output({"command": "today", "date": now.strftime("%Y-%m-%d"), "domains": data})
        else:
            print_today()

    elif cmd == "week":
        if use_json:
            creds = get_creds()
            t_min, t_max = get_time_range_week()
            now = datetime.now(CST)
            end = now + timedelta(days=7)
            data = events_json(creds, t_min, t_max)
            json_output({"command": "week", "startDate": now.strftime("%Y-%m-%d"),
                         "endDate": end.strftime("%Y-%m-%d"), "domains": data})
        else:
            print_week()

    elif cmd == "tasks":
        if use_json:
            creds = get_creds()
            json_output(tasks_json(creds))
        else:
            print_tasks()

    elif cmd == "conflicts":
        if use_json:
            creds = get_creds()
            t_min, t_max = get_time_range_today()
            all_events = get_all_events(creds, t_min, t_max)
            conflicts = detect_conflicts(all_events)
            json_output({"command": "conflicts", "count": len(conflicts),
                         "conflicts": [{"a": {"domain": a["domain"], "summary": a["summary"],
                                              "start": a["start"].isoformat(), "end": a["end"].isoformat()},
                                        "b": {"domain": b["domain"], "summary": b["summary"],
                                              "start": b["start"].isoformat(), "end": b["end"].isoformat()}}
                                       for a, b in conflicts]})
        else:
            print_conflicts()

    elif cmd == "conflicts-week":
        if use_json:
            creds = get_creds()
            t_min, t_max = get_time_range_week()
            all_events = get_all_events(creds, t_min, t_max)
            conflicts = detect_conflicts(all_events)
            json_output({"command": "conflicts-week", "count": len(conflicts),
                         "conflicts": [{"a": {"domain": a["domain"], "summary": a["summary"],
                                              "start": a["start"].isoformat(), "end": a["end"].isoformat()},
                                        "b": {"domain": b["domain"], "summary": b["summary"],
                                              "start": b["start"].isoformat(), "end": b["end"].isoformat()}}
                                       for a, b in conflicts]})
        else:
            creds = get_creds()
            t_min, t_max = get_time_range_week()
            all_events = get_all_events(creds, t_min, t_max)
            print_conflicts(all_events)

    elif cmd == "drive-inbox":
        if use_json:
            creds = get_creds()
            files = list_drive_folder(creds, DRIVE_FOLDERS["00_Inbox"])
            json_output({"command": "drive-inbox", "count": len(files),
                         "files": [{"id": f.get("id"), "name": f.get("name"),
                                    "mimeType": f.get("mimeType"), "modifiedTime": f.get("modifiedTime")}
                                   for f in files]})
        else:
            print_drive_inbox()

    elif cmd == "brief":
        if use_json:
            print(json.dumps({"error": "brief command does not support --json (use individual commands)"}))
            sys.exit(1)
        else:
            print_brief()

    elif cmd == "calendars":
        if use_json:
            json_output({"command": "calendars",
                         "calendars": {name: cid for name, cid in CALENDARS.items()}})
        else:
            print_calendars()

    elif cmd == "complete-task":
        if len(args) < 2:
            if use_json:
                json_output({"command": "complete-task", "success": False,
                             "error": "No task title provided"})
            else:
                print("Usage: python3 arnoldos.py complete-task \"Task title\"")
            sys.exit(1)
        search = " ".join(args[1:])
        creds = get_creds()
        if use_json:
            json_output(complete_task_json(creds, search))
        else:
            complete_task(creds, search)


    elif cmd == "preaching-schedule":
        creds = get_creds()
        # Optional: --days N or --date YYYY-MM-DD
        days = 30
        target_date = None
        for i, a in enumerate(args[1:], 1):
            if a == "--days" and i + 1 < len(args):
                try:
                    days = int(args[i + 1])
                except ValueError:
                    pass
            elif a == "--date" and i + 1 < len(args):
                target_date = args[i + 1]
        result = preaching_schedule(creds, days=days, target_date=target_date)
        if use_json:
            json_output(result)
        else:
            schedule = result["schedule"]
            if not schedule:
                print("📅 No upcoming preaching events found.")
            else:
                print(f"📅 Upcoming Preaching ({result['count']} events)\n")
                for s in schedule:
                    status_icon = {"not_started": "⬜", "brainstorm": "📝", "draft": "✏️", "final": "✅"}.get(s["status"], "?")
                    passage_display = s["passage"] if s["passage"] and s["passage"] != "TBD" else "TBD"
                    print(f"  {s['date']}  {s['summary']:<30}  {passage_display:<25}  {status_icon} {s['status']}")

    elif cmd == "drive-read":
        creds = get_creds()
        if len(args) < 2:
            if use_json:
                json_output({"command": "drive-read", "success": False, "error": "Usage: drive-read <file_id> OR drive-read --folder <key> --prefix <prefix>"})
            else:
                print("Usage:\n  python3 arnoldos.py drive-read <file_id>\n  python3 arnoldos.py drive-read --folder Ministry/Brainstorm --prefix 2026-02-15")
            sys.exit(1)
        # Check for --folder/--prefix mode
        if "--folder" in args:
            folder_key = None
            prefix = None
            for i, a in enumerate(args):
                if a == "--folder" and i + 1 < len(args):
                    folder_key = args[i + 1]
                elif a == "--prefix" and i + 1 < len(args):
                    prefix = args[i + 1]
            if not folder_key or not prefix:
                result = {"command": "drive-read", "success": False, "error": "Both --folder and --prefix required"}
            else:
                result = drive_find_and_read(creds, folder_key, prefix)
        else:
            result = drive_read_file(creds, args[1])
        if use_json:
            json_output(result)
        else:
            if result.get("success"):
                print(f"📄 {result['name']}\n{'=' * 60}\n{result['content']}")
            else:
                print(f"❌ {result.get('error', 'Unknown error')}")

    elif cmd == "create-event":
        # create-event <domain> <summary> <start> <end> [--description "..."] [--location "..."]
        if len(args) < 5:
            msg = "Usage: arnoldos.py create-event <domain> <summary> <start> <end> [--description ...] [--location ...]"
            if use_json:
                json_output({"command": "create-event", "success": False, "error": msg})
            else:
                print(msg)
                print("  domain: Chapel, Ministry, Trading, Dev, Family, Personal")
                print("  start/end: YYYY-MM-DD (all-day) or YYYY-MM-DDTHH:MM:SS (timed)")
                print("Example: arnoldos.py create-event Ministry 'Team Meeting' 2026-02-03T14:00:00 2026-02-03T15:00:00")
            sys.exit(1)
        domain = args[1]
        summary = args[2]
        start = args[3]
        end = args[4]
        description = None
        location = None
        i = 5
        while i < len(args):
            if args[i] == "--description" and i + 1 < len(args):
                description = args[i + 1]
                i += 2
            elif args[i] == "--location" and i + 1 < len(args):
                location = args[i + 1]
                i += 2
            else:
                i += 1
        creds = get_creds()
        result = create_calendar_event(creds, domain, summary, start, end, description, location)
        if use_json:
            json_output(result)
        else:
            if result["success"]:
                print(f"✅ Created event: {result['event']['summary']}")
                print(f"   Domain: {result['event']['domain']}")
                print(f"   Start: {result['event']['start']}")
                print(f"   Link: {result['event'].get('htmlLink', 'N/A')}")
            else:
                print(f"❌ Failed: {result['error']}")

    elif cmd == "update-event":
        # update-event <domain> <event_id> [--summary "..."] [--description "..."] [--start ...] [--end ...] [--location "..."]
        if len(args) < 3:
            msg = "Usage: arnoldos.py update-event <domain> <event_id> [--summary ...] [--description ...] [--start ...] [--end ...] [--location ...]"
            if use_json:
                json_output({"command": "update-event", "success": False, "error": msg})
            else:
                print(msg)
            sys.exit(1)
        domain = args[1]
        event_id = args[2]
        summary = None
        description = None
        start = None
        end = None
        location = None
        i = 3
        while i < len(args):
            if args[i] == "--summary" and i + 1 < len(args):
                summary = args[i + 1]
                i += 2
            elif args[i] == "--description" and i + 1 < len(args):
                description = args[i + 1]
                i += 2
            elif args[i] == "--start" and i + 1 < len(args):
                start = args[i + 1]
                i += 2
            elif args[i] == "--end" and i + 1 < len(args):
                end = args[i + 1]
                i += 2
            elif args[i] == "--location" and i + 1 < len(args):
                location = args[i + 1]
                i += 2
            else:
                i += 1
        creds = get_creds()
        result = update_calendar_event(creds, domain, event_id, summary, start, end, description, location)
        if use_json:
            json_output(result)
        else:
            if result["success"]:
                print(f"✅ Updated event: {result['event']['summary']}")
                print(f"   Domain: {result['event']['domain']}")
            else:
                print(f"❌ Failed: {result['error']}")


    elif cmd == "create-task":
        # create-task <title> [--notes "..."] [--due YYYY-MM-DD]
        if len(args) < 2:
            msg = "Usage: arnoldos.py create-task <title> [--notes ...] [--due YYYY-MM-DD]"
            if use_json:
                json_output({"command": "create-task", "success": False, "error": msg})
            else:
                print(msg)
                print("Example: arnoldos.py create-task '[MINISTRY] Sermon prep: Feb 15' --due 2026-02-14")
            sys.exit(1)
        # Parse title (may be quoted)
        title = args[1]
        notes = None
        due = None
        i = 2
        while i < len(args):
            if args[i] == "--notes" and i + 1 < len(args):
                notes = args[i + 1]
                i += 2
            elif args[i] == "--due" and i + 1 < len(args):
                due = args[i + 1]
                i += 2
            else:
                i += 1
        creds = get_creds()
        result = create_task(creds, title, notes, due)
        if use_json:
            json_output(result)
        else:
            if result["success"]:
                print(f"✅ Created task: {result['task']['title']}")
                if result['task'].get('due'):
                    print(f"   Due: {result['task']['due']}")
            else:
                print(f"❌ Failed: {result['error']}")

    elif cmd == "quick":
        # quick <natural language text> [--domain DOMAIN]
        if len(args) < 2:
            msg = "Usage: arnoldos.py quick <text> [--domain DOMAIN]"
            if use_json:
                json_output({"command": "quick", "success": False, "error": msg})
            else:
                print(msg)
                print('Example: arnoldos.py quick "UCG Passover reminder March 31"')
                print('Example: arnoldos.py quick "finish sermon draft by Friday" --domain MINISTRY')
            sys.exit(1)
        
        # Parse args - everything before --domain is the text
        text_parts = []
        force_domain = None
        i = 1
        while i < len(args):
            if args[i] == "--domain" and i + 1 < len(args):
                force_domain = args[i + 1]
                i += 2
            else:
                text_parts.append(args[i])
                i += 1
        
        text = " ".join(text_parts)
        creds = get_creds()
        result = quick_capture(creds, text, force_domain)
        
        if use_json:
            json_output(result)
        else:
            if result["success"]:
                task = result["task"]
                inf = result["inference"]
                print(f"✅ Created: {task['title']}")
                if task.get('due'):
                    print(f"   Due: {task['due'][:10]}")
                print(f"   Domain: {inf['domain']} (confidence: {inf['confidence']})")
                if inf.get('matched_keywords'):
                    print(f"   Matched: {', '.join(inf['matched_keywords'])}")
            else:
                print(f"❌ {result['error']}")
                if result.get('parsed'):
                    p = result['parsed']
                    print(f"   Parsed text: {p.get('text', 'N/A')}")
                    print(f"   Parsed date: {p.get('due', 'None')}")
                    print(f"   Candidates: {', '.join(p.get('domain_candidates', []))}")


    elif cmd == "quick-event":
        # quick-event <natural language text> [--domain DOMAIN]
        if len(args) < 2:
            msg = "Usage: arnoldos.py quick-event <text> [--domain DOMAIN]"
            if use_json:
                json_output({"command": "quick-event", "success": False, "error": msg})
            else:
                print(msg)
                print('Example: arnoldos.py quick-event "meeting with John Thursday 2pm"')
                print('Example: arnoldos.py quick-event "bitcoin review Friday 10am" --domain TRADING')
            sys.exit(1)
        
        # Parse args
        text_parts = []
        force_domain = None
        i = 1
        while i < len(args):
            if args[i] == "--domain" and i + 1 < len(args):
                force_domain = args[i + 1]
                i += 2
            else:
                text_parts.append(args[i])
                i += 1
        
        text = " ".join(text_parts)
        creds = get_creds()
        result = quick_event(creds, text, force_domain)
        
        if use_json:
            json_output(result)
        else:
            if result["success"]:
                evt = result["event"]
                inf = result["inference"]
                print(f"✅ Created event: {evt['summary']}")
                print(f"   Calendar: {inf['calendar']}")
                print(f"   Date: {inf['parsed_date']}")
                print(f"   Time: {inf['parsed_time']}")
                print(f"   Domain: {inf['domain']} (confidence: {inf['confidence']})")
                if inf.get('matched_keywords'):
                    print(f"   Matched: {', '.join(inf['matched_keywords'])}")
                if evt.get('htmlLink'):
                    print(f"   Link: {evt['htmlLink']}")
            else:
                print(f"❌ {result['error']}")
                if result.get('parsed'):
                    p = result['parsed']
                    print(f"   Parsed text: {p.get('text', 'N/A')}")
                    print(f"   Parsed date: {p.get('date', 'None')}")


    elif cmd == "drive-upload":
        # drive-upload <folder_key> <filename> <local_file_path>
        if len(args) < 4:
            msg = "Usage: arnoldos.py drive-upload <folder_key> <filename> <local_file_path>"
            if use_json:
                json_output({"command": "drive-upload", "success": False, "error": msg})
            else:
                print(msg)
                print("Folder keys: Ministry, Ministry/Brainstorm, Ministry/Sermons, Chapel, Trading, Dev, etc.")
                print("Example: arnoldos.py drive-upload Ministry/Brainstorm 2026-02-15-romans-8.docx ./output.docx")
            sys.exit(1)
        folder_key = args[1]
        filename = args[2]
        local_path = args[3]
        if not os.path.exists(local_path):
            result = {"command": "drive-upload", "success": False, "error": f"File not found: {local_path}"}
        else:
            with open(local_path, 'rb') as f:
                content_bytes = f.read()
            # Detect mime type from extension
            if filename.endswith('.docx'):
                mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif filename.endswith('.txt'):
                mime = "text/plain"
            elif filename.endswith('.md'):
                mime = "text/markdown"
            elif filename.endswith('.pdf'):
                mime = "application/pdf"
            else:
                mime = "application/octet-stream"
            creds = get_creds()
            result = drive_upload_file(creds, folder_key, filename, content_bytes, mime)
        if use_json:
            json_output(result)
        else:
            if result["success"]:
                print(f"✅ Uploaded: {result['file']['name']}")
                print(f"   Folder: {result['file']['folder']}")
                print(f"   Link: {result['file']['webViewLink']}")
            else:
                print(f"❌ Failed: {result['error']}")


    else:
        if use_json:
            json_output({"error": f"Unknown command: {cmd}"})
        else:
            print(__doc__)
