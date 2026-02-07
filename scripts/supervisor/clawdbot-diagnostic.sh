#!/usr/bin/env bash
set -uo pipefail

# ============================================================================
# clawdbot-diagnostic.sh — Comprehensive health check for ClawdBot stack
# ============================================================================

PASS="✅"
FAIL="❌"
WARN="⚠️"

pass_count=0
fail_count=0
warn_count=0

mark_pass() { echo "  $PASS $1"; ((pass_count++)); }
mark_fail() { echo "  $FAIL $1"; ((fail_count++)); }
mark_warn() { echo "  $WARN $1"; ((warn_count++)); }

section() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  $1"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

CLAWDBOT_JSON="$HOME/.clawdbot/clawdbot.json"
CLAWD_DIR="$HOME/clawd"

# ============================================================================
# 1. SERVICE HEALTH
# ============================================================================
section "1. SERVICE HEALTH"

check_service_system() {
  local svc="$1"
  if sudo systemctl is-active --quiet "$svc" 2>/dev/null; then
    mark_pass "$svc is active (system)"
  else
    mark_fail "$svc is NOT active (system)"
  fi
}

check_service_system "clawdbot"
check_service_system "cloudflared"
check_service_system "code-server@ubuntu76"

# clawd-files runs as a standalone python3 process, not a systemd unit
if ss -tlnp 2>/dev/null | grep -q ":18790 "; then
  local_proc=$(ss -tlnp 2>/dev/null | grep ":18790 " | grep -oP 'users:\(\("\K[^"]+' || echo "unknown")
  mark_pass "clawd-files is listening on :18790 (${local_proc})"
else
  mark_fail "clawd-files is NOT listening on :18790"
fi

# ============================================================================
# 2. CONNECTIVITY
# ============================================================================
section "2. CONNECTIVITY"

check_url() {
  local url="$1"
  local label="$2"
  shift 2
  local extra_flags=("$@")
  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${extra_flags[@]}" "$url" 2>/dev/null) || true
  if [[ "$http_code" =~ ^(200|301|302|304)$ ]]; then
    mark_pass "$label → HTTP $http_code"
  elif [[ "$http_code" == "401" || "$http_code" == "403" ]]; then
    mark_warn "$label → HTTP $http_code (reachable, auth required)"
  elif [[ "$http_code" == "000" ]]; then
    mark_fail "$label → connection failed"
  elif [[ "$http_code" =~ ^[0-9]+$ ]] && (( http_code >= 400 )); then
    mark_fail "$label → HTTP $http_code"
  else
    mark_warn "$label → HTTP $http_code"
  fi
}

check_url "https://localhost:18789" "localhost:18789 (clawdbot)" -k
check_url "https://ai.btctx.us" "ai.btctx.us (tunnel)"
check_url "http://localhost:18790" "localhost:18790 (clawd-files)"
check_url "https://ai.btctx.us/files/" "ai.btctx.us/files/ (files via tunnel)"

# ============================================================================
# 3. CONFIG INTEGRITY
# ============================================================================
section "3. CONFIG INTEGRITY"

if [[ -f "$CLAWDBOT_JSON" ]]; then
  mark_pass "clawdbot.json exists"
else
  mark_fail "clawdbot.json NOT found at $CLAWDBOT_JSON"
fi

