---
name: engineering-literacy-cad
description: Engineering reasoning protocols for CAD agents. Addresses the gap between syntactically valid geometry and physically meaningful designs. Teaches manufacturing awareness, dimensional consistency, assembly hierarchy, and model-vs-reality verification.
version: 1.0.0
model_target: any-claude-model
companion_skills:
  - SKILL.md
  - SPATIAL_AWARENESS.md
  - AURAFRIDAY_PATTERNS.md
last_updated: 2026-02-10
---

# Engineering Literacy for CAD Agents v1.0

## Preamble: Why This Skill Exists

AI CAD agents produce geometry that satisfies the viewer but not the shop floor. The models render correctly, the code compiles, the bounding boxes pass verification -- and the part is still wrong. The gap is not in programming. The gap is in domain knowledge: manufacturing processes, material behavior, assembly relationships, tolerances, surface development, and engineering standards.

A programmer generating shapes thinks: "Does the geometry exist in the right location with the right dimensions?" An engineer designing parts thinks: "Can this be built? Will it fit? Will it survive the loads? Does the model faithfully represent the physical thing?"

This skill file enforces engineering reasoning before and during modeling. It layers on top of SKILL.md and SPATIAL_AWARENESS.md. Load all three for any serious CAD work.

**Source analysis**: Every rule here addresses a real failure mode observed in the myFireplace CAD audit. See `CAD_AGENT_SKILL_GAP_ANALYSIS.md` for the full findings.

**Execution context**: All code examples target the Fusion 360 API via AuraFriday MCP-Link (`adsk.core`, `adsk.fusion` namespaces). All dimensions use centimeters unless stated otherwise.

---

## Section 1: Model vs Reality Protocol

### 1.1 The Core Problem

An agent asked to model "a 270-degree tiled corner post" builds a smooth annular arc. The physical post is a 9-sided polygon of flat tile strips with grout lines. The agent never states that the model is an idealization. The human approves a smooth rendering; the physical result is a faceted polygon.

### 1.2 Mandatory Check

Before completing ANY model, execute this protocol:

**State the physical form.** Not "a bracket" but "an L-bracket bent from 1/4-inch A36 steel plate."

**State the simplifications.** Smooth arcs vs flat facets? Sharp corners vs bend radii? Missing fastener holes? Uniform thickness vs weld buildup?

**Quantify the discrepancies.** Not "the error is small" but "the chord-to-arc deviation is 0.25mm at facet center, within the 3mm grout tolerance."

**Inform the user** before sign-off.

### 1.3 Checklist

```
[ ] Physical form stated
[ ] Simplifications listed
[ ] Discrepancies quantified (numbers, not adjectives)
[ ] User informed of idealizations
```

### 1.4 Example

```
MODEL VS REALITY ASSESSMENT
Physical form: 270-degree corner post, 9 flat subway tile strips at 30-degree
  intervals, 1.70" outer radius, 1/8" grout lines.
Simplifications:
  1. Model uses smooth arcs; physical post is a 9-sided polygon
  2. Grout cuts are rectangular; physical grout lines are radial wedges
  3. Adhesive layer (1-2mm) not modeled
Discrepancies:
  1. Chord-to-arc deviation: ~0.25mm (within 3mm grout tolerance)
  2. Grout cut width error at outer radius: 0.4mm
  3. Missing adhesive shifts outer face outward ~1.5mm
```

---

## Section 2: Manufacturing Method Declaration

Every fabricated part gets a manufacturing header block. Not optional.

```python
# === MANUFACTURING DECLARATION ===
# Method: Bent from plate
# Material: ASTM A36 hot-rolled steel, 1/4" (6.35mm) plate
# Tolerance: +/-0.5mm (plasma cut), +/-0.1mm (machined)
# Bend radii: 1x material thickness minimum (6.35mm)
# Finish: Mill scale, no coating
```

### 2.1 Method-Specific Rules

