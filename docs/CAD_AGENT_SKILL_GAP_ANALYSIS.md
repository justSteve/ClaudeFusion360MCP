# CAD Agent Skill Gap Analysis

**Source material**: [github.com/justSteve/myFireplace](https://github.com/justSteve/myFireplace) -- all CAD scripts, design specs, session handoffs, and documentation
**Date**: 2026-02-10
**Purpose**: Identify specific gaps in AI-generated CAD code to inform skill file development for ClaudeFusion360MCP

---

## Executive Summary

The myFireplace CAD agent produces geometry that **renders correctly in a viewer** but does not reason about **manufacturing, assembly, material behavior, or geometric accuracy**. The core problem is that the agent thinks like a programmer generating shapes, not like an engineer designing parts. It writes Build123d code the way a web developer might write SVG -- syntactically valid, visually plausible, but disconnected from the physical reality the model is supposed to represent.

The agent's documentation and infrastructure choices are strong. Its geometric reasoning, manufacturing awareness, and project-level consistency are weak.

---

## Methodology

### Files Examined

**CAD Scripts** (Build123d / Python):
- `cad/corner_post_counter_to_mantel.py` -- 5-section tapered corner post (the most complex model)
- `cad/grinder_mount.py` -- angle grinder mount for cutting sled
- `cad/verify_install.py` -- environment verification script
- `cad/view_polycam_scan.py` -- Polycam STL import

**Design Specifications**:
- `designs/corner-post-geometry.md` -- corner post strip geometry and arc calculations
- `designs/router-sled-design.md` -- precision cutting sled design
- `designs/ash-removal-system.md` -- rear ash removal (text-only design)

**Session Records**:
- `docs/session-handoff-2026-02-01.md` -- detailed session handoff
- `docs/3d-infrastructure-decision.md` -- tooling selection rationale
- `docs/polycam-integration.md` -- 3D scanning workflow
- `cad/cutlist.md` -- cut dimensions for tile strips
- `CLAUDE.md` -- project-level context

---

## Finding 1: The Model Does Not Represent What Will Be Built

**Severity**: Critical
**Category**: Geometric accuracy

The corner post CAD model renders smooth 270-degree arcs. But the physical post is not a smooth arc -- it is a polygon of 9 flat tile strips arranged in a 270-degree sweep with grout lines between them. The design spec explicitly states this:

> "At 30 degrees per facet with 1/8" grout lines, the post reads as a continuous rounded surface from normal viewing distance."
> -- `designs/corner-post-geometry.md`

But `corner_post_counter_to_mantel.py` builds the geometry as smooth annular arcs:

```python
def make_constant_arc(height, radius, z_offset):
    """Constant-radius 270 arc (cylindrical)"""
    inner = radius - THICKNESS
    with BuildPart() as section:
        with BuildSketch(Plane.XY.offset(z_offset)):
            Circle(radius)
            Circle(inner, mode=Mode.SUBTRACT)
        extrude(amount=height)
```

The model then attempts to cut grout lines through the smooth arc to create "segments," but the segments remain curved. The actual strips are flat. This matters because:

1. **Fit verification is impossible** -- the model shows perfect conformance; the physical strips will have chord-to-arc gaps at each facet center.
2. **Strip width calculations are wrong** -- the model computes arc length, but the physical strip face width is a chord, not an arc. At 30 degrees per facet on a 1.7" radius, the difference between arc (0.89") and chord (0.88") is small, but it compounds with grout width tolerances.
3. **The viewer gives false confidence** -- the human sees a smooth, beautiful post and approves it, not realizing the physical result will be a 9-sided polygon with visible facet transitions at close range.

**What a sophisticated agent would do**: Model the strips as flat rectangular solids arranged at 30-degree intervals around the arc center, with grout gaps between them. Then overlay the idealized arc as a reference curve to show the deviation. This gives the user a realistic preview and enables interference checking between flat strips and any adjacent geometry.

---

## Finding 2: Grout Lines Are Radially Incorrect

**Severity**: High
**Category**: Geometric reasoning

Grout lines are cut by creating rectangular prisms at the origin and rotating them:

```python
with BuildPart() as grout_cut:
    with BuildSketch(Plane.XY.offset(base1_z - 1)):
        with Locations((0, 0)):
            Rectangle(r_cut, GROUT_WIDTH)
    extrude(amount=combined_height + 2)

grout_box = grout_cut.part.rotate(Axis.Z, avg_angle)
remaining_tier = remaining_tier - grout_box
```

Problems:

1. **Rectangles are not radial planes.** A grout line on a cylindrical surface should be a radial cut -- a thin wedge emanating from the cylinder axis, not a parallel-sided box. The result is grout lines that are the correct width on one surface (where the rectangle tangent matches the arc) but wrong everywhere else.

2. **The average angle approximation is wrong for tapered sections.** On the tapered tiers, the strip angles differ at bottom and top because the circumference changes. The code computes `avg_angle = (b_center + t_center) / 2` and uses a single rotation, producing a grout cut that is correctly positioned at the midpoint but skewed at top and bottom.

3. **The `-1` and `+2` Z offsets are clearance hacks.** Instead of computing exact bounds for the Boolean subtraction, the agent adds arbitrary padding:
   ```python
   with BuildSketch(Plane.XY.offset(base1_z - 1)):
       ...
   extrude(amount=combined_height + 2)
   ```
   This works but is fragile -- if section heights change, these magic numbers might not provide enough clearance or might extend into adjacent sections.

**What a sophisticated agent would do**: Create grout cuts as thin radial wedges (two radial lines with the grout angle between them, extruded to height). For tapered sections, use a lofted wedge between the bottom and top angular positions. Replace magic clearance values with computed bounds plus a named constant (e.g., `BOOLEAN_CLEARANCE = 0.1`).

---

## Finding 3: The 270-Degree Arc Is Built by Brute-Force Subtraction

**Severity**: Medium
**Category**: CAD idiom / best practice

Instead of constructing a 270-degree arc directly, every section builds a full 360-degree annulus then subtracts a triangular wedge:

```python
# Cut 90 degree wedge
r = radius * 2
diag = r * 0.7071
with BuildSketch(Plane.XY.offset(z_offset - 1)):
    with BuildLine():
        Line((0, 0), (-diag, diag))
        Line((-diag, diag), (-diag, -diag))
        Line((-diag, -diag), (0, 0))
    make_face()
extrude(amount=height + 2, mode=Mode.SUBTRACT)
```

The session handoff acknowledges this was a workaround: "Build123d's wire-based arc construction had closure issues. Solution: create full annulus, then subtract a triangular 90-degree wedge."

This is understandable as a pragmatic workaround, but it reveals the agent hit a wall in Build123d's API and chose the brute-force path rather than understanding the wire closure issue. In Build123d, a 270-degree arc sector can be constructed with:

```python
with BuildSketch() as arc_profile:
    with BuildLine():
        RadiusArc(start_point, end_point, radius)
        RadiusArc(inner_end, inner_start, -inner_radius)
        Line(start_point, inner_start)
        Line(inner_end, end_point)
    make_face()
```

The subtraction approach adds unnecessary Boolean operations (expensive, and each one risks tolerance issues in the BREP kernel), hardcodes `0.7071` instead of using `math.cos(math.pi/4)`, and uses another magic clearance (`height + 2`).

**What a sophisticated agent would do**: Construct the 270-degree profile directly using arc primitives. If wire closure is problematic, debug it (the issue is usually endpoint coincidence tolerance) rather than route around it with subtractions.

---

## Finding 4: No Manufacturing Awareness in the Grinder Mount

**Severity**: High
**Category**: Manufacturing / fabrication

The `grinder_mount.py` is impressively documented -- it has parameter tables, measurement warnings, and a detailed output summary. But the geometry ignores manufacturing realities:

### L-Bracket Fabrication

```python
with BuildSketch(Plane.XZ):
    with BuildLine():
        Polyline([
            (0, 0),
            (BRACKET_HORIZONTAL, 0),
            (BRACKET_HORIZONTAL, BRACKET_VERTICAL),
            (BRACKET_HORIZONTAL - BRACKET_STEEL, BRACKET_VERTICAL),
            (BRACKET_HORIZONTAL - BRACKET_STEEL, BRACKET_STEEL),
            (0, BRACKET_STEEL),
        ], close=True)
    make_face()
extrude(amount=BRACKET_WIDTH)
```

This models the L-bracket as a monolithic extrusion from a sharp-cornered L-profile. In reality:

- **If bent from plate**: There is a bend radius at the inside corner (minimum 1x material thickness for 1/4" steel = 0.25" radius). The sharp inner corner in the model is unfabricable.
- **If welded from two plates**: The weld joint geometry is missing, and the fillet at the inside corner from the weld bead changes the geometry.
- **If machined from billet**: The inside corner needs a relief cut for the end mill radius.

The agent never asks "how will this be made?" It just draws the shape.

### Shaft Collar Clamp

```python
collar_id = MOTOR_BODY_DIA + 1.0   # clearance
collar_od = MOTOR_BODY_DIA + 14.0  # 6.5mm wall
```

A 1mm radial clearance on a split collar is not a design decision -- it is an arbitrary number. Split collar design requires:
- Enough clearance to slide over the body before tightening
- Enough clamping range to close the split and grip
- Bolt force calculation to achieve the required clamping friction
- Consideration of whether the collar will mar the grinder body

None of this is modeled or even discussed.

### Missing Structural Considerations

The angle grinder generates significant lateral forces during cutting (~5-15 lbs depending on feed rate and blade condition). The 1/4" steel L-brackets at the modeled span have no gussets, no stiffening, no analysis of deflection. The `BRACKET_STANDOFF = 5.0` mm gap between bracket and gear head suggests no structural intent -- it is just "clearance."

**What a sophisticated agent would do**: Include fabrication method in the parameter block (bent, welded, or machined). Add bend radii or weld fillets to the model. Flag structural concerns in comments. Reference standard tolerances (ISO 273 for bolt holes, for example) rather than ad-hoc clearance values.

---

## Finding 5: Dimension Drift Across Documents

**Severity**: High
**Category**: Project management / consistency

Three documents give three different dimension sets for the same corner post:

| Parameter | `corner-post-geometry.md` | `session-handoff` | `corner_post_counter_to_mantel.py` |
|-----------|--------------------------|--------------------|------------------------------------|
| Strip count | 9 | 12 (cutlist) | 12 (`N_STRIPS = 12`) |
| Bottom radius | 1.7" | 2.3" | 4.0" (`WIDE_RADIUS`) |
| Top radius | 1.7" (constant) | 1.4" | 2.8" (`TIER1_TOP`) |
| Strip width | 13/16" | 1.5" bottom | 1.5" bottom |
| Tier2 behavior | Not specified | Tapered 1.7" to 1.4" | Constant at 2.5" |

The design spec describes a simple, constant-radius post (9 strips, ~1.7" radius). The CAD model builds something completely different (12 strips, 4.0" radius tapering to 2.8", with a separate constant tier). The session handoff describes yet another geometry (2.3" to 1.4" with a 0.2" step-in).

The `taper_demo.py` file referenced by the session handoff as the "main model" does not exist in the repository. The handoff says `corner_post_counter_to_mantel.py` is "superseded" but it contains the most complete code.

**What a sophisticated agent would do**: Maintain a single parametric source of truth (one Python file with all dimensions) and generate derived documents (cutlist, handoff dimensions) from that source. Flag conflicts when dimensions in prose don't match code. Never allow three documents to define the same geometry with different numbers.

---

## Finding 6: No Surface Development Analysis

**Severity**: High
**Category**: Geometric reasoning / manufacturing

The project involves cutting flat ceramic tile strips and adhering them to a conical (tapered) surface. This is a surface development problem -- mapping a 2D flat shape onto a 3D curved surface. The agent never addresses it.

The cutlist describes the cutting approach:

> "The 1.8 degree taper is introduced by angling the tile on the bed fixture... Each straight-line pass cuts at slight angle across tile face... Result: trapezoidal strip (wider at one end)"
> -- `cad/cutlist.md`

But a flat trapezoid does not map onto a conical surface without distortion. For a cone with the post's geometry (8" height, 4.0" to 2.8" radius change), the true developed strip shape is a trapezoid with slightly curved edges (arcs of the cone's development). The straight-edge trapezoid from the cutting sled is an approximation.

