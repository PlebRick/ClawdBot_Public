# 🚨 RECOVERY.md — Full ClawdBot Disaster Recovery Runbook
*Created: 2026-01-31 | Estimated full recovery time: 45–90 minutes*

This document enables a **complete rebuild** of ClawdBot (Clawd 🐾) from scratch on new hardware. A fresh Clawd instance can follow this step-by-step and be fully operational by the end.

> **Prerequisites:** A Linux machine (Ubuntu recommended), internet access, and Rick available to provide secrets/credentials at each phase.

---

> **Recovery Templates:** After cloning the repo, all service templates, crontab backup,
> requirements.txt, and a redacted clawdbot.json structure reference are in `~/clawd/system/`.
> The REAL clawdbot.json (with API keys) should be stored in your password manager.
>
> **Node version:** v22 (via nvm). **Python:** 3.x with deps in `system/requirements.txt`.

## Phase 1 — System Setup (~15 min)

### 1.1 Install Node.js via nvm
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc
nvm install 22
node -v  # expect v22.x
```

### 1.2 Install ClawdBot (or MoltBot when available)
```bash
# As of 2026-01-31, the real package is still "clawdbot" on npm.
# Check: npm view moltbot version — if it's > 0.1.0, use moltbot instead.
npm install -g clawdbot@latest
```

### 1.3 Install Python dependencies
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip
# After cloning repo (Phase 2):
pip3 install -r ~/clawd/system/requirements.txt
# Or if repo not yet cloned:
pip3 install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 python-docx requests beautifulsoup4 lxml
```

### 1.4 Install system tools
```bash
# GitHub CLI
sudo apt-get install -y gh

# Cloudflared
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt-get update && sudo apt-get install -y cloudflared

# Gitleaks (pre-commit secret scanning)
cd /tmp
wget -q https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_8.21.2_linux_x64.tar.gz
tar xzf gitleaks_*.tar.gz gitleaks
sudo mv gitleaks /usr/local/bin/

# Bird (X/Twitter CLI)
npm install -g @steipete/bird

# ClawdHub
npm install -g clawdhub

# Claude Code (optional)
npm install -g @anthropic-ai/claude-code

# Gemini CLI (optional)
npm install -g @google/gemini-cli
```

### 1.5 Install web-scout dependencies
```bash
cd ~/clawd/skills/web-scout
npm install
npx playwright install chromium
```

### ✅ Phase 1 Verification
```bash
node -v                    # v22.x
clawdbot --version         # 2026.x.x
python3 --version          # 3.10+
pip3 show google-api-python-client  # installed
gh --version               # 2.x
cloudflared --version      # 2026.x
gitleaks version           # 8.x
bird --version             # 0.8.x
```

---

## Phase 2 — Clone Workspace (~5 min)

### 2.1 Authenticate GitHub
```bash
gh auth login
# Choose: GitHub.com → HTTPS → Authenticate with browser
# Account: PlebRick
```

### 2.2 Clone the backup repo
```bash
cd ~
git clone https://github.com/PlebRick/ClawdBot_Backup.git clawd
cd clawd
```

### 2.3 Set up gitleaks pre-commit hook
```bash
echo '#!/bin/bash
gitleaks protect --staged --no-banner' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 2.4 Generate SSH key (for future use)
```bash
ssh-keygen -t ed25519 -C "clawd@$(hostname)" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
# → Add this to GitHub: Settings → SSH Keys
```

### ✅ Phase 2 Verification
```bash
ls ~/clawd/AGENTS.md          # exists
ls ~/clawd/MEMORY.md           # exists
ls ~/clawd/memory/context/     # 30+ files
ls ~/clawd/scripts/            # 9 scripts
git log --oneline -1           # shows latest commit
gitleaks protect --staged --no-banner  # "no leaks found"
```

---

### 2.5 Restore clawdbot.json from encrypted backup
```bash
# Option A: From Drive backup (download clawdbot-config-YYYY-MM-DD.json.gpg from Drive/02_ClawdBot/Backups/)
mkdir -p ~/.clawdbot
gpg --decrypt ~/Downloads/clawdbot-config-*.json.gpg > ~/.clawdbot/clawdbot.json
chmod 600 ~/.clawdbot/clawdbot.json

