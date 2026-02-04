# Clawd Dashboard — Product Spec


## 1. Overview


**Clawd Dashboard** is a web-based control panel for Clawdbot, Rick's always-on AI assistant running on a System76 Ubuntu laptop. Today, Rick interacts with Clawd primarily via Telegram and has no visual overview of system health, sessions, memory, cron jobs, or costs. The dashboard provides at-a-glance status, memory browsing, task management, and quick actions — all from a browser, anywhere.


**Why it matters:**
- No SSH or CLI needed to check on Clawd's health
- Visual overview of costs, sessions, and activity
- Edit memory/TODO files without Telegram back-and-forth
- Manage cron jobs and trigger actions with one click


---


## 2. Tech Stack


| Layer | Choice |
|-------|--------|
| Framework | Next.js 14+ (App Router) |
| Styling | Tailwind CSS 4 |
| Components | shadcn/ui |
| State | React Server Components + `fetch` (no Redux); SWR for client polling |
| Deployment | Vercel |
| API layer | Gateway HTTP endpoints + `/tools/invoke` proxy |
| Auth | Token-based middleware gate (single user) |


---


## 3. Pages & Features (Prioritized)


### P0 — MVP (Weekend Build)


#### 3.1 Status Overview (`/`)
The home page. Single-screen health dashboard.


- **Gateway status**: online/offline indicator (via `GET /health` or `/tools/invoke` with `health` tool)
- **Current model**: display active model name
- **Uptime**: gateway process uptime
- **Active sessions count**: from `sessions_list` tool
- **Channel health**: Telegram/WhatsApp connected status
- **Daily cost estimate**: if available from status/usage data
- **System info**: hostname, OS, node version


Data source: `POST /tools/invoke` with `tool: "gateway"`, `tool: "sessions_list"`, `tool: "session_status"`


#### 3.2 Memory Browser (`/memory`)
Browse, search, and edit memory files in the workspace.


- **File tree**: list files under `memory/` directory
- **File viewer**: syntax-highlighted markdown viewer
- **Edit mode**: textarea editor with save button
- **Search**: full-text search across memory files (via `memory_search` tool or `read` + grep)


Data source: `POST /tools/invoke` with `tool: "read"` (list/read files), `tool: "write"` / `tool: "edit"` (save)


#### 3.3 TODO Viewer (`/todos`)
Visual checklist synced with `memory/context/todo.md`.


- **Checklist UI**: render `- [ ]` / `- [x]` as interactive checkboxes
- **Toggle items**: click to check/uncheck, writes back to file
- **Add items**: inline input to append new TODOs
- **Categories**: parse headings as sections


Data source: `POST /tools/invoke` with `tool: "read"` to fetch, `tool: "edit"` to update


#### 3.4 Active Sessions (`/sessions`)
List all conversation sessions.


- **Session list**: key, channel, last activity, message count
- **Filter**: by channel (telegram, whatsapp, etc.)
- **Session detail**: click to view recent messages/history


Data source: `POST /tools/invoke` with `tool: "sessions_list"`, `args: { action: "json" }`


### P1 — Post-MVP


#### 3.5 Cron Job Manager (`/cron`)
- **Job list**: name, schedule, enabled/disabled, last run, next run
- **Toggle**: enable/disable jobs
- **Run history**: view last N executions and output
- **Add job**: form to create new cron entries


Data source: `POST /tools/invoke` with `tool: "cron"`, various actions


#### 3.6 Logs & Activity Feed (`/logs`)
- **Live tail**: auto-refreshing log viewer (poll every 5s)
- **Filter**: by level (info/warn/error), by keyword
- **Time range**: last hour / last day / custom


Data source: `POST /tools/invoke` with `tool: "gateway"` + logs action, or direct log tail RPC


#### 3.7 Browser Tabs Viewer (`/browser`)
- **Tab list**: URL, title, favicon for each open tab
- **Screenshot**: capture current tab screenshot
- **Quick actions**: open URL, close tab


