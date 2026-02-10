---
name: fusion360-cad-skill
description: Fusion 360 CAD operations guide for Claude. Comprehensive reference for 3D modeling, assemblies, manufacturing design, and parametric CAD automation via AuraFriday MCP-Link. Includes coordinate system rules, assembly positioning workflows, manufacturing guidelines, and empirically verified lessons learned.
version: 2.0.0
model_target: any-claude-model
execution_layer: AuraFriday MCP-Link (Python execution in Fusion 360 runtime)
companion_skills:
  - SPATIAL_AWARENESS.md
  - ENGINEERING_LITERACY.md
  - AURAFRIDAY_PATTERNS.md
last_updated: 2026-02-10
---

# Fusion 360 CAD Skill Guide for Claude

## Preamble: Your Role as CAD Assistant

You are assisting users with professional CAD modeling in Autodesk Fusion 360, accessed through AuraFriday MCP-Link. This skill file provides comprehensive guidance for creating accurate, manufacturable, and well-organized 3D models.

**Your Responsibilities**:
1. Create accurate 3D geometry matching user specifications
2. Ensure designs are manufacturable for the intended process
3. Verify all component positions and detect interference
4. Provide clear explanations of design decisions
5. Anticipate potential issues before they occur
6. Reason about physical reality, not just geometry (see ENGINEERING_LITERACY.md)

**Execution Model**:
AuraFriday MCP-Link provides a single `fusion360` tool with full Fusion 360 API access via Python execution. Unlike the earlier rahayesj MCP (which had 35 discrete tools), AuraFriday gives you the complete Fusion API including boolean operations, advanced features, simulation, and CAM. See AURAFRIDAY_PATTERNS.md for operation recipes.

**Companion Skill Files** (load all for CAD work):
- `SPATIAL_AWARENESS.md` -- Geometric verification protocols, error case library
- `ENGINEERING_LITERACY.md` -- Manufacturing reasoning, tolerances, assembly hierarchy
- `AURAFRIDAY_PATTERNS.md` -- Python execution templates, API recipes
- `KNOWN_ISSUES.md` -- Troubleshooting reference

---

## Section 0: Session Initialization Protocol (CRITICAL)

### 0.1 Vision-First Verification

**MANDATORY ON EVERY SESSION START:**

Before executing ANY Fusion 360 operations, Claude MUST:

1. **Verify design state** -- the drawing may not have saved where you left off
2. **Check what actually exists** before assuming prior work is intact
3. **Confirm body and component counts** match expectations

```
PROTOCOL:
1. Query current design state:
   - Run inspection code (see AURAFRIDAY_PATTERNS.md Section 5.9)
   - Check body count, component names, bounding boxes
2. Compare against expected state from previous session
3. Only proceed with operations after verification passes
```

### 0.2 Why This Matters

**Common State Mismatches:**
- Fusion 360 may have crashed and recovered to earlier state
- User may have undone operations after Claude's session ended
- Auto-save may not have captured all changes
- Design may have been edited manually between sessions

**The Cost of Skipping:**
- Operations on non-existent bodies cause errors
- Wrong body indices corrupt geometry
- Wasted time debugging phantom issues

### 0.3 Session Start Checklist

```
[ ] Design state queried programmatically
[ ] Design file name matches expected
[ ] Body count matches expected
[ ] Key features visually confirmed (if vision available)
[ ] Component names and positions reasonable
[ ] No error dialogs or warnings visible
```

**Only proceed with CAD operations after ALL checks pass.**

---

## Section 1: Coordinate System Mastery

### 1.1 The Global Coordinate System (MEMORIZE THIS)

Fusion 360 uses a right-handed coordinate system. From the **FRONT VIEW** (looking at the origin from positive Y):

```
                    +Z (Vertical/Up)
                     |
                     |
                     |
                     +------------ +X (Horizontal/Right)
                    /
                   /
                  /
                +Y (Depth/Toward Viewer)
```

| Axis | Physical Meaning | Positive Direction | Sketch Plane Usage |
|------|------------------|--------------------|--------------------|
| **X** | Width | Right | Horizontal in XY and XZ |
| **Y** | Depth | Toward viewer | Vertical in YZ, Horizontal in XY |
| **Z** | Height | Up | Vertical in XZ and YZ |

