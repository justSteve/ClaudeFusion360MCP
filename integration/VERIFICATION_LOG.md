# Coordinate System Verification Log

**Status:** PENDING -- requires AuraFriday MCP-Link installation (Phase 1)

## Purpose

Verify that the coordinate system rules documented in SKILL.md and SPATIAL_AWARENESS.md hold when using AuraFriday MCP-Link's Python execution mode with Fusion 360's native API.

## Tests to Run

### Test 1: Z is UP
Create a box on XY plane, extrude +2cm. Verify the body extends from Z=0 to Z=2.

```python
import adsk.core, adsk.fusion

sketch = rootComponent.sketches.add(rootComponent.xYConstructionPlane)
lines = sketch.sketchCurves.sketchLines
lines.addTwoPointRectangle(
    adsk.core.Point3D.create(-1, -1, 0),
    adsk.core.Point3D.create(1, 1, 0)
)
profile = sketch.profiles.item(0)
extrudes = rootComponent.features.extrudeFeatures
ext_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))
result = extrudes.add(ext_input)

body = result.bodies.item(0)
bb = body.boundingBox
print(f"Test 1 - Z is UP:")
print(f"  Min: ({bb.minPoint.x:.2f}, {bb.minPoint.y:.2f}, {bb.minPoint.z:.2f})")
print(f"  Max: ({bb.maxPoint.x:.2f}, {bb.maxPoint.y:.2f}, {bb.maxPoint.z:.2f})")
print(f"  Expected: min=(−1,−1,0) max=(1,1,2)")
print(f"  PASS: {abs(bb.maxPoint.z - 2.0) < 0.001}")
```

### Test 2: XZ Plane Z-Negation
Create geometry on XZ plane with sketch y=−0.5 to y=−1.5. Verify it appears at World Z=0.5 to Z=1.5.

```python
import adsk.core, adsk.fusion

sketch = rootComponent.sketches.add(rootComponent.xZConstructionPlane)
lines = sketch.sketchCurves.sketchLines
lines.addTwoPointRectangle(
    adsk.core.Point3D.create(-1, -1.5, 0),
    adsk.core.Point3D.create(1, -0.5, 0)
)
profile = sketch.profiles.item(0)
extrudes = rootComponent.features.extrudeFeatures
ext_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.0))
result = extrudes.add(ext_input)

body = result.bodies.item(0)
bb = body.boundingBox
print(f"Test 2 - XZ Plane Z-Negation:")
print(f"  Min: ({bb.minPoint.x:.2f}, {bb.minPoint.y:.2f}, {bb.minPoint.z:.2f})")
print(f"  Max: ({bb.maxPoint.x:.2f}, {bb.maxPoint.y:.2f}, {bb.maxPoint.z:.2f})")
print(f"  Expected World Z: 0.5 to 1.5")
print(f"  PASS: {abs(bb.minPoint.z - 0.5) < 0.001 and abs(bb.maxPoint.z - 1.5) < 0.001}")
```

### Test 3: Units are Centimeters
Create a 2x2x2 box. Verify bounding box dimensions are 2cm on each side.

```python
# (Same as Test 1 -- verify dimensions are in cm, not mm or m)
```

## Results

| Test | Expected | Actual | Pass/Fail | Date |
|------|----------|--------|-----------|------|
| Z is UP | maxPoint.z = 2.0 | PENDING | -- | -- |
| XZ Z-Negation | Z range = 0.5 to 1.5 | PENDING | -- | -- |
| Units = cm | size = 2x2x2 | PENDING | -- | -- |

## Notes

Run these tests after completing Phase 1 installation (AuraFriday MCP-Link server + Fusion add-in). Record results here and update SKILL.md/SPATIAL_AWARENESS.md if any rules need adjustment.