Data source: `POST /tools/invoke` with `tool: "browser"`, `args: { action: "tabs" }`


#### 3.8 Quick Actions (`/actions` or sidebar widget)
One-click buttons:
- **Restart Gateway** — `tool: "gateway"` restart action
- **Backup to GitHub** — `tool: "exec"` with git push command
- **Run security audit** — `tool: "exec"` with `clawdbot security audit`
- **Clear sessions** — session management
- **Force model refresh** — reload model status


### P2 — Future


- **Cost tracking over time** (chart with daily/weekly spend)
- **Multi-agent view** (if multiple agents configured)
- **Node management** (paired devices, camera, screen)
- **Webhook/hook manager**
- **Config editor** (edit `clawdbot.json` with validation)
- **Mobile-optimized layout**


---


## 4. API Integration


### Primary: `/tools/invoke` (HTTP POST)


The dashboard uses the Gateway's tool invoke endpoint as its primary API. This is **always enabled** and respects Gateway auth + tool policy.


**Base URL**: `https://ai.btctx.us` (Cloudflare tunnel to localhost:18789)


**Pattern for all calls:**


```typescript
async function invokeGatewayTool(tool: string, args: Record<string, any> = {}) {
  const res = await fetch(`${GATEWAY_URL}/tools/invoke`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${GATEWAY_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ tool, args }),
  });
  if (!res.ok) throw new Error(`Gateway error: ${res.status}`);
  return res.json();
}
```


### Key tool → endpoint mappings


| Dashboard Feature | Tool | Args |
|---|---|---|
| Health/status | `gateway` | `{ action: "status" }` |
| Session list | `sessions_list` | `{ action: "json" }` |
| Session history | `sessions_history` | `{ sessionKey: "..." }` |
| Read file | `read` | `{ path: "memory/..." }` |
| Write file | `write` | `{ path: "...", content: "..." }` |
| Edit file | `edit` | `{ path: "...", oldText: "...", newText: "..." }` |
| Cron list | `cron` | `{ action: "list" }` |
| Cron toggle | `cron` | `{ action: "toggle", id: "..." }` |
| Browser tabs | `browser` | `{ action: "tabs" }` |
| Browser screenshot | `browser` | `{ action: "screenshot" }` |
| Exec command | `exec` | `{ command: "..." }` |
| Logs | `gateway` | `{ action: "logs" }` |


### Secondary: `/v1/responses` (Chat)


For an optional embedded chat widget, use the OpenResponses endpoint:


```
POST /v1/responses
{ "model": "clawdbot:main", "input": "...", "stream": true }
```


This requires `gateway.http.endpoints.responses.enabled: true` in config.


### CORS


The Gateway runs behind a Cloudflare tunnel (`ai.btctx.us`). Vercel-deployed frontend will make cross-origin requests. Options:
1. **Next.js API routes as proxy** (recommended) — all Gateway calls go through `/api/gateway/[...path]` route handlers, avoiding CORS entirely
2. Configure CORS headers on the Cloudflare tunnel (if supported)


**Recommended: Use Next.js API routes as a proxy.** This also keeps the Gateway token server-side.


---


## 5. Authentication


### Approach: Single-user token gate


Since this is a personal dashboard (one user: Rick), use a simple password/token gate:


```
DASHBOARD_PASSWORD=<secret>
```


#### Flow:
1. User visits dashboard → sees login page
2. Enters password → POST `/api/auth/login`
3. Server validates against `DASHBOARD_PASSWORD` env var
4. Sets an HTTP-only secure cookie (`clawd-session`) with a signed JWT (24h expiry)
5. Middleware checks cookie on all `/api/*` and page routes
6. Logout clears cookie


#### Implementation:
- `middleware.ts` — checks for valid session cookie, redirects to `/login` if missing
- `/api/auth/login` — validates password, sets cookie
- `/api/auth/logout` — clears cookie
- No database needed; stateless JWT