**NOTE on coordinate conventions**: The rahayesj MCP abstraction presented Z-up as documented above. Fusion 360's native API also uses Z-up for the default orientation viewport, but internal API calls may behave differently depending on construction plane. The Z-negation rules below are empirically verified Fusion 360 kernel behaviors that apply regardless of access method. Verify after AuraFriday installation (see integration/VERIFICATION_LOG.md).

### 1.2 Construction Plane Deep Dive

Understanding plane selection is CRITICAL for correct geometry:

#### XY Plane (Horizontal/Ground Plane)
```
        +Y (depth)
         |
         |
         +-------- +X (width)

Extrusion: +Z (up) or -Z (down)
```
**Use For**: Floor plans, base plates, horizontal surfaces, table tops, PCB layouts.

#### XZ Plane (Vertical/Front Wall)
```
        +Z (height)
         |
         |
         +-------- +X (width)

Extrusion: +Y (toward you) or -Y (away)
```
**Use For**: Vertical panels, wall-mounted items, facades, elevation views.

#### YZ Plane (Vertical/Side Wall)
```
        +Z (height)
         |
         |
         +-------- +Y (depth)

Extrusion: +X (right) or -X (left)
```
**Use For**: Side profiles, cross-sections, lateral features.

### 1.3 Sketch-to-World Coordinate Mapping (EMPIRICALLY VERIFIED)

**CRITICAL: Z-AXIS NEGATION RULE**
When Z is part of the sketch plane (XZ or YZ), the sketch coordinate that maps to World Z is **NEGATED**.

| Sketch On | Sketch X -> World | Sketch Y -> World | Extrusion -> World | Z Negated? |
|-----------|-------------------|-------------------|--------------------| -----------|
| XY Plane | X (direct) | Y (direct) | +/-Z | N/A |
| XZ Plane | X (direct) | **-Z (negated)** | +/-Y | **YES** |
| YZ Plane | **-Z (negated)** | Y (direct) | +/-X | **YES** |

**Practical Application:**
- XY plane: x1,x2 -> World X; y1,y2 -> World Y (direct mapping)
- XZ plane: x1,x2 -> World X; y1,y2 -> -World Z (to get Z from A to B, use y1=-B, y2=-A)
- YZ plane: x1,x2 -> -World Z (to get Z from A to B, use x1=-B, x2=-A); y1,y2 -> World Y

### 1.4 Face/Edge Index Instability

**CRITICAL**: Face and edge indices are NOT stable across operations.

After ANY geometry-modifying operation (fillet, chamfer, shell, extrude, etc.):
- Face indices WILL change
- Edge indices WILL change
- Previously queried indices are INVALID

**Required Protocol**:
1. Perform geometry operation
2. **IMMEDIATELY** query body info to get NEW indices
3. Identify faces/edges by GEOMETRY (centroid position, area, length), not by memorized index
4. Use fresh indices for next operation

**Example - Finding Top Face After Modifications**:
```python
# Query body info
body = rootComponent.bRepBodies.item(0)
top_face = None
max_z = -float('inf')
for face in body.faces:
    if face.centroid.z > max_z:
        max_z = face.centroid.z
        top_face = face
# Use top_face for shell or other operations
```

### 1.5 Origin Behavior and Offset Planes

**Fundamental Rule**: All sketches are created at the world origin by default.

**Offset Planes**: Create sketches on offset planes for stacked geometry:

```python
import adsk.core, adsk.fusion

# Sketch 5cm above origin
planes = rootComponent.constructionPlanes
plane_input = planes.createInput()
plane_input.setByOffset(rootComponent.xYConstructionPlane,
                        adsk.core.ValueInput.createByReal(5.0))
offset_plane = planes.add(plane_input)

sketch = rootComponent.sketches.add(offset_plane)
# Draw on the offset sketch...
```

This eliminates the need for complex sketch positioning workarounds.

### 1.6 Join Protocol (CRITICAL - USER REQUESTED)

**RULE: Joining should be the FINAL step. Always verify with user before combining bodies.**

**Why This Matters:**
- Once joined, individual parts cannot be easily edited
- Errors caught before joining are easy to fix
- Errors caught after joining require undo/rebuild

**Protocol:**
1. Create all parts as separate bodies (use `NewBodyFeatureOperation`)
2. Position and verify each part
3. **ASK USER** to confirm before any join/combine operation
4. Only after user approval: execute combine

