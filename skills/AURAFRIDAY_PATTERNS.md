---
name: aurafriday-patterns
description: Operation patterns and recipes for Fusion 360 via AuraFriday MCP-Link. Replaces the 35-tool rahayesj MCP reference with Python execution templates using Fusion 360's native API.
version: 1.0.0
model_target: any-claude-model
companion_skills:
  - SKILL.md
  - SPATIAL_AWARENESS.md
  - ENGINEERING_LITERACY.md
last_updated: 2026-02-10
---

# AuraFriday Patterns: Fusion 360 MCP-Link Operation Reference

Replaces `TOOL_REFERENCE.md` (35 discrete rahayesj MCP tools). AuraFriday MCP-Link
exposes a single `fusion360` MCP tool backed by Python execution inside the Fusion 360
runtime. Every former tool call is now a Python code block sent through one interface.

---

## 1. The AuraFriday MCP-Link Model

AuraFriday exposes **one** MCP tool: `fusion360` with three operation modes:

| Mode | Purpose | Use When |
|------|---------|----------|
| `execute_python` | Run Python in Fusion 360 runtime | All modeling operations (primary mode) |
| `generic_api` | Simple property reads | Quick queries (document name, units) |
| `get_api_documentation` | Look up API classes/methods | Discovering unfamiliar API surfaces |

`execute_python` is the workhorse -- full Fusion 360 API access, no artificial
restrictions. The rahayesj MCP implemented 9 of 35 declared tools; AuraFriday
gives access to the entire API.

### Pre-Injected Variables

Available in scope automatically. Do not re-declare.

| Variable | Type | Description |
|----------|------|-------------|
| `app` | `adsk.core.Application` | Running Fusion 360 instance |
| `ui` | `adsk.core.UserInterface` | UI access (dialogs, palettes) |
| `design` | `adsk.fusion.Design` | Active design |
| `rootComponent` | `adsk.fusion.Component` | Root component of active design |

**Results:** Print statements are the return channel. Always print meaningful output.

**Units:** All lengths in **centimeters**. 50mm = `5.0`, 1 inch = `2.54`. Values > 50 are suspect.

**Efficiency:** Unlike rahayesj (one MCP roundtrip per tool), AuraFriday allows
multiple operations in a single Python block. Sketch, draw, and extrude in one call.

---

## 2. Python Execution Template

Standard skeleton for every `execute_python` call:

```python
import adsk.core, adsk.fusion, traceback
try:
    # --- operation code (uses pre-injected app, ui, design, rootComponent) ---
    print("Success: <describe result>")
except:
    print(f"Error: {traceback.format_exc()}")
```

Always wrap in try/except. Unhandled Fusion exceptions produce opaque errors.
All recipes below use this pattern -- the try/except is shown once per recipe.

---

## 3. Construction Planes and Coordinate System

| Common Name | API Property | Normal |
|-------------|-------------|--------|
| XY Plane (ground) | `rootComponent.xYConstructionPlane` | Z |
| XZ Plane (front) | `rootComponent.xZConstructionPlane` | Y |
| YZ Plane (side) | `rootComponent.yZConstructionPlane` | X |

| Axis | API Property |
|------|-------------|
| X | `rootComponent.xConstructionAxis` |
| Y | `rootComponent.yConstructionAxis` |
| Z | `rootComponent.zConstructionAxis` |

In Fusion 360's native API: **Y is UP**, XZ is the ground plane. The Z-negation
rules from SPATIAL_AWARENESS.md applied to the rahayesj abstraction layer only.
When writing direct Python through AuraFriday, use Fusion's native conventions.

**VERIFICATION NEEDED:** Confirm AuraFriday applies no coordinate transformation.
Record findings in VERIFICATION_LOG.md.

---

## 4. Feature Operation Enums

```python
adsk.fusion.FeatureOperations.NewBodyFeatureOperation    # 0 - New body
adsk.fusion.FeatureOperations.JoinFeatureOperation       # 1 - Add to existing
adsk.fusion.FeatureOperations.CutFeatureOperation        # 2 - Subtract
adsk.fusion.FeatureOperations.IntersectFeatureOperation  # 3 - Keep intersection
```

rahayesj only supported NewBody. AuraFriday gives all four. Still follow the
**JOIN PROTOCOL**: create as NewBody, verify placement, ask user, then combine.

---

## 5. Common Recipes

Complete, runnable Python blocks using pre-injected variables.

### 5.1 Box (Sketch + Rectangle + Extrude)

```python
import adsk.core, adsk.fusion, traceback
try:
    sketch = rootComponent.sketches.add(rootComponent.xYConstructionPlane)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-5, -3, 0),
        adsk.core.Point3D.create(5, 3, 0)
    )
    ext_input = rootComponent.features.extrudeFeatures.createInput(
        sketch.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))
    result = rootComponent.features.extrudeFeatures.add(ext_input)
    print(f"Box 10x6x2cm: {result.bodies.item(0).name}")
except:
    print(f"Error: {traceback.format_exc()}")
```

### 5.2 Cylinder (Circle + Extrude)