**If bent:** Add bend radii to ALL inside corners. Minimums: 1x thickness (steel), 0.5x (aluminum), 2x (stainless). Never model a sharp inside corner on a bent part.

```python
# WRONG: Sharp corner -- unfabricable as a bent part
lines.addByTwoPoints(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(5.0,0,0))
lines.addByTwoPoints(adsk.core.Point3D.create(5.0,0,0), adsk.core.Point3D.create(5.0,3.0,0))

# RIGHT: Include bend radius
MATERIAL_THICKNESS = 0.635  # cm (1/4 inch)
BEND_RADIUS = MATERIAL_THICKNESS  # 1x thickness for A36
# Horizontal flange stops short, arc bridges to vertical flange
arcs.addByCenterStartSweep(
    adsk.core.Point3D.create(5.0 - BEND_RADIUS, BEND_RADIUS, 0),
    adsk.core.Point3D.create(5.0 - BEND_RADIUS, 0, 0),
    math.pi / 2
)
```

**If welded:** Note joint type. Add weld fillets if they affect clearance. Flag weld distortion on thin stock (<3mm, >300mm length).

**If machined:** Inside corners need end mill relief. All inside radii >= tool_radius.

**If cast:** Draft angles (1 degree/inch minimum). Fillets on all inside corners. Min wall: 3mm aluminum, 4mm steel.

**If 3D printed:** Reference Section 4.4 tolerances. Note overhangs >45 degrees (FDM). Note bridge spans >10mm.

**If adhesive-applied:** Note substrate prep, working time, and whether flat-on-curved triggers Section 6 analysis. Never ignore adhesive thickness.

### 2.2 Hard Rules

- NEVER model a sharp inside corner on a bent part.
- NEVER ignore the difference between bent and machined L-brackets (different corner geometry).
- NEVER omit the manufacturing header. Ask the user if you do not know the method.

---

## Section 3: Single Source of Truth

All dimensions from ONE parameter block. No magic numbers. No duplicated constants.

### 3.1 Parameter Block Template

```python
import math

# === DIMENSIONAL PARAMETERS (Single Source of Truth) ===
# All dimensions in inches. Fusion 360 API uses cm: multiply by 2.54.

POST_ARC_SPAN = 270       # degrees - total arc coverage
N_STRIPS = 9              # tile strips in arc
STRIP_ANGLE = POST_ARC_SPAN / N_STRIPS  # 30 degrees per strip
OUTER_RADIUS = 1.70       # inches - to outer tile face
TILE_THICKNESS = 0.25     # inches - 6mm subway tile
INNER_RADIUS = OUTER_RADIUS - TILE_THICKNESS  # 1.45 inches
GROUT_WIDTH = 0.125       # inches - 1/8" grout lines
BOOLEAN_CLEARANCE = 0.1   # cm - clearance for clean boolean operations

# Derived
STRIP_FACE_WIDTH = 2 * OUTER_RADIUS * math.sin(math.radians(STRIP_ANGLE / 2))
# = 0.882 inches (chord, NOT arc)

def to_cm(inches):
    """Convert inches to centimeters for Fusion 360 API."""
    return inches * 2.54
```

### 3.2 Rules

- Every constant MUST have units in its comment.
- Derived dimensions MUST reference parent constants, not restate values.
- Boolean clearance MUST be a named constant, not a magic number.
- Conflicting dimensions across documents: flag as error, ask user to resolve.

### 3.3 Anti-Patterns

```python
# BAD: Magic numbers
extrude(amount=height + 2)   # What is 2? Why 2?
sketch_offset = base1_z - 1  # Why -1?

# GOOD: Named clearance
extrude(amount=height + BOOLEAN_CLEARANCE)
sketch_offset = base1_z - BOOLEAN_CLEARANCE
```

---

## Section 4: Standard Tolerances

Never guess clearances. Reference standards. Default to medium fit when user does not specify. Mark any non-standard clearance "ad-hoc -- verify."

### 4.1 ISO 273 Bolt Clearance Holes (Metric)

