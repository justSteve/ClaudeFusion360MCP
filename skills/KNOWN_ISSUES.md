# Known Issues and Solutions

Common pitfalls when working with Fusion 360 via AuraFriday MCP-Link (or any API interface).

> **Note on Empirical Verification**: Issues #11 (XZ Plane Y-Axis Inversion) and #12
> (Auto-Join Protocol) are empirically verified against Autodesk engineering documentation
> and real CAD failures. These findings are implementation-agnostic -- they apply to any
> system that interfaces with Fusion 360's coordinate system.

---

## 1. Unit Confusion (Most Common!)

### Problem
All Fusion 360 API dimensions are in **centimeters**, but users often think in millimeters.

### Symptoms
- Parts are 10x too large or too small
- A "50mm box" becomes half a meter

### Solution
**Always convert:** `mm ÷ 10 = cm`

| User Says | You Enter |
|-----------|-----------|
| 50 mm | `5.0` |
| 100 mm | `10.0` |
| 25.4 mm (1 inch) | `2.54` |

**Red flag:** Any dimension > 50 is probably wrong (that's half a meter!).

---

## 2. Extrusion Direction

### Problem
Extrusions go the wrong way (into the part instead of out, or vice versa).

### The Rules
From the **front view** (looking at origin from +Y):

| Sketch Plane | Positive Extrusion | Negative Extrusion |
|--------------|-------------------|-------------------|
| XY plane | +Z (up) | -Z (down) |
| XZ plane | +Y (toward you) | -Y (away) |
| YZ plane | +X (right) | -X (left) |

### Solution
Always visualize which way the normal points before extruding.

---

## 3. Component Positioning

### Problem
Components appear at origin instead of intended position, or overlap.

### Key Concepts
- **Stacking** = Same X,Y, different Z (parts on top of each other)
- **Spreading** = Different X,Y (parts side by side)

### Solution
1. **Always query component positions** before positioning new ones
2. Use occurrence transforms after creation
3. Verify by querying bounding boxes after moves

---

## 4. Save vs Export

### Problem
User asks to "save" but Claude exports a STEP file. Design is lost when Fusion closes.

### Key Distinction
| Action | What Happens |
|--------|--------------|
| **Save** | Persists .f3d to Fusion cloud |
| **Export** | Creates external file (STL, STEP) |

**Export ≠ Save.** They are completely different operations.

### Solution
The MCP currently lacks a save command. When user says "save":
1. Inform them the MCP cannot save directly
2. Ask them to manually save (Ctrl+S or File → Save)
3. Wait for confirmation
4. Then export if requested

---

## 5. Blade/Edge Bevels

### Problem
Trying to create beveled edges on thin parts using boolean cuts (fails or creates bad geometry).

### Solution
Use **chamfer**, not boolean operations:
```python
edges = adsk.core.ObjectCollection.create()
# ... add target edges ...
chamfer_input = rootComponent.features.chamferFeatures.createInput2()
chamfer_input.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
    edges, adsk.core.ValueInput.createByReal(thickness / 2), True
)
rootComponent.features.chamferFeatures.add(chamfer_input)
```

For knife/blade edges, chamfer distance should be approximately half the material thickness.

---

## 6. Component Deletion

### Problem
Deleting a component causes index shifts, breaking subsequent operations.

### Solution
1. **Delete in reverse order** (highest index first)
2. Or delete by name, not index
3. Always re-query component list after any deletion

---

## 7. Fastener Holes

### Problem
Holes for fasteners are wrong size or position.

### Solution
Standard clearance holes (mm -> cm for Fusion API):

| Fastener | Clearance Hole | API Value (cm) |
|----------|---------------|----------------|
| M3 | 3.4 mm | `0.34` |
| M4 | 4.5 mm | `0.45` |
| M5 | 5.5 mm | `0.55` |
| #6 | 4.0 mm | `0.40` |
| 1/4" | 7.0 mm | `0.70` |

See ENGINEERING_LITERACY.md Section 4 for full ISO 273 tolerance tables.

---

## 8. Mating Parts / Interference

### Problem
Parts that should fit together either collide or have gaps.

### Solution
1. Design with **clearances** (0.2-0.5mm for 3D printing)
2. Query bounding boxes to verify distances
3. Check for interference before combining

---

## 9. Session State Mismatch

### Problem
Claude assumes prior work exists, but Fusion crashed/recovered to earlier state.

### Solution
**At session start, always:**
1. Query design state (body count, component list, bounding boxes)
2. Check body count matches expectations
3. Don't assume anything from previous sessions

---

## 10. Multiple Operations Per Call

### Problem (Historical)
The rahayesj MCP required separate MCP calls for each operation (~50ms roundtrip each), making multi-step modeling slow.

### Solution (AuraFriday)
With AuraFriday's Python execution, multiple operations run in a single block:
```python
import adsk.core, adsk.fusion

# All of this executes in one MCP call
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
print("Created box in single execution block")
```

No batching API needed -- just write sequential Python.

---

## 11. XZ Plane Y-Axis Inversion (CONFIRMED - BY DESIGN)

### Problem
When drawing geometry on the XZ plane with `center_y=0.3`, the resulting geometry appears at World Z=-0.3 instead of Z=0.3. The Y-axis is **inverted** relative to World Z.

### Root Cause (Confirmed by Autodesk Engineering)

This is **intentional behavior**, not a bug. The XZ plane has inverted Y because of two competing requirements:

**Requirement 1:** Positive extrusion on XZ plane must go toward +Y (into the model)
**Requirement 2:** All Fusion coordinate systems must be right-handed

To satisfy BOTH requirements, Sketch Y must map to -World Z.

```
XZ Plane Coordinate Mapping:
  Sketch X  →  World X   (unchanged)
  Sketch Y  →  World -Z  (INVERTED!)
  Extrude+  →  World +Y  (as expected)
```

### Plane Comparison

| Plane | Sketch X | Sketch Y | Normal (Extrude+) | Natural? |
|-------|----------|----------|-------------------|----------|
| XY | World +X | World +Y | World +Z | ✓ Yes |
| YZ | World +Y | World +Z | World +X | ✓ Yes |
| **XZ** | World +X | **World -Z** | World +Y | ✗ **INVERTED** |

### Solution: Negate Y for Z Positioning

```python
# To place geometry at World Z = target_z on XZ plane:
sketch_y = -target_z  # NEGATE!

# Example: Center at World Z = +0.3
# When creating sketch geometry on XZ plane, use center_y = -0.3

# Example: Center at World Z = -1.0
# When creating sketch geometry on XZ plane, use center_y = +1.0
```

### Quick Reference

| Target World Z | Use center_y = |
|----------------|----------------|
| +2.0 | -2.0 |
| +0.3 | -0.3 |
| 0 | 0 |
| -0.5 | +0.5 |
| -2.0 | +2.0 |

**Formula: `center_y = -target_world_z`**

### Alternative: Use XY Plane Instead

```python
# Avoid XZ plane entirely for Z-critical positioning:
# Create an offset construction plane at target_z
# Sketch on that offset plane -- XY has direct mapping, no inversion
# Extrude goes +Z (no negation needed)
```

### Source

Autodesk Engineering Director Jeff Strater confirmed this is by design:
- Thread: https://forums.autodesk.com/t5/fusion-support-forum/sketch-on-xz-plane-shows-z-positive-downwards-left-handed-coord/td-p/11675127
- Detailed explanation: https://forums.autodesk.com/t5/fusion-design-validate-document/why-is-my-sketch-text-appearing-upside-down/m-p/6645704

---

## 12. Auto-Join Without User Verification

### Problem
Claude automatically joins newly created bodies to the main model without asking for user verification first. If the geometry is wrong, it's now permanently merged and requires manual undo.

### Why This Happens
- Trying to be "efficient" by combining steps
- Overconfidence that geometry is correct
- Ignoring documented join protocol

### Impact
- Wrong geometry gets baked into model
- User must manually undo (Ctrl+Z) multiple operations
- Time wasted, trust eroded

### Solution: ALWAYS Verify Before Join

```python
# 1. Create geometry as separate body (NewBodyFeatureOperation)
# ... extrude code ...

# 2. Confirm body exists
print(f"Bodies: {rootComponent.bRepBodies.count}")

# 3. ASK USER - DO NOT SKIP THIS
# "Created [part] as separate body. Please verify position/shape."
# "Confirm to join?"

# 4. Wait for explicit "yes" before combining:
# target = rootComponent.bRepBodies.item(0)
# tools = adsk.core.ObjectCollection.create()
# tools.add(rootComponent.bRepBodies.item(1))
# combine_input = rootComponent.features.combineFeatures.createInput(target, tools)
# combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
# rootComponent.features.combineFeatures.add(combine_input)
```

### Hard Rule
**NEVER call combine without explicit user approval.** The 10 seconds saved by auto-joining can cost 10 minutes of cleanup when something is wrong.

---
*Document current as of v2.0 (AuraFriday MCP-Link)*
