# Fusion 360 MCP Tool Audit

**Audit Date**: 2026-02-10
**Task**: A5 (ClaudeFusion360MCP-vqt)
**MCP Server Version**: v7.2 Enhanced
**TOOL_REFERENCE.md Version**: v4.0

---

## Summary Counts

| Metric | Count |
|--------|-------|
| Tools defined in MCP server (`fusion360_mcp_server.py`) | 39 |
| Tools implemented in add-in (`FusionMCP.py`) | 9 |
| Tools documented in `TOOL_REFERENCE.md` | 38 |
| Full (server + add-in + doc) | 9 |
| Server Only (server + doc, no add-in) | 29 |
| Server Only, Missing Doc (server only, no add-in, no doc) | 1 |
| Doc Only (doc but not in any code) | 0 |
| Missing Doc (in code but not documented) | 1 |

**Note**: CLAUDE.md states "35 tools" in the MCP server. The actual count from `@mcp.tool()` decorators is 39. The difference is 4 tools added in v7.2 (undo, delete_body, delete_sketch) and the combine tool added in v7.1, which were apparently added after the CLAUDE.md count was written. The TOOL_REFERENCE.md does document the v7.2 utility tools (undo, delete_body, delete_sketch) but omits combine.

---

## Full Audit Table

| # | Tool Name | MCP Server | Add-in | TOOL_REFERENCE.md | Status |
|---|-----------|:----------:|:------:|:-----------------:|--------|
| 1 | `batch` | Yes | No | Yes | Server Only |
| 2 | `create_sketch` | Yes | Yes | Yes | Full |
| 3 | `finish_sketch` | Yes | Yes | Yes | Full |
| 4 | `draw_rectangle` | Yes | Yes | Yes | Full |
| 5 | `draw_circle` | Yes | Yes | Yes | Full |
| 6 | `draw_line` | Yes | No | Yes | Server Only |
| 7 | `draw_arc` | Yes | No | Yes | Server Only |
| 8 | `draw_polygon` | Yes | No | Yes | Server Only |
| 9 | `extrude` | Yes | Yes | Yes | Full |
| 10 | `revolve` | Yes | Yes | Yes | Full |
| 11 | `fillet` | Yes | Yes | Yes | Full |
| 12 | `chamfer` | Yes | No | Yes | Server Only |
| 13 | `shell` | Yes | No | Yes | Server Only |
| 14 | `draft` | Yes | No | Yes | Server Only |
| 15 | `pattern_rectangular` | Yes | No | Yes | Server Only |
| 16 | `pattern_circular` | Yes | No | Yes | Server Only |
| 17 | `mirror` | Yes | No | Yes | Server Only |
| 18 | `fit_view` | Yes | Yes | Yes | Full |
| 19 | `get_design_info` | Yes | Yes | Yes | Full |
| 20 | `get_body_info` | Yes | No | Yes | Server Only |
| 21 | `measure` | Yes | No | Yes | Server Only |
| 22 | `create_component` | Yes | No | Yes | Server Only |
| 23 | `list_components` | Yes | No | Yes | Server Only |
| 24 | `delete_component` | Yes | No | Yes | Server Only |
| 25 | `check_interference` | Yes | No | Yes | Server Only |
| 26 | `move_component` | Yes | No | Yes | Server Only |
| 27 | `rotate_component` | Yes | No | Yes | Server Only |
| 28 | `create_revolute_joint` | Yes | No | Yes | Server Only |
| 29 | `create_slider_joint` | Yes | No | Yes | Server Only |
| 30 | `set_joint_angle` | Yes | No | Yes | Server Only |
| 31 | `set_joint_distance` | Yes | No | Yes | Server Only |
| 32 | `combine` | Yes | No | No | Server Only, Missing Doc |
| 33 | `undo` | Yes | No | Yes | Server Only |
| 34 | `delete_body` | Yes | No | Yes | Server Only |
| 35 | `delete_sketch` | Yes | No | Yes | Server Only |
| 36 | `export_stl` | Yes | No | Yes | Server Only |
| 37 | `export_step` | Yes | No | Yes | Server Only |
| 38 | `export_3mf` | Yes | No | Yes | Server Only |
| 39 | `import_mesh` | Yes | No | Yes | Server Only |

---

## Implemented Tools (9) - Full Status

These tools are defined in the MCP server, implemented in the Fusion add-in, and documented in TOOL_REFERENCE.md.

