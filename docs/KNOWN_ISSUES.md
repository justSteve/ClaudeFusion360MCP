# Known Issues and Solutions

Common pitfalls when using the Fusion 360 MCP, and how to avoid them.

---

## 1. Unit Confusion (Most Common!)

### Problem
All MCP dimensions are in **centimeters**, but users often think in millimeters.

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
1. **Always call `list_components()`** before positioning
2. Use `move_component()` after creation
3. Verify with `get_design_info()` to check positions

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
```
chamfer(edges=[...], distance=thickness/2)
```

For knife/blade edges, chamfer distance should be approximately half the material thickness.

---

## 6. Component Deletion

### Problem
Deleting a component causes index shifts, breaking subsequent operations.

### Solution
1. **Delete in reverse order** (highest index first)
2. Or delete by name, not index
3. Always re-query `list_components()` after any deletion

---

## 7. Fastener Holes

### Problem
Holes for fasteners are wrong size or position.

### Solution
Standard clearance holes (mm → cm for MCP):

| Fastener | Clearance Hole | Enter in MCP |
|----------|---------------|--------------|
| M3 | 3.4 mm | `0.34` |
| M4 | 4.5 mm | `0.45` |
| M5 | 5.5 mm | `0.55` |
| #6 | 4.0 mm | `0.40` |
| 1/4" | 7.0 mm | `0.70` |

---

## 8. Mating Parts / Interference

### Problem
Parts that should fit together either collide or have gaps.

### Solution
1. Design with **clearances** (0.2-0.5mm for 3D printing)
2. Use `measure()` to verify distances
3. Check interference with `get_body_info()` before combining

---

## 9. Session State Mismatch

### Problem
Claude assumes prior work exists, but Fusion crashed/recovered to earlier state.

### Solution
**At session start, always:**
1. Call `get_design_info()` to verify current state
2. Check body count matches expectations
3. Don't assume anything from previous sessions

---

## 10. Batch Operations

### Problem
Many small operations are slow (each has ~50ms roundtrip).

### Solution
Use `batch_operations()` for multiple related commands:
```python
batch_operations([
    {"tool": "draw_rectangle", "params": {...}},
    {"tool": "draw_circle", "params": {...}},
    {"tool": "extrude", "params": {...}}
])
```

This is 5-10x faster than individual calls.

---

*Document current as of MCP v7.2*