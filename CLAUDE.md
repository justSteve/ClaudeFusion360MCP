# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Skill library for Fusion 360 CAD agents. Provides spatial reasoning, coordinate system mastery, engineering literacy, and manufacturing awareness for AI-assisted CAD modeling via AuraFriday MCP-Link.

This is NOT an MCP server implementation. The original rahayesj MCP code is preserved in `archive/`. Actual Fusion 360 execution is handled by AuraFriday MCP-Link, which provides full Fusion 360 API access through a single MCP tool with Python execution.

## Architecture

```
Claude Desktop / Claude Code
  |
  +-- Skill files loaded (skills/*.md)
  |   Provides: coordinate rules, verification protocols,
  |             engineering literacy, manufacturing guidelines,
  |             AuraFriday operation patterns
  |
  +-- AuraFriday MCP-Link Server (MCP connection)
      |   Provides: fusion360 tool with full API access,
      |             Python execution in Fusion runtime
      |
      +-- Fusion 360 (via MCP-Link add-in)
          Provides: actual CAD modeling environment
```

## Key Files

| File | Purpose |
|------|---------|
| `skills/SKILL.md` | Primary CAD skill -- coordinate systems, assembly, manufacturing, verified lessons |
| `skills/SPATIAL_AWARENESS.md` | Geometric verification protocols, error case library |
| `skills/ENGINEERING_LITERACY.md` | Manufacturing reasoning, tolerances, model-vs-reality |
| `skills/AURAFRIDAY_PATTERNS.md` | Python execution templates, API recipes |
| `skills/KNOWN_ISSUES.md` | Troubleshooting reference |
| `skills/BUILD123D_BRIDGE.md` | Concept mapping from Build123d to Fusion 360 |
| `integration/AURAFRIDAY_SETUP.md` | Installation and configuration guide |
| `integration/VERIFICATION_LOG.md` | Coordinate system verification test results |

## Critical Domain Knowledge

### Units: ALL dimensions are in CENTIMETERS
- 50mm = 5.0 (not 50)
- 1 inch = 2.54
- Any value > 50 should raise suspicion (that's half a meter)

### XZ Plane Y-Axis Inversion (By Design)
When sketching on XZ plane, Sketch Y maps to World -Z. This is a Fusion 360 kernel behavior confirmed by Autodesk engineering. See SPATIAL_AWARENESS.md for details.

### Face/Edge Index Instability
Indices change after ANY geometry operation. Always re-query body info before referencing edges or faces.

### Join Protocol
Never auto-join bodies. Create as separate bodies, get user verification, then combine.

### Export != Save
They are separate operations. AuraFriday can export but cannot save to Fusion cloud.

## Repository Structure

```
ClaudeFusion360MCP/
+-- skills/                    # Skill files for CAD agents
|   +-- SKILL.md               # Primary skill (coordinate system, assembly, manufacturing)
|   +-- SPATIAL_AWARENESS.md   # Verification protocols
|   +-- ENGINEERING_LITERACY.md # Engineering reasoning
|   +-- AURAFRIDAY_PATTERNS.md # API recipes
|   +-- KNOWN_ISSUES.md        # Troubleshooting
|   +-- BUILD123D_BRIDGE.md    # Migration reference
+-- integration/               # AuraFriday setup and verification
|   +-- AURAFRIDAY_SETUP.md
|   +-- VERIFICATION_LOG.md
+-- archive/                   # Original rahayesj MCP code (preserved)
|   +-- mcp-server/
|   +-- fusion-addin/
|   +-- TOOL_REFERENCE_rahayesj.md
+-- docs/                      # Analysis and research
|   +-- CAD_AGENT_SKILL_GAP_ANALYSIS.md
+-- CLAUDE.md                  # This file
+-- README.md                  # Public-facing overview
```

## Repository Links

- **This Fork:** https://github.com/justSteve/ClaudeFusion360MCP
- **Original:** https://github.com/rahayesj/ClaudeFusion360MCP
- **AuraFriday MCP-Link:** https://apps.autodesk.com/FUSION/en/Detail/Index?id=7269770001970905100
- **AuraFriday GitHub:** https://github.com/AuraFriday/Fusion-360-MCP-Server

## Fusion 360 CAD Operations

When performing CAD operations via the fusion360 MCP tool, load and follow these skill files:

- **Primary skill:** `skills/SKILL.md` - coordinate systems, assembly, manufacturing
- **Spatial verification:** `skills/SPATIAL_AWARENESS.md` - pre/post operation checklists
- **Engineering literacy:** `skills/ENGINEERING_LITERACY.md` - tolerances, model-vs-reality
- **API recipes:** `skills/AURAFRIDAY_PATTERNS.md` - Python execution templates
- **Troubleshooting:** `skills/KNOWN_ISSUES.md` - error case library

**Mandatory rules:**

1. ALL dimensions in centimeters (divide mm by 10)
2. XZ plane: Sketch Y = World -Z (negated)
3. YZ plane: Sketch X = World -Z (negated)
4. Re-query face/edge indices after every geometry operation
5. Never auto-join - create as separate bodies, verify with user, then combine
6. State manufacturing method and model-vs-reality for every part

## Debugging

- Fusion 360 logs appear in the Text Commands palette (View > Text Commands)
- AuraFriday MCP-Link server logs on its configured port
- Check Fusion 360 add-in status via Shift+S in Fusion
