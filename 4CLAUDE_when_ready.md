# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fusion 360 MCP Server enables Claude AI to control Autodesk Fusion 360 through the Model Context Protocol (MCP). The system uses file-based IPC between an MCP server and a Fusion 360 add-in.

## Architecture

```
Claude Desktop  <--MCP-->  fusion360_mcp_server.py  <--File System-->  FusionMCP.py (add-in)
                                                          |
                                              ~/fusion_mcp_comm/
                                              ├── command_*.json
                                              └── response_*.json
```

**Communication flow:**
1. MCP server writes commands to `~/fusion_mcp_comm/command_{timestamp}.json`
2. Fusion add-in polls for commands (100ms interval), executes via Fusion API
3. Add-in writes results to `~/fusion_mcp_comm/response_{timestamp}.json`
4. MCP server polls for response (50ms interval, 45s timeout)

## Key Files

| File | Purpose |
|------|---------|
| `mcp-server/fusion360_mcp_server.py` | MCP server with 40+ tools - run by Claude Desktop |
| `fusion-addin/FusionMCP.py` | Fusion 360 add-in that executes commands |
| `docs/SKILL.md` | Claude Project instructions for CAD operations |
| `docs/SPATIAL_AWARENESS.md` | Coordinate system and verification protocols |
| `docs/KNOWN_ISSUES.md` | Critical pitfalls including XZ plane inversion |

## Development Commands

```bash
# Install MCP framework
pip install mcp

# Test MCP server directly
python mcp-server/fusion360_mcp_server.py
```

The add-in is installed via Fusion 360 UI (Utilities → Add-Ins → Add) and runs inside Fusion 360's Python environment.

## Critical Domain Knowledge

### Units: ALL dimensions are in CENTIMETERS
- 50mm = 5.0 (not 50)
- 1 inch = 2.54
- Any value > 50 should raise suspicion (that's half a meter)

### XZ Plane Y-Axis Inversion (By Design)
When sketching on XZ plane, Sketch Y maps to World -Z:
```python
# To place geometry at World Z = +0.3:
draw_polygon(center_y=-0.3)  # NEGATE the Z value
```
This applies to both XZ and YZ planes. XY plane has direct mapping.

### Face/Edge Index Instability
Indices change after ANY geometry operation. Always call `get_body_info()` fresh before referencing edges or faces.

### Join Protocol
Never auto-join bodies. Create as separate bodies, get user verification, then combine.

## MCP Tool Categories

| Category | Tools |
|----------|-------|
| Sketch | `create_sketch`, `draw_rectangle`, `draw_circle`, `draw_line`, `draw_arc`, `draw_polygon`, `finish_sketch` |
| 3D | `extrude`, `revolve`, `fillet`, `chamfer`, `shell`, `draft` |
| Patterns | `pattern_rectangular`, `pattern_circular`, `mirror` |
| Components | `create_component`, `move_component`, `rotate_component`, `list_components`, `delete_component` |
| Boolean | `combine` (cut/join/intersect) |
| Inspection | `get_design_info`, `get_body_info`, `measure`, `check_interference` |
| Export | `export_stl`, `export_step`, `export_3mf`, `import_mesh` |
| Utility | `undo`, `delete_body`, `delete_sketch`, `batch` |

## Adding New Tools

1. Add tool function with `@mcp.tool()` decorator in `fusion360_mcp_server.py`
2. Add command handler in `execute_command()` switch in `FusionMCP.py`
3. Implement using Fusion 360 API (`adsk.fusion`, `adsk.core`)
4. Update TOOL_REFERENCE.md

## Debugging

- Add-in logs appear in Fusion 360's Text Commands palette
- MCP server errors surface in Claude Desktop
- Check `~/fusion_mcp_comm/` for orphaned command/response files
- "Timeout after 45s" = Fusion 360 or add-in not running