| Bolt | Close Fit | Medium Fit | Coarse Fit |
|------|-----------|------------|------------|
| M3   | 3.2mm     | 3.4mm      | 3.6mm      |
| M4   | 4.3mm     | 4.5mm      | 4.8mm      |
| M5   | 5.3mm     | 5.5mm      | 5.8mm      |
| M6   | 6.4mm     | 6.6mm      | 7.0mm      |
| M8   | 8.4mm     | 9.0mm      | 10.0mm     |
| M10  | 10.5mm    | 11.0mm     | 12.0mm     |
| M12  | 13.0mm    | 13.5mm     | 14.5mm     |

### 4.2 Press Fit / Interference Fit

| Fit Type     | Clearance/Interference Per Side |
|--------------|-------------------------------|
| Sliding fit  | +0.025 to +0.075mm            |
| Location fit | 0 to +0.025mm                 |
| Light press  | -0.005 to -0.025mm            |
| Heavy press  | -0.025 to -0.050mm            |

Note: Same-material press fits (aluminum into aluminum) will gall. Flag it.

### 4.3 3D Print Tolerances

| Process | XY Accuracy | Z Accuracy | Min Feature |
|---------|------------|------------|-------------|
| FDM     | +/-0.5mm   | +/-0.2mm   | 0.8mm       |
| SLA     | +/-0.15mm  | +/-0.1mm   | 0.3mm       |
| SLS     | +/-0.3mm   | +/-0.2mm   | 0.5mm       |

### 4.4 Sheet Metal Bend Radii

| Material        | Min Inside Radius   | Springback   |
|-----------------|---------------------|--------------|
| Mild steel      | 1.0x thickness      | 2-5 degrees  |
| Stainless steel | 2.0x thickness      | 5-10 degrees |
| Aluminum 6061   | 0.5x thickness      | 1-3 degrees  |

### 4.5 Implementation

```python
ISO_273_CLEARANCE = {
    "M6":  {"close": 6.4,  "medium": 6.6,  "coarse": 7.0},
    "M8":  {"close": 8.4,  "medium": 9.0,  "coarse": 10.0},
    "M10": {"close": 10.5, "medium": 11.0, "coarse": 12.0},
    "M12": {"close": 13.0, "medium": 13.5, "coarse": 14.5},
}

def bolt_clearance_radius_cm(bolt_size, fit="medium"):
    """Return clearance hole RADIUS in cm for Fusion 360 API."""
    diameter_mm = ISO_273_CLEARANCE[bolt_size][fit]
    return (diameter_mm / 2) / 10  # mm diameter to cm radius

# Usage
circles.addByCenterRadius(
    adsk.core.Point3D.create(bolt_x, bolt_y, 0),
    bolt_clearance_radius_cm("M8")  # ISO 273 medium fit: 9.0mm dia
)

# NEVER this:
circles.addByCenterRadius(point, 0.425)  # 8.5mm -- WHERE FROM?
```

---

## Section 5: Assembly Structure

Components, not loose bodies.

### 5.1 Rules

- Multi-part models MUST use component hierarchy.
- Each component gets its own sketches, features, and body.
- Position using parametric offsets from the parameter block, not manual coordinates.
- Create components in assembly order (install order).
- Name every component descriptively.

### 5.2 Hierarchy Template

```
Root Component
+-- Base Assembly
|   +-- Base Plate (steel)
|   +-- Mounting Bracket Left (steel, bent)
|   +-- Mounting Bracket Right (steel, bent)
+-- Clamp Assembly
|   +-- Split Collar Upper (aluminum)
|   +-- Split Collar Lower (aluminum)
+-- Fasteners (reference geometry)
    +-- M8 Bolts x4
    +-- M6 Bolts x2
```

### 5.3 Parametric Positioning