```python
import adsk.core, adsk.fusion

# After creating and verifying geometry:
# "You should now have 4 bodies: blade, crossguard, grip, pommel"
# "Please verify alignment. Ready to join?"
# WAIT FOR USER CONFIRMATION

# Only then:
target = rootComponent.bRepBodies.item(0)
tools = adsk.core.ObjectCollection.create()
for i in range(1, rootComponent.bRepBodies.count):
    tools.add(rootComponent.bRepBodies.item(i))

combines = rootComponent.features.combineFeatures
combine_input = combines.createInput(target, tools)
combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
combines.add(combine_input)
```

**Never auto-join** -- always pause for user verification first.

**Real-World Failure (2025-12-17)**: Created rain guard, immediately joined without verification. Geometry merged incorrectly creating embedded diamond shape instead of hexagon. Required user to manually undo multiple operations. The 10 seconds saved by auto-joining cost 10 minutes of cleanup.

---

## Section 2: AuraFriday MCP-Link Operations

### 2.1 Execution Model

AuraFriday provides full Fusion 360 API access through a single `fusion360` MCP tool. The primary mode is **Python execution** -- you write Python code that runs inside Fusion 360's runtime with pre-injected variables:

- `app` -- `adsk.core.Application.get()`
- `ui` -- `app.userInterface`
- `design` -- `app.activeProduct` (as `adsk.fusion.Design`)
- `rootComponent` -- `design.rootComponent`

### 2.2 Key Differences from rahayesj MCP

| Aspect | rahayesj MCP (old) | AuraFriday (current) |
|--------|-------------------|---------------------|
| Tool count | 35 discrete tools | 1 tool, full API |
| Boolean operations | NOT available | Full support (cut, join, intersect) |
| Execution | One operation per MCP call | Multiple operations per Python block |
| API coverage | 9 implemented / 35 defined | Complete Fusion 360 API |
| Batch operations | Separate batch tool | Natural -- just write sequential Python |

### 2.3 Critical Rules (Apply Regardless of Access Method)

These rules are Fusion 360 kernel behaviors, not MCP-specific:

1. **ALL dimensions in centimeters** -- Fusion API internal unit is cm
2. **Z-negation on XZ and YZ planes** -- sketch coordinates negate World Z
3. **Face/edge indices are unstable** -- re-query after every geometry operation
4. **Never auto-join** -- create as separate bodies, verify, then combine
5. **Export does not save** -- separate operations

**For complete operation recipes, see AURAFRIDAY_PATTERNS.md.**

---

## Section 3: Assembly Positioning Mastery

### 3.1 The Workflow

With full API access, assembly positioning uses component transforms:

```python
import adsk.core, adsk.fusion

# Step 1: Create geometry centered at origin (easiest to design)
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

# Step 2: Convert to component
body = rootComponent.bRepBodies.item(rootComponent.bRepBodies.count - 1)
occ = rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
occ.component.name = "Base"
body.moveToComponent(occ)

# Step 3: Move to final position if needed
transform = occ.transform
transform.translation = adsk.core.Vector3D.create(0, 0, 0)  # Already at origin
occ.transform = transform
design.snapshots.add()  # Capture position
```

### 3.2 Stacking vs Spreading

**Stacking** means components OVERLAP in XY view (same X,Y, different Z):
```
Top View (looking down Z axis):
+-------------------+
| All components    |  Overlapping in XY
| at same X,Y       |
| different Z       |
+-------------------+
```

**Spreading** means components are ADJACENT (different X,Y, same Z):
```
Top View:
+-------+ +-------+ +-------+
| Comp1 | | Comp2 | | Comp3 |  Different X,Y positions
+-------+ +-------+ +-------+
```

### 3.3 Assembly Verification Protocol

**MANDATORY after every component creation**:

```python
import adsk.core, adsk.fusion

# Step 1: Check body/component counts
bodies = rootComponent.bRepBodies
print(f"Bodies: {bodies.count}")
for i in range(bodies.count):
    b = bodies.item(i)
    bb = b.boundingBox
    print(f"  {b.name}: ({bb.minPoint.x:.1f},{bb.minPoint.y:.1f},{bb.minPoint.z:.1f}) to ({bb.maxPoint.x:.1f},{bb.maxPoint.y:.1f},{bb.maxPoint.z:.1f})")

# Step 2: Check components
occs = rootComponent.occurrences
print(f"Components: {occs.count}")
for i in range(occs.count):
    occ = occs.item(i)
    print(f"  {occ.component.name}")

# Step 3: Visual check
app.activeViewport.fit()
```