# Option B: From password manager
# Paste raw JSON into ~/.clawdbot/clawdbot.json
chmod 600 ~/.clawdbot/clawdbot.json
```
> **This restores ALL API keys, agent configs, cron jobs, channel settings, and model allowlist.**
> If restored, you can skip most of Phase 3 (keys are already in the config).
> Still need: Google OAuth tokens (Phase 3.3), Bird cookies (3.8), GPG passphrase setup.

## Phase 3 — Credentials (~15 min)

Each credential lives **outside** the repo. Rick must provide or regenerate each one.

### 3.1 Anthropic API Key
- **What:** API key for Claude models (the brain)
- **Where to get:** https://console.anthropic.com → API Keys
- **File path:** Set via `clawdbot onboard` or directly in `~/.clawdbot/clawdbot.json` under `auth.profiles`
- **Test:**
  ```bash
  ANTHROPIC_API_KEY=sk-ant-... clawdbot gateway  # starts without auth errors
  ```

### 3.2 Telegram Bot Token
- **What:** Token for the Telegram bot interface
- **Where to get:** Telegram → @BotFather → `/mybot` → existing bot or create new
- **File path:** `~/.clawdbot/clawdbot.json` → `channels.telegram.botToken`
- **Test:**
  ```bash
  curl -s "https://api.telegram.org/bot<TOKEN>/getMe" | python3 -m json.tool
  # Should return bot username
  ```

### 3.3 Google OAuth Credentials
- **What:** OAuth2 client for Calendar, Tasks, Drive, Gmail access
- **Where to get:** https://console.cloud.google.com → APIs & Services → Credentials → OAuth 2.0 Client
- **Account:** chaplaincen@gmail.com
- **File path (client credentials):** `~/.config/clawd/google-credentials.json`
- **File path (tokens):** `~/.config/clawd/google-tokens.json` (generated by auth flow)
- **Setup:**
  ```bash
  mkdir -p ~/.config/clawd
  # Place google-credentials.json (downloaded from GCP)
  cd ~/clawd/scripts
  python3 google-oauth.py auth
  # Browser opens → authorize → tokens saved
  ```
- **Test:**
  ```bash
  python3 ~/clawd/scripts/arnoldos.py calendar today
  # Should return today's calendar events
  ```

### 3.4 YouTube API Key
- **What:** API key for YouTube search (morning brief, sermon research)
- **Where to get:** https://console.cloud.google.com → APIs & Services → Credentials → API Keys
- **File path:** `~/.config/clawd/youtube-api-key.json`
- **Format:**
  ```json
  { "api_key": "AIza..." }
  ```
- **Test:**
  ```bash
  ~/clawd/scripts/youtube-latest.sh "test"
  # Should return video results
  ```

### 3.5 Brave Search API Key
- **What:** Web search for the agent
- **Where to get:** https://brave.com/search/api/ → Get API Key
- **File path:** `~/.clawdbot/clawdbot.json` → `tools.web.search.apiKey`
- **Test:** Ask Clawd to search something — should return results without errors

### 3.6 ElevenLabs API Key (TTS — "sag" skill)
- **What:** Text-to-speech voice generation
- **Where to get:** https://elevenlabs.io → Profile → API Keys
- **File path:** `~/.clawdbot/clawdbot.json` → `skills.entries.sag.apiKey`
- **Test:** Ask Clawd for a voice message — should generate audio

### 3.7 Gemini API Key
- **What:** Fallback model + Gemini CLI
- **Where to get:** https://aistudio.google.com/apikey
- **File path:** `~/.clawdbot/clawdbot.json` → `env.vars.GEMINI_API_KEY`
- **Test:**
  ```bash
  GEMINI_API_KEY=AIza... gemini "hello"
  ```

### 3.8 Bird / X Twitter Credentials
- **What:** Cookie-based auth for X/Twitter CLI
- **Where to get:** Extract from logged-in Chrome browser session
- **File path:** `~/.clawdbot/bird-env`
- **Format:**
  ```bash
  export AUTH_TOKEN=<auth_token_cookie_value>
  export CT0=<ct0_cookie_value>
  ```
- **Permissions:** `chmod 600 ~/.clawdbot/bird-env`
- **Test:**
  ```bash
  source ~/.clawdbot/bird-env && bird me
  # Should show @FaithFreedmBTC profile
  ```

### 3.9 Web-Scout Chrome Cookies
- **What:** Extracted Chrome cookies for headless browser automation (Logos, ITC, etc.)
- **Where to get:** Log into sites in Chrome, then extract
- **Setup:**
  ```bash
  cd ~/clawd/skills/web-scout
  DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus" python3 scripts/extract-cookies.py
  ```
- **File path:** `~/clawd/skills/web-scout/cookies/` (gitignored)
- **Test:**
  ```bash
  ls ~/clawd/skills/web-scout/cookies/*.json  # should list cookie files
  ```

### 3.10 Gateway Auth Password
- **What:** Password for the web UI at ai.btctx.us
- **Where to get:** Rick chooses a new password
- **File path:** `~/.clawdbot/clawdbot.json` → `gateway.auth.password`
- **Note:** Also set `gateway.auth.token` (a random hex string for API auth)
  ```bash
  # Generate a random token:
  openssl rand -hex 20
  ```


### 3.11 OpenRouter API Key

- **What:** Multi-model gateway for Qwen3, Grok, Gemini Pro, Nano Banana image gen
- **Where to get:** https://openrouter.ai → Dashboard → API Keys
- **Config location:** `~/.clawdbot/clawdbot.json` → `env.vars.OPENROUTER_API_KEY`
- **Format:** `sk-or-v1-...`
- **Also set:** Spend cap in OpenRouter dashboard ($10-20/month recommended)
- **Models allowlist:** Must add models to `agents.defaults.models` in clawdbot.json + restart gateway
- **Current models:** qwen3, grok, grok-think, gemini-pro, nano-banana (see tech reference Section 14)

### ✅ Phase 3 Verification
```bash
# Run each test command above. All should pass before proceeding.
# Quick smoke test:
python3 ~/clawd/scripts/arnoldos.py calendar today   # Google auth works
source ~/.clawdbot/bird-env && bird me                # Twitter works
curl -s "https://api.telegram.org/bot<TOKEN>/getMe"   # Telegram works
```

---

## Phase 4 — Gateway Configuration (~10 min)

### 4.1 Create systemd environment file
```bash
sudo tee /etc/clawdbot-env << 'EOF'
AUTH_TOKEN=<bird_auth_token_value>
CT0=<bird_ct0_value>
EOF
sudo chmod 600 /etc/clawdbot-env
```

### 4.2 Write gateway config
Use the template below. Replace all `REDACTED` values with real credentials from Phase 3.

```bash
mkdir -p ~/.clawdbot
cat > ~/.clawdbot/clawdbot.json << 'TEMPLATE'
{
  "env": {
    "vars": {
      "GEMINI_API_KEY": "REDACTED"
    }
  },
  "auth": {
    "profiles": {
      "anthropic:default": {
        "provider": "anthropic",
        "mode": "token"
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-opus-4-5",
        "fallbacks": [
          "google/gemini-2.5-flash"
        ]
      },
      "models": {
        "anthropic/claude-opus-4-5": {
          "alias": "opus"
        }
      },
      "workspace": "/home/ubuntu76/clawd",
      "contextPruning": {
        "mode": "cache-ttl",
        "ttl": "1h"
      },
      "compaction": {
        "mode": "safeguard"
      },
      "heartbeat": {
        "every": "1h"
      },
      "maxConcurrent": 4,
      "subagents": {
        "maxConcurrent": 8
      }
    }
  },
  "tools": {
    "web": {
      "search": {
        "apiKey": "REDACTED"
      }
    }
  },
  "messages": {
    "ackReactionScope": "group-mentions"
  },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto"
  },
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "session-memory": {
          "enabled": true
        },
        "command-logger": {
          "enabled": true
        },
        "boot-md": {
          "enabled": true
        }
      }
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "dmPolicy": "pairing",
      "botToken": "REDACTED",
      "groupPolicy": "allowlist",
      "streamMode": "partial"
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "controlUi": {
      "enabled": true,
      "allowInsecureAuth": true
    },
    "auth": {
      "mode": "password",
      "token": "REDACTED",
      "password": "REDACTED"
    },
    "trustedProxies": [
      "127.0.0.1",
      "::1"
    ],
    "tailscale": {
      "mode": "off",
      "resetOnExit": false
    },
    "tls": {
      "enabled": true,
      "autoGenerate": true
    }
  },
  "skills": {
    "install": {
      "nodeManager": "npm"
    },
    "entries": {
      "sag": {
        "apiKey": "REDACTED"
      }
    }
  },
  "plugins": {
    "entries": {
      "telegram": {
        "enabled": true
      },
      "google-gemini-cli-auth": {
        "enabled": true
      }
    }
  }
}
TEMPLATE
chmod 600 ~/.clawdbot/clawdbot.json
```

### 4.3 Create systemd service
> **Template available:** `~/clawd/system/clawdbot.service.template` — copy and adjust paths if needed.
```bash
sudo tee /etc/systemd/system/clawdbot.service << EOF
[Unit]
Description=Clawdbot Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(whoami)
Environment=HOME=$HOME
Environment=PATH=$(dirname $(which node)):/usr/local/bin:/usr/bin:/bin
EnvironmentFile=/etc/clawdbot-env
WorkingDirectory=$HOME
ExecStart=$(which node) $(which clawdbot) gateway
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable clawdbot
```

### 4.4 Set up Cloudflare Tunnel (for ai.btctx.us access)
> **Templates available:** `~/clawd/system/cloudflared.service.template` and `~/clawd/system/cloudflared-config.yml.template`
```bash
# Login to Cloudflare
cloudflared tunnel login
# Browser opens → authorize for btctx.us domain

# Create tunnel (or re-use existing)
cloudflared tunnel create clawd
# Note the tunnel UUID and credentials-file path

# Write config
sudo mkdir -p /etc/cloudflared
sudo tee /etc/cloudflared/config.yml << EOF
tunnel: clawd
credentials-file: /home/$(whoami)/.cloudflared/<TUNNEL_UUID>.json

ingress:
  - hostname: ai.btctx.us
    service: https://localhost:18789
    originRequest:
      noTLSVerify: true
  - service: http_status:404
EOF

# Create DNS route
cloudflared tunnel route dns clawd ai.btctx.us

# Create systemd service
sudo tee /etc/systemd/system/cloudflared.service << EOF
[Unit]
Description=cloudflared
After=network-online.target
Wants=network-online.target

[Service]
TimeoutStartSec=15
Type=notify
ExecStart=/usr/bin/cloudflared --no-autoupdate --config /etc/cloudflared/config.yml tunnel run
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable cloudflared
```

### 4.5 Set up cron jobs
```bash
# QUICK RESTORE: Import from backup (if repo already cloned)
crontab ~/clawd/system/crontab.bak

# OR MANUAL: Add each entry individually
# Memory sync to Google Drive (every 6 hours)
(crontab -l 2>/dev/null; echo '0 */6 * * * ~/clawd/scripts/sync-memory-to-drive.sh >> ~/clawd/logs/memory-sync.log 2>&1') | crontab -