```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import { jwtVerify } from 'jose';


export async function middleware(request: Request) {
  const cookie = request.cookies.get('clawd-session');
  if (!cookie) return NextResponse.redirect('/login');
  try {
    await jwtVerify(cookie.value, new TextEncoder().encode(process.env.JWT_SECRET));
    return NextResponse.next();
  } catch {
    return NextResponse.redirect('/login');
  }
}


export const config = { matcher: ['/((?!login|_next|favicon).*)'] };
```


---


## 6. Deployment


### Vercel Configuration


**Environment Variables:**


| Variable | Description | Example |
|---|---|---|
| `GATEWAY_URL` | Clawdbot Gateway base URL | `https://ai.btctx.us` |
| `GATEWAY_TOKEN` | Gateway auth token | `your-gateway-token` |
| `DASHBOARD_PASSWORD` | Login password | `your-dashboard-password` |
| `JWT_SECRET` | Cookie signing secret (32+ chars) | `random-secret-string` |


**`vercel.json`** (optional):
```json
{
  "framework": "nextjs",
  "regions": ["iad1"]
}
```


### Deployment steps:
1. `npx create-next-app@latest clawd-dashboard --typescript --tailwind --app --src-dir`
2. `npx shadcn@latest init`
3. Set env vars in Vercel project settings
4. `vercel deploy` or connect GitHub repo for auto-deploy


### Domain:
- Default: `clawd-dashboard.vercel.app`
- Custom: `dash.btctx.us` (add CNAME in Cloudflare)


---


## 7. Phase Plan


### Phase 1: MVP (Weekend — Day 1-2)
- [x] Project setup (Next.js + Tailwind + shadcn/ui)
- [ ] Auth (login page + middleware + JWT cookie)
- [ ] API proxy route (`/api/gateway/invoke`)
- [ ] Status overview page (`/`)
- [ ] Memory browser (`/memory`) — read-only first, then edit
- [ ] TODO viewer (`/todos`) — interactive checkboxes
- [ ] Basic layout (sidebar nav, responsive)


### Phase 2: Operations (Week 2)
- [ ] Active sessions list (`/sessions`)
- [ ] Cron job manager (`/cron`)
- [ ] Quick action buttons (sidebar or `/actions`)
- [ ] Logs viewer (`/logs`) with polling


### Phase 3: Polish (Week 3+)
- [ ] Browser tabs viewer (`/browser`)
- [ ] Embedded chat widget (via `/v1/responses`)
- [ ] Dark/light theme toggle
- [ ] Mobile-responsive polish
- [ ] Cost tracking charts
- [ ] Keyboard shortcuts


---


## 8. Security Considerations


### Gateway exposure
- The Gateway is behind a Cloudflare tunnel (`ai.btctx.us`), **not** directly on the internet
- All Gateway calls use bearer token auth — token never exposed to the browser
- Next.js API routes act as a proxy, keeping `GATEWAY_TOKEN` server-side only


### Dashboard auth
- Password-protected with HTTP-only secure cookies (no localStorage tokens)
- JWT with expiry (24h) — auto-logout
- Rate-limit login attempts (consider `@upstash/ratelimit` or simple in-memory counter)


### Tool policy
- The `/tools/invoke` endpoint respects Gateway tool policy — the dashboard can only invoke tools the Gateway allows
- Consider creating a dedicated Gateway tool profile for dashboard access (read-heavy, limited exec)
- Avoid exposing unrestricted `exec` through the dashboard UI — whitelist specific commands


### Network
- Vercel → Cloudflare tunnel → localhost is the full path; no direct port exposure
- Cloudflare provides DDoS protection and TLS termination
- Consider Cloudflare Access as an additional auth layer (zero-trust)


### Data
- No sensitive data stored on Vercel — it's a stateless proxy
- Session cookies are HTTP-only, Secure, SameSite=Strict
- Memory file edits go through the Gateway's tool policy (not direct filesystem access)