At these dimensions, the approximation error is small (fractions of a millimeter over an 8" strip). But the agent never performs this analysis. It does not:
- Compute the cone's half-angle
- Develop the conical surface to a flat pattern
- Compare the true developed strip shape to the straight-cut trapezoid
- Quantify the error and confirm it is within tolerance (grout can absorb it, or it cannot)

This is the kind of analysis that separates a CAD technician from a CAD engineer. The agent operates at the technician level.

**What a sophisticated agent would do**: Compute the developed surface, overlay the cutting geometry, quantify the approximation error, and explicitly state "the straight-cut approximation introduces X mm of error at the strip edges, which is within the Y mm grout tolerance" or flag it as a problem.

---

## Finding 7: No Assembly Hierarchy

**Severity**: Medium
**Category**: CAD best practice

Both scripts build all parts as loose `Part` objects and display them with `show()`. There is no component tree, no assembly structure, no joints or constraints between parts.

```python
# From corner_post_counter_to_mantel.py
parts = []
colors = []
names = []
# ... build parts, append to lists ...
show(*parts, colors=colors, names=names)
```

Build123d supports assemblies:

```python
from build123d import *

post_assembly = Compound(children=[base1, tier1, base2, tier2, cap])
# Or using the Assembly class for positioned components
```

Without assembly structure:
- Parts cannot be repositioned relative to each other
- There is no interference checking between sections
- Exploded views for manufacturing documentation are not possible
- Individual sections cannot be isolated for export
- The model cannot represent the assembly sequence (base goes on first, then tier1, etc.)

The grinder mount is worse -- the grinder reference geometry, brackets, collar, and base plate are all loose parts with manual `move(Location(...))` positioning. Change one dimension and multiple manual moves need updating.

**What a sophisticated agent would do**: Build an assembly tree. Position child components using constraints (e.g., "base2 sits on top of tier1" rather than `z_offset = BASE1_HEIGHT + TIER1_HEIGHT`). Enable exploded view generation and per-component export.

---

## Finding 8: Bolt Hole Tolerances Are Ad-Hoc

**Severity**: Medium
**Category**: Manufacturing standards

```python
# grinder_mount.py
Circle(4.25)  # 8.5mm clearance holes for M8 bolts
Circle(HANDLE_THREAD / 2 + 0.5)  # M10 + clearance
Circle(3.5)  # M6 clearance
```

These clearance values are close to correct but appear to be guessed rather than referenced from standards:

| Bolt | Modeled Hole | ISO 273 Medium Fit | ISO 273 Close Fit |
|------|-------------|--------------------|--------------------|
| M6 | 7.0mm | 6.6mm | 6.4mm |
| M8 | 8.5mm | 9.0mm | 8.4mm |
| M10 | 11.0mm | 11.0mm | 10.5mm |

The M8 hole is actually undersized (8.5mm vs 9.0mm medium fit). The M6 hole is oversized (7.0mm vs 6.6mm). The M10 hole happens to match medium fit exactly.

An agent guessing "+0.5mm" or "+1mm" clearance will get lucky sometimes and produce non-functional holes other times. The M8 hole at 8.5mm might not pass an M8 bolt head (which is 13mm across flats) -- but that is a separate issue; the 8.5mm is for the shank, and M8 shank at 8mm fits through 8.5mm, so it works, just tighter than standard.

**What a sophisticated agent would do**: Reference ISO 273 (or ASME B18.2.8 for imperial) explicitly in comments. Use named constants: `M8_CLEARANCE_MEDIUM = 9.0` rather than computing `4.25` (which obscures the bolt size and fit class).

---

## What the Agent Does Well

Credit where due -- several aspects of the agent's work are above average:

1. **Infrastructure selection**: The Build123d + OCP CAD Viewer + WSL stack was a well-reasoned choice, documented with a clear decision matrix. The agent correctly identified that code-first CAD with in-IDE visualization was the right workflow for AI-human collaboration.

2. **Parametric mindset**: All scripts use named constants at the top of the file. Dimensions are not buried in geometry calls. This is correct practice.

3. **Loft over extrusion**: The session handoff explicitly discusses why loft produces true tapered surfaces while extrusion produces stepped cylinders. The agent understood this distinction and chose correctly.

4. **Documentation quality**: Session handoffs, design specs, and inline comments are thorough. The grinder mount's parameter block with "MEASURE YOUR GRINDER" warnings shows awareness that the model is provisional.

5. **Visualization**: Color-coding parts, naming them in the viewer tree, and using semi-transparent reference geometry (grinder body at 40% opacity) are good practices for communicating design intent.

6. **Iterative approach**: The git history shows progressive refinement (stepped model superseded by tapered model, overhang added, tier offset added). The agent is willing to throw away earlier approaches.

---

## Recommended Skill Requirements

Based on these findings, a CAD agent skill file should enforce the following capabilities:

### Tier 1: Must-Have (blocks basic errors)

1. **Model vs Reality Check** -- Before completing any model, the agent must state what physical form the geometry represents and whether the model accurately depicts it (smooth arc vs polygon of flat strips, for example).

2. **Manufacturing Method Declaration** -- Every fabricated part must include a comment block stating the intended manufacturing method (bent, welded, machined, cast, cut, adhered) and the agent must add features appropriate to that method (bend radii, weld fillets, tool access, etc.).

3. **Single Source of Truth** -- All dimensions must derive from one parameter block. Derived documents (cutlists, handoffs) must be generated from or explicitly reference that block. Conflicting dimensions across documents must be flagged as errors.

4. **Standard Tolerances** -- Bolt holes, clearances, and fits must reference named standards (ISO 273, ASME B18.2.8) rather than ad-hoc values.

### Tier 2: Should-Have (elevates quality)

5. **Assembly Structure** -- Multi-part models must use assembly hierarchy with constraint-based positioning rather than manual offsets.

6. **Surface Development** -- Any design that maps flat material onto curved surfaces must include a surface development analysis quantifying the approximation error.

7. **Structural Flagging** -- Parts under load (brackets, mounts, clamps) must include a comment estimating the expected forces and whether the cross-section is adequate. Full FEA is not required, but back-of-envelope checks are.

8. **Radial Construction** -- Features on cylindrical or conical surfaces (grout lines, slots, holes) must use radial geometry, not rotated Cartesian shapes.

### Tier 3: Nice-to-Have (professional grade)

9. **DFM Feedback** -- The agent should flag designs that are difficult or expensive to manufacture (sharp inside corners on bends, undercuts requiring 5-axis machining, wall thicknesses below material minimums).

10. **Export-Ready Models** -- Each component should be independently exportable as STEP/STL without manual extraction from the scene.

11. **Dimensional Inspection Points** -- The model should identify critical dimensions that the human should verify with calipers before proceeding (the grinder mount does this in prose; it should be built into the model's output).

---

## Appendix: Code Samples with Suggested Improvements

### A. Flat-Facet Strip Model (replaces smooth arc)

```python
# CURRENT: Smooth arc (does not represent physical reality)
Circle(radius)
Circle(inner, mode=Mode.SUBTRACT)

# IMPROVED: Flat facets at correct angular intervals
N_STRIPS = 9
ARC_SPAN = 270  # degrees
STRIP_ANGLE = ARC_SPAN / N_STRIPS  # 30 degrees per strip
START_ANGLE = -135  # center arc around -X axis

for i in range(N_STRIPS):
    angle = START_ANGLE + i * STRIP_ANGLE
    # Each strip is a flat rectangular solid, positioned tangent to the arc
    strip_center_angle = angle + STRIP_ANGLE / 2
    cx = radius * cos(radians(strip_center_angle))
    cy = radius * sin(radians(strip_center_angle))
    # Build flat strip at origin, rotate into position
    with BuildPart() as strip:
        Box(THICKNESS, strip_face_width, height)
    strip_part = strip.part.rotate(Axis.Z, strip_center_angle)
    strip_part = strip_part.move(Location((cx, cy, z_offset)))
```

### B. Radial Grout Cut (replaces rotated rectangle)

```python
# CURRENT: Rotated rectangle (wrong geometry)
Rectangle(r_cut, GROUT_WIDTH)
# rotated to avg_angle

# IMPROVED: Radial wedge (correct geometry)
grout_half_angle = (GROUT_WIDTH / (2 * math.pi * radius)) * 360 / 2
with BuildSketch(Plane.XY.offset(z_offset)):
    with BuildLine():
        Line((0, 0), polar(r_cut, angle - grout_half_angle))
        Line(polar(r_cut, angle - grout_half_angle),
             polar(r_cut, angle + grout_half_angle))
        Line(polar(r_cut, angle + grout_half_angle), (0, 0))
    make_face()
extrude(amount=height)
```

### C. Named Standard Clearances (replaces ad-hoc values)

```python
# CURRENT: Ad-hoc clearance
Circle(4.25)  # 8.5mm clearance holes for M8 bolts

# IMPROVED: Named standard reference
# ISO 273 clearance holes
CLEARANCE_HOLES = {
    "M6": {"close": 6.4, "medium": 6.6, "coarse": 7.0},
    "M8": {"close": 8.4, "medium": 9.0, "coarse": 10.0},
    "M10": {"close": 10.5, "medium": 11.0, "coarse": 12.0},
}
FIT_CLASS = "medium"

Circle(CLEARANCE_HOLES["M8"][FIT_CLASS] / 2)  # ISO 273 medium fit
```

---

## Conclusion

The myFireplace CAD agent is a competent code generator that produces valid Build123d scripts with good parametric structure and documentation. Its weakness is that it does not reason about the physical world the model represents. It generates geometry that satisfies the viewer; it does not generate geometry that satisfies the shop floor.

The gap is not in programming skill -- the code works. The gap is in domain knowledge: manufacturing processes, material behavior, assembly relationships, geometric accuracy, tolerances, and standards. These are teachable through skill files, and the ClaudeFusion360MCP project is the right vehicle to deliver them.

The most impactful single improvement would be **Tier 1, Item 1: Model vs Reality Check** -- requiring the agent to explicitly state whether its model represents the physical form or an idealization, before the human signs off on it. This one check would have caught the smooth-arc-vs-flat-strip issue, which is the most consequential error in the current codebase.
