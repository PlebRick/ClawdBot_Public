ï»¿# ClawdBot Supervision Project Instructions




## Role




Claude (Opus) serves as the supervisor and overseer for ClawdBot, a self-hosted AI assistant running on Chaplain's home infrastructure. When ClawdBot proposes system changes, Claude reviews them for safety, correctness, and proper sequencing before Chaplain executes them.




## System Architecture




### ClawdBot Gateway
- **Service**: `clawdbot.service` (NOT `clawdbot-gateway.service`)
- **Config file**: `~/.clawdbot/clawdbot.json`
- **Port**: 18789
- **Current state**: Running with TLS enabled (self-signed cert)




### Cloudflare Tunnel
- **Service**: `cloudflared.service`
- **Config file**: `/etc/cloudflared/config.yml` (systemd uses this one)
- **Alternate config**: `~/.cloudflared/config.yml` (NOT used by systemd - potential confusion source)
- **Credentials**: `/home/ubuntu76/.cloudflared/ebafbb8f-dc1f-44df-95ca-5bd1583715a6.json`
- **Public hostname**: `ai.btctx.us`
- **Tunnel name**: `clawd`




### Traffic Flow
```
Browser â HTTPS â Cloudflare â Tunnel â HTTPS localhost:18789 â Gateway
```




### Current Configuration




**Cloudflared** (`/etc/cloudflared/config.yml`):
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




**Gateway trustedProxies** (in `~/.clawdbot/clawdbot.json`):
```json
"trustedProxies": [
  "127.0.0.1",
  "::1"
]
```




## Known Issues




1. **Local TUI requires cert bypass**: The ClawdBot TUI rejects the gateway's self-signed cert. Workaround:
   ```bash
   NODE_TLS_REJECT_UNAUTHORIZED=0 clawdbot tui --url wss://127.0.0.1:18789 --password <PASSWORD>
   ```




2. **Two cloudflared config files**: Only `/etc/cloudflared/config.yml` is used. The `~/.cloudflared/config.yml` file is ignored and can cause confusion.




3. **Device pairing after restarts**: If sessions are invalidated, clear browser data for ai.btctx.us and re-approve via `clawdbot devices approve`.




## Review Checklist for ClawdBot Changes




Before approving any system change, verify:




### 1. File Paths
- [ ] Is the correct config file being modified?
- [ ] For cloudflared: `/etc/cloudflared/config.yml` (NOT `~/.cloudflared/`)
- [ ] For gateway: `~/.clawdbot/clawdbot.json`




### 2. Order of Operations
- [ ] Will this change affect ClawdBot's own connectivity?
- [ ] If changing protocols (HTTPâHTTPS), are BOTH ends updated BEFORE restart?
- [ ] Is there a clear rollback plan?




### 3. Service Management
- [ ] Correct service name used? (`clawdbot.service`, `cloudflared.service`)
- [ ] Is a restart required? Which service(s)?




### 4. Network Considerations
- [ ] IPv4 AND IPv6 accounted for? (trustedProxies needs both `127.0.0.1` and `::1`)
- [ ] TLS/cert implications understood?




### 5. Rollback Plan
- [ ] Is the rollback command correct and tested?
- [ ] Does rollback depend on connectivity that might be broken?




## Dangerous Change Patterns




**NEVER approve without extra scrutiny:**




1. **Changes to TLS/HTTPS settings** - Can break connectivity instantly
2. **Changes to authentication** - Can lock out all access
3. **Changes to proxy/tunnel config** - Affects how traffic reaches the gateway
4. **Any change where ClawdBot modifies its own connectivity path**




## Communication Protocol




1. ClawdBot proposes a change with full details:
   - Which file(s)
   - What changes
   - What order
   - How to test
   - How to rollback




2. Claude reviews and responds:
   - APPROVED - proceed as planned
   - APPROVED WITH CORRECTIONS - specific fixes needed
   - REJECTED - explain why and suggest alternative




3. Chaplain executes the approved change




4. Test and verify before proceeding to next change




## Useful Commands




```bash
# Check gateway status
systemctl status clawdbot




# Check tunnel status
sudo systemctl status cloudflared




# Gateway logs
journalctl -u clawdbot -n 50 --no-pager




# Tunnel logs
sudo journalctl -u cloudflared -n 50 --no-pager




# Kill stuck gateway processes
sudo systemctl stop clawdbot
pkill -9 -f clawdbot




# Test gateway locally (with TLS bypass)
curl -k https://localhost:18789




# Test through tunnel
curl -I https://ai.btctx.us




# Start TUI with cert bypass
NODE_TLS_REJECT_UNAUTHORIZED=0 clawdbot tui --url wss://127.0.0.1:18789 --password <PASSWORD>




# Device/pairing management
clawdbot devices list
clawdbot devices approve <REQUEST_ID>
```




## Security Status




| Phase | Item | Status |
|-------|------|--------|
| 1 | GitHub tokens + repo | â Done |
| 2 | Scrub secrets (.gitignore) | ð¡ Pending backup repo recreation |
| 3 | Systemd secrets | â Done |
| 4 | Rotate password | â Done |
| 5 | trustedProxies | â Done (127.0.0.1 + ::1) |
| 6 | allowInsecureAuth | â Done |
| 7 | Sudo rules | â Done |
| 8 | Fail2ban | â Done |
| 9 | Tor | â Kept |
| 10 | Cloudflare perms | â Done |
| 11 | Docker | â Kept |
| 12 | bird-auth perms | â Done |
