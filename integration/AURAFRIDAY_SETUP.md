# AuraFriday MCP-Link Integration Guide

**Status:** DRAFT - sections marked [TODO] need verification after Phase 1 installation
**Created:** 2026-02-10
**Repository:** https://github.com/justSteve/ClaudeFusion360MCP
### Step 4: Clone This Repository

```bash
git clone https://github.com/justSteve/ClaudeFusion360MCP.git
cd ClaudeFusion360MCP
```

The skill files are in the `skills/` directory:
- `skills/SKILL.md` - Primary CAD skill (coordinate systems, assembly, manufacturing guidelines, verified lessons)
- `skills/SPATIAL_AWARENESS.md` - Geometric verification protocols (pre/post operation checklists, error case library)
- `skills/ENGINEERING_LITERACY.md` - Manufacturing reasoning, tolerances, model-vs-reality
- `skills/AURAFRIDAY_PATTERNS.md` - Python execution templates and API recipes
- `skills/KNOWN_ISSUES.md` - Battle-tested troubleshooting guide
- `skills/BUILD123D_BRIDGE.md` - Concept mapping from Build123d to Fusion 360

---

## Claude Desktop Configuration

### MCP Server Configuration

Add the AuraFriday MCP-Link server to your Claude Desktop MCP configuration.

**Config file location:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

[TODO: Confirm exact config path and server connection method after C1 research. AuraFriday MCP-Link Server uses SSE (Server-Sent Events) for its MCP connection, which may require a different config format than the stdio-based example below.]

```json
{
  "mcpServers": {
    "fusion-mcp-link": {
      "command": "path/to/mcp-link-server",
      "args": []
    }
  }
}
```

**Platform-specific paths:**

Windows (if installed via installer):
```json
{
  "mcpServers": {
    "fusion-mcp-link": {
      "command": "C:\\Program Files\\MCP-Link-Server\\mcp-link-server.exe",
      "args": []
    }
  }
}
```

**Note:** AuraFriday MCP-Link uses SSE transport (not stdio). Use this config format:



```json
{
  "mcpServers": {
    "fusion-mcp-link": {
      "url": "https://127-0-0-1.local.aurafriday.com:31173/sse"
    }
  }
}
```

**Confirmed SSE endpoint:** `https://127-0-0-1.local.aurafriday.com:31173/sse`

---

## Loading Skill Files

The spatial reasoning skill files from this repository provide Claude with critical CAD knowledge that AuraFriday's generic API does not include. These cover coordinate system rules, verification protocols, and empirically-discovered pitfalls.

### Option A: Claude Desktop - Project Instructions

In Claude Desktop, create a project and add the skill files as project knowledge:

1. Open Claude Desktop
2. Create a new Project (or open an existing one)
3. Click on "Project knowledge" (or similar)
4. Upload the following files from this repo's `skills/` directory:
   - `SKILL.md` (primary - coordinate systems, assembly, manufacturing)
   - `SPATIAL_AWARENESS.md` (companion - verification protocols, error case library)
   - `ENGINEERING_LITERACY.md` (manufacturing reasoning, tolerances)
   - `AURAFRIDAY_PATTERNS.md` (Python API recipes)
   - `KNOWN_ISSUES.md` (reference - troubleshooting)

**Alternative:** Paste the content of these files into the project's custom instructions.

### Option B: Claude Code - CLAUDE.md Reference

For Claude Code, reference the skill files in your project's `CLAUDE.md`:

