#!/usr/bin/env python3
"""
ITC Data Fetcher — Python wrapper for weekly market report integration

Usage: python3 itc-data.py
Output: JSON with ITC risk metrics and session status

If session expired, sends Telegram alert and returns graceful error.
"""

import subprocess
import json
import sys
import os

def fetch_itc_data():
    """Fetch ITC data via Node.js script."""
    script_path = os.path.join(os.path.dirname(__file__), 'itc-data.js')
    
    try:
        result = subprocess.run(
            ['node', script_path],
            capture_output=True,
            text=True,
            timeout=120  # 2 min timeout for multiple page loads
        )
        
        if result.returncode != 0:
            return {
                "source": "itc",
                "ok": False,
                "error": f"Script failed: {result.stderr[:200]}"
            }
        
        data = json.loads(result.stdout)
        
        # Check for session expiration
        if data.get('sessionExpired'):
            send_telegram_alert("⚠️ ITC Firebase session expired! Re-login required at https://app.intothecryptoverse.com")
        
        return data
        
    except subprocess.TimeoutExpired:
        return {
            "source": "itc",
            "ok": False,
            "error": "ITC fetch timeout (120s)"
        }
    except json.JSONDecodeError as e:
        return {
            "source": "itc",
            "ok": False,
            "error": f"JSON parse error: {e}"
        }
    except Exception as e:
        return {
            "source": "itc",
            "ok": False,
            "error": str(e)
        }


def send_telegram_alert(message):
    """Send alert via Telegram."""
    try:
        # Use clawdbot sessions_send or direct API
        subprocess.run(
            ['clawdbot', 'send', '--channel', 'telegram', '--to', 'rick', message],
            capture_output=True,
            timeout=10
        )
    except Exception:
        # Fallback: just log it
        print(f"ALERT (Telegram failed): {message}", file=sys.stderr)


if __name__ == '__main__':
    data = fetch_itc_data()
    print(json.dumps(data, indent=2))