```python
# GOOD: Derived from parameter block
PLATE_HEIGHT = to_cm(0.25)
BRACKET_Z = PLATE_HEIGHT  # sits on plate
CLAMP_Z = BRACKET_Z + BRACKET_HEIGHT  # sits on bracket

transform = adsk.core.Matrix3D.create()
transform.translation = adsk.core.Vector3D.create(0, 0, BRACKET_Z)
bracket_occ.transform = transform
# If PLATE_HEIGHT changes, everything updates.

# BAD: Hardcoded absolute positions
move_component(x=12.5, y=0, z=7.3, name="Bracket")
# Breaks when any upstream dimension changes.
```

---

## Section 6: Surface Development

When flat material maps onto curved surfaces, quantify the approximation error.

### 6.1 Cylinder: Chord vs Arc

```
Arc length:   L_arc   = R * theta
Chord length: L_chord = 2 * R * sin(theta / 2)
Error:        L_arc - L_chord
```

For small facet angles (<15 degrees), the error is negligible. For larger angles, compute and state it.

### 6.2 Cone Development

```
Cone half-angle:  alpha = atan((R_bottom - R_top) / height)
Slant height:     S = height / cos(alpha)
Development radius: r_dev = R_bottom / sin(alpha)
Developed strip width at bottom: W = r_dev * theta * sin(alpha)
```

A straight-cut trapezoid approximates the true developed shape (which has curved edges). Error increases with strip angle, cone angle, and slant height.

### 6.3 Mandatory Statement

Any time the agent models flat material on a curved surface:

```
SURFACE DEVELOPMENT NOTE:
  The straight-cut approximation introduces [X] mm of error at strip edges.
  This [is within / exceeds] the [Y] mm tolerance.
```

### 6.4 Example

```python
import math
R_BOTTOM, R_TOP, H = 1.70, 1.40, 8.0  # inches
STRIP_ANGLE = 30  # degrees
alpha = math.atan((R_BOTTOM - R_TOP) / H)
slant = H / math.cos(alpha)
r_dev = R_BOTTOM / math.sin(alpha) if alpha > 0.001 else float('inf')
theta_dev = math.radians(STRIP_ANGLE) * math.sin(alpha)
W_true = r_dev * theta_dev           # arc (true shape)
W_chord = 2 * r_dev * math.sin(theta_dev / 2)  # chord (straight cut)
error_mm = abs(W_true - W_chord) * 25.4
print(f"Error: {error_mm:.3f} mm")    # Compare against grout tolerance
```

---

## Section 7: Structural Flagging

Parts under load get force estimates. Not FEA -- back-of-envelope checks.

### 7.1 Template

```python
# === STRUCTURAL ASSESSMENT ===
# Part: Angle grinder mounting bracket
# Span: 150mm between bolts
# Material: A36 steel, 1/4" x 2" (6.35 x 50.8mm)
# Expected load: 50-70N lateral from grinding
#
# I = (b * h^3) / 12 = 1084 mm^4
# sigma = M/S = (70*150/4) / (1084/3.175) = 7.7 MPa
# A36 yield = 250 MPa -- safety factor 32x (adequate)
# Deflection: F*L^3/(48*E*I) = 0.023mm (negligible)
#
# CONCLUSION: Adequate. No gussets needed at this span/load.
```

### 7.2 Rules

- Never model a bracket or mount without stating expected load.
- If load is unknown: state "load unknown -- assessment deferred to user."
- If stress > 50% yield: recommend thicker stock or gussets.
- If deflection > 0.5mm on a precision surface: flag it.
- Bolted joints: bolt shear capacity must exceed load by 3x minimum.

---

## Section 8: Radial Construction

Features on cylindrical/conical surfaces use radial geometry.

### 8.1 Visual Comparison

```
CORRECT: Radial wedge          INCORRECT: Rotated rectangle
  (thin at center,               (constant width,
   widens toward outside)         wrong everywhere except tangent)

       / \                           |  |
      /   \                          |  |
     /     \                         |  |
    /       \                        |  |
   /    *    \                       |  |
```

A rotated rectangle is the correct width at exactly one point. It is too wide at the outer face and too narrow at the inner face.

### 8.2 Correct Radial Wedge

