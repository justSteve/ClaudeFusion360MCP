# ClaudeFusion360MCP Implementation Plan

**Created:** 2026-02-10  
**Target Path:** `C:\myStuff\_infra\ClaudeFusion360MCP`  
**Repository:** https://github.com/justSteve/ClaudeFusion360MCP

---

## Executive Summary

The `justSteve/ClaudeFusion360MCP` fork contains **exceptional documentation** but an **incomplete implementation**. The MCP server defines 35 tools; the Fusion add-in implements only 9. However, the documentation alone—particularly the spatial reasoning protocols and empirically-verified error cases—represents significant value that can be leveraged with more mature implementations like AuraFriday MCP-Link.

**Recommended Path:** Hybrid approach—use AuraFriday MCP-Link for actual Fusion control while preserving and enhancing rahayesj's skill documentation as a "spatial reasoning companion."

---

## Current State Assessment

### What Exists

| Component | Status | Value |
|-----------|--------|-------|
| `docs/SKILL.md` (40KB) | ✅ Complete | High - Anthropic-spec skill file with comprehensive CAD guidance |
| `docs/SPATIAL_AWARENESS.md` (14KB) | ✅ Complete | High - Empirically-verified coordinate system rules |
| `docs/KNOWN_ISSUES.md` (7.5KB) | ✅ Complete | High - Battle-tested troubleshooting |
| `docs/TOOL_REFERENCE.md` (13KB) | ✅ Complete | Medium - Tool documentation |
| `mcp-server/fusion360_mcp_server.py` (23KB) | ✅ Complete | Medium - Well-designed API spec (35 tools) |
| `fusion-addin/FusionMCP.py` (6.6KB) | ⚠️ Incomplete | Low - Only 9 of 35 tools implemented |

### Implementation Gap Analysis

**MCP Server advertises 35 tools. Add-in implements 9:**

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

**Goal:** Position the repo as "Claude Spatial Reasoning Skills for Fusion 360 MCP"

**Effort:** Low (4-8 hours)  
**Risk:** None  
**Value:** Immediate usability with AuraFriday MCP-Link

#### Steps:

1. **Restructure Repository**
   ```
   ClaudeFusion360MCP/
   ├── README.md              # New: Focus on skill file usage
   ├── skills/
   │   ├── SKILL.md           # Renamed from docs/
   │   ├── SPATIAL_AWARENESS.md
   │   ├── KNOWN_ISSUES.md
   │   └── TOOL_REFERENCE.md
   ├── archive/               # Preserve original code
   │   ├── mcp-server/
   │   └── fusion-addin/
   └── integration/
       └── AURAFRIDAY_SETUP.md  # New: How to use with MCP-Link
   ```

2. **Update README.md**
   - Document that this is a skill/knowledge companion
   - Point to AuraFriday MCP-Link for actual implementation
   - Explain how to load skill files into Claude sessions

3. **Create Integration Guide**
   - Step-by-step for combining with AuraFriday
   - Claude Desktop config snippets
   - Verification workflow

4. **Clean Up Documentation**
   - Fix UTF-8 encoding issues (visible in SKILL.md)
   - Update version references
   - Add changelog

---

### Option B: Complete the Add-in Implementation

**Goal:** Make the rahayesj implementation fully functional

**Effort:** High (40-80 hours)  
**Risk:** Medium - May duplicate AuraFriday's work  
**Value:** Full control, no external dependencies

#### Phase 1: Foundation (8-12 hours)

1. **Set up development environment**
   - Install Fusion 360
   - Configure add-in debugging
   - Verify existing 9 tools work

2. **Implement missing sketch tools**
   ```python
   # In FusionMCP.py execute_command():
   elif tool_name == 'draw_line':
       return draw_line(design, rootComp, params)
   elif tool_name == 'draw_arc':
       return draw_arc(design, rootComp, params)
   elif tool_name == 'draw_polygon':
       return draw_polygon(design, rootComp, params)
   ```

3. **Implement handlers**
   ```python
   def draw_line(design, rootComp, params):
       activeEdit = design.activeEditObject
       if not activeEdit:
           return {"success": False, "error": "No active sketch"}
       sketch = activeEdit
       p1 = adsk.core.Point3D.create(params['x1'], params['y1'], 0)
       p2 = adsk.core.Point3D.create(params['x2'], params['y2'], 0)
       sketch.sketchCurves.sketchLines.addByTwoPoints(p1, p2)
       return {"success": True}
   ```

#### Phase 2: Features & Patterns (12-16 hours)

4. **Implement feature tools**
   - chamfer (similar to fillet)
   - shell (ShellFeatures API)
   - draft (DraftFeatures API)

5. **Implement pattern tools**
   - pattern_rectangular (RectangularPatternFeatures)
   - pattern_circular (CircularPatternFeatures)
   - mirror (MirrorFeatures)

#### Phase 3: Components & Joints (12-16 hours)

6. **Implement component tools**
   - create_component
   - list_components
   - move_component
   - rotate_component

7. **Implement joint tools**
   - create_revolute_joint
   - create_slider_joint

#### Phase 4: Inspection & Export (8-12 hours)

8. **Implement inspection tools**
   - get_body_info (enumerate edges/faces)
   - measure (BRepBody properties)

9. **Implement export tools**
   - export_stl
   - export_step
   - export_3mf

---

### Option C: Bridge to AuraFriday (Recommended Long-term)

**Goal:** Use AuraFriday's generic API with rahayesj's spatial reasoning skills

**Effort:** Medium (16-24 hours)  
**Risk:** Low - Leverages proven implementation  
**Value:** Best of both worlds

#### Architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Desktop                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Skills Loaded:                                       │    │
│  │   - rahayesj SKILL.md (spatial reasoning)           │    │
│  │   - rahayesj SPATIAL_AWARENESS.md (verification)    │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ AuraFriday MCP-Link Server                          │    │
│  │   - Generic Fusion API access                        │    │
│  │   - Python execution in Fusion runtime               │    │
│  │   - 10+ MCP tools                                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Autodesk Fusion 360                                  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

#### Steps:

1. **Install AuraFriday MCP-Link**
   - Download from Autodesk App Store
   - Install MCP-Link server from GitHub
   - Configure Claude Desktop

2. **Adapt Skill Files**
   - Update tool references to match AuraFriday's API
   - Create mapping document (rahayesj tool → AuraFriday equivalent)
   - Test spatial awareness rules with generic API

3. **Create Unified Claude Desktop Config**
   ```json
   {
     "mcpServers": {
       "fusion-mcp-link": {
         "command": "python",
         "args": ["path/to/aurafriday/mcp_link.py"]
       }
     },
     "skills": [
       "path/to/ClaudeFusion360MCP/skills/SKILL.md",
       "path/to/ClaudeFusion360MCP/skills/SPATIAL_AWARENESS.md"
     ]
   }
   ```

4. **Validate Integration**
   - Test coordinate system rules
   - Verify Z-negation handling
   - Confirm face/edge index protocols

---

## Recommended Implementation Sequence

### Week 1: Foundation

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Install Fusion 360 Personal Use | Working F360 installation |
| 2 | Install AuraFriday MCP-Link | Verified connection to F360 |
| 3 | Test basic operations via Claude | Cube creation confirmed |
| 4 | Fork cleanup (Option A steps 1-2) | Restructured repo |
| 5 | Integration guide draft | AURAFRIDAY_SETUP.md |

### Week 2: Validation

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Test Z-negation rules | Verified or updated documentation |
| 2 | Test face/edge index protocols | Confirmed instability handling |
| 3 | Test component positioning | Stack vs spread verified |
| 4 | Document any AuraFriday-specific quirks | AURAFRIDAY_NOTES.md |
| 5 | Create example workflows | examples/ directory |

### Week 3+ (Optional): Add-in Enhancement

If AuraFriday doesn't meet needs, begin Option B implementation starting with highest-value missing tools:

**Priority 1 (Most Useful):**
- export_stl (critical for 3D printing workflow)
- get_body_info (needed for intelligent operations)
- shell (enclosures are common)

**Priority 2 (Frequently Used):**
- draw_line, draw_arc (complex shapes)
- chamfer (manufacturing)
- pattern_rectangular (mounting holes)

**Priority 3 (Advanced):**
- Joints (mechanical assemblies)
- combine (boolean operations)

---

## Key Technical Notes

### Fusion 360 API Patterns (from rahayesj implementation)

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

### Critical Rules from Documentation

1. **ALL dimensions in centimeters** (mm ÷ 10)
2. **Z-negation on XZ/YZ planes** (Sketch Y/X → -World Z)
3. **Face/edge indices are unstable** - re-query after any modification
4. **Never auto-join** - always verify with user first
5. **Export ≠ Save** - they are separate operations

### File-Based IPC Protocol

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

## Files to Create

### 1. `/skills/AURAFRIDAY_SETUP.md`

```markdown
# Using These Skills with AuraFriday MCP-Link

## Prerequisites
1. Fusion 360 (Personal Use or higher)
2. AuraFriday MCP-Link from Autodesk App Store
3. MCP-Link server from https://aurafriday.com/downloads/
4. Claude Desktop

## Installation
[Step-by-step instructions]

## Loading Skills
[How to configure Claude Desktop to use these skill files]

## Verification
[Test commands to confirm everything works]
```

### 2. `/skills/TOOL_MAPPING.md`

```markdown
# Tool Mapping: rahayesj → AuraFriday

| rahayesj Tool | AuraFriday Equivalent | Notes |
|---------------|----------------------|-------|
| create_sketch | Generic API: Sketches.add() | Direct |
| extrude | Generic API: ExtrudeFeatures.add() | Direct |
| ... | ... | ... |
```

### 3. `/examples/phone-case.md`

```markdown
# Example: Phone Case with Camera Cutout

This example demonstrates:
- Shell creation
- Component positioning
- Z-negation handling
- Export to STL

[Full worked example with spatial verification]
```

---

## Success Criteria

### Minimum Viable Product (Option A)

- [ ] Repository restructured with clear purpose
- [ ] README explains skill-only usage
- [ ] AuraFriday integration guide complete
- [ ] At least one worked example validated

### Full Implementation (Option B or C)

- [ ] All 35 tools functional
- [ ] All spatial awareness rules verified
- [ ] Export to STL working for 3D print workflow
- [ ] Component assembly workflow validated
- [ ] Documentation updated with any corrections

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| AuraFriday API differs from rahayesj spec | Create mapping document, update skill files |
| Z-negation rules incorrect | Validate empirically with test geometry |
| Fusion API changes | Pin to known-working Fusion version |
| MCP protocol changes | Document tested versions |

---

## Appendix: Repository Links

- **Your Fork:** https://github.com/justSteve/ClaudeFusion360MCP
- **Original:** https://github.com/rahayesj/ClaudeFusion360MCP
- **AuraFriday MCP-Link:** https://apps.autodesk.com/FUSION/en/Detail/Index?id=7269770001970905100
- **AuraFriday GitHub:** https://github.com/AuraFriday/Fusion-360-MCP-Server
- **Joe Spencer's (reference):** https://github.com/Joe-Spencer/fusion-mcp-server

---

*End of Implementation Plan*
