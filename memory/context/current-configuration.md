# Current Configuration
# Last updated: 2026-01-31


## Services
- Gateway: `clawdbot.service` (config: `~/.clawdbot/clawdbot.json`)
- Tunnel: `cloudflared.service` (config: `/etc/cloudflared/config.yml`)


## Cloudflared Config (ACTIVE — /etc/cloudflared/config.yml)
```yaml
tunnel: clawd
credentials-file: /home/ubuntu76/.cloudflared/ebafbb8f-dc1f-44df-95ca-5bd1583715a6.json


ingress:
  - hostname: ai.btctx.us
    service: https://localhost:18789
    originRequest:
      noTLSVerify: true
  - service: http_status:404
```


## trustedProxies (in ~/.clawdbot/clawdbot.json)
```json
"trustedProxies": ["127.0.0.1", "::1"]
```


## Security Status — All Complete
✅ GitHub tokens
✅ Systemd secrets
✅ Password rotated
✅ trustedProxies (IPv4 + IPv6)
✅ allowInsecureAuth: false
✅ Gateway TLS enabled
✅ Sudo rules
✅ Fail2ban
✅ Cloudflare perms
✅ bird-auth perms
✅ Git backup — private repo (github.com/PlebRick/ClawdBot_Backup), gitleaks pre-commit, RECOVERY.md


## TUI Note
TUI requires `NODE_TLS_REJECT_UNAUTHORIZED=0` for local connections due to self-signed cert.
This is a usability quirk, not a security issue.