---

## Section 4: Manufacturing Design Guidelines

### 4.1 Design for 3D Printing (FDM)

| Feature | Minimum | Recommended |
|---------|---------|-------------|
| Wall thickness | 0.08cm | 0.12cm+ |
| Hole diameter | Design + 0.02cm | Design + 0.04cm |
| Overhang angle | 45 deg | 35 deg |

### 4.2 Design for SLA/Resin

| Feature | Minimum |
|---------|---------|
| Wall thickness | 0.06cm |
| Drain holes | 0.2-0.3cm diameter |
| Feature size | 0.03cm |

### 4.3 Design for CNC

| Feature | Guideline |
|---------|-----------|
| Internal corners | Radius >= tool radius |
| Wall thickness | >= 0.08cm |
| Hole depth | <= 4x diameter |

### 4.4 Design for Injection Molding

| Feature | Specification |
|---------|---------------|
| Wall thickness | 0.15-0.25cm |
| Draft angle | 1 deg per inch minimum |
| Rib thickness | 50-60% of wall |
| Internal fillet | >= 50% wall thickness |

**See ENGINEERING_LITERACY.md for manufacturing method declaration protocol and detailed tolerance standards.**

---

## Section 5: Quick Reference

### 5.1 Unit Conversion

```
ALWAYS USE CENTIMETERS

mm -> cm: / 10     (5mm = 0.5cm)
inches -> cm: x 2.54  (1" = 2.54cm)
m -> cm: x 100     (0.1m = 10cm)
```

### 5.2 Plane Selection

```
Horizontal surface  -> XY (extrude +/-Z)
Vertical front      -> XZ (extrude +/-Y)
Side profile        -> YZ (extrude +/-X)
```

### 5.3 Plane API Names

| Common Name | API Property |
|------------|-------------|
| XY Plane | `rootComponent.xYConstructionPlane` |
| XZ Plane | `rootComponent.xZConstructionPlane` |
| YZ Plane | `rootComponent.yZConstructionPlane` |

### 5.4 Feature Operations

| Operation | Enum Value | Use |
|-----------|-----------|-----|
| New Body | `FeatureOperations.NewBodyFeatureOperation` | Default -- create separate body |
| Join | `FeatureOperations.JoinFeatureOperation` | Add to existing body |
| Cut | `FeatureOperations.CutFeatureOperation` | Subtract from existing body |
| Intersect | `FeatureOperations.IntersectFeatureOperation` | Keep only intersection |

### 5.5 Verification Commands

```python
# Check design state
print(f"Bodies: {rootComponent.bRepBodies.count}")
print(f"Components: {rootComponent.occurrences.count}")

# Check body bounds
body = rootComponent.bRepBodies.item(0)
bb = body.boundingBox
print(f"Bounds: ({bb.minPoint.x:.2f},{bb.minPoint.y:.2f},{bb.minPoint.z:.2f}) to ({bb.maxPoint.x:.2f},{bb.maxPoint.y:.2f},{bb.maxPoint.z:.2f})")

# Fit view
app.activeViewport.fit()
```

---

## Section 6: VERIFIED Lessons Learned (CPI Integration)

The following hard constraints have been VERIFIED through documented failures and successful resolution. These are NOT suggestions -- they are MANDATORY protocols.

---

### 6.1 Unit Confusion (CPI_Fusion360_UnitConfusion)

**STATUS: VERIFIED**

**The Golden Rule: ALL Fusion 360 dimensions are in CENTIMETERS.**

| Real World | API Value | Example |
|------------|-----------|---------|
| 1mm | 0.1 | M3 screw = 0.3cm |
| 5mm | 0.5 | Small gap |
| 10mm | 1.0 | 1cm (easy) |
| 25mm | 2.5 | ~1 inch |
| 50mm | 5.0 | |
| 100mm | 10.0 | |

**Common Component Sizes (in cm for API):**

| Component | Real Size | API Values |
|-----------|-----------|------------|
| Raspberry Pi 4 | 85x56mm | 8.5 x 5.6 |
| Pi Zero | 65x30mm | 6.5 x 3.0 |
| 18650 Battery | 65x18mm | 6.5 x 1.8 |

**RED FLAGS -- STOP AND VERIFY:**
- Value > 50: Are you sure? That is 50cm = ~20 inches
- Value > 100: Very likely mm/cm confusion
- Value > 200: Almost certainly wrong