```markdown
## Fusion 360 CAD Skills

When performing CAD operations via the fusion360 MCP tool, load and follow these skill files:

- Primary skill: `C:\myStuff\_infra\ClaudeFusion360MCP\skills\SKILL.md`
- Spatial verification: `C:\myStuff\_infra\ClaudeFusion360MCP\skills\SPATIAL_AWARENESS.md`
- Engineering literacy: `C:\myStuff\_infra\ClaudeFusion360MCP\skills\ENGINEERING_LITERACY.md`
- API recipes: `C:\myStuff\_infra\ClaudeFusion360MCP\skills\AURAFRIDAY_PATTERNS.md`
- Troubleshooting: `C:\myStuff\_infra\ClaudeFusion360MCP\skills\KNOWN_ISSUES.md`

Key rules:
- ALL dimensions in centimeters (mm / 10)
- Z-negation on XZ and YZ planes (Sketch Y -> -World Z on XZ; Sketch X -> -World Z on YZ)
- Face/edge indices are unstable after any geometry operation - always re-query
- Never auto-join bodies - always verify with user first
- State manufacturing method and model-vs-reality for every part
```

### Option C: Direct Prompt Loading

At the start of any Claude session involving Fusion 360 work, paste or reference:

```
Please load and follow the spatial reasoning rules from:
- SKILL.md (coordinate system, tool reference, unit conversion)
- SPATIAL_AWARENESS.md (verification protocols)

Critical rules:
1. ALL dimensions in centimeters
2. XZ plane: Sketch Y = -World Z (negated)
3. YZ plane: Sketch X = -World Z (negated)
4. Re-query face/edge indices after every geometry operation
5. Never auto-join - create as separate bodies, verify, then combine
```

---

## Coordinate System Reconciliation

**Important:** AuraFriday's built-in `best_practices.md` documents Fusion 360's native coordinate system where **Y is UP**. The skill files in this repository document the rahayesj MCP's coordinate convention where **Z is UP**.

This discrepancy exists because the two systems interface with Fusion 360 differently:

| Aspect | AuraFriday (Generic API) | Skill Files (rahayesj MCP) |
|--------|--------------------------|---------------------------|
| Vertical axis | Y is UP | Z is UP |
| Ground plane | XZ plane | XY plane |
| API style | Direct Fusion API calls | Abstracted tool functions |

**When using AuraFriday's generic API or Python execution**, the native Fusion 360 conventions apply (Y is UP). The skill files' Z-negation rules and plane mappings apply specifically to the rahayesj MCP tool abstractions (create_sketch, draw_rectangle, extrude, etc.).

