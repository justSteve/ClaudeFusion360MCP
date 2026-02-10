# AuraFriday MCP-Link for Fusion 360 -- API Research

Task: C1 (ClaudeFusion360MCP-vt6)
Research Date: 2026-02-10
Sources: GitHub repo, Autodesk App Store listing, source code analysis

---

## Overview

AuraFriday MCP-Link is a **two-component system** for AI control of Fusion 360:

1. **MCP-Link Server** (`mcp-link-server`) -- A standalone local MCP SSE server that runs on Windows/Mac/Linux. This is a separate downloadable binary, not part of the Fusion add-in. It provides the MCP protocol endpoint that AI clients (Claude Desktop, Cursor, Claude Code, etc.) connect to.

2. **Fusion 360 Add-in** (`Fusion-360-MCP-Server`) -- A Fusion 360 add-in written in Python that runs inside Fusion's runtime. It connects *to* the MCP-Link Server as a **reverse/remote tool**, registering itself as the `fusion360` tool.

**Key architectural insight**: AuraFriday does NOT expose 35 discrete MCP tools. It exposes **one MCP tool** called `fusion360` with a **generic API handler** that can execute *any* Fusion 360 API call. The AI sends JSON payloads describing the API path to traverse.

| Attribute | Value |
|-----------|-------|
| Add-in Version | 1.2.73 (as of 2026-01-28) |
| Server Version | 1.2.72 |
| Author | Christopher Nathan Drake (AuraFriday / Ocean Hydro) |
| License | **Proprietary** (source viewable, not open source) |
| Autodesk Store | [Link](https://apps.autodesk.com/FUSION/en/Detail/Index?id=7269770001970905100) |
| Add-in GitHub | [AuraFriday/Fusion-360-MCP-Server](https://github.com/AuraFriday/Fusion-360-MCP-Server) |
| Server GitHub | [AuraFriday/mcp-link-server](https://github.com/AuraFriday/mcp-link-server) |
| First Release | 2025-11-07 |
| Last Updated | 2026-01-28 |
| Price | Free |

---

## Tool Inventory

### The Single MCP Tool: `fusion360`

AuraFriday registers exactly **one tool** with the MCP server: `fusion360`. This tool accepts a JSON object and routes to different operation handlers based on the payload.

The tool description advertised to AI clients is extensive (~4KB) and documents the full API surface inline, so the AI understands what it can do without separate documentation.

### Operation Types

The `fusion360` tool dispatches on an `operation` field. If no operation is specified, it falls through to the **Generic API Call** handler.

#### 1. Generic API Calls (default -- no `operation` field)

Execute any Fusion 360 API method dynamically by path traversal.

```json
{
  "api_path": "rootComponent.sketches.add",
  "args": ["rootComponent.xYConstructionPlane"],
  "kwargs": {},
  "store_as": "my_sketch",
  "return_properties": ["name", "isVisible"]
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_path` | string | Yes | Dotted path to API method/property |
| `args` | array | No | Positional arguments (can contain object constructors, stored refs, API paths) |
| `kwargs` | object | No | Keyword arguments |
| `store_as` | string | No | Store result in session context as `$name` |
| `return_properties` | array | No | Which properties of the result to return |

**Path Shortcuts:**
- `app` --> `adsk.core.Application.get()`
- `ui` --> `app.userInterface`
- `design` --> `app.activeProduct`
- `rootComponent` --> `app.activeProduct.rootComponent`
- `$variable_name` --> Previously stored object
- `adsk.core.ClassName.method` --> Direct module access
- `adsk.fusion.ClassName.method` --> Direct module access

**Object Constructors (in args):**
```json
{"type": "Point3D", "x": 5, "y": 10, "z": 0}
{"type": "Vector3D", "x": 1, "y": 0, "z": 0}
{"type": "ValueInput", "value": 2.5}
{"type": "ValueInput", "expression": "2.5 cm"}
{"type": "ObjectCollection"}
```

**Special Commands:**
- `api_path: "get_pid"` -- Returns Fusion 360 process ID
- `api_path: "clear_context"` -- Clears all stored objects

#### 2. Python Execution (`operation: "execute_python"`)

Run arbitrary Python code with TRUE INLINE execution (`exec(compile(code), globals())`). Full, unsandboxed access to the entire Fusion runtime.

```json
{
  "operation": "execute_python",
  "code": "import adsk.core\nprint(f'Version: {app.version}')",
  "session_id": "my_session",
  "persistent": true
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | string | Yes | Python source code to execute |
| `session_id` | string | No | Session identifier (default: "default") |
| `persistent` | boolean | No | If true, variables persist across calls (default: true) |

**Pre-injected Variables in Python Context:**
- `app` -- `adsk.core.Application.get()`
- `ui` -- `app.userInterface`
- `design` -- Active design (if document open)
- `rootComponent` -- `design.rootComponent` (if document open)
- `fusion_context` -- Dict of objects stored via `store_as`
- `mcp` -- MCP bridge for calling other MCP tools

**Returns:** `stdout`, `stderr`, `return_value` (if `__return__` global set), `session_variables`, `success`

#### 3. MCP Tool Calling (`operation: "call_tool"`)

Call another tool registered on the MCP-Link server from within the Fusion context.

```json
{
  "operation": "call_tool",
  "tool_name": "sqlite",
  "arguments": {
    "input": {
      "sql": "SELECT * FROM designs",
      "tool_unlock_token": "29e63eb5"
    }
  }
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tool_name` | string | Yes | Name of the MCP tool to call |
| `arguments` | object | No | Arguments to pass to that tool |

#### 4. Script Management

Save/load/list/delete Python scripts for reuse.

| Operation | Required Params | Description |
|-----------|----------------|-------------|
| `save_script` | `filename`, `code` | Save Python script to disk |
| `load_script` | `filename` | Load script contents |
| `list_scripts` | (none) | List all saved scripts |
| `delete_script` | `filename` | Delete a saved script |

Scripts are stored in `<AuraFriday_root>/user_data/python_scripts/`.

#### 5. API Documentation (`operation: "get_api_documentation"`)

Live introspection of the Fusion 360 API using Python's `inspect` module.

```json
{
  "operation": "get_api_documentation",
  "search_term": "ExtrudeFeature",
  "category": "class_name",
  "max_results": 3
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search_term` | string | Yes | What to search for |
| `category` | string | No | `class_name`, `member_name`, `description`, or `all` |
| `max_results` | integer | No | Limit results (default: 3) |

Supports namespace prefixes: `"fusion.Sketch"`, `"core.Application"`.

#### 6. Online Documentation (`operation: "get_online_documentation"`)

Fetches rich docs from Autodesk's cloudhelp pages.

```json
{
  "operation": "get_online_documentation",
  "class_name": "ExtrudeFeatures",
  "member_name": "createInput"
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `class_name` | string | Yes | Fusion API class name |
| `member_name` | string | No | Specific method or property |

Returns: description, parameter tables, return types, code sample links.

#### 7. Best Practices (`operation: "get_best_practices"`)

Returns the built-in `best_practices.md` file content. No parameters.

---

### MCP-Link Server Built-in Tools

The MCP-Link Server (separate from the Fusion add-in) ships with these additional tools that the AI can use directly, or that the Fusion add-in can call via `call_tool`:

| Tool ID | Description | Access |
|---------|-------------|--------|
| `filesystem` | Read, write, manage files on local system | Free |
| `terminal` | Execute system commands and scripts | Free |
| `browser` | Automate Chrome/Edge (via extension bridge) | Free |
| `sqlite` | SQL queries with semantic search and vector embeddings | Free |
| `docker` | Sandbox tools in secure containers | Free |
| `cards` | Draw random cards for agent decision-making | Free |
| `tts` | Text-to-speech using system audio | Free |
| `stt` | Speech-to-text from microphone | Free |
| `whatsapp` | Message automation via WhatsApp | Licensed |
| `openrouter` | Proxy to 500+ AI models | Configured |
| `ai_chat` | Multi-agent chat coordination | Licensed |
| `network` | HTTP requests and API integrations | Free |
| `crypto` | Encryption and signing operations | Free |
| `remote` | Let external systems register as tools (how Fusion connects) | Free |
| `connector` | Add any 3rd party MCP tools | Free |
| `user` | Show HTML popups for forms and confirmations | Free |
| `python` | Execute code locally with MCP tool access | Free |
| `context7` | Pull live documentation for any library | Free |
| `huggingface` | Run AI models offline (local inference) | Free |
| `desktop` | Control Windows apps (click, type, read) | Free |

---

## Communication Architecture

### Protocol Stack

```
AI Client (Claude Desktop / Cursor / Claude Code)
    |
    | MCP SSE (Server-Sent Events)
    | HTTPS on port 31173
    | URL: https://127-0-0-1.local.aurafriday.com:31173/sse
    |
MCP-Link Server (standalone binary)
    |
    | SSE + JSON-RPC (reverse tool calls)
    | HTTPS with auth token
    |
Fusion 360 Add-in (runs inside Fusion's Python runtime)
    |
    | Direct API calls (adsk.core, adsk.fusion, adsk.cam)
    |
Fusion 360 Application
```

### Connection Flow (detailed)

1. **MCP-Link Server starts** -- Either via installer auto-start or manual launch. Listens on `https://127-0-0-1.local.aurafriday.com:31173/sse`.

2. **Fusion Add-in starts** -- When Fusion launches with add-in enabled:
   a. Finds native messaging manifest at `%LOCALAPPDATA%\AuraFriday\com.aurafriday.shim.json`
   b. Runs the native binary referenced in the manifest (Chrome Native Messaging protocol: 4-byte length prefix + JSON)
   c. Extracts `server_url` and `Authorization` header from the response
   d. Opens an SSE connection to the MCP-Link server
   e. Calls `tools/list` to verify the `remote` tool exists
   f. Calls `tools/call` on the `remote` tool with `operation: "register"` to register `fusion360`
   g. Enters a listening loop for reverse calls via the SSE stream

3. **AI sends a command** -- Claude Desktop (or other MCP client) calls `fusion360` tool via MCP:
   a. MCP-Link Server receives the tool call
   b. Server sends a `reverse` message over SSE to the Fusion add-in
   c. Add-in's `fusion_tool_handler` receives the call data
   d. If on a daemon thread, work is queued for main thread execution
   e. Main thread processes via Fusion's `CustomEvent` system
   f. Result is sent back via `tools/reply` JSON-RPC POST

### Key Difference from Our Repo

| Aspect | Our Repo (rahayesj fork) | AuraFriday MCP-Link |
|--------|--------------------------|---------------------|
| Communication | File-based IPC (`~/fusion_mcp_comm/`) | SSE + JSON-RPC over HTTPS |
| Server | Python FastMCP server (`fusion360_mcp_server.py`) | Standalone compiled binary |
| Tool Granularity | 35 discrete MCP tools | 1 generic tool with operation routing |
| Execution Model | Predefined command handlers | Generic API path traversal + arbitrary Python |
| MCP Protocol | Standard MCP (stdio transport) | MCP over SSE with reverse call pattern |
| Dependencies | None (file polling) | Native messaging manifest + MCP-Link Server binary |

### Thread Safety

AuraFriday uses a sophisticated thread-safety model:

- **Background SSE thread** receives reverse calls from the MCP server
- **Work queue** (`fusion_api_work_queue`) transfers work items to the main thread
- **Fusion CustomEvent** (`FusionAPIProcessorEvent`) triggers main-thread processing
- **Timer thread** fires the event every 50ms (fallback) or immediately when work arrives
- **Reentrant lock** prevents duplicate processing
- **Log buffer** collects messages from daemon threads, flushed on main thread

---

## Setup Process

### Prerequisites

1. **Fusion 360** (any recent version)
2. **MCP-Link Server binary** -- Download from [GitHub releases](https://github.com/AuraFriday/mcp-link-server/releases/tag/latest)
   - Windows: `AuraFriday-mcp-link-server-setup-v1.2.72-windows-x86_64.exe`
   - macOS Intel: `...-mac-intel.pkg`
   - macOS ARM: `...-mac-arm.pkg`
   - Linux: `...-linux-x86_64.run`
3. **AI client** that supports MCP (Claude Desktop, Cursor, Claude Code, etc.)

### Installation Steps

1. **Install MCP-Link Server** -- Run the installer. It auto-starts and runs on boot. Server endpoint: `https://127-0-0-1.local.aurafriday.com:31173/sse`

2. **Install the Fusion Add-in** -- Either:
   - **App Store**: Install from [Autodesk App Store](https://apps.autodesk.com/FUSION/en/Detail/Index?id=7269770001970905100) (174 KB download)
   - **Manual**: Clone the GitHub repo, then in Fusion: `Shift+S` --> Add-Ins tab --> green `+` --> navigate to cloned folder --> Run

3. **Configure AI Client** -- Point your MCP client at the SSE endpoint. The MCP-Link Server auto-configures most popular clients (Cursor, Roo Code, Windsurf, Claude Code).

4. **Verify** -- Check Fusion's TEXT COMMANDS window for connection logs. The add-in auto-connects on startup (`MCP_AUTO_CONNECT = True` in `config.py`).

### Claude Desktop Configuration

The MCP-Link Server handles configuration, but the connection would be:
```json
{
  "mcpServers": {
    "aurafriday": {
      "url": "https://127-0-0-1.local.aurafriday.com:31173/sse",
      "headers": {
        "Authorization": "Bearer <auto-generated-token>"
      }
    }
  }
}
```

The auth token is auto-generated by the MCP-Link Server installer and discovered by the add-in via native messaging.

---

## Python Script Execution

**Yes, AuraFriday fully supports Python script execution inside the Fusion runtime.**

This is one of its most powerful features. The `execute_python` operation uses `exec(compile(code, "<ai-code>", "exec"), globals())` -- true inline execution in the add-in's global scope.

### What This Means

- Full access to `adsk.core`, `adsk.fusion`, `adsk.cam`
- Access to ALL loaded add-ins (via `sys.modules`)
- File system access
- Network access
- System command execution
- Database access (via MCP bridge to SQLite tool)
- Browser automation (via MCP bridge)
- No sandboxing whatsoever

### Security Implications

The code explicitly states: "Python execution has FULL system access - use responsibly!" There is no sandboxing, no permission model, no approval flow for Python execution. Any code the AI generates runs with full privileges.

---

## Limitations

### Documented Limitations

1. **Enum values must be passed as integers** (e.g., `0` for `NewBodyFeatureOperation`), not symbolic names
2. **Some complex objects need specific construction patterns** -- not all Fusion API types have a simple `{"type": "X", ...}` constructor
3. **Context is lost when add-in reloads** -- session isolation by design
4. **Python execution has full system access** -- security depends entirely on trusting the AI
5. **McMaster-Carr integration opens interactive dialog** -- requires manual user selection

### Implicit Limitations (from source code analysis)

6. **Proprietary license** -- Cannot fork, modify, redistribute, or create derivative works. Source is "viewable" only.
7. **Depends on MCP-Link Server binary** -- Closed-source compiled binary that must be running
8. **Single-tool MCP surface** -- AI must construct JSON payloads manually; no discrete tool schema for individual CAD operations
9. **No offline MCP operation** -- Requires the MCP-Link Server to be running locally (though Fusion operations themselves are local)
10. **Auto-update system** -- The add-in checks for and applies updates automatically with RSA signature verification. Updates are downloaded from AuraFriday CDN.
11. **Native messaging dependency** -- Uses Chrome Native Messaging protocol for server discovery; requires the manifest to be installed
12. **No explicit unit handling** -- The generic API handler passes values through as-is; the AI must know that Fusion uses centimeters

---

## Comparison Notes (vs Our Repo's 35-Tool Definition)

### Architectural Philosophy

| Aspect | Our Repo | AuraFriday |
|--------|----------|------------|
| **Approach** | Curated tool set with explicit schemas | Generic API gateway + Python execution |
| **AI Guidance** | Tool names/params guide the AI | Long tool description + best practices doc |
| **Safety** | Implicit (each tool is scoped) | None (full API + system access) |
| **Discoverability** | AI sees 35 named tools with descriptions | AI sees 1 tool with a 4KB description blob |
| **Error Handling** | Per-tool error messages | Generic traceback with contextual hints |

### Feature Coverage Comparison

| Capability | Our Repo (35 tools) | AuraFriday (generic) |
|-----------|---------------------|----------------------|
| Create sketch | `create_sketch` tool | `api_path: "rootComponent.sketches.add"` |
| Draw shapes | `draw_circle`, `draw_rectangle`, `draw_line`, `draw_arc`, `draw_polygon` | Via api_path or `execute_python` |
| Extrude | `extrude` tool with taper_angle | Via api_path or Python |
| Revolve | `revolve` tool | Via api_path or Python |
| Fillet/Chamfer | `fillet`, `chamfer` with edge selection | Via api_path or Python |
| Shell | `shell` tool | Via api_path or Python |
| Draft | `draft` tool | Via api_path or Python |
| Patterns | `pattern_rectangular`, `pattern_circular` | Via api_path or Python |
| Mirror | `mirror` tool | Via api_path or Python |
| Components | `create_component`, `list_components`, `delete_component`, `move_component`, `rotate_component` | Via api_path or Python |
| Joints | `create_revolute_joint`, `create_slider_joint`, `set_joint_angle`, `set_joint_distance` | Via api_path or Python |
| Boolean | `combine` tool | Via api_path or Python |
| Inspection | `get_body_info`, `measure` | Via api_path or Python |
| Export | `export_stl`, `export_step`, `export_3mf` | Via api_path or Python |
| Import | `import_mesh` | Via api_path or Python |
| Undo | `undo` tool | Via `app.executeTextCommand` |
| Batch | `batch` tool | N/A (single-call architecture) |
| Arbitrary Python | Not supported | `execute_python` operation |
| API Documentation | Not supported | `get_api_documentation`, `get_online_documentation` |
| Cross-tool calls | Not supported | `call_tool` operation (SQLite, browser, etc.) |
| Script management | Not supported | `save_script`, `load_script`, etc. |
| CAM/Manufacturing | Not supported | Full `adsk.cam` via Python |
| Electronics/PCB | Not supported | Full electronics workspace via Python |

### Strengths of Our Repo vs AuraFriday

1. **Discrete tool schemas** -- Each of our 35 tools has explicit parameter names, types, and descriptions. This gives the AI much stronger guidance about what parameters to use and what values are valid. AuraFriday's generic approach requires the AI to know/guess the Fusion API structure.

2. **Spatial reasoning documentation** -- Our `SKILL.md`, `SPATIAL_AWARENESS.md`, and `KNOWN_ISSUES.md` provide CAD-specific spatial reasoning guidance that AuraFriday's `best_practices.md` partially covers but not as deeply (e.g., our XZ plane Y-axis inversion documentation, join protocol, face/edge index instability warnings).

3. **No proprietary dependencies** -- Our approach uses file-based IPC with no external binary dependencies. AuraFriday requires their closed-source MCP-Link Server binary.

4. **Simpler mental model** -- An AI calling `draw_circle(center_x=0, center_y=0, radius=2)` is much more intuitive than constructing a JSON payload to navigate the Fusion API graph.

5. **Batch operations** -- Our `batch` tool allows multiple commands in a single MCP call, reducing round-trips.

### Strengths of AuraFriday vs Our Repo

1. **100% API coverage** -- AuraFriday can execute literally any Fusion API call without adding new tool definitions. Our repo requires implementing each handler in the add-in.

2. **Python execution** -- Arbitrary Python in the Fusion runtime enables complex workflows that are impossible with discrete tools.

3. **Production-ready** -- Thread-safe architecture, auto-reconnect, auto-updates, centralized logging.

4. **Cross-tool ecosystem** -- SQLite, browser automation, user popups, AI model access all available from within Fusion context.

5. **API documentation built in** -- The AI can introspect the Fusion API or fetch Autodesk's official docs during operation.

6. **Context/session management** -- Objects can be stored and referenced across calls with `$variable` syntax.

### Integration Opportunity (Option C)

The ideal integration would combine:
- **Our spatial reasoning skill files** (SKILL.md, SPATIAL_AWARENESS.md, KNOWN_ISSUES.md) loaded into Claude's context
- **AuraFriday's MCP-Link** as the execution backend

This gives the AI:
- Deep CAD domain knowledge from our docs (coordinate systems, verification protocols, known pitfalls)
- Unlimited Fusion API access from AuraFriday's generic handler + Python execution
- The broader MCP-Link tool ecosystem (SQLite, browser, etc.)

The only requirement: Claude Desktop needs AuraFriday's MCP-Link Server running, and our skill files loaded as project context.

---

## Version History and Update Frequency

| Date | Version | Notable Changes |
|------|---------|-----------------|
| 2025-11-07 | 1.0.0 | Initial release on Autodesk App Store |
| 2025-11 | ~1.1.x | Thread-safe architecture, CustomEvent system |
| 2025-11 | ~1.1.x | Python execution + MCP tool integration |
| 2026-01-28 | 1.2.73 | Enhanced Python integration, ValueInput support, triple documentation sources, auto-updates |

The project shows active development with 13 commits on the add-in repo and 16 on the server repo. The author (Christopher Drake) appears to be the sole developer, maintaining both components.

---

## Key Source Files Reference

| File | Purpose | Size |
|------|---------|------|
| `MCP-Link.py` | Static loader stub (never auto-updated). Entry point for Fusion. | Small |
| `mcp_main.py` | Main add-in logic. Loaded after update check. | Small |
| `mcp_integration.py` | Core MCP infrastructure: connection, tool handler, Python execution, all operation routing | ~700 lines |
| `config.py` | Configuration flags (DEBUG, MCP_AUTO_CONNECT, tool name) | Small |
| `lib/mcp_client.py` | MCP client: SSE connection, native messaging discovery, JSON-RPC, reverse calls | ~600 lines |
| `lib/mcp_bridge.py` | Bridge for Python code to call other MCP tools via `mcp.call()` | ~80 lines |
| `lib/update_loader.py` | Auto-update system with RSA signature verification | ~300 lines |
| `lib/signature_verify.py` | RSA signature verification | ~200 lines |
| `best_practices.md` | Fusion 360 design best practices (returned by `get_best_practices`) | ~150 lines |
