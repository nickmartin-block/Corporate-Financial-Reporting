# SOP: Google Workspace MCP Setup

Connect Claude Code to Google Drive, Sheets, and Docs via MCP.

---

## Recommended Server
**`@presto-ai/google-workspace-mcp`**
- Covers: Drive, Sheets, Docs, Gmail, Calendar
- Requirements: Node.js installed

---

## Prerequisites

### 1. Install Node.js
Download from https://nodejs.org (LTS version recommended)

### 2. Create a Google Cloud Project
1. Go to https://console.cloud.google.com
2. Create a new project (e.g., "Claude MCP")
3. Enable these APIs:
   - Google Drive API
   - Google Sheets API
   - Google Docs API
4. Go to **APIs & Services > Credentials**
5. Create credentials → **OAuth 2.0 Client ID** → Desktop app
6. Download `credentials.json`
7. Store it somewhere safe (e.g., `~/.config/google-workspace-mcp/credentials.json`)

---

## Setup: Mac (do this after migration)

```bash
claude mcp add google-workspace \
  --transport stdio \
  -- npx -y @presto-ai/google-workspace-mcp
```

On first run, a browser window will open for Google OAuth consent.
Tokens are saved automatically after auth.

---

## Setup: Windows (limited support — prefer Mac)

```bash
claude mcp add google-workspace \
  --transport stdio \
  -- cmd /c npx -y @presto-ai/google-workspace-mcp
```

> Note: Windows requires the `cmd /c` wrapper for stdio MCP servers.
> MCP access is more reliable on Mac — complete setup after migration.

---

## Portability (Windows → Mac)

| Item | Portable? | Notes |
|------|-----------|-------|
| `credentials.json` | Yes | Copy to Mac; same Google Cloud project works |
| OAuth tokens | No | Re-run auth on Mac — tokens are machine-specific |
| MCP config in `.mcp.json` | Yes | Project-scoped config travels with this folder |

### To use project-scoped config (recommended for portability):
Instead of user-scoped config, add to `.mcp.json` in this project folder:
```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "npx",
      "args": ["-y", "@presto-ai/google-workspace-mcp"],
      "transport": "stdio"
    }
  }
}
```

---

## Verify Setup
Once connected, test with:
```
/mcp
```
You should see `google-workspace` listed as an active server.

---

## Status
- [ ] Google Cloud project created
- [ ] APIs enabled (Drive, Sheets, Docs)
- [ ] credentials.json downloaded
- [ ] MCP server added to Claude Code
- [ ] OAuth auth completed
- [ ] Test run successful