| Tool | Add-in Function | Notes |
|------|-----------------|-------|
| `create_sketch` | `create_sketch()` | Add-in ignores `offset` parameter (server supports it) |
| `finish_sketch` | `finish_sketch()` | |
| `draw_rectangle` | `draw_rectangle()` | |
| `draw_circle` | `draw_circle()` | |
| `extrude` | `extrude_profile()` | Add-in ignores `profile_index` and `taper_angle` (server supports them) |
| `revolve` | `revolve_profile()` | |
| `fillet` | `add_fillet()` | Add-in ignores `edges` and `body_index` (server supports them); always fillets all edges on most recent body |
| `fit_view` | `fit_view()` | |
| `get_design_info` | `get_design_info()` | Add-in returns fewer fields than server doc implies (no component_count, no active_sketch_status) |

---

## Unimplemented Tools by Category (30)

### Sketch Geometry (3)

| Tool | Priority (CLAUDE.md) | Phase (Option B) |
|------|----------------------|------------------|
| `draw_line` | Priority 2 | Phase 1 |
| `draw_arc` | Priority 2 | Phase 1 |
| `draw_polygon` | -- | Phase 1 |

### Features & Patterns (6)

| Tool | Priority (CLAUDE.md) | Phase (Option B) |
|------|----------------------|------------------|
| `chamfer` | Priority 2 | Phase 2 |
| `shell` | Priority 1 | Phase 2 |
| `draft` | -- | Phase 2 |
| `pattern_rectangular` | Priority 2 | Phase 2 |
| `pattern_circular` | -- | Phase 2 |
| `mirror` | -- | Phase 2 |

### Components (6)

| Tool | Priority (CLAUDE.md) | Phase (Option B) |
|------|----------------------|------------------|
| `create_component` | -- | Phase 3 |
| `list_components` | -- | Phase 3 |
| `delete_component` | -- | Phase 3 |
| `check_interference` | -- | Phase 3 |
| `move_component` | -- | Phase 3 |
| `rotate_component` | -- | Phase 3 |

### Joints (4)

| Tool | Priority (CLAUDE.md) | Phase (Option B) |
|------|----------------------|------------------|
| `create_revolute_joint` | Priority 3 | Phase 3 |
| `create_slider_joint` | Priority 3 | Phase 3 |
| `set_joint_angle` | Priority 3 | Phase 3 |
| `set_joint_distance` | Priority 3 | Phase 3 |

### Inspection (2)

| Tool | Priority (CLAUDE.md) | Phase (Option B) |
|------|----------------------|------------------|
| `get_body_info` | Priority 1 | Phase 4 |
| `measure` | -- | Phase 4 |

### Boolean (1)

| Tool | Priority (CLAUDE.md) | Phase (Option B) |
|------|----------------------|------------------|
| `combine` | Priority 3 | Phase 3 |

### Utility (4)

| Tool | Priority (CLAUDE.md) | Phase (Option B) |
|------|----------------------|------------------|
| `batch` | -- | -- |
| `undo` | -- | -- |
| `delete_body` | -- | -- |
| `delete_sketch` | -- | -- |

### Export/Import (4)

| Tool | Priority (CLAUDE.md) | Phase (Option B) |
|------|----------------------|------------------|
| `export_stl` | Priority 1 | Phase 4 |
| `export_step` | -- | Phase 4 |
| `export_3mf` | -- | Phase 4 |
| `import_mesh` | -- | Phase 4 |

---

## Documentation Gaps

| Issue | Detail |
|-------|--------|
| `combine` not in TOOL_REFERENCE.md | Tool is defined in MCP server (v7.1) with full docstring but has no entry in TOOL_REFERENCE.md |
| CLAUDE.md tool count stale | States "35 tools" but MCP server has 39 `@mcp.tool()` decorators |
| Add-in parameter parity gaps | `create_sketch` ignores `offset`; `extrude` ignores `profile_index` and `taper_angle`; `fillet` ignores `edges` and `body_index` |
| `get_design_info` return value gap | TOOL_REFERENCE.md and MCP server docstring mention component_count and active sketch status, but add-in only returns design_name, body_count, sketch_count |

---

## Priority Implementation Order (from CLAUDE.md)

| Priority | Tools | Rationale |
|----------|-------|-----------|
| **1** | `export_stl`, `get_body_info`, `shell` | Core inspection and output capability |
| **2** | `draw_line`, `draw_arc`, `chamfer`, `pattern_rectangular` | Sketch completeness and common features |
| **3** | Joints (`create_revolute_joint`, `create_slider_joint`, `set_joint_angle`, `set_joint_distance`), `combine` | Assembly and boolean operations |
| *Unranked* | All remaining 20 tools | No explicit priority assigned in CLAUDE.md |

---

## Source Files

| Source | Path |
|--------|------|
| MCP Server | `mcp-server/fusion360_mcp_server.py` |
| Fusion Add-in | `fusion-addin/FusionMCP.py` |
| Tool Reference | `docs/TOOL_REFERENCE.md` |
| Project CLAUDE.md | `CLAUDE.md` |