# Dashboard cache scripts (every 60s)
# See system/crontab.bak for full list: cache-tasks, cache-today, cache-week,
# cache-gateway-status, cache-tree, cache-cron, cache-preaching

# Self-backup (daily midnight)
(crontab -l 2>/dev/null; echo '0 0 * * * crontab -l > ~/clawd/system/crontab.bak 2>&1') | crontab -
```

### 4.6 Set Anthropic API key
```bash
# Option A: Environment variable in systemd
echo "ANTHROPIC_API_KEY=sk-ant-..." | sudo tee -a /etc/clawdbot-env
sudo chmod 600 /etc/clawdbot-env

# Option B: Via clawdbot onboard
clawdbot onboard
```

### ✅ Phase 4 Verification
```bash
cat ~/.clawdbot/clawdbot.json | python3 -m json.tool  # valid JSON
sudo systemctl start clawdbot
sudo systemctl status clawdbot          # active (running)
sudo systemctl start cloudflared
sudo systemctl status cloudflared       # active (running)
journalctl -u clawdbot --no-pager -n 20  # no errors
curl -sk https://localhost:18789          # responds
crontab -l                                # shows memory-sync job
```

---

## Phase 5 — Verify Everything (~10 min)

### 5.1 Gateway is running
```bash
sudo systemctl status clawdbot      # active (running)
sudo systemctl status cloudflared   # active (running)
```

### 5.2 Web UI accessible
```bash
# Local
curl -sk https://localhost:18789 | head -5

