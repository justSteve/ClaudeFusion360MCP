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
| `mcp-server/fusion360_mcp_server.py` | MCP server with 35 tools - run by Claude Desktop |
| `fusion-addin/FusionMCP.py` | Fusion 360 add-in that executes commands |
| `docs/SKILL.md` | Claude Project instructions for CAD operations |
| `docs/SPATIAL_AWARENESS.md` | Coordinate system and verification protocols |
| `docs/KNOWN_ISSUES.md` | Critical pitfalls including XZ plane inversion |

---

## Current State Assessment

This fork contains **exceptional documentation** but an **incomplete implementation**. The MCP server defines 35 tools; the Fusion add-in implements only 9.

### Implementation Gap

```
✅ IMPLEMENTED (9):
   create_sketch, draw_circle, draw_rectangle, extrude, revolve,
   fillet, finish_sketch, fit_view, get_design_info

❌ NOT IMPLEMENTED (26):
   Sketch: draw_line, draw_arc, draw_polygon
   Features: chamfer, shell, draft
   Patterns: pattern_rectangular, pattern_circular, mirror
   Components: create_component, list_components, delete_component,
               move_component, rotate_component, check_interference
   Joints: create_revolute_joint, create_slider_joint,
           set_joint_angle, set_joint_distance
   Inspection: get_body_info, measure
   Boolean: combine
   Utility: undo, delete_body, delete_sketch, batch
   Export: export_stl, export_step, export_3mf
   Import: import_mesh
```

---

## Implementation Options

### Option A: Documentation-Only Fork (Recommended Starting Point)

Position the repo as "Claude Spatial Reasoning Skills for Fusion 360 MCP" - use with AuraFriday MCP-Link for actual Fusion control.

**Effort:** Low (4-8 hours) | **Risk:** None

**Proposed Structure:**
```
ClaudeFusion360MCP/
├── README.md              # Focus on skill file usage
├── skills/
│   ├── SKILL.md
│   ├── SPATIAL_AWARENESS.md
│   ├── KNOWN_ISSUES.md
│   └── TOOL_REFERENCE.md
├── archive/               # Preserve original code
│   ├── mcp-server/
│   └── fusion-addin/
└── integration/
    └── AURAFRIDAY_SETUP.md
```

### Option B: Complete the Add-in Implementation

Make the implementation fully functional.

**Effort:** High (40-80 hours) | **Risk:** Medium

**Phase 1 (8-12 hrs):** Missing sketch tools (draw_line, draw_arc, draw_polygon)
**Phase 2 (12-16 hrs):** Features & patterns (chamfer, shell, draft, patterns, mirror)
**Phase 3 (12-16 hrs):** Components & joints
**Phase 4 (8-12 hrs):** Inspection & export

### Option C: Bridge to AuraFriday (Recommended Long-term)

Use AuraFriday's proven MCP-Link with this repo's spatial reasoning skills.

**Effort:** Medium (16-24 hours) | **Risk:** Low

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Desktop                            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Skills Loaded:                                           ││
│  │   - SKILL.md (spatial reasoning)                        ││
│  │   - SPATIAL_AWARENESS.md (verification)                 ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ AuraFriday MCP-Link Server                              ││
│  │   - Generic Fusion API access                            ││
│  │   - Python execution in Fusion runtime                   ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Autodesk Fusion 360                                      ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

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

### Export ≠ Save
They are separate operations. MCP can export but cannot save to Fusion cloud.

---

## Fusion 360 API Patterns

```python
# Get active design
app = adsk.core.Application.get()
design = app.activeProduct
rootComp = design.rootComponent

# Get active sketch (for drawing operations)
activeEdit = design.activeEditObject

# Create points
point = adsk.core.Point3D.create(x, y, z)

# Extrusion pattern
sketch = rootComp.sketches.item(rootComp.sketches.count - 1)
profile = sketch.profiles.item(sketch.profiles.count - 1)
extrudes = rootComp.features.extrudeFeatures
extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(distance))
extrude = extrudes.add(extInput)
```

---

## File-Based IPC Protocol

```
Communication Directory: ~/fusion_mcp_comm/

Command Format:
{
  "type": "tool",
  "name": "tool_name",
  "params": {...},
  "id": timestamp_ms
}

Response Format:
{
  "success": true/false,
  "error": "message if failed",
  ...tool-specific data
}

Timing:
- Polling interval: 50ms
- Timeout: 45 seconds
```

---

## Adding New Tools (Option B)

1. Add tool function with `@mcp.tool()` decorator in `fusion360_mcp_server.py`
2. Add command handler in `execute_command()` switch in `FusionMCP.py`
3. Implement using Fusion 360 API (`adsk.fusion`, `adsk.core`)
4. Update TOOL_REFERENCE.md

**Priority for implementation:**
- **Priority 1:** export_stl, get_body_info, shell
- **Priority 2:** draw_line, draw_arc, chamfer, pattern_rectangular
- **Priority 3:** Joints, combine

---

## Repository Links

- **This Fork:** https://github.com/justSteve/ClaudeFusion360MCP
- **Original:** https://github.com/rahayesj/ClaudeFusion360MCP
- **AuraFriday MCP-Link:** https://apps.autodesk.com/FUSION/en/Detail/Index?id=7269770001970905100
- **AuraFriday GitHub:** https://github.com/AuraFriday/Fusion-360-MCP-Server

---

## Debugging

- Add-in logs appear in Fusion 360's Text Commands palette
- MCP server errors surface in Claude Desktop
- Check `~/fusion_mcp_comm/` for orphaned command/response files
- "Timeout after 45s" = Fusion 360 or add-in not running