[TODO: Test whether AuraFriday's generic API presents the same coordinate conventions as the Fusion 360 native API, or if there is an abstraction layer. This is the most important thing to verify in C4 validation.]

**Practical guidance until verified:**
- When using `fusion360.execute({"operation": "execute_python", ...})` with direct Fusion API calls, use Fusion's native coordinate system (Y is UP, XZ is the ground plane)
- The SPATIAL_AWARENESS.md verification protocols (pre/post operation checklists, bounding box interpretation) remain valuable regardless of coordinate convention
- The KNOWN_ISSUES.md troubleshooting (unit confusion, save vs export, index instability) applies universally

---

## Mapping rahayesj Tools to AuraFriday Operations

The skill files reference tool names like `create_sketch`, `extrude`, `fillet`, etc. These are rahayesj's abstracted MCP tools. With AuraFriday, you achieve the same results through either the Generic API or Python execution.

### Example: Creating a Sketch + Rectangle + Extrusion

**rahayesj tool style (from SKILL.md):**
```python
create_sketch(plane="XY")
draw_rectangle(x1=-5, y1=-5, x2=5, y2=5)
finish_sketch()
extrude(distance=2)
```

**AuraFriday Generic API equivalent:**
```json
// Step 1: Create sketch
{
  "api_path": "design.rootComponent.sketches.add",
  "args": ["design.rootComponent.xYConstructionPlane"],
  "store_as": "my_sketch"
}

// Step 2: Draw rectangle
{
  "api_path": "$my_sketch.sketchCurves.sketchLines.addTwoPointRectangle",
  "args": [
    {"type": "Point3D", "x": -5, "y": -5, "z": 0},
    {"type": "Point3D", "x": 5, "y": 5, "z": 0}
  ]
}

// Step 3: Get profile and extrude
{
  "api_path": "design.rootComponent.features.extrudeFeatures.addSimple",
  "args": ["$my_sketch.profiles.item(0)", {"type": "ValueInput", "value": 2.0}, 0]
}
```

**AuraFriday Python execution equivalent:**
```python
import adsk.core, adsk.fusion

sketch = rootComponent.sketches.add(rootComponent.xYConstructionPlane)
lines = sketch.sketchCurves.sketchLines
lines.addTwoPointRectangle(
    adsk.core.Point3D.create(-5, -5, 0),
    adsk.core.Point3D.create(5, 5, 0)
)
profile = sketch.profiles.item(0)
extrudes = rootComponent.features.extrudeFeatures
ext_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))
extrudes.add(ext_input)
print('Created 10x10x2 cm box')
```

[TODO: Verify the Generic API syntax above works correctly. The `addSimple` method and profile access patterns need testing with AuraFriday's specific object resolution.]

### Quick Reference: Plane Names

| rahayesj Plane | AuraFriday API Path |
|---------------|---------------------|
| "XY" | `design.rootComponent.xYConstructionPlane` |
| "XZ" | `design.rootComponent.xZConstructionPlane` |
| "YZ" | `design.rootComponent.yZConstructionPlane` |

[TODO: Confirm these property names in AuraFriday's context. They should match standard Fusion API.]

---

## Verification: End-to-End Test

Once everything is installed and configured, run through these tests to verify the integration is working.

### Test 1: Basic Connection

1. Open Fusion 360 (ensure MCP-Link add-in is running - check TEXT COMMANDS window)
2. Start the MCP-Link server
3. Open Claude Desktop with the MCP server configured
4. Ask Claude: "Can you check if the Fusion 360 connection is working?"
5. Claude should be able to call the `fusion360` tool and get a response

**Expected:** Claude confirms the connection and can query design info.

### Test 2: Create a Test Cube (2cm x 2cm x 2cm)

Ask Claude:
```
Create a simple test cube in Fusion 360: 2cm x 2cm x 2cm, centered at the origin.
```

**Verification steps:**
1. A new sketch should appear on a construction plane
2. A rectangle profile should be created
3. The profile should be extruded to create a solid body
4. In Fusion 360, use Inspect > Measure to verify the cube is 2cm on each side

### Test 3: Unit Conversion Check

Ask Claude:
```
Create a box that is 50mm wide, 30mm deep, and 20mm tall.
```

**Verification:** Claude should convert to centimeters before sending to Fusion:
- Width: 5.0 cm
- Depth: 3.0 cm
- Height: 2.0 cm

If the box comes out 10x too large, the unit conversion rule from SKILL.md was not applied.

### Test 4: Multi-Body Workflow

Ask Claude:
```
Create two separate boxes:
- Box A: 4cm x 4cm x 2cm at the origin
- Box B: 3cm x 3cm x 1cm, positioned on top of Box A
Do NOT join them - keep as separate bodies.
```

**Verification:**
1. Two separate bodies should appear in the design
2. Box B should sit on top of Box A (no overlap, no gap)
3. Claude should have verified positioning before finishing

### Test 5: Coordinate System Verification

[TODO: This test depends on which coordinate convention AuraFriday uses. If AuraFriday uses native Fusion (Y-up), the Z-negation rules from SKILL.md need to be adapted. Design this test after confirming the coordinate system.]

Ask Claude to create geometry on the XZ plane and verify it appears at the expected world coordinates. This tests whether the Z-negation rules from SPATIAL_AWARENESS.md apply in the AuraFriday context.

---

## Troubleshooting

### Connection Issues

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| Claude cannot see fusion360 tool | MCP-Link server not running | Start the MCP-Link server application |
| fusion360 tool returns errors | Add-in not running in Fusion 360 | Open Fusion 360, verify add-in via Shift+S |
| "Connection refused" | Server not on expected port | Check MCP-Link server logs for actual port |
| Timeout on commands | Fusion 360 busy or unresponsive | Check Fusion 360 is not in a dialog or processing |

### Geometry Issues

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| Parts 10x too large | mm/cm unit confusion | Divide all mm values by 10 (KNOWN_ISSUES.md #1) |
| Geometry in wrong location | Coordinate system mismatch | Verify which convention applies (see Coordinate Reconciliation above) |
| Face/edge operations fail | Stale indices | Re-query get_body_info() after every operation |
| Extrusion goes wrong direction | Incorrect sign on distance | Review extrusion direction table in SKILL.md Section 1.2 |
| Bodies merged unexpectedly | Auto-join behavior | Ensure extrude uses NewBodyFeatureOperation (operation type 0) |

### Skill File Issues

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| Claude ignores coordinate rules | Skill files not loaded | Verify files are in project instructions or CLAUDE.md |
| Z-negation applied incorrectly | Using AuraFriday direct API | Z-negation rules apply to rahayesj MCP abstractions; with direct Fusion API the native coordinate system applies |
| Claude uses wrong tool names | Mixing rahayesj and AuraFriday APIs | Clarify in prompt: use AuraFriday's generic API or Python execution |

### AuraFriday-Specific

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| Python execution fails | Syntax error or missing import | Check TEXT COMMANDS in Fusion for error details |
| store_as variable not found | Variable expired or wrong session | Re-create the stored object |
| Generic API path not resolving | Incorrect property name | Use get_api_documentation to look up correct path |

[TODO: Add more AuraFriday-specific troubleshooting after hands-on testing]

---

## What Skill Files Provide That AuraFriday Does Not

AuraFriday MCP-Link is excellent at providing raw API access to Fusion 360. These skill files complement it by providing:

1. **Coordinate system mastery** - Detailed plane-to-world mappings with verified Z-negation rules (SKILL.md Section 1)
2. **Pre/post operation verification protocols** - Checklists that prevent geometry placement errors (SPATIAL_AWARENESS.md Section 3)
3. **Error case library** - Documented failure cases with root cause analysis (SPATIAL_AWARENESS.md Section 4)
4. **Manufacturing design guidelines** - DFM rules for FDM, SLA, CNC, and injection molding (SKILL.md Section 4)
5. **Unit conversion enforcement** - Red flags and conversion tables to prevent mm/cm confusion (SKILL.md Section 6.1)
6. **Index instability awareness** - Protocol for handling face/edge index changes after geometry operations (SKILL.md Section 1.4.4)
7. **Join protocol** - Mandatory verification before combining bodies (SKILL.md Section 1.6)

---

## Next Steps

After completing the verification tests:

1. **Document any AuraFriday-specific quirks** encountered during testing
2. **Update coordinate system notes** based on actual AuraFriday behavior
3. **Create worked examples** combining AuraFriday's Python execution with spatial reasoning rules
4. **Build a tool mapping table** documenting equivalent AuraFriday calls for every rahayesj tool in TOOL_REFERENCE.md

---

## Reference Links

| Resource | URL |
|----------|-----|
| This Repository | https://github.com/justSteve/ClaudeFusion360MCP |
| AuraFriday MCP-Link (App Store) | https://apps.autodesk.com/FUSION/en/Detail/Index?id=7269770001970905100 |
| AuraFriday Fusion Add-in (GitHub) | https://github.com/AuraFriday/Fusion-360-MCP-Server |
| AuraFriday MCP-Link Server (Releases) | https://github.com/AuraFriday/mcp-link-server/releases/tag/latest |
| AuraFriday Support Email | ask@aurafriday.com |
| Original rahayesj Repository | https://github.com/rahayesj/ClaudeFusion360MCP |
| Autodesk Fusion API Docs | https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-7B5A90C8-E94C-48DA-B16B-430729B734DC |

---

*End of AuraFriday Integration Guide (DRAFT)*