# Remote (after Cloudflare tunnel is up)
curl -s https://ai.btctx.us | head -5
```

### 5.3 Telegram responds
Send a message to the bot on Telegram. Should get a response.

### 5.4 Google integrations
```bash
python3 ~/clawd/scripts/arnoldos.py calendar today     # Calendar
python3 ~/clawd/scripts/arnoldos.py tasks list          # Tasks
python3 ~/clawd/scripts/morning-brief-data.py           # Market data
```

### 5.5 Memory is intact
Ask Clawd: *"What's my name? What church do I pastor? What's our current TODO list?"*
Clawd should answer from MEMORY.md and memory/context files.

### 5.6 Git backup works
```bash
cd ~/clawd
echo "# test" >> /tmp/test-git.txt  # don't actually modify workspace
git status                           # should show clean working tree
git remote -v                        # origin → ClawdBot_Backup.git
```

### 5.7 Skills work
```bash
# Bird/Twitter
source ~/.clawdbot/bird-env && bird me

# Web Scout (if cookies are set up)
ls ~/clawd/skills/web-scout/cookies/*.json
```

---

## Quick Reference — All Secret Locations

| Secret | Path | Source |
|--------|------|--------|
| Anthropic API key | `/etc/clawdbot-env` or env var | console.anthropic.com |
| Telegram bot token | `~/.clawdbot/clawdbot.json` | @BotFather |
| Google OAuth client | `~/.config/clawd/google-credentials.json` | GCP Console |
| Google OAuth tokens | `~/.config/clawd/google-tokens.json` | `google-oauth.py auth` |
| YouTube API key | `~/.config/clawd/youtube-api-key.json` | GCP Console |
| Brave Search key | `~/.clawdbot/clawdbot.json` | brave.com/search/api |
| ElevenLabs key | `~/.clawdbot/clawdbot.json` | elevenlabs.io |
| Gemini API key | `~/.clawdbot/clawdbot.json` | aistudio.google.com |
| Bird auth/CT0 | `~/.clawdbot/bird-env` + `/etc/clawdbot-env` | Chrome cookies |
| Gateway password | `~/.clawdbot/clawdbot.json` | Rick chooses |
| Gateway token | `~/.clawdbot/clawdbot.json` | `openssl rand -hex 20` |
| Cloudflare tunnel | `~/.cloudflared/<UUID>.json` | `cloudflared tunnel login` |
| Web-scout cookies | `~/clawd/skills/web-scout/cookies/` | `extract-cookies.py` |

---

## Notes

- **MoltBot migration:** As of 2026-01-31, the npm package is still `clawdbot`. When `moltbot` gets a real release (version > 0.1.0), install that instead. Config dir may change from `~/.clawdbot/` to `~/.moltbot/`. See `memory/context/moltbot-migration-plan.md` for details.
- **Username:** Current system user is `ubuntu76`. If different on new hardware, update paths in systemd service, cron jobs, and cloudflared config.
- **TUI quirk:** Local TUI connections require `NODE_TLS_REJECT_UNAUTHORIZED=0` due to self-signed TLS cert. Not a security issue.
- **Fail2ban:** Consider re-enabling on new hardware: `sudo apt install fail2ban`.
- **Sudo:** Current setup has full NOPASSWD sudo. Reconfigure per security needs on new hardware.