if [[ -f "$CLAWDBOT_JSON" ]]; then
  if python3 -c "import json; json.load(open('$CLAWDBOT_JSON'))" 2>/dev/null; then
    mark_pass "clawdbot.json is valid JSON"
  else
    mark_fail "clawdbot.json is NOT valid JSON"
  fi

  # Check API keys in env.vars
  for key in ANTHROPIC_API_KEY OPENROUTER_API_KEY GEMINI_API_KEY; do
    has_key=$(python3 -c "
import json, sys
cfg = json.load(open('$CLAWDBOT_JSON'))
env_vars = cfg.get('env', {}).get('vars', {})
print('yes' if '$key' in env_vars else 'no')
" 2>/dev/null) || has_key="error"
    if [[ "$has_key" == "yes" ]]; then
      mark_pass "$key present in env.vars"
    else
      mark_fail "$key missing from env.vars"
    fi
  done

  # Check gateway.auth.mode
  auth_mode=$(python3 -c "
import json
cfg = json.load(open('$CLAWDBOT_JSON'))
print(cfg.get('gateway', {}).get('auth', {}).get('mode', ''))
" 2>/dev/null) || auth_mode=""
  if [[ "$auth_mode" == "token" || "$auth_mode" == "password" ]]; then
    mark_pass "gateway.auth.mode is \"$auth_mode\""
  else
    mark_fail "gateway.auth.mode is \"$auth_mode\" (expected \"token\" or \"password\")"
  fi

  # Check trustedProxies
  proxies_check=$(python3 -c "
import json
cfg = json.load(open('$CLAWDBOT_JSON'))
proxies = cfg.get('gateway', {}).get('trustedProxies', [])
has_v4 = '127.0.0.1' in proxies
has_v6 = '::1' in proxies
if has_v4 and has_v6:
    print('both')
elif has_v4:
    print('v4only')
elif has_v6:
    print('v6only')
else:
    print('none')
" 2>/dev/null) || proxies_check="error"
  if [[ "$proxies_check" == "both" ]]; then
    mark_pass "trustedProxies has 127.0.0.1 and ::1"
  else
    mark_fail "trustedProxies check: $proxies_check (need both 127.0.0.1 and ::1)"
  fi
fi

# Cloudflared config
if [[ -f /etc/cloudflared/config.yml ]]; then
  mark_pass "/etc/cloudflared/config.yml exists"
else
  mark_fail "/etc/cloudflared/config.yml NOT found"
fi

cf_unit_config=$(sudo systemctl cat cloudflared 2>/dev/null) || cf_unit_config=""
if echo "$cf_unit_config" | grep -q "/etc/cloudflared/config.yml"; then
  mark_pass "cloudflared systemd unit references /etc/cloudflared/config.yml"
else
  mark_fail "cloudflared systemd unit does NOT reference /etc/cloudflared/config.yml"
fi

# ============================================================================
# 4. SKILLS
# ============================================================================
section "4. SKILLS"

SKILLS_DIR="$CLAWD_DIR/skills"
required_skills=("arnoldos" "sermon-writer" "bible-brainstorm" "web-scout" "liturgy")

for skill in "${required_skills[@]}"; do
  skill_dir="$SKILLS_DIR/$skill"
  skill_md="$skill_dir/SKILL.md"
  if [[ ! -d "$skill_dir" ]]; then
    mark_fail "skill directory missing: $skill"
    continue
  fi
  if [[ ! -f "$skill_md" ]]; then
    mark_fail "SKILL.md missing for: $skill"
    continue
  fi
  # Skills use varying formats:
  #   - YAML frontmatter: ---\nname: ...\ndescription: ...\n---
  #   - Markdown heading:  # Name\n## Description\n...
  #   - Plain text with name/description somewhere in the file
  has_name=$(grep -cP '^(name:|#\s+\S)' "$skill_md" 2>/dev/null) || has_name=0
  has_desc=$(grep -ciP '^(description:|\#{1,2}\s+description)' "$skill_md" 2>/dev/null) || has_desc=0
  if (( has_name > 0 && has_desc > 0 )); then
    mark_pass "skill $skill has SKILL.md with name + description"
  else
    mark_warn "skill $skill SKILL.md missing name ($has_name) or description ($has_desc)"
  fi
done

# ============================================================================
# 5. MEMORY SYSTEM
# ============================================================================
section "5. MEMORY SYSTEM"

MEMORY_DB="$HOME/.clawdbot/memory/main.sqlite"

if [[ -f "$MEMORY_DB" ]]; then
  mark_pass "memory DB exists: main.sqlite"
  chunk_count=$(sqlite3 "$MEMORY_DB" "SELECT COUNT(*) FROM chunks;" 2>/dev/null) || chunk_count="error"
  if [[ "$chunk_count" == "error" ]]; then
    mark_warn "could not query chunk count from memory DB"
  else
    echo "       chunks in DB: $chunk_count"
    if (( chunk_count > 0 )); then
      mark_pass "memory DB has $chunk_count chunks"
    else
      mark_warn "memory DB has 0 chunks"
    fi
  fi
  last_indexed=$(sqlite3 "$MEMORY_DB" "SELECT MAX(indexed_at) FROM chunks;" 2>/dev/null) || last_indexed="unknown"
  echo "       last indexed: ${last_indexed:-never}"
else
  mark_fail "memory DB NOT found: $MEMORY_DB"
fi

MEMORY_MD="$CLAWD_DIR/MEMORY.md"
if [[ -f "$MEMORY_MD" ]]; then
  mark_pass "MEMORY.md exists"
else
  mark_fail "MEMORY.md NOT found"
fi

bootstrap_files=("AGENTS.md" "SOUL.md" "USER.md" "IDENTITY.md" "TOOLS.md" "HEARTBEAT.md")
for bf in "${bootstrap_files[@]}"; do
  bf_path="$CLAWD_DIR/$bf"
  if [[ ! -f "$bf_path" ]]; then
    mark_fail "bootstrap file missing: $bf"
    continue
  fi
  char_count=$(wc -c < "$bf_path")
  if (( char_count <= 20000 )); then
    mark_pass "$bf exists (${char_count} chars, under 20K)"
  else
    mark_warn "$bf exists but is ${char_count} chars (over 20K limit)"
  fi
done

# ============================================================================
# 6. CRON JOBS
# ============================================================================
section "6. CRON JOBS"

cron_output=$(crontab -l 2>/dev/null) || cron_output=""
if [[ -z "$cron_output" ]]; then
  mark_warn "no crontab entries found"
else
  mark_pass "crontab has entries"
  while IFS= read -r line; do
    # Skip comments and blank lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    # Extract script paths from the cron line
    scripts=$(echo "$line" | grep -oP '(/[\w./-]+\.sh)' 2>/dev/null) || scripts=""
    for script in $scripts; do
      if [[ -f "$script" ]]; then
        mark_pass "cron script exists: $script"
      else
        mark_fail "cron script missing: $script"
      fi
    done
  done <<< "$cron_output"
fi

CRONTAB_BAK="$CLAWD_DIR/system/crontab.bak"
if [[ -f "$CRONTAB_BAK" ]]; then
  bak_age_sec=$(( $(date +%s) - $(stat -c %Y "$CRONTAB_BAK") ))
  bak_age_hr=$(( bak_age_sec / 3600 ))
  if (( bak_age_sec < 172800 )); then
    mark_pass "crontab.bak is fresh (${bak_age_hr}h old, <48h)"
  else
    mark_warn "crontab.bak is stale (${bak_age_hr}h old, >48h)"
  fi
else
  mark_fail "crontab.bak NOT found at $CRONTAB_BAK"
fi

# ============================================================================
# 7. CACHE FRESHNESS
# ============================================================================
section "7. CACHE FRESHNESS"

CACHE_DIR="$CLAWD_DIR/memory/cache"
cache_files=("tasks.json" "today.json" "week.json")

for cf in "${cache_files[@]}"; do
  cf_path="$CACHE_DIR/$cf"
  if [[ ! -f "$cf_path" ]]; then
    mark_fail "cache file missing: $cf"
    continue
  fi
  age_sec=$(( $(date +%s) - $(stat -c %Y "$cf_path") ))
  age_min=$(( age_sec / 60 ))
  age_rem_sec=$(( age_sec % 60 ))
  if (( age_sec < 300 )); then
    mark_pass "$cf is fresh (${age_min}m ${age_rem_sec}s old, <5m)"
  else
    mark_warn "$cf is stale (${age_min}m ${age_rem_sec}s old, should be <5m)"
  fi
done

# ============================================================================
# 8. GIT & BACKUP
# ============================================================================
section "8. GIT & BACKUP"

if [[ -d "$CLAWD_DIR/.git" ]]; then
  mark_pass "~/clawd is a git repo"

  uncommitted=$(git -C "$CLAWD_DIR" status --porcelain 2>/dev/null) || uncommitted=""
  if [[ -z "$uncommitted" ]]; then
    mark_pass "no uncommitted changes"
  else
    change_count=$(echo "$uncommitted" | wc -l)
    mark_warn "$change_count uncommitted change(s)"
    echo "$uncommitted" | head -10 | sed 's/^/       /'
  fi

  last_commit_msg=$(git -C "$CLAWD_DIR" log -1 --pretty=format:"%s" 2>/dev/null) || last_commit_msg="unknown"
  last_commit_age=$(git -C "$CLAWD_DIR" log -1 --pretty=format:"%ar" 2>/dev/null) || last_commit_age="unknown"
  echo "       last commit: \"$last_commit_msg\" ($last_commit_age)"

  PRE_COMMIT_HOOK="$CLAWD_DIR/.git/hooks/pre-commit"
  if [[ -f "$PRE_COMMIT_HOOK" ]]; then
    if grep -q "gitleaks" "$PRE_COMMIT_HOOK" 2>/dev/null; then
      mark_pass "gitleaks pre-commit hook is installed"
    else
      mark_warn "pre-commit hook exists but does not reference gitleaks"
    fi
  else
    mark_fail "pre-commit hook NOT found"
  fi
else
  mark_fail "~/clawd is NOT a git repo"
fi

# ============================================================================
# 9. DISK & RESOURCES
# ============================================================================
section "9. DISK & RESOURCES"

echo "  Disk usage (root):"
df -h / | tail -1 | awk '{printf "       %s total, %s used, %s avail (%s)\n", $2, $3, $4, $5}'

root_pct=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if (( root_pct < 80 )); then
  mark_pass "root disk at ${root_pct}%"
elif (( root_pct < 95 )); then
  mark_warn "root disk at ${root_pct}% (getting full)"
else
  mark_fail "root disk at ${root_pct}% (critical)"
fi

clawd_size=$(du -sh "$CLAWD_DIR" 2>/dev/null | awk '{print $1}') || clawd_size="unknown"
clawdbot_size=$(du -sh "$HOME/.clawdbot" 2>/dev/null | awk '{print $1}') || clawdbot_size="unknown"
echo "       ~/clawd:     $clawd_size"
echo "       ~/.clawdbot: $clawdbot_size"

echo "  RAM:"
free -h | grep Mem | awk '{printf "       %s total, %s used, %s free, %s available\n", $2, $3, $4, $7}'
avail_mb=$(free -m | grep Mem | awk '{print $7}')
if (( avail_mb > 512 )); then
  mark_pass "available RAM: ${avail_mb}MB"
elif (( avail_mb > 128 )); then
  mark_warn "available RAM low: ${avail_mb}MB"
else
  mark_fail "available RAM critical: ${avail_mb}MB"
fi

# ============================================================================
# 10. MODEL REGISTRY
# ============================================================================
section "10. MODEL REGISTRY"

if [[ -f "$CLAWDBOT_JSON" ]]; then
  python3 -c "
import json, sys

cfg = json.load(open('$CLAWDBOT_JSON'))
agents = cfg.get('agents', {})
defaults = agents.get('defaults', {})
models = defaults.get('models', {})

if not models:
    print('  $FAIL no agents.defaults.models found')
    sys.exit(0)

default_model = defaults.get('model', 'not set')
if isinstance(default_model, dict):
    primary = default_model.get('primary', '?')
    fallbacks = default_model.get('fallbacks', [])
    print(f'  Default model (primary): {primary}')
    if fallbacks:
        print(f'  Fallbacks: {\", \".join(fallbacks)}')
else:
    print(f'  Default model: {default_model}')

print()
print('  Registered models:')
for model_id in sorted(models.keys()):
    model_cfg = models[model_id]
    alias = model_cfg.get('alias', '') if isinstance(model_cfg, dict) else ''
    alias_str = f' (alias: {alias})' if alias else ''
    print(f'    {model_id}{alias_str}')

print()
print(f'  $PASS model registry loaded ({len(models)} model(s))')
" 2>/dev/null || mark_fail "could not parse model registry from clawdbot.json"
else
  mark_fail "cannot read model registry — clawdbot.json missing"
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Timestamp: $(date -Iseconds)"
echo "  Hostname:  $(hostname)"
echo "  Uptime:    $(uptime -p)"
echo ""
echo "  $PASS Passed: $pass_count"
echo "  $FAIL Failed: $fail_count"
echo "  $WARN Warnings: $warn_count"
echo ""

if (( fail_count == 0 && warn_count == 0 )); then
  echo "  All checks passed. System is healthy."
elif (( fail_count == 0 )); then
  echo "  No failures, but $warn_count warning(s) to review."
else
  echo "  $fail_count failure(s) detected — action required."
fi
echo ""
