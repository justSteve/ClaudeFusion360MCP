---
name: build123d-fusion360-bridge
description: Concept mapping between Build123d and Fusion 360 API for teams transitioning CAD workflows. Identifies what transfers (intent, parameters, manufacturing awareness) and what does not (syntax, geometry construction patterns).
version: 1.0.0
last_updated: 2026-02-10
---

# Build123d to Fusion 360 Bridge

Reference for teams transitioning from Build123d (Python code-first CAD) to Fusion 360 via AuraFriday MCP-Link. The myFireplace project used Build123d for initial CAD exploration and is transitioning to Fusion 360.

---

## Concept Mapping

| Build123d Concept | Fusion 360 Equivalent | Notes |
|---|---|---|
| `BuildPart()` context | `rootComponent` / component | Fusion uses component hierarchy |
| `BuildSketch(Plane.XY)` | `sketches.add(xYConstructionPlane)` | Same concept, different syntax |
| `BuildLine()` context | Sketch curves API | `sketchCurves.sketchLines`, etc. |
| `Plane.XY.offset(5)` | Construction plane with offset | `constructionPlanes.createInput().setByOffset()` |
| `extrude(amount=2)` | `extrudeFeatures.addSimple()` or `.createInput()` | Fusion has more extrusion options |
| `mode=Mode.SUBTRACT` | `FeatureOperations.CutFeatureOperation` | Fusion uses enum, not mode parameter |
| `mode=Mode.ADD` / `Mode.INTERSECT` | `JoinFeatureOperation` / `IntersectFeatureOperation` | Full boolean support |
| `Circle(radius)` | `sketchCircles.addByCenterRadius()` | Takes Point3D + radius |
| `Rectangle(width, height)` | `sketchLines.addTwoPointRectangle()` | Takes two corner Point3D |
| `Line(start, end)` | `sketchLines.addByTwoPoints()` | Takes two Point3D |
| `RadiusArc(start, end, radius)` | `sketchArcs.addByThreePoints()` or `.addByCenterStartEnd()` | Multiple arc creation methods |
| `Polyline(points, close=True)` | Multiple `addByTwoPoints()` calls | No single polyline API |
| `make_face()` | Automatic - profiles form from closed curves | Fusion auto-detects closed regions |
| `fillet(edges, radius)` | `filletFeatures.createInput()` | Select edges, set radius |
| `chamfer(edges, distance)` | `chamferFeatures.createInput()` | Select edges, set distance |
| `shell(thickness)` | `shellFeatures.createInput()` | Select body, faces, thickness |
| `loft(sections)` | `loftFeatures.createInput()` | Add sections, rails |
| `Compound(children)` | Component with sub-components | Fusion's component tree |
| `part.rotate(Axis.Z, angle)` | Transform matrix / `move()` on occurrence | Transforms apply to occurrences |
| `part.move(Location(x,y,z))` | Transform matrix on occurrence | `occurrence.transform` |
| `show(*parts, colors)` | Automatic viewport update | Fusion updates live |
| `export("file.step")` | `exportManager.createSTEPExportOptions()` | More export control in Fusion |

---

## What Transfers

These aspects of Build123d work carry over directly to Fusion 360:

1. **Parametric mindset** -- Named constants, parameter blocks, derived dimensions. Both systems reward the habit of never hard-coding a value twice.
2. **Manufacturing awareness** -- DFM considerations, material properties, tolerances. The knowledge of what is actually buildable does not change with the tool.
3. **Design intent** -- What you are trying to build and why. Sketches-to-profiles-to-features is the same mental model.
4. **Assembly thinking** -- Component relationships, clearances, fits. Build123d's `Compound` maps to Fusion's component tree.
5. **Verification habits** -- Checking dimensions after operations. In Fusion, call `get_design_info()` or `get_body_info()` after each step.
6. **Unit discipline** -- Both use centimeters at the API level (Build123d can vary; Fusion API is always cm).

---

## What Does NOT Transfer

These require rethinking when moving to Fusion 360:

1. **Context manager pattern** -- Build123d uses `with BuildPart():` / `with BuildSketch():` to scope operations. Fusion uses explicit object creation and method chains. There is no implicit scope.
2. **Implicit current object** -- Build123d operates on the "current" part or sketch within the context manager. Fusion requires explicit references to sketches, profiles, and bodies at every step.
3. **Mode parameter for booleans** -- Build123d attaches `mode=Mode.SUBTRACT` directly to geometry creation. Fusion separates geometry creation from boolean operations. You create the body first, then combine.
4. **Wire construction** -- Build123d's `BuildLine()` context for complex profiles has no direct Fusion equivalent. Fusion auto-detects profiles from closed sketch curves; you draw the curves individually.
5. **Display/Show** -- Build123d requires explicit `show()` calls to render geometry. Fusion updates the viewport automatically after each operation.
6. **Coordinate system** -- Build123d defaults to Z-up (matching the rahayesj MCP convention). Fusion's native API uses Y-up. The rahayesj MCP abstracted this; AuraFriday exposes the native convention. See SPATIAL_AWARENESS.md for the XZ plane inversion issue.

---

## Migration Checklist

When converting a Build123d script to Fusion 360 via AuraFriday:

```
[ ] Extract parameter block (units in inches with to_cm() converter, or direct cm)
[ ] Map each BuildPart to a Fusion component
[ ] Map each BuildSketch to a Fusion sketch on the correct plane
[ ] Replace extrude/mode with separate extrude + combine operations
[ ] Replace implicit geometry targeting with explicit body/face references
[ ] Add get_design_info() verification after each major operation
[ ] Test that boolean operations (cut, join) produce correct geometry
[ ] Verify coordinate system orientation (Build123d Z-up vs Fusion Y-up)
```

---

## Example: Extrude with Boolean Cut

Build123d approach:

```python
with BuildPart() as part:
    with BuildSketch(Plane.XY):
        Rectangle(10, 10)
    extrude(amount=5)
    with BuildSketch(Plane.XY.offset(5)):
        Circle(2)
    extrude(amount=-5, mode=Mode.SUBTRACT)
```

Fusion 360 equivalent (via AuraFriday MCP-Link):

```python
# Create base sketch and extrude
sketch1 = rootComp.sketches.add(rootComp.xYConstructionPlane)
sketch1.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(-5, -5, 0),
    adsk.core.Point3D.create(5, 5, 0)
)
prof1 = sketch1.profiles.item(0)
ext1 = rootComp.features.extrudeFeatures.addSimple(
    prof1, adsk.core.ValueInput.createByReal(5.0),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)

# Create cut sketch on offset plane and subtract
planeInput = rootComp.constructionPlanes.createInput()
planeInput.setByOffset(rootComp.xYConstructionPlane,
    adsk.core.ValueInput.createByReal(5.0))
offsetPlane = rootComp.constructionPlanes.add(planeInput)
sketch2 = rootComp.sketches.add(offsetPlane)
sketch2.sketchCurves.sketchCircles.addByCenterRadius(
    adsk.core.Point3D.create(0, 0, 0), 2.0
)
prof2 = sketch2.profiles.item(0)
cutInput = rootComp.features.extrudeFeatures.createInput(
    prof2, adsk.fusion.FeatureOperations.CutFeatureOperation
)
cutInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(5.0))
rootComp.features.extrudeFeatures.add(cutInput)
```

The Fusion version is more verbose but each step is explicit and inspectable.

---

## Build123d Status

Build123d was used for the myFireplace project's initial CAD exploration. It proved that narrative-to-CAD works but revealed the agent lacks engineering depth. Fusion 360 via AuraFriday supersedes Build123d for this project because:

- Full assembly support (constraints, joints, interference checking)
- Native boolean operations with richer options than Build123d
- Simulation and CAM capabilities
- Industry-standard file formats and cloud collaboration
- The gap analysis findings (see CAD_AGENT_SKILL_GAP_ANALYSIS.md) are easier to address in Fusion's richer environment

Build123d remains valuable for rapid prototyping and code-first exploration. This bridge document exists so that knowledge from Build123d work is not lost when moving to Fusion 360.

---

```yaml
skill_name: build123d-fusion360-bridge
version: 1.0.0
created: 2026-02-10
last_updated: 2026-02-10
```