```python
import adsk.core, adsk.fusion, traceback
try:
    sketch = rootComponent.sketches.add(rootComponent.xYConstructionPlane)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0), 2.5
    )
    ext_input = rootComponent.features.extrudeFeatures.createInput(
        sketch.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(5.0))
    result = rootComponent.features.extrudeFeatures.add(ext_input)
    print(f"Cylinder r=2.5cm h=5cm: {result.bodies.item(0).name}")
except:
    print(f"Error: {traceback.format_exc()}")
```

### 5.3 Fillet Edges

```python
import adsk.core, adsk.fusion, traceback
try:
    body = rootComponent.bRepBodies.item(0)
    edges = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        edges.add(edge)  # Or filter by geometry type/position
    fillet_input = rootComponent.features.filletFeatures.createInput()
    fillet_input.addConstantRadiusEdgeSet(
        edges, adsk.core.ValueInput.createByReal(0.2), True
    )
    rootComponent.features.filletFeatures.add(fillet_input)
    print(f"Fillet 0.2cm on {edges.count} edges of {body.name}")
except:
    print(f"Error: {traceback.format_exc()}")
```

### 5.4 Shell (Hollow Body)

```python
import adsk.core, adsk.fusion, traceback
try:
    body = rootComponent.bRepBodies.item(0)
    # Find top face (highest Y in Fusion's Y-up system)
    top_face = max(body.faces, key=lambda f: f.centroid.y)
    faces = adsk.core.ObjectCollection.create()
    faces.add(top_face)
    shell_input = rootComponent.features.shellFeatures.createInput([body], False)
    shell_input.insideThickness = adsk.core.ValueInput.createByReal(0.15)
    shell_input.addFacesToRemove(faces)
    rootComponent.features.shellFeatures.add(shell_input)
    print(f"Shelled {body.name}: 0.15cm walls, top removed")
except:
    print(f"Error: {traceback.format_exc()}")
```

Shell API signature may vary across Fusion versions. Use `get_api_documentation`
if the above fails.

### 5.5 Boolean Operations

```python
import adsk.core, adsk.fusion, traceback
try:
    target = rootComponent.bRepBodies.item(0)
    tool = rootComponent.bRepBodies.item(1)
    tools = adsk.core.ObjectCollection.create()
    tools.add(tool)
    combine_input = rootComponent.features.combineFeatures.createInput(target, tools)
    combine_input.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
    combine_input.isKeepToolBodies = False
    rootComponent.features.combineFeatures.add(combine_input)
    print(f"Cut: {tool.name} subtracted from {target.name}")
except:
    print(f"Error: {traceback.format_exc()}")
```

Swap `CutFeatureOperation` for `JoinFeatureOperation` or `IntersectFeatureOperation`.
**JOIN PROTOCOL:** Create tool body, verify position, get user confirmation, then combine.

### 5.6 Create Component from Body

```python
import adsk.core, adsk.fusion, traceback
try:
    body = rootComponent.bRepBodies.item(rootComponent.bRepBodies.count - 1)
    occ = rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = "MyPartName"
    body.moveToComponent(occ)
    print(f"Body moved to component '{occ.component.name}'")
except:
    print(f"Error: {traceback.format_exc()}")
```

### 5.7 Export (STEP + STL)

```python
import adsk.core, adsk.fusion, traceback, os
try:
    mgr = design.exportManager
    step_path = os.path.expanduser("~/Desktop/my_part.step")
    mgr.execute(mgr.createSTEPExportOptions(step_path))
    stl_path = os.path.expanduser("~/Desktop/my_part.stl")
    stl_opts = mgr.createSTLExportOptions(rootComponent.bRepBodies.item(0), stl_path)
    stl_opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
    mgr.execute(stl_opts)
    print(f"Exported: {step_path}, {stl_path}")
except:
    print(f"Error: {traceback.format_exc()}")
```

Export is not Save. MCP cannot save to Fusion cloud storage.

### 5.8 Rectangular Pattern

```python
import adsk.core, adsk.fusion, traceback
try:
    bodies = adsk.core.ObjectCollection.create()
    bodies.add(rootComponent.bRepBodies.item(0))
    pat_input = rootComponent.features.rectangularPatternFeatures.createInput(
        bodies, rootComponent.xConstructionAxis,
        adsk.core.ValueInput.createByReal(4),
        adsk.core.ValueInput.createByReal(2.5),
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType
    )
    pat_input.setDirectionTwo(
        rootComponent.yConstructionAxis,
        adsk.core.ValueInput.createByReal(3),
        adsk.core.ValueInput.createByReal(2.5)
    )
    rootComponent.features.rectangularPatternFeatures.add(pat_input)
    print("4x3 rectangular pattern, 2.5cm spacing")
except:
    print(f"Error: {traceback.format_exc()}")
```

### 5.9 Design Inspection