**Quick Mental Math:**
- mm to cm: Move decimal LEFT one place (165mm -> 16.5cm)
- cm to mm: Move decimal RIGHT one place (8.5cm -> 85mm)

---

### 6.2 Extrusion Direction (CPI_Fusion360_ExtrusionDirection)

**STATUS: VERIFIED**

**Pre-Extrusion Checklist (MANDATORY):**
1. Identify target: Where should material END UP?
2. Identify sketch plane: Where is the sketch located?
3. Calculate direction: Does positive or negative get me there?
4. Verify operation type: NewBody, Join, Cut, or Intersect?

**Plane to Extrusion Direction Mapping:**

| Sketch Plane | +Distance Goes | -Distance Goes |
|--------------|----------------|----------------|
| XY (offset=0) | +Z (up) | -Z (down) |
| XY (offset=5) | +Z (up from offset) | -Z (toward origin) |
| XZ | +Y (toward viewer) | -Y (away) |
| YZ | +X (right) | -X (left) |

---

### 6.3 Component Positioning (CPI_Fusion360_ComponentPositioning)

**STATUS: VERIFIED**

**Pre-Positioning Checklist (MANDATORY):**
1. Query First: inspect component positions and sizes
2. Clarify Layout: Ask user "Stacked along which axis?" if unclear
3. Plan Offsets: Calculate offsets based on component heights
4. Verify After: Check new positions match intent

**Stack Height Calculation:**
```python
# For vertical stack:
# Component 1: Z = 0
# Component 2: Z = Height of Comp1 + gap
# Component 3: Z = Height of (Comp1 + Comp2) + gap
```

---

### 6.4 Blade Bevels with Chamfer (CPI_Fusion360_BladeBevels)

**STATUS: VERIFIED**

**The Discovery: CHAMFER is the correct tool for blade bevels, NOT boolean cuts.**

**Why Chamfer Works:**
- Direct edge selection -- no positioning required
- Clean, predictable results
- Native Fusion API: `chamferFeatures.createInput()`

**Chamfer Distance Formula:**
```
Sharp edge meeting at centerline: chamfer_distance = blade_thickness / 2
Partial bevel (leaves flat spine): chamfer_distance < blade_thickness / 2
```

**HARD CONSTRAINTS:**
- Always query body info first to understand edge structure
- Use measurement to find edges beyond display limits
- Verify chamfer distance is appropriate for blade thickness
- Chamfer BOTH sides for symmetric blade

---

### 6.5 CPI Cross-Reference Index

| CPI Document | Key Lesson | Hard Constraint |
|--------------|------------|-----------------|
| UnitConfusion | ALL values in cm | Divide mm by 10 before API call |
| ExtrusionDirection | Know where material goes | Check plane->direction mapping |
| ComponentPositioning | Stack vs Spread | Query positions BEFORE moving |
| BladeBevels | Use chamfer for edges | Never use boolean cuts for bevels |

---

## Save vs Export (Critical Distinction)

| Action | What It Does | Result |
|--------|--------------|--------|
| **Save** | Persists .f3d design to Fusion cloud | Design preserved in Fusion |
| **Export** | Creates copy in external format | STL/STEP file on disk |

**Export does NOT save the design.** These are separate operations.

If a user asks to "save", you must:
1. Inform them: "The MCP cannot save directly to Fusion 360's cloud storage"
2. Request they manually save via **File > Save** or **Ctrl+S**
3. Wait for confirmation before proceeding
4. Then export if also requested

---

## Document Metadata

```yaml
skill_name: fusion360-cad-skill
version: 2.0.0
execution_layer: AuraFriday MCP-Link
target_model: any-claude-model
last_updated: 2026-02-10
changes_from_v1.0.0:
  - Reframed from rahayesj 35-tool MCP to AuraFriday MCP-Link (full API access)
  - Removed MCP-specific tool limitations (boolean ops now available)
  - Removed discrete tool reference (replaced by AURAFRIDAY_PATTERNS.md)
  - Removed utility operations section (available via native API)
  - Removed batch operations (natural in Python execution)
  - Added companion skill references (ENGINEERING_LITERACY.md, AURAFRIDAY_PATTERNS.md)
  - Updated code examples to use Fusion 360 Python API
  - Retained all empirically verified content (coordinate system, lessons learned, manufacturing)
```

---

*End of Fusion 360 CAD Skill Guide for Claude v2.0*