### Recommendations
1. Use a strong, unique `DASHBOARD_PASSWORD` (not the Gateway token)
2. Keep `GATEWAY_TOKEN` and `JWT_SECRET` as Vercel encrypted env vars
3. Consider adding Cloudflare Access on `dash.btctx.us` for defense-in-depth
4. Audit Gateway tool policy to ensure dashboard can't escalate beyond intended scope
5. Add CSP headers in `next.config.js` to prevent XSS


---


## Appendix: File Structure


```
clawd-dashboard/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout with sidebar
│   │   ├── page.tsx                # Status overview (/)
│   │   ├── login/page.tsx          # Login form
│   │   ├── memory/page.tsx         # Memory browser
│   │   ├── todos/page.tsx          # TODO viewer
│   │   ├── sessions/page.tsx       # Sessions list
│   │   ├── cron/page.tsx           # Cron manager
│   │   ├── logs/page.tsx           # Log viewer
│   │   ├── browser/page.tsx        # Browser tabs
│   │   └── actions/page.tsx        # Quick actions
│   ├── api/
│   │   ├── auth/
│   │   │   ├── login/route.ts
│   │   │   └── logout/route.ts
│   │   └── gateway/
│   │       └── invoke/route.ts     # Proxy to Gateway /tools/invoke
│   ├── components/
│   │   ├── sidebar.tsx
│   │   ├── status-card.tsx
│   │   ├── file-tree.tsx
│   │   ├── markdown-editor.tsx
│   │   ├── todo-list.tsx
│   │   ├── session-table.tsx
│   │   ├── cron-table.tsx
│   │   └── log-viewer.tsx
│   ├── lib/
│   │   ├── gateway.ts              # Gateway API client (server-side)
│   │   ├── auth.ts                 # JWT helpers
│   │   └── utils.ts
│   └── middleware.ts               # Auth check
├── public/
├── tailwind.config.ts
├── next.config.ts
├── package.json
└── .env.local                      # Local dev env vars
```


---


## Appendix: Gateway API Quick Reference


| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/tools/invoke` | POST | Bearer token | Invoke any allowed tool (primary API) |
| `/v1/responses` | POST | Bearer token | OpenResponses chat (needs config enable) |
| `/v1/chat/completions` | POST | Bearer token | OpenAI-compat chat (needs config enable) |
| WebSocket `:18789` | WS | Token in connect frame | Full protocol (sessions, events, presence) |


All HTTP endpoints share the same port (18789) and auth config.


## Data Fetching Architecture (Updated 2026-01-31)


### Two Gateway Interfaces
1. **WebSocket RPC** — `health`, `status`, `sessions.list`, etc. Used by built-in control UI only.
2. **Agent tools via HTTP** — `memory_get`, `memory_search`, etc. Used by this dashboard via `/api/gateway/invoke`.


### Cache Pattern
Gateway-only data must be cached to files by cron, then read via `memory_get`:
```
cron (60s) → scripts/cache-*.sh → memory/cache/*.json
dashboard → useGateway("memory_get", { path: "memory/cache/X.json" }) → parse text wrapper → display
```


### Cache Scripts
| Script | Frequency | Output |
|--------|-----------|--------|
| cache-tasks.sh | 60s | memory/cache/tasks.json |
| cache-today.sh | 60s (30s offset) | memory/cache/today.json |
| cache-week.sh | 5min | memory/cache/week.json |
| cache-preaching.sh | 5min | memory/cache/preaching.json |
| cache-gateway-status.sh | 60s | memory/cache/gateway-status.json |
| cache-tree.sh | 60s | memory/cache/tree.json |
| cache-cron.sh | 60s | memory/cache/cron.json |


### Important: memory_get Response Format
`memory_get` returns `{ text: "<json string>", path: "..." }` — the `text` field is a **string** that must be `JSON.parse()`d on the client side. See `parseMemoryGetResult()` in `page.tsx`.


### Cron Environment Gotcha
Cron runs with minimal env. Scripts that call `clawdbot` or `systemctl --user` need:
- Explicit PATH including `~/.nvm/versions/node/v22.22.0/bin`
- `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$UID/bus` for systemd user services