```python
import adsk.core, adsk.fusion, traceback
try:
    bodies = rootComponent.bRepBodies
    print(f"Bodies: {bodies.count}")
    for i in range(bodies.count):
        b = bodies.item(i)
        bb = b.boundingBox
        print(f"  {i}: {b.name}  min({bb.minPoint.x:.2f},{bb.minPoint.y:.2f},{bb.minPoint.z:.2f}) max({bb.maxPoint.x:.2f},{bb.maxPoint.y:.2f},{bb.maxPoint.z:.2f})  F:{b.faces.count} E:{b.edges.count}")
    comps = design.allComponents
    print(f"Components: {comps.count}")
    for i in range(comps.count):
        c = comps.item(i)
        print(f"  {i}: {c.name} ({c.bRepBodies.count} bodies)")
except:
    print(f"Error: {traceback.format_exc()}")
```

Run at session start and after every operation. Face/edge indices change after
any geometry modification -- never cache them across operations.

### 5.10 Offset Construction Plane

```python
import adsk.core, adsk.fusion, traceback
try:
    plane_input = rootComponent.constructionPlanes.createInput()
    plane_input.setByOffset(
        rootComponent.xYConstructionPlane,
        adsk.core.ValueInput.createByReal(3.0)
    )
    offset_plane = rootComponent.constructionPlanes.add(plane_input)
    sketch = rootComponent.sketches.add(offset_plane)
    print("Sketch on XY + 3cm offset plane")
except:
    print(f"Error: {traceback.format_exc()}")
```

---

## 6. API Discovery

Use `get_api_documentation` operation mode to query AuraFriday's built-in reference.
Alternatively, introspect in Python:

```python
import adsk.core, adsk.fusion
print(dir(rootComponent.features))                          # Feature types
print(dir(rootComponent.features.extrudeFeatures))          # Extrude methods
print(f"Units: {design.unitsManager.defaultLengthUnits}")   # Current units
print(f"Bodies: {rootComponent.bRepBodies.count}")           # Body count
```

---

## 7. Session Management

**Start-of-session:** Run recipe 5.9, verify units are cm, confirm document name.

**Operational discipline:**
- Print after every operation (Claude has no visual feedback)
- Re-inspect before referencing geometry (indices change after any modification)
- One logical operation per execution block for clear error diagnosis
- try/except is mandatory on every block

**Crash recovery:** Re-run inspection, compare counts, re-execute lost operations.

---

## 8. Migration Reference: rahayesj to AuraFriday

| rahayesj Tool | AuraFriday Python API |
|---------------|----------------------|
| `create_sketch` | `sketches.add(plane)` |
| `draw_circle` | `sketchCircles.addByCenterRadius()` |
| `draw_rectangle` | `sketchLines.addTwoPointRectangle()` |
| `draw_line` | `sketchLines.addByTwoPoints()` |
| `draw_arc` | `sketchArcs.addByThreePoints()` |
| `draw_polygon` | `sketchLines` in a loop |
| `extrude` | `extrudeFeatures.createInput() + .add()` |
| `revolve` | `revolveFeatures.createInput() + .add()` |
| `fillet` | `filletFeatures.createInput() + .add()` |
| `chamfer` | `chamferFeatures.createInput() + .add()` |
| `shell` | `shellFeatures.createInput() + .add()` |
| `draft` | `draftFeatures.createInput() + .add()` |
| `pattern_rectangular` | `rectangularPatternFeatures` |
| `pattern_circular` | `circularPatternFeatures` |
| `mirror` | `mirrorFeatures` |
| `combine` | `combineFeatures` |
| `create_component` | `occurrences.addNewComponent()` |
| `move_component` | `occurrence.transform` matrix |
| `rotate_component` | `occurrence.transform` matrix |
| `get_body_info` | Iterate `bRepBodies`, print |
| `get_design_info` | Iterate components/bodies, print |
| `measure` | `measureManager.measureMinimumDistance()` |
| `export_stl` | `exportManager.createSTLExportOptions()` |
| `export_step` | `exportManager.createSTEPExportOptions()` |
| `export_3mf` | `exportManager.createC3MFExportOptions()` |
| `import_mesh` | `importManager.createMeshImportOptions()` |
| `finish_sketch` | Not needed (auto-finishes) |
| `fit_view` | `app.activeViewport.fit()` |
| `undo` | `design.undoManager.undo()` |
| `delete_body` | `body.deleteMe()` |
| `delete_sketch` | `sketch.deleteMe()` |
| `delete_component` | `occurrence.deleteMe()` |
| `batch` | Not needed (use one Python block) |

**Key differences from rahayesj:**
- No artificial tool boundaries -- combine operations in one script
- Full boolean support (Cut, Join, Intersect) vs. NewBody only
- No coordinate abstraction -- use Fusion's native Y-up system
- No finish_sketch or batch tool needed

---

```yaml
# Document Metadata
skill_name: aurafriday-patterns
version: 1.0.0
target_model: any-claude-model
created: 2026-02-10
last_updated: 2026-02-10
replaces: TOOL_REFERENCE.md (rahayesj 35-tool reference)
note: >
  Python examples based on Fusion 360 API patterns and AuraFriday MCP-Link
  documentation. Some recipes may need adjustment after testing against the
  actual AuraFriday runtime. Record findings in VERIFICATION_LOG.md.
```