```python
# Radial grout cut -- two radial lines separated by grout angle
grout_half_angle = math.degrees(math.atan((GROUT_WIDTH / 2) / OUTER_RADIUS))
angle_lo = math.radians(GROUT_ANGLE_DEG - grout_half_angle)
angle_hi = math.radians(GROUT_ANGLE_DEG + grout_half_angle)
r_inner = to_cm(OUTER_RADIUS - CUT_DEPTH)
r_outer = to_cm(OUTER_RADIUS + 0.1)

p1 = adsk.core.Point3D.create(r_inner * math.cos(angle_lo), r_inner * math.sin(angle_lo), 0)
p2 = adsk.core.Point3D.create(r_outer * math.cos(angle_lo), r_outer * math.sin(angle_lo), 0)
p3 = adsk.core.Point3D.create(r_outer * math.cos(angle_hi), r_outer * math.sin(angle_hi), 0)
p4 = adsk.core.Point3D.create(r_inner * math.cos(angle_hi), r_inner * math.sin(angle_hi), 0)
lines.addByTwoPoints(p1, p2)
lines.addByTwoPoints(p2, p3)
lines.addByTwoPoints(p3, p4)
lines.addByTwoPoints(p4, p1)
```

### 8.3 Hole Patterns: Use Polar Coordinates

```python
# RIGHT: Parametric polar array
N_BOLTS = 8
BOLT_CIRCLE_RADIUS = to_cm(2.5)
for i in range(N_BOLTS):
    angle = math.radians(i * (360 / N_BOLTS))
    bx = BOLT_CIRCLE_RADIUS * math.cos(angle)
    by = BOLT_CIRCLE_RADIUS * math.sin(angle)
    circles.addByCenterRadius(adsk.core.Point3D.create(bx, by, 0),
                               bolt_clearance_radius_cm("M8"))
```

Or use Fusion 360's `circularPatternFeatures` on a single hole.

### 8.4 Hard Rules

- Grout lines on cylinders: radial wedges, NOT rotated rectangles.
- Hole patterns: polar coordinates or circular pattern feature.
- Tapered surfaces: lofted radial geometry between top and bottom positions.
- NEVER approximate a radial feature with a rotated rectangular solid.

---

## Appendix: Pre-Modeling Checklist

```
ENGINEERING LITERACY CHECKLIST
==============================
1. MODEL VS REALITY
   [ ] Physical form stated
   [ ] Simplifications listed
   [ ] Discrepancies quantified

2. MANUFACTURING
   [ ] Header block written
   [ ] Method-specific features added (bend radii, draft, fillets)
   [ ] Material and finish specified

3. DIMENSIONS
   [ ] Single parameter block, no magic numbers
   [ ] Units in every comment
   [ ] Derived values reference parents

4. TOLERANCES
   [ ] Bolt holes per ISO 273
   [ ] Fit class stated
   [ ] Ad-hoc values flagged

5. ASSEMBLY (if multi-part)
   [ ] Component hierarchy used
   [ ] Every component named
   [ ] Positions from parameter block

6. SURFACE DEVELOPMENT (if flat-on-curved)
   [ ] Approximation error quantified
   [ ] Error vs tolerance stated

7. STRUCTURAL (if load-bearing)
   [ ] Expected forces stated
   [ ] Cross-section assessed
   [ ] Deflection estimated

8. RADIAL (if cylindrical/conical)
   [ ] Radial construction used
   [ ] No rotated rectangles
```

---

## Document Metadata

```yaml
skill_name: engineering-literacy-cad
version: 1.0.0
target_model: any-claude-model
companion_skills:
  - SKILL.md
  - SPATIAL_AWARENESS.md
  - AURAFRIDAY_PATTERNS.md
created: 2026-02-10
last_updated: 2026-02-10
source_analysis: CAD_AGENT_SKILL_GAP_ANALYSIS.md
changelog:
  v1.0.0: Initial release based on myFireplace gap analysis
```

---

*End of Engineering Literacy for CAD Agents v1.0*
